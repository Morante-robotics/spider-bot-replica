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


def keep_in_spec(part, allow=None):
    shell = box([40, 40, 40])                       # the envelope: a 40 mm cube, inset 2 → a 36 mm cube inside
    return spec(PARTS={"m": {"mesh": part, "fixed": True}},
                KEEP_IN={"shell": {"mesh": shell, "inset": 2.0, "parts": ["m"], "samples": 2000,
                                   "allow": allow or {}, "why": "test"}})


def test_part_inside_the_inset_envelope_passes():
    rep = run(cv.check_keep_in, keep_in_spec(box([30, 30, 30])))
    assert not rep.fails


def test_part_through_the_shell_wall_fails():
    """Base v2 chassis, 2026-11-14: the module's keel and rear foot left the carcass and no check said so."""
    rep = run(cv.check_keep_in, keep_in_spec(box([30, 30, 37])))        # 0.5 mm into the 2 mm wall, top and bottom
    assert rep.fails


def test_bounded_keel_allowance():
    keel = join(box([30, 30, 30]), box([6, 6, 10], (0, 0, -20)))         # a keel down to z -25, outside the cube
    ok = run(cv.check_keep_in, keep_in_spec(keel, {"keel": {"box": ((-4, -4, -30), (4, 4, -17)), "min_z": -25.5,
                                                            "why": "keel"}}))
    assert not ok.fails
    low = run(cv.check_keep_in, keep_in_spec(keel, {"keel": {"box": ((-4, -4, -30), (4, 4, -17)), "min_z": -24.0,
                                                             "why": "keel"}}))
    assert low.fails


def test_allowance_with_its_own_inset():
    # chassis rev 5: the rear end may stand in the shell's wall (inset 0 there) but never out of the carcass
    long = box([30, 37, 30], (0, 0.5, 0))              # +Y face at 19: in the 2 mm wall, 1 mm inside the carcass
    ok = run(cv.check_keep_in, keep_in_spec(long, {"end": {"box": ((-20, 17, -20), (20, 30, 20)), "inset": 0.5,
                                                           "why": "end"}}))
    assert not ok.fails and not ok.warns
    out = box([30, 43, 30], (0, 3.5, 0))               # +Y face at 25: out of the carcass
    bad = run(cv.check_keep_in, keep_in_spec(out, {"end": {"box": ((-20, 17, -20), (20, 30, 20)), "inset": 0.0,
                                                           "why": "end"}}))
    assert bad.fails and "end" in bad.text()


def test_unbounded_allowance_warns_and_max_z_bounds_it():
    top = join(box([30, 30, 30]), box([6, 6, 10], (0, 0, 20)))          # a boss up to z 25, out of the cube's top
    a = {"box": ((-4, -4, 17), (4, 4, 30)), "why": "boss"}
    free = run(cv.check_keep_in, keep_in_spec(top, {"boss": a}))
    assert not free.fails and free.warns == 1 and "no bound" in free.text()
    hi = run(cv.check_keep_in, keep_in_spec(top, {"boss": {**a, "max_z": 24.0}}))
    assert hi.fails and "above its bound" in hi.text()
    ok = run(cv.check_keep_in, keep_in_spec(top, {"boss": {**a, "max_z": 25.5}}))
    assert not ok.fails and not ok.warns


def test_keep_in_z_filter_and_bodies():
    # the deck above z 10 is another part's: samples above it are not checked; a nut (body, not a part) is
    tall = box([30, 30, 40], (0, 0, 10))               # out through the top (z 30), inside below z 10
    s = keep_in_spec(tall)
    s.KEEP_IN["shell"]["z"] = (None, 10.0)
    assert not run(cv.check_keep_in, s).fails
    s.KEEP_IN["shell"]["z"] = (None, 25.0)
    assert run(cv.check_keep_in, s).fails
    s = keep_in_spec(box([10, 10, 10]))
    s.KEEP_IN["shell"]["bodies"] = {"nut": box([5, 5, 5], (0, 0, 18))}   # out through the inset (top at 20.5)
    rep = run(cv.check_keep_in, s)
    assert rep.fails and "nut" in rep.text()


