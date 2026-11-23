"""Stages of a mesh build cached on disk (agent rule «Fast iteration»: a fix rebuilds only what is downstream of it).

    st = Stages(os.path.join(OUT, ".cache"), deps=[files...], tag="full")   # out/.cache/full, out/.cache/shared
    base = st.run("carcass", st_carcass)                 # computed once, then read back from the cache
    band = st.run("band", st_band, outline, body)        # rebuilt when its inputs or its own parameters change
    st.report()

A stage's key is the hash of:
- its function's source, and every module-level value and same-module function it names (recursively: a parameter
  such as `CLIPS` or a helper such as `clips()` is part of the key of every stage that reads it; an attribute of an
  imported module it names, `BV.FORK_GAP`, too, by its current value);
- the values of its arguments (meshes by their vertices and faces, shapely geometry by its WKB, numbers by repr);
- the content of the `deps` files (other designs' build.py, input STLs) and the `tag` (full or lite), unless the stage
  is run with shared=True (it does not depend on the mode).
Results are pickled with every trimesh.Trimesh replaced by its (vertices, faces): read back, a mesh is the same arrays
(so the hash of a downstream stage's input is the same whether it was computed or read).
"""
import hashlib
import inspect
import os
import pickle
import sys
import time
import types

import numpy as np
import trimesh
from shapely.geometry.base import BaseGeometry

try:
    import timebudget as _tb
except ImportError:                                          # tools/ not on sys.path: no time budget
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import timebudget as _tb

_SIMPLE = (int, float, str, bool, type(None), complex, bytes)


class _M:
    """A pickled mesh: its arrays only."""
    __slots__ = ("v", "f")

    def __init__(self, m):
        self.v, self.f = np.asarray(m.vertices), np.asarray(m.faces)


