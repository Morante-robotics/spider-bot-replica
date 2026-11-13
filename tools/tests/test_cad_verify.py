"""Regression tests for tools/cad_verify.py: every failure that reached a print once must keep failing here.

Each test builds a tiny mechanism from boxes and cylinders (no files), runs one check and reads the report.
Run from the repo root (a few seconds):

    .venv/bin/python -m pytest
"""
import os
import sys
from types import SimpleNamespace

import numpy as np
import trimesh

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cad_verify as cv  # noqa: E402


def box(size, at=(0, 0, 0)):
    m = trimesh.creation.box(size)
    m.apply_translation(at)
    return m


def cut(a, b):
    return trimesh.boolean.difference([a, b], engine="manifold")


def join(*ms):
    return trimesh.boolean.union(list(ms), engine="manifold")


def spec(**kw):
    s = SimpleNamespace(**kw)
    return s


def run(check, s, *args):
    rep = cv.Report()
    meshes = {n: p["mesh"] for n, p in s.PARTS.items()}
    check(s, meshes, rep, *args)
    return rep


def shaft():
    """Ø4 shaft along X, 20 long, with two collars 0.3 mm inside the walls (so it cannot slide out)."""
    rod = cv.rod(4.0, 20, [-10, 0, 0], [1, 0, 0])
    collars = [cv.rod(8.0, 1.0, [x, 0, 0], [1, 0, 0]) for x in (-5.7, 4.7)]
    return join(rod, *collars)


def frame(open_slot):
    """Two walls at x = ±6..±8 on a floor. The shaft goes through a Ø4.5 hole, or down an open slot (gear train
    test v1, 2026-11-11: the crankshafts lifted out of their open slots)."""
    walls = [box([2, 20, 20], (x, 0, 0)) for x in (-7, 7)] + [box([16, 20, 2], (0, 0, -11))]
    f = join(*walls)
    hole = cv.rod(4.5, 30, [-15, 0, 0], [1, 0, 0])
    f = cut(f, hole)
    if open_slot:
        f = cut(f, box([30, 4.5, 12], (0, 0, 6)))
    return f


def test_open_slot_does_not_hold_the_shaft():
    s = spec(PARTS={"frame": {"mesh": frame(True), "fixed": True}, "shaft": {"mesh": shaft()}},
             RETAIN={"shaft": {"spin": [1, 0, 0], "play": 0.5}})
    rep = run(cv.check_retention, s, True)
    assert rep.fails == 1 and "+Z" in rep.text()


def test_hole_holds_the_shaft():
    s = spec(PARTS={"frame": {"mesh": frame(False), "fixed": True}, "shaft": {"mesh": shaft()}},
             RETAIN={"shaft": {"spin": [1, 0, 0], "play": 0.5}})
    rep = run(cv.check_retention, s, True)
    assert rep.fails == 0, rep.text()


def window(c):
    """A 10 mm block in a window with c mm a side, not touching."""
    ring = cut(box([30, 30, 6]), box([10 + 2 * c, 10 + 2 * c, 20]))
    return {"ring": {"mesh": ring, "fixed": True}, "block": {"mesh": box([10, 10, 6])}}


WINDOW = SimpleNamespace(side=0.5, status="measured", what="block in its window")


def test_fit_below_the_measured_one_fails():
    # base v1, 2026-11-13: the cap had 0.3 mm a side, the measured fit is 0.5, it did not go in
    s = spec(PARTS=window(0.3), JOINTS={("block", "ring"): {"fit": WINDOW}})
    rep = run(cv.check_joints, s)
    assert rep.fails == 1, rep.text()


def test_measured_fit_passes():
    s = spec(PARTS=window(0.5), JOINTS={("block", "ring"): {"fit": WINDOW}})
    rep = run(cv.check_joints, s)
    assert rep.fails == 0, rep.text()


def test_assumed_fit_warns():
    fit = SimpleNamespace(side=0.5, status="assumed", what="new snap", source="never printed")
    s = spec(PARTS=window(0.6), JOINTS={("block", "ring"): {"fit": fit}})
    rep = run(cv.check_joints, s)
    assert rep.fails == 0 and rep.warns == 1


def test_missing_joints_warns():
    rep = run(cv.check_joints, spec(PARTS=window(0.5)))
    assert rep.warns == 1


def test_gear_without_mark_fails():
    # base v1, 2026-11-13: no marks on the gears, Morante could not set their phase
    parts = {"frame": {"mesh": box([5, 5, 5]), "fixed": True},
             "gear1": {"mesh": cv.rod(10, 3, [20, 0, 0], [0, 0, 1])},
             "gear2": {"mesh": cv.rod(10, 3, [31, 0, 0], [0, 0, 1])}}
    rep = cv.Report()
    cv.check_marks(spec(PARTS=parts, GEARS=[("gear1", "gear2")], MARKS={"gear1": "dot"}), rep)
    assert rep.fails == 1 and "gear2" in rep.text()