def test_keep_in_default_parts_are_the_static_ones():
    s = keep_in_spec(box([10, 10, 10]))
    del s.KEEP_IN["shell"]["parts"]
    s.PARTS["lid"] = {"mesh": box([10, 10, 4], (0, 0, 19))}          # static, out of the inset: must be checked
    s.PARTS["arm"] = {"mesh": box([4, 4, 4], (0, 0, 0))}             # moves: not in the default list
    s.MOTION = [0, 1]
    s.poses = lambda t: {"arm": cv.move([0, 0, 30 * t])}
    rep = run(cv.check_keep_in, s)
    assert rep.fails and "lid" in rep.text() and "shell: arm" not in rep.text()


def motor_rig():
    """A motor with its shaft along -X, a pinion pressed on it (zero clearance), a frame with a slot the pinion
    drops into from above, and a bench jig (chassis rev 6: the pinion cannot drop in alone and the motor follow)."""
    frame = cut(box([20, 20, 10], (0, 0, 0)), box([8, 30, 20], (-2, 0, 8)))     # slot, open at the top
    motor = box([10, 8, 8], (8, 0, 10))                 # x 3..13, z 6..14: above the frame top (5)
    shaft = cv.rod(3.0, 6, [3, 0, 10], [-1, 0, 0])       # x -3..3
    pin = cut(cv.rod(8.0, 4, [-3, 0, 10], [1, 0, 0]), shaft)   # x -3..1 on the shaft
    jig = cut(box([3, 10, 10], (-4.5, 0, 10)), cv.rod(4.0, 10, [-10, 0, 10], [1, 0, 0]))  # pusher x -6..-3
    parts = {"frame": {"mesh": frame, "fixed": True}, "motor": {"mesh": motor, "hardware": True},
             "shaft": {"mesh": shaft, "hardware": True, "fixed": True}, "pinion": {"mesh": pin},
             "jig": {"mesh": jig, "bench": True}}
    return parts


def test_sub_assembly_moves_as_one_body():
    parts = motor_rig()
    seq = [("frame", None),
           (("jig", "pinion"), [-1, 0, 0], {"bench": ["motor", "shaft"], "except": {"shaft": "press fit"}}),
           (("motor", "shaft", "pinion"), [0, 0, 1])]
    s = spec(PARTS=parts, ASSEMBLY=seq,
             ACCESS=[{"at": ("motor", "shaft", "pinion"), "tool": cv.tool("finger", [8, 0, 14], [0, 0, 1]),
                      "why": "lowered by hand"}])
    rep = run(cv.check_assembly, s)
    assert not rep.fails, rep.text()
    assert "as one body" in rep.text() and "on the bench" in rep.text()
    acc = run(cv.check_access, s)
    assert not acc.fails, acc.text()
    # the jig is a bench part: the motion and retention checks never see it
    assert "jig" not in cv.placed(s, {n: p["mesh"] for n, p in parts.items()}, 0)


def test_bench_step_sees_only_its_bench_parts():
    parts = motor_rig()
    # from the wrong side the pinion runs into the motor on the bench: blocked
    seq = [("frame", None), (("jig", "pinion"), [1, 0, 0], {"bench": ["motor", "shaft"]}),
           (("motor", "shaft", "pinion"), [0, 0, 1])]
    rep = run(cv.check_assembly, spec(PARTS=parts, ASSEMBLY=seq))
    assert rep.fails and "on the bench" in rep.text()
    # a machine part (a roof over the slot) does not block a bench step, but blocks the drop
    parts["roof"] = {"mesh": box([20, 20, 2], (0, 0, 20)), "fixed": True}
    seq = [("frame", None), ("roof", None),
           (("jig", "pinion"), [-1, 0, 0], {"bench": ["motor", "shaft"]}),
           (("motor", "shaft", "pinion"), [0, 0, 1])]
    rep = run(cv.check_assembly, spec(PARTS=parts, ASSEMBLY=seq))
    assert rep.fails == 1 and "motor + shaft + pinion (as one body) cannot" in rep.text()
    # a jig that is not marked as a bench part never goes into the machine: a failure
    parts["jig"].pop("bench")
    rep = run(cv.check_assembly, spec(PARTS=parts, ASSEMBLY=seq[:1] + seq[2:]))
    assert "jig: only in bench steps" in rep.text()


def test_negative_fit_needs_the_overlap():
    pad = box([4, 4, 2], (0, 0, 0.7))                     # 0.3 into the block below (top at 0)
    blk = box([10, 10, 2], (0, 0, -1))
    fit = SimpleNamespace(side=-0.3, status="assumed", source="test")
    s = spec(PARTS={"blk": {"mesh": blk, "fixed": True}, "pad": {"mesh": pad}},
             JOINTS={("pad", "blk"): {"fit": fit, "why": "preload"}})
    rep = run(cv.check_joints, s)
    assert not rep.fails and rep.warns == 1 and "interference" in rep.text()
    s.PARTS["pad"]["mesh"] = box([4, 4, 2], (0, 0, 1.5))   # 0.5 above: the preload is missing
    assert run(cv.check_joints, s).fails


