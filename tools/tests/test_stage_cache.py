"""stage_cache: a parameter of another project module, reached through a function, must reach the key."""
import os
import sys
import types
import importlib.util
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import stage_cache as sc  # noqa: E402


def test_other_module_parameter_changes_key():
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp_mod_for_cache.py")
    try:
        with open(d, "w") as f:
            f.write("WALL = 1.6\n\ndef cavity(x):\n    return x * WALL\n")
        spec = importlib.util.spec_from_file_location("_tmp_mod_for_cache", d)
        bv = importlib.util.module_from_spec(spec)
        sys.modules["_tmp_mod_for_cache"] = bv
        spec.loader.exec_module(bv)
        ns = {"BV": bv}
        exec("def st_bowl(b):\n    return BV.cavity(b)\n", ns)
        # inspect.getsource needs a file: write the stage function to one too
        src = os.path.join(os.path.dirname(d), "_tmp_stage_for_cache.py")
        with open(src, "w") as f:
            f.write("import _tmp_mod_for_cache as BV\n\ndef st_bowl(b):\n    return BV.cavity(b)\n")
        sys.path.insert(0, os.path.dirname(d))
        import _tmp_stage_for_cache as st
        k1 = sc.fingerprint(st.st_bowl).hexdigest()
        bv.WALL = 1.2
        k2 = sc.fingerprint(st.st_bowl).hexdigest()
        assert k1 != k2
    finally:
        for p in (d, os.path.join(os.path.dirname(d), "_tmp_stage_for_cache.py")):
            if os.path.exists(p):
                os.remove(p)