def test_unreachable_pin_fails():
    # base v1, 2026-11-13: the pin holes could not be reached once the parts were in place
    plate = cut(box([20, 20, 4]), cv.rod(3.3, 10, [0, 0, -5], [0, 0, 1]))
    roof = box([20, 20, 2], (0, 0, 15))
    pin = cv.rod(3.0, 10, [0, 0, -2], [0, 0, 1])
    parts = {"plate": {"mesh": plate, "fixed": True}, "roof": {"mesh": roof, "fixed": True},
             "pin": {"mesh": pin, "hardware": True}}
    s = spec(PARTS=parts, ASSEMBLY=[("plate", None), ("roof", None), ("pin", [0, 0, 1])],
             ACCESS=[{"at": "pin", "tool": cv.tool("finger", [0, 0, 8], [0, 0, 1]), "why": "push it in"}])
    rep = run(cv.check_access, s)
    assert rep.fails == 1 and "roof" in rep.text()


def test_support_standing_on_the_part_warns():
    # base v1, 2026-11-13: support in pockets nobody could reach. A bridge over a closed pocket
    pocket = cut(box([30, 30, 12]), box([16, 16, 8], (0, 0, 0)))
    rep = cv.Report()
    cv.check_print(spec(PARTS={"p": {"mesh": pocket}}), {"p": pocket}, rep)
    assert rep.warns == 1 and "over the part itself" in rep.text()


def test_relative_position_cache_key():
    a, b = np.eye(4), cv.move([1, 0, 0])
    both = cv.rot([0, 0, 1], 30)
    assert cv.rel_key(a, b) == cv.rel_key(both @ a, both @ b)
    assert cv.rel_key(a, b) != cv.rel_key(a, cv.move([1.1, 0, 0]))


def test_part_floating_above_its_seat_fails():
    # base v1, 2026-11-13: the big gear did not go fully into its pocket
    floor = box([20, 20, 4], (0, 0, -2))
    for lift, fails in ((0.5, 1), (0.0, 0)):
        disc = cv.rod(10, 3, [0, 0, lift], [0, 0, 1])
        parts = {"floor": {"mesh": floor, "fixed": True}, "gear": {"mesh": disc}}
        rep = run(cv.check_seats, spec(PARTS=parts, SEATS={"gear": {"on": "floor", "dir": [0, 0, -1]}}))
        assert rep.fails == fails, rep.text()


def test_thin_upright_peg_warns():
    # base v1, 2026-11-13: thin pegs printed upright broke the posts they sat in
    base = box([20, 20, 2], (0, 0, 1))
    thin = join(base, cv.rod(3.0, 8, [0, 0, 2], [0, 0, 1]))
    thick = join(base, cv.rod(5.0, 8, [0, 0, 2], [0, 0, 1]))
    assert cv.upright_slender(thin) and not cv.upright_slender(thick)


def test_gear_motion_checks_gears_on_their_own_steps():
    g1 = cv.rod(10, 3, [0, 0, 0], [0, 0, 1])
    g2 = cv.rod(10, 3, [10.3, 0, 0], [0, 0, 1])
    parts = {"g1": {"mesh": g1, "fixed": True}, "g2": {"mesh": g2}}
    s = spec(PARTS=parts, GEARS=[("g1", "g2")], MOTION=[0, 1], GEAR_MOTION=[0, 1, 2],
             poses=lambda t: {"g2": cv.rot([0, 0, 1], 10 * t, [10.3, 0, 0])})
    rep = run(cv.check_motion, s)
    assert "3 pair positions computed" in rep.text() and "ok    gears g1 × g2: gap 0.30" in rep.text(), rep.text()


def test_disk_cache_reuses_pairs(tmp_path):
    parts = window(0.5)
    meshes = {n: p["mesh"] for n, p in parts.items()}
    f = cv.load_cache(str(tmp_path / "spec.py"), meshes)
    s = spec(PARTS=parts)
    rows, n, hits = cv.scan_pairs(s, meshes, [0], None, 0.5)
    assert hits == 0 and cv.NEW
    cv.save_cache(f)
    cv.load_cache(str(tmp_path / "spec.py"), meshes)
    rows2, n2, hits2 = cv.scan_pairs(s, meshes, [0], None, 0.5)
    assert hits2 == 1 and rows2 == rows