def test_exploded_view_numbers_match_the_assembly_steps():
    """figures.exploded left the bench steps out and numbered k + 1, so every number after a bench step was off
    (rev 6: off by 2 after step 19) while the kit shows that picture «con su número de paso»."""
    import figures
    s = spec(ASSEMBLY=[("base", None), ("a", [0, 0, 1]),
                       ("jig-part", [1, 0, 0], {"bench": ["motor"]}), ("fork", [0, 0, 1], {"bench": ["motor"]}),
                       (("motor", "pinion"), [0, 0, 1]), ("b", [0, 0, 1])])
    got = [(k, nums) for k, _, _, nums in figures.exploded_steps(cv.steps(s))]
    assert got == [(0, ["1"]), (1, ["2"]), (2, ["5a", "5b"]), (3, ["6"])]


def test_allowance_is_checked_above_the_z_filter():
    """Chassis rev 6: the front-slope allowance bounded the module top (z ≤ 74.8) but the entry's z filter (≤ 72.3)
    dropped every sample above 72.3 first, so that band was never checked."""
    top = join(box([30, 30, 30]), box([6, 6, 10], (0, 0, 20)))          # a boss up to z 25, out of the cube's top
    s = keep_in_spec(top, {"boss": {"box": ((-4, -4, 10), (4, 4, 30)), "max_z": 24.0, "why": "boss"}})
    s.KEEP_IN["shell"]["z"] = (None, 16.0)                               # the filter stops under the boss's top
    hi = run(cv.check_keep_in, s)
    assert hi.fails and "above its bound" in hi.text()


def swing_spec(post_gap=0.4, frame_gap=3.0, nested=False):
    """A still frame round an arm that turns a full circle about Z every 30°: the frame clears the arm's tip by
    frame_gap at every step (inside the frame's box: a pose-by-pose scan computes it at every step); a still post
    comes post_gap from the tip at 90° only; a second arm moves too (both move: always pose by pose). nested: a still
    block wholly inside the arm at 180° (an overlap with no surfaces touching)."""
    arm = box([20, 4, 4], (10, 0, 0))                                 # x 0..20 at 0°, tip corners at r 20.1
    h = 20.1 + frame_gap
    frame = cut(box([2 * h + 6, 2 * h + 6, 4]), box([2 * h, 2 * h, 10]))
    parts = {"frame": {"mesh": frame, "fixed": True}, "arm": {"mesh": arm},
             "arm2": {"mesh": box([10, 4, 4], (5, 0, 4.5))}}             # 0.5 above the arm, turning 15° behind it
    if post_gap is not None:
        parts["post"] = {"mesh": box([4, 1, 4], (0, 20 + post_gap + 0.5, 0)), "fixed": True}
    if nested:
        parts["core"] = {"mesh": box([1, 1, 1], (-15, 0, 0)), "fixed": True}
    return spec(PARTS=parts, MOTION=list(range(0, 360, 30)), MIN_GAP=0.2,
                poses=lambda t: {"arm": cv.rot([0, 0, 1], t), "arm2": cv.rot([0, 0, 1], t - 15)})


def motion_report(s, sweep, seen_clear=False):
    """The motion check's report, cache empty. seen_clear: as if every still × moving pair had been clear last time
    (then it goes to its envelope at once, without the one-step probe)."""
    cv.HASH.clear(), cv.DISK.clear(), cv.NEW.clear()
    if seen_clear:
        cv.DISK.update({("sweep-last", a, b): "clear" for a in s.PARTS for b in s.PARTS if a != b})
    rep = cv.Report()
    cv.check_motion(s, {n: p["mesh"] for n, p in s.PARTS.items()}, rep, sweep=sweep)
    return rep.text()


def verdicts(txt):
    """The report without its bookkeeping lines (how many pairs were computed, and how)."""
    return [ln for ln in txt.splitlines() if "pair positions computed" not in ln and "swept envelopes" not in ln]