def _pack(x):
    if isinstance(x, trimesh.Trimesh):
        return _M(x)
    if isinstance(x, dict):
        return {k: _pack(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return type(x)(_pack(v) for v in x)
    return x


def _unpack(x):
    if isinstance(x, _M):
        return trimesh.Trimesh(x.v, x.f, process=False)
    if isinstance(x, dict):
        return {k: _unpack(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return type(x)(_unpack(v) for v in x)
    return x


def _feed(h, x):
    """Hash a value (meshes, arrays, shapely geometry, containers, plain data)."""
    if isinstance(x, trimesh.Trimesh):
        h.update(b"M")
        h.update(np.ascontiguousarray(x.vertices, dtype=np.float64).tobytes())
        h.update(np.ascontiguousarray(x.faces, dtype=np.int64).tobytes())
    elif isinstance(x, np.ndarray):
        h.update(b"A" + str(x.dtype).encode() + str(x.shape).encode())
        h.update(np.ascontiguousarray(x).tobytes())
    elif isinstance(x, dict):
        h.update(b"D")
        for k in sorted(x, key=repr):
            h.update(repr(k).encode())
            _feed(h, x[k])
    elif isinstance(x, (list, tuple)):
        h.update(b"L%d" % len(x))
        for v in x:
            _feed(h, v)
    elif isinstance(x, BaseGeometry):
        h.update(b"G" + x.wkb)
    elif isinstance(x, _SIMPLE) or isinstance(x, np.generic):
        h.update(repr(x).encode())
    else:
        raise TypeError(f"stage_cache: cannot hash a {type(x).__name__}")


def _plain(v):
    """True for a value that is a parameter (numbers, strings, containers of them, arrays)."""
    if isinstance(v, _SIMPLE) or isinstance(v, (np.ndarray, np.generic)):
        return True
    if isinstance(v, (list, tuple)):
        return all(_plain(x) for x in v)
    if isinstance(v, dict):
        return all(_plain(x) for x in v.values())
    return isinstance(v, BaseGeometry)


def _names(code):
    out = set(code.co_names)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            out |= _names(c)
    return out


_REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def _in_repo(fn):
    try:
        return os.path.realpath(inspect.getsourcefile(fn) or "").startswith(_REPO + os.sep)
    except TypeError:
        return False


def fingerprint(fn, h=None, seen=None):
    """Hash fn's source, the module-level parameters and same-module functions it names, recursively."""
    h = h or hashlib.sha256()
    seen = set() if seen is None else seen
    if fn in seen:
        return h
    seen.add(fn)
    h.update(inspect.getsource(fn).encode())
    g = fn.__globals__
    names = sorted(_names(fn.__code__))
    mods = [g[n] for n in names if isinstance(g.get(n), types.ModuleType)]
    for n in names:
        if n in g:
            v = g[n]
            if inspect.isfunction(v) and v.__module__ == fn.__module__:
                fingerprint(v, h, seen)
            elif _plain(v):
                h.update(f"{n}=".encode())
                _feed(h, v)
        for m in mods:                                       # attributes of imported modules it names: by value
            v = getattr(m, n, None)
            if inspect.isfunction(v) and v.__module__ == m.__name__ and _in_repo(v):
                fingerprint(v, h, seen)                      # a project module's function: its source and parameters
            elif v is not None and _plain(v):
                h.update(f"{m.__name__}.{n}=".encode())
                _feed(h, v)
    return h


def file_hash(paths):
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(p.encode())
        with open(p, "rb") as f:
            h.update(f.read())
    return h.hexdigest()


class Stages:
    """Stages under root/<tag> (full, lite); a stage run with shared=True does not depend on the tag and is kept in
    root/shared, so one mode reuses what the other built."""

    def __init__(self, root, deps=(), tag=""):
        self.root, self.tag = root, tag
        for d in (tag, "shared"):
            os.makedirs(os.path.join(root, d), exist_ok=True)
        self.base = file_hash(deps)
        self.log = []                                        # (name, seconds, hit)

    def key(self, name, fn, args, shared=False):
        h = fingerprint(fn)
        h.update(self.base.encode() + name.encode() + (b"" if shared else self.tag.encode()))
        for a in args:
            _feed(h, a)
        return h.hexdigest()[:24]

    def run(self, name, fn, *args, shared=False):
        t = time.time()
        k = self.key(name, fn, args, shared)
        path = os.path.join(self.root, "shared" if shared else self.tag, f"{name}-{k}.pkl")
        if os.path.exists(path):
            with open(path, "rb") as f:
                out = _unpack(pickle.load(f))
            self.log.append((name, time.time() - t, True))
            _tb.log(name, time.time() - t, False)
            return out
        _tb.start()
        with _tb.stage(name):
            out = fn(*args)
        with open(path + ".tmp", "wb") as f:
            pickle.dump(_pack(out), f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(path + ".tmp", path)
        # results are re-read as arrays: return the same arrays the cache holds, so a cold and a warm run agree
        out = _unpack(_pack(out))
        self.log.append((name, time.time() - t, False))
        _tb.log(name, time.time() - t, True)
        return out

    def prune(self, keep_last=4):
        """Drop old entries: keep the newest `keep_last` keys of each stage."""
        for d in (self.tag, "shared"):
            folder = os.path.join(self.root, d)
            by = {}
            for fn in os.listdir(folder):
                if fn.endswith(".pkl"):
                    by.setdefault(fn.rsplit("-", 1)[0], []).append(os.path.join(folder, fn))
            for files in by.values():
                files.sort(key=os.path.getmtime)
                for p in files[:-keep_last]:
                    os.remove(p)

    def report(self):
        tot = sum(t for _, t, _ in self.log)
        print(f"stages ({sum(1 for *_, hit in self.log if hit)} of {len(self.log)} from the cache, {tot:.1f} s):")
        for n, t, hit in self.log:
            print(f"  {n:<16} {t:6.1f} s  {'cached' if hit else 'built'}")
