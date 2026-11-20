"""tools/rounds.py: the plan checks catch what a review round used to, and the score arithmetic applies every cap.

Run from the repo root: .venv/bin/python -m pytest
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import rounds as r  # noqa: E402

SPEC2 = {"design": "t", "level": "N2", "purpose": "p", "gates": [], "judge": {"enabled": False},
         "refine_rounds": 0, "must_have": ["two eyes"]}


def plan2(**kw):
    p = {"summary": "s",
         "parts": [{"name": "frame", "role": "ground", "why_separate": "w", "grams": 3, "print_orient": "flat"},
                   {"name": "block", "role": "r", "why_separate": "w", "grams": 1, "print_orient": "flat"}],
         "joints": [{"name": "j", "a": "block", "b": "frame", "fit": "fits.WINDOW", "in_from": "+z",
                     "apart_by": "lift", "held": {d: "wall" for d in ("+x", "-x", "+y", "-y", "+z", "-z")}}],
         "assembly": [{"part": "frame", "from": None, "tool": "hand", "check": "flat"},
                      {"part": "block", "from": "+z", "tool": "hand", "check": "flush"}],
         "acceptance": [{"id": "a1", "text": "held", "how": "verify", "check": "retention", "priority": "must"}]}
    p.update(kw)
    return p


def test_clean_plan_passes_and_gets_must_have_items():
    p = plan2()
    err, warn, norm = r.check_plan(p, SPEC2)
    assert not err, err
    assert any(x["id"] == "m1" and x["text"] == "two eyes" for x in p["acceptance"])


def test_gravity_unknown_fit_missing_step_and_placeholder_fail():
    p = plan2()
    p["joints"][0]["held"]["+z"] = "gravity"
    p["joints"][0]["fit"] = "fits.NO_SUCH_FIT"
    p["assembly"].pop()
    p["summary"] = "<one line>"
    err, _, _ = r.check_plan(p, SPEC2)
    text = "\n".join(err)
    assert "held.+z" in text and "NO_SUCH_FIT" in text and "block never goes in" in text and "placeholder" in text


def test_acceptance_needs_a_known_check_and_how():
    p = plan2(acceptance=[{"id": "a1", "text": "x", "how": "verify", "check": "vibes"},
                          {"id": "a2", "text": "y", "how": "guess"}])
    err, _, _ = r.check_plan(p, SPEC2)
    assert any("a cad_verify check" in e for e in err) and any("how" in e for e in err)


GATES_OK = {"gates": [{"name": "cad_verify", "kind": "cad_verify", "verdict": "PASS", "partial": False, "fails": [],
                       "checks": {"retention": {"ok": 3, "warn": 0, "fail": 0}}}]}
RUB = {"pass_threshold": 0.75, "gate_fail_cap": 0.6, "floor_cap": 0.6,
       "criteria": [{"id": "a", "weight": 0.5}, {"id": "b", "weight": 0.5, "floor": 0.3},
                    {"id": "sil", "kind": "measured", "weight": 0.5, "map": {"0.27": 0.1, "0.85": 1.0}}],
       "defects": [{"id": "float", "penalty": 0.1, "cap": 0.6}]}


def judgment(a=0.9, b=0.9, float_=False, acc=True):
    return {"criteria": {"a": {"score": a}, "b": {"score": b}}, "defects": {"float": {"present": float_}},
            "acceptance": {"v1": {"verified": acc}}, "improvement_plan": [{"priority": 1, "target": "x",
                                                                          "instruction": "do y"}]}


PLAN_S = {"acceptance": [{"id": "a1", "text": "held", "how": "verify", "check": "retention", "priority": "must"},
                         {"id": "v1", "text": "eyes", "how": "visual", "priority": "must"},
                         {"id": "p1", "text": "Morante likes it", "how": "morante", "priority": "must"}]}


def test_clean_round_passes_and_unmeasured_criterion_is_dropped():
    s = r.score_round(SPEC2, PLAN_S, GATES_OK, RUB, judgment(), {})
    assert s["overall"] == 0.9 and s["passed"] and not s["caps"]
    assert any("sil not measured" in n for n in s["notes"])


def test_measured_criterion_counts_when_measured():
    s = r.score_round(SPEC2, PLAN_S, GATES_OK, RUB, judgment(), {"sil": 0.27})
    assert abs(s["overall"] - (0.45 + 0.45 + 0.05) / 1.5) < 1e-3


def test_gate_fail_defect_floor_and_acceptance_cap():
    bad = {"gates": [dict(GATES_OK["gates"][0], verdict="FAIL", fails=["x is not held"],
                          checks={"retention": {"ok": 0, "warn": 0, "fail": 1}})]}
    s = r.score_round(SPEC2, PLAN_S, bad, RUB, judgment(), {})
    assert s["overall"] == 0.6 and not s["passed"] and s["improvement"][0].startswith("[gate/cad_verify]")
    s = r.score_round(SPEC2, PLAN_S, GATES_OK, RUB, judgment(float_=True), {})
    assert s["overall"] == 0.6
    s = r.score_round(SPEC2, PLAN_S, GATES_OK, RUB, judgment(b=0.2), {})
    assert not s["passed"] and any(x.startswith("[floor/b]") for x in s["improvement"])
    s = r.score_round(SPEC2, PLAN_S, GATES_OK, RUB, judgment(acc=False), {})
    assert s["overall"] == 0.8 and any(x.startswith("[acceptance/v1]") for x in s["improvement"])


def test_partial_gate_never_verifies_and_caps_n2():
    part = {"gates": [dict(GATES_OK["gates"][0], partial=True)]}
    s = r.score_round(SPEC2, PLAN_S, part, RUB, judgment(), {})
    assert ("a1", "must", "verify", "pending", "held") in s["acceptance"]
    assert s["overall"] <= 0.85


def test_silhouette_iou_ignores_framing(tmp_path):
    a = np.zeros((100, 100), np.uint8)
    a[20:60, 10:90] = 255
    b = np.zeros((300, 200), np.uint8)
    b[100:180, 20:180] = 255                     # same 2:1 box, other size and place
    c = np.zeros((100, 100), np.uint8)
    c[10:90, 40:60] = 255                        # a tall box
    for name, im in (("a", a), ("b", b), ("c", c)):
        Image.fromarray(im).save(tmp_path / f"{name}.png")
    assert r.silhouette_iou(tmp_path / "a.png", tmp_path / "b.png") > 0.95
    assert r.silhouette_iou(tmp_path / "a.png", tmp_path / "c.png") < 0.4


def test_eval_map():
    m = {"0.27": 0.1, "0.85": 1.0}
    assert r.eval_map(m, 0.1) == 0.1 and r.eval_map(m, 0.9) == 1.0 and abs(r.eval_map(m, 0.56) - 0.55) < 1e-9


def test_exit_code_is_the_verdict(tmp_path):
    """validate/check print FAIL and must also exit non-zero, so `validate WS && ...` stops on a bad plan."""
    import json
    import subprocess
    ws, tool = tmp_path / "t", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rounds.py")
    ws.mkdir()

    def run(*args):
        return subprocess.run([sys.executable, tool, *args, str(ws)], capture_output=True, text=True).returncode

    assert run("validate") == 2  # no spec.json: it could not run
    (ws / "spec.json").write_text(json.dumps({**SPEC2, "level": "N1"}))  # N2 also needs a cad_verify gate
    (ws / "plan.json").write_text(json.dumps(plan2(summary="TODO")))
    assert run("validate") == 1
    (ws / "plan.json").write_text(json.dumps(plan2()))
    assert run("validate") == 0
    assert run("check") == 0  # no gates
    assert run("best") == 2  # no scored round


# ---------------------------------------------------------------- ready to print

READY_SPEC = '''
PARTS = {"frame": {"mesh": None}, "pin": {"mesh": None, "hardware": True, "label": "pasador"}}
JOINTS = {("pin", "frame"): {"fit": None}}
MARKS = {}
LABELS = {"es": {"frame": "marco"}}
MEASURE = [("pin bore", 3.3)]
'''


def ready_score(**kw):
    s = {"overall": 0.9, "passed": True, "improvement": [], "caps": [],
         "acceptance": [("a1", "must", "verify", "verified", "held"), ("m1", "must", "morante", "pending", "looks")]}
    s.update(kw)
    return s


def ready(tmp_path, spec_src=READY_SPEC, rs=None, verify="cad_verify: PASS (0 failures, 1 warnings)\n",
          kit="<p>ok</p>", status=None, coupons=False):
    f = tmp_path / "verify.py"
    f.write_text(spec_src)
    names, unl = r.spec_names(str(f))
    rs = [(0, ready_score(), None)] if rs is None else rs
    return r.ready_items(plan2(), rs, verify, names, unl, status or {"WINDOW": "measured"}, kit, coupons)


def fails(items):
    return [t for st, t in items if st == "FAIL"]


def test_ready_passes_a_complete_design_and_leaves_the_hand_items(tmp_path):
    items = ready(tmp_path)
    assert not fails(items), fails(items)
    assert sum(st == "HAND" for st, _ in items) == 2


def test_ready_fails_partial_verify_missing_kit_and_falta(tmp_path):
    assert any("verify-result" in t for t in fails(ready(tmp_path, verify="cad_verify: PARTIAL PASS (0, 0)\n")))
    assert any("verify-result" in t for t in fails(ready(tmp_path, verify=None)))
    assert any("kit" in t for t in fails(ready(tmp_path, kit=None)))
    assert any("FALTA: 2" in t for t in fails(ready(tmp_path, kit="FALTA: a FALTA: b")))


def test_ready_fails_spec_gaps_unlabelled_hardware_and_assumed_fits(tmp_path):
    src = READY_SPEC.replace(', "label": "pasador"', "").replace('MEASURE = [("pin bore", 3.3)]', "MEASURE = []")
    f = fails(ready(tmp_path, spec_src=src.replace('"es"', '"en"')))
    assert any("MEASURE empty" in t for t in f) and any("LABELS" in t for t in f)
    assert any("without a label: 1" in t for t in f)
    assert any("WINDOW" in t for t in fails(ready(tmp_path, status={"WINDOW": "assumed"})))
    assert not any("WINDOW" in t for t in fails(ready(tmp_path, status={"WINDOW": "assumed"}, coupons=True)))


def test_ready_fails_when_the_best_round_is_not_the_last_or_has_open_items(tmp_path):
    rs = [(0, ready_score(overall=0.9), None), (1, ready_score(overall=0.8), None)]
    assert any("not the last" in t for t in fails(ready(tmp_path, rs=rs)))
    s = ready_score(improvement=["[gate/cad_verify] x"],
                    acceptance=[("a1", "must", "verify", "failed", "held")])
    f = fails(ready(tmp_path, rs=[(0, s, None)]))
    assert any("gate items in its score: 1" in t for t in f) and any("a1" in t for t in f)