def test_swept_envelope_gives_the_per_pose_report():
    """Still part × moving part: one query against the moving part's swept envelope; a pair that comes closer is
    scanned pose by pose, so its worst step is named exactly as before. Pairs where both parts move: pose by pose."""
    for kw in ({}, {"post_gap": 0.1}, {"frame_gap": 0.6, "post_gap": None}, {"nested": True}):
        s = swing_spec(**kw)
        old = motion_report(s, False)
        for seen in (False, True):
            new = motion_report(s, True, seen)
            assert verdicts(old) == verdicts(new), (kw, seen, old, new)
            assert "swept envelopes" in new and "swept envelopes" not in old
    for seen in (False, True):
        txt = motion_report(swing_spec(post_gap=0.1), True, seen)
        assert "FAIL  arm × post: gap 0.10 mm < 0.2 (at 90)" in txt, txt               # named at its step, as before
        assert "arm × frame" not in txt and "2 pairs clear at every step" in txt, txt   # 3 mm off: one query
        assert "arm × arm2: gap 0.50 mm" in txt, txt                                    # both move: pose by pose
        # close at its first step near (90°): the probe sends it to the scan; seen clear before: the envelope does
        assert ("1 closer" if seen else "1 close at their first step") in txt, txt
    assert "arm × frame: gap 0.70 mm (closest at 0)" in motion_report(swing_spec(frame_gap=0.6, post_gap=None), True)
    # the core is wholly inside the arm at 180° (no surfaces touch), and far from it at 150°, its first step near
    nested = motion_report(swing_spec(nested=True), True)
    assert "FAIL  arm × core: overlap 1.00 mm³ (worst at 180)" in nested and "1 overlapping or touching" in nested, \
        nested


def test_per_pose_flag_turns_the_envelopes_off(monkeypatch):
    monkeypatch.setattr(cv, "SWEEP", False)
    s = swing_spec()
    rep = cv.Report()
    cv.check_motion(s, {n: p["mesh"] for n, p in s.PARTS.items()}, rep)
    assert "swept envelopes" not in rep.text()


def test_swept_envelope_result_is_cached(tmp_path):
    s = swing_spec(post_gap=0.1)
    meshes = {n: p["mesh"] for n, p in s.PARTS.items()}
    f = cv.load_cache(str(tmp_path / "spec.py"), meshes)
    cv.DISK[("sweep-last", "post", "arm")] = "clear"
    rows, skip, disjoint, st = cv.sweep_pairs(s, meshes, s.MOTION, None, 0.5)
    assert st["cached"] == 0 and frozenset(("arm", "frame")) in skip and frozenset(("arm", "post")) in disjoint
    cv.save_cache(f)
    cv.load_cache(str(tmp_path / "spec.py"), meshes)
    rows2, skip2, disjoint2, st2 = cv.sweep_pairs(s, meshes, s.MOTION, None, 0.5)
    assert st2["cached"] == st["settled"] + st["disjoint"] + st["scanned"] and (rows2, skip2, disjoint2) == \
        (rows, skip, disjoint)
    # the arm on another path is another envelope: not taken from the cache
    s.poses = lambda t: {"arm": cv.rot([0, 0, 1], t + 1), "arm2": cv.rot([0, 0, 1], t - 14)}
    assert cv.sweep_pairs(s, meshes, s.MOTION, None, 0.5)[3]["cached"] == 0


def test_pair_close_last_time_is_scanned_step_by_step(tmp_path):
    """After a fix to the still part (a new hash), a pair that came closer last time skips the envelope (it would
    only add a query to the scan it needs anyway); the scan records whether it is still close."""
    s = swing_spec(post_gap=0.1)
    path = str(tmp_path / "spec.py")

    def run_with_cache(post_gap, dx=0.0):
        # a new version of the post: post_gap off the tip at 90°, or beside it (dx), 1.27 mm off its corner
        s.PARTS["post"]["mesh"] = box([4, 1, 4], (dx, 20 + post_gap + 0.5, 0))
        meshes = {n: p["mesh"] for n, p in s.PARTS.items()}
        f = cv.load_cache(path, meshes)
        rep = cv.Report()
        cv.check_motion(s, meshes, rep)
        cv.save_cache(f)
        return rep.text()

    assert "0 close last time" in run_with_cache(0.1)
    txt = run_with_cache(0.15)                                   # still close: scanned step by step at once
    assert "1 close last time" in txt and "FAIL  arm × post: gap 0.15 mm < 0.2 (at 90)" in txt, txt
    assert verdicts(txt) == verdicts(motion_report(s, False))
    txt = run_with_cache(0.9, dx=4.9)                            # moved clear: scanned once more, learnt clear
    assert "1 close last time" in txt and "arm × post" not in txt, txt
    txt = run_with_cache(0.95, dx=4.95)                          # the next version goes to the envelope again
    assert "0 close last time" in txt and "arm × post" not in txt, txt


def test_smoke_skips_assembly_access_and_print():
    calls = []
    names = ("check_integrity", "check_motion", "check_retention", "check_assembly", "check_print", "check_keep_out",
             "check_access", "check_joints", "check_seats", "check_keep_in", "check_marks")
    saved = {n: getattr(cv, n) for n in names}
    try:
        for n in names:
            setattr(cv, n, lambda *a, _n=n, **k: calls.append(_n))
        cv.run_checks(None, None, None, SimpleNamespace(quick=True, smoke=True), None)
    finally:
        for n, f in saved.items():
            setattr(cv, n, f)
    assert not {"check_assembly", "check_print", "check_access"} & set(calls)
    assert "check_motion" in calls


def test_keep_in_distances_come_from_the_disk_cache(tmp_path, monkeypatch):
    # an unchanged part is not measured again on the next run, with the same verdict; a changed part is
    calls = []
    real = trimesh.proximity.signed_distance
    monkeypatch.setattr(trimesh.proximity, "signed_distance", lambda m, p: calls.append(len(p)) or real(m, p))
    inside, out = keep_in_spec(box([30, 30, 30])), keep_in_spec(box([30, 30, 37]))
    f = cv.load_cache(str(tmp_path / "spec.py"), {})
    first = run(cv.check_keep_in, inside)
    assert len(calls) == 1 and not first.fails
    cv.save_cache(f)
    cv.load_cache(str(tmp_path / "spec.py"), {})
    again = run(cv.check_keep_in, inside)
    assert len(calls) == 1 and again.text() == first.text()
    assert run(cv.check_keep_in, out).fails and len(calls) == 2


def hook_parts():
    """An L-hook: a hook box sits under an overhang (y 2..10, z 4..6) on a base. A straight drop hits the
    overhang; lowered in the open (y < 2) and then slid +Y 4 mm it gets in."""
    base = box([20, 20, 2], (0, 0, -1))                              # z -2..0
    over = box([20, 8, 2], (0, 6, 5))                                # overhang y 2..10, z 4..6
    hook = box([4, 4, 4], (0, 4, 2))                                 # placed y 2..6, z 0..4
    return {"base": {"mesh": base, "fixed": True}, "over": {"mesh": over, "fixed": True}, "hook": {"mesh": hook}}


HOOK_SEQ = [("base", None), ("over", None)]


def test_path_down_then_slide_passes():
    s = spec(PARTS=hook_parts(), ASSEMBLY=HOOK_SEQ + [("hook", [[0, 0, -8], [0, 4, 0]])])
    rep = run(cv.check_assembly, s)
    assert not rep.fails, rep.text()
    assert "goes in: down 8 mm, then +Y 4 mm" in rep.text()
    # a straight drop from above hits the overhang
    rep = run(cv.check_assembly, spec(PARTS=hook_parts(), ASSEMBLY=HOOK_SEQ + [("hook", [0, 0, 1])]))
    assert rep.fails
    # steps() keeps a unit "d" (the side the last move comes from) and the path
    st = cv.steps(s)[-1]
    assert np.allclose(st["d"], [0, -1, 0]) and len(st["path"]) == 2


def test_path_blocked_on_move_2_fails():
    parts = hook_parts()
    parts["wall"] = {"mesh": box([20, 1, 4], (0, 0.5, 2)), "fixed": True}      # y 0..1, z 0..4: in the way of the slide only
    s = spec(PARTS=parts, ASSEMBLY=HOOK_SEQ + [("wall", None), ("hook", [[0, 0, -8], [0, 8, 0]])])
    rep = run(cv.check_assembly, s)
    assert rep.fails and "blocked on move 2" in rep.text(), rep.text()


def test_straight_step_is_unchanged():
    s = spec(PARTS=hook_parts(), ASSEMBLY=HOOK_SEQ + [("hook", [0, -1, 0])])
    st = cv.steps(s)[-1]
    assert st["path"] is None and np.allclose(st["d"], [0, -1, 0])
    rep = run(cv.check_assembly, s)
    assert not rep.fails and "goes in from -Y" in rep.text(), rep.text()
