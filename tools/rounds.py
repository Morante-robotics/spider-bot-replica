#!/usr/bin/env python3
"""Design rounds: the request, the plan, the gates, a blind judge and the score, one design folder at a time.

The method is adapted from 3dcodeverse's harness (github.com/gaoypeng/3dcodeverse, Apache-2.0): the request and the
plan are data validated before any code, deterministic gates run in code, a judge in a fresh context sees only a
brief and pictures, the score is arithmetic on the judge's answers with explicit caps, and every round is a snapshot
that can be compared and restored. Here the CAD is build123d, the gates are tools/cad_verify.py (or a level's own
check), the reference is the model the design reproduces, and nothing is committed: commits stay Morante's call.

A design folder is the workspace:

    spec.json        the request (level, purpose, must-haves, dimensions with sources, references, gates, views,
                     judge, refine rounds Morante asked for). Written once, by `init`; never edited after
    plan.json        the plan (parts, joints, assembly, alternatives, acceptance, open questions). Validated by
                     `validate`, which writes design-plan.md from it; never edited after it validated (a re-plan
                     starts the rounds over)
    build.py, ...    the source (spec["src"]); out/ and images/ are what it writes
    rounds/rNN/      src/ snapshot, gates.json, views, brief.md, judgment.json (the judge), score.json (not in git)

Commands (from the repo root; WS is the design folder, e.g. cad/legs):

    uv run python tools/rounds.py init WS --level N2 --purpose "..." [--must-have ...] [--ref reference.jpg] [--rounds 1]
    uv run python tools/rounds.py init WS --level N1 --purpose "..." --mesh PART=ref.stl [--mesh ...] [--edit]
                                         --rounds 1      # a conversion from reference meshes (mesh-to-cad agent)
    uv run python tools/rounds.py except WS PART --reason "..." [--p95 MM] [--max MM] [--judge 0.69] [--drop "..."]
                                                       # an exception Morante approved for one part
    uv run python tools/rounds.py validate WS          # until PASS; writes WS/design-plan.md
    uv run python tools/rounds.py check WS             # every gate in spec["gates"]: PASS / FAIL with each failure
    uv run python tools/rounds.py round WS 0           # snapshot + gates + views + brief; prints JUDGE INSTRUCTION
    uv run python tools/rounds.py score WS 0           # after the judge wrote judgment.json
    uv run python tools/rounds.py status WS            # every round's score, caps and verdict; the best round
    uv run python tools/rounds.py best WS              # copy the best round's src back (then run check again)
    uv run python tools/rounds.py ready WS --kit K     # the ready-to-print checklist from the files (N2 only)

Every command prints its verdict first (PASS / FAIL / ERROR), then the numbers and what to fix. The exit code is the
verdict, so `validate WS && ...` stops on a bad plan: 0 = PASS, 1 = FAIL, 2 = ERROR (it could not run).
"""
import argparse
import ast
import datetime
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
RUBRICS = os.path.join(TOOLS, "rubrics")
LEVELS = ("N0", "N1", "N2")
HOWS = ("verify", "measure", "visual", "morante", "print")
VERIFY_CHECKS = ("integrity", "motion", "gears", "retention", "assembly", "print", "keep-out", "access", "joints",
                 "seats", "keep-in", "marks")
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PLACEHOLDER = re.compile(r"<[A-Za-z][\w ./-]{0,40}>|\bTODO\b|\bTBD\b|\?\?\?")


# ---------------------------------------------------------------- files

def jload(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def jsave(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")


def expand(path, ws):
    """A path in spec.json: {refs} is $CAD_REFS (the private reference folder, never in git), {ws} the design
    folder, {root} the repo; relative paths are relative to the design folder."""
    refs = os.environ.get("CAD_REFS", "")
    p = os.path.expanduser(path.replace("{refs}", refs).replace("{ws}", ws).replace("{root}", ROOT))
    return p if os.path.isabs(p) else os.path.join(ws, p)


def src_files(ws, spec):
    out = []
    for pat in spec.get("src", ["*.py"]):
        out += sorted(glob.glob(expand(pat, ws)))
    return [p for p in out if os.path.isfile(p)]


def digest(paths):
    h = hashlib.sha256()
    for p in paths:
        h.update(os.path.relpath(p).encode())
        with open(p, "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:16]


def snap_name(p, ws):
    """Where a source file goes in a round's src/: its path inside the design folder, or under _root/ by its path in
    the repo when it lives elsewhere (a level's shared script), never outside src/."""
    rel = os.path.relpath(p, ws)
    if rel.startswith(".."):
        rel = os.path.join("_root", os.path.relpath(p, ROOT))
    if rel.startswith("_root" + os.sep + ".."):
        sys.exit(f"ERROR source {p} is outside the repo")
    return rel


def rdir(ws, n):
    return os.path.join(ws, "rounds", f"r{int(n):02d}")


def rubric(name):
    path = os.path.join(RUBRICS, f"{name}.json")
    if not os.path.exists(path):
        sys.exit(f"ERROR no rubric {name!r} in {RUBRICS}")
    return jload(path)


# ---------------------------------------------------------------- init

def cmd_init(a):
    ws = os.path.abspath(a.ws)
    path = os.path.join(ws, "spec.json")
    if os.path.exists(path):
        print(f"ERROR {path} exists: spec.json is written once (a new request is a new design or a re-plan)")
        return 2
    spec = {"design": os.path.basename(ws), "level": a.level, "purpose": a.purpose,
            "pass_criterion": a.pass_criterion or "", "must_have": a.must_have or [], "must_not": a.must_not or [],
            "dims": {}, "references": [{"image": r, "label": "reference"} for r in (a.ref or [])],
            "src": ["build.py", "verify.py"] if a.level == "N2" else ["*.py"],
            "gates": [{"name": "cad_verify", "kind": "cad_verify", "spec": "verify.py"}] if a.level == "N2" else [],
            "views": {}, "judge": {"enabled": bool(a.ref), "rubric": "looks"},
            "refine_rounds": a.rounds, "asked": f"Morante, {datetime.date.today().isoformat()}"}
    if a.mesh:
        err = mesh_spec(spec, ws, a.mesh, a.edit)
        if err:
            print(f"ERROR {err}")
            return 2
    jsave(path, spec)
    print(f"PASS wrote {path}\n  next: fill dims (each with its source), gates and views; then write plan.json "
          f"(cad/_template/plan.json) and run validate")
    return 0


def mesh_spec(spec, ws, meshes, edit):
    """A conversion (`init --mesh PART=REF ...`): the parts are rebuilt as parameters from reference meshes. Adds the
    gates every conversion runs (source: no mesh read; build + its --sweep; edit for an organic part; fidelity per
    part, tools/mesh_ref.py compare at its default limits, relative to the part's size; other limits only through
    `except`), the views and the reference picture (both
    from mesh_ref.py views, same framing), the judge, and each reference's size as a dim. Returns an error or None."""
    sys.path.insert(0, TOOLS)
    import mesh_ref
    pairs = []
    for m in meshes:
        if "=" not in m:
            return f"--mesh {m}: PART=path/to/reference.stl"
        part, ref = m.split("=", 1)
        if not KEBAB.match(part):
            return f"--mesh {m}: part names are kebab-case"
        if not os.path.exists(os.path.join(ROOT, ref)):
            return f"--mesh {m}: {ref} not found (paths from the repo root)"
        pairs.append((part, ref))
    py = "{root}/.venv/bin/python"
    spec["src"] = ["build.py", "plan.json"]
    spec["must_not"] = (spec["must_not"] or []) + ["build.py reads a mesh: the reference meshes are read only by the "
                                                   "gates and the designer's probes"]
    spec["gates"] = [{"name": "source", "kind": "command", "cmd": f"{py} tools/mesh_ref.py source {{ws}}/build.py",
                      "fail_regex": "^FAIL"},
                     {"name": "build", "kind": "command", "cmd": f"cd {{ws}} && {py} build.py --sweep",
                      "fail_regex": "^FAIL", "timeout": 600}]
    if edit:
        spec["gates"].append({"name": "edit", "kind": "command", "cmd": f"cd {{ws}} && {py} build.py --edit",
                              "fail_regex": "^FAIL", "timeout": 600})
    for part, ref in pairs:
        spec["gates"].append({"name": f"fidelity-{part}", "kind": "command", "fail_regex": "^FAIL", "timeout": 600,
                              "cmd": f"{py} tools/mesh_ref.py compare {{ws}}/out/{part}.stl {ref} "
                                     f"--png {{ws}}/images/fidelity-{part}.png --json {{ws}}/out/fidelity-{part}.json"})
        m = mesh_ref.load(os.path.join(ROOT, ref))
        spec["dims"][f"{part}_extent"] = {"value": [round(float(x), 2) for x in m.extents], "unit": "mm",
                                          "source": f"tools/mesh_ref.py info {ref}"}
        spec["dims"][f"{part}_fidelity"] = {"value": list(mesh_ref.limits(m)), "unit": "mm (p95, max)",
                                            "source": "tools/mesh_ref.py limits(): 3 % / 6 % of the largest extent, "
                                                      "floors 1.0 / 2.0 mm (Morante, 2026-11-21)"}
    refs = " ".join(r for _, r in pairs)
    parts = " ".join(f"{{ws}}/out/{p}.stl" for p, _ in pairs)
    cmd = f"{py} tools/mesh_ref.py views {{out}} --ref {refs} --parts {parts}"
    images = ["{out}"]
    if edit:
        cmd += " --edits {dir}/edits.png {ws}/out/edit-*.stl"
        images.append("{dir}/edits.png")
    spec["views"] = {"cmd": cmd, "images": images, "timeout": 600}
    os.makedirs(os.path.join(ws, "images"), exist_ok=True)
    mesh_ref.views(os.path.join(ws, "images", "reference.png"), [os.path.join(ROOT, r) for _, r in pairs])
    spec["references"] = [{"image": "{ws}/images/reference.png",
                           "label": "the reference mesh(es) to reproduce, same four views and framing"}]
    spec["judge"] = {"enabled": True, "rubric": "looks"}
    return None


# ---------------------------------------------------------------- validate

def check_spec(spec, ws):
    err, warn = [], []
    for k in ("design", "level", "purpose", "gates", "judge", "refine_rounds"):
        if k not in spec:
            err.append(f"spec.{k}: missing")
    if spec.get("level") not in LEVELS:
        err.append(f"spec.level: {spec.get('level')!r}, one of {', '.join(LEVELS)}")
    for k, d in (spec.get("dims") or {}).items():
        if not isinstance(d, dict) or "value" not in d or not d.get("source"):
            err.append(f"spec.dims.{k}: needs value and source (file + parameter, or a measurement)")
    for i, r in enumerate(spec.get("references") or []):
        p = expand(r.get("image", ""), ws)
        if not os.path.exists(p):
            warn.append(f"spec.references[{i}]: {r.get('image')} not found (set CAD_REFS to the private "
                        f"reference folder)")
    for i, g in enumerate(spec.get("gates") or []):
        if g.get("kind") not in ("cad_verify", "command"):
            err.append(f"spec.gates[{i}].kind: cad_verify or command")
        if g.get("kind") == "command" and not g.get("cmd"):
            err.append(f"spec.gates[{i}].cmd: missing")
    if spec.get("judge", {}).get("enabled"):
        if not spec.get("views", {}).get("cmd"):
            err.append("spec.views.cmd: the judge needs pictures (a command that writes {out})")
        if not spec.get("references"):
            warn.append("spec.references: a looks judge without a reference image judges from words only")
    if spec.get("level") == "N2" and not any(g.get("kind") == "cad_verify" for g in spec.get("gates") or []):
        err.append("spec.gates: an N2 design has a cad_verify gate")
    err += check_exceptions(spec)
    return err, warn


EXCEPTION_KINDS = ("fidelity", "judge", "drop")


def check_exceptions(spec):
    """Every departure from the default rules is an exception Morante approved, with his reason (`except`): a fidelity
    gate with its own limits, a judge threshold under the rubric's, a detail left out."""
    err, ex = [], spec.get("exceptions") or []
    for i, e in enumerate(ex):
        if e.get("kind") not in EXCEPTION_KINDS or not e.get("part") or not e.get("reason") or not e.get("by"):
            err.append(f"spec.exceptions[{i}]: needs kind ({', '.join(EXCEPTION_KINDS)}), part, reason and by")
    has = {(e.get("kind"), e.get("part")) for e in ex}
    for g in spec.get("gates") or []:
        if g.get("name", "").startswith("fidelity-") and re.search(r"--(p95|max)\b", g.get("cmd", "")):
            part = g["name"][len("fidelity-"):]
            if ("fidelity", part) not in has:
                err.append(f"spec.gates {g['name']}: own limits without an approved exception (rounds.py except)")
    thr = (spec.get("judge") or {}).get("pass_threshold")
    if thr is not None and thr < rubric(spec["judge"].get("rubric", "looks")).get("pass_threshold", 0.75) \
            and not any(k == "judge" for k, _ in has):
        err.append(f"spec.judge.pass_threshold {thr}: under the rubric's without an approved exception "
                   f"(rounds.py except)")
    return err


def cmd_except(a):
    """Record an exception Morante approved for one part: its own fidelity limits, a lower judge threshold (for the
    design the part belongs to), or a detail left out. The only change to spec.json after init; the reason is his."""
    ws = os.path.abspath(a.ws)
    path = os.path.join(ws, "spec.json")
    spec = jload(path)
    if spec is None:
        print(f"ERROR {path}: no spec.json")
        return 2
    if a.p95 is None and a.max is None and a.judge is None and not a.drop:
        print("ERROR say what the exception is: --p95/--max, --judge or --drop")
        return 2
    ex = spec.setdefault("exceptions", [])
    rec = {"part": a.part, "reason": a.reason, "by": "Morante", "date": datetime.date.today().isoformat()}
    if a.p95 is not None or a.max is not None:
        g = next((g for g in spec.get("gates", []) if g.get("name") == f"fidelity-{a.part}"), None)
        if g is None:
            print(f"ERROR no gate fidelity-{a.part} in {path}")
            return 2
        cmd = re.sub(r" --(p95|max) [0-9.]+", "", g["cmd"])
        lim = (f" --p95 {a.p95}" if a.p95 is not None else "") + (f" --max {a.max}" if a.max is not None else "")
        g["cmd"] = re.sub(r"(compare \S+ \S+)", lambda m: m.group(1) + lim, cmd, count=1)
        ex.append({**rec, "kind": "fidelity", "value": {k: v for k, v in (("p95", a.p95), ("max", a.max))
                                                         if v is not None}})
    if a.judge is not None:
        spec.setdefault("judge", {})["pass_threshold"] = a.judge
        spec["judge"]["pass_threshold_why"] = f"exception for {a.part}: {a.reason}"
        ex.append({**rec, "kind": "judge", "value": a.judge})
    for d in a.drop or []:
        ex.append({**rec, "kind": "drop", "value": d})
    jsave(path, spec)
    print(f"PASS {path}: exception for {a.part} recorded; the rounds after this one use it")
    return 0


def fit_names():
    sys.path.insert(0, ROOT)
    try:
        from cad import fits
    except Exception:          # noqa: BLE001  the check says why it could not run
        return None
    return {k for k, v in vars(fits).items() if type(v).__name__ == "Fit"}


def check_plan(plan, spec):
    """Deterministic plan checks. Returns (errors, warnings, normalisations); may add acceptance items."""
    err, warn, norm = [], [], []
    level = spec.get("level")
    txt = json.dumps(plan, ensure_ascii=False)
    for m in sorted(set(PLACEHOLDER.findall(txt))):
        err.append(f"placeholder left in the plan: {m!r}")
    if len(txt) > 12000:
        warn.append(f"plan.json is {len(txt) // 1000} kB: one sentence per part; prose goes in the build log")
    if not plan.get("summary"):
        err.append("plan.summary: one line, what it is and what moves")
    parts = plan.get("parts") or []
    if not parts:
        err.append("plan.parts: empty")
    names = [p.get("name") for p in parts]
    for i, p in enumerate(parts):
        n = p.get("name")
        if not n or not KEBAB.match(n):
            err.append(f"plan.parts[{i}].name: {n!r} is not kebab-case")
        if names.count(n) > 1:
            err.append(f"plan.parts[{i}].name: {n!r} twice")
        if not p.get("role"):
            err.append(f"plan.parts[{i}].role: missing")
        if level == "N2" and not p.get("hardware"):
            for k in ("why_separate", "print_orient", "grams"):
                if p.get(k) in (None, ""):
                    err.append(f"plan.parts[{i}] ({n}).{k}: missing (N2)")
    known = set(names)
    fits_known = fit_names() if level == "N2" else set()
    for i, j in enumerate(plan.get("joints") or []):
        for k in ("a", "b"):
            if j.get(k) not in known:
                err.append(f"plan.joints[{i}].{k}: {j.get(k)!r} is not a part")
        if level == "N2":
            fit = (j.get("fit") or "").removeprefix("fits.")
            if not fit:
                err.append(f"plan.joints[{i}] ({j.get('name')}).fit: a fits.py entry")
            elif fits_known is not None and fit not in fits_known:
                err.append(f"plan.joints[{i}] ({j.get('name')}).fit: fits.{fit} does not exist; add it to "
                           f"cad/fits.py as assumed, with its coupon")
            held = j.get("held") or {}
            for d in ("+x", "-x", "+y", "-y", "+z", "-z"):
                if not held.get(d) or str(held.get(d)).strip().lower() in ("gravity", "nothing", "none"):
                    err.append(f"plan.joints[{i}] ({j.get('name')}).held.{d}: what stops it ('gravity' or "
                               f"'nothing' is a defect unless the spec allows it)")
            for k in ("in_from", "apart_by"):
                if not j.get(k):
                    err.append(f"plan.joints[{i}] ({j.get('name')}).{k}: missing")
    if level == "N2":
        steps = plan.get("assembly") or []
        placed = [s.get("part") for s in steps]
        for n, p in zip(names, parts):
            if n not in placed:
                err.append(f"plan.assembly: {n} never goes in (every part and fastener has a step)")
        for i, s in enumerate(steps):
            if s.get("part") not in known:
                err.append(f"plan.assembly[{i}].part: {s.get('part')!r} is not a part")
            if i and not (s.get("from") and s.get("tool") and s.get("check")):
                err.append(f"plan.assembly[{i}]: from, tool (hand or which tool) and check (how you know it is "
                           f"right)")
    acc = plan.setdefault("acceptance", [])
    ids = [x.get("id") for x in acc]
    for i, x in enumerate(acc):
        if not x.get("id") or ids.count(x.get("id")) > 1:
            err.append(f"plan.acceptance[{i}].id: missing or repeated")
        if x.get("how") not in HOWS:
            err.append(f"plan.acceptance[{i}].how: {x.get('how')!r}, one of {', '.join(HOWS)}")
        if x.get("how") == "verify" and x.get("check") not in VERIFY_CHECKS:
            err.append(f"plan.acceptance[{i}].check: a cad_verify check ({', '.join(VERIFY_CHECKS)})")
        x.setdefault("priority", "must")
        if x["priority"] not in ("must", "should"):
            err.append(f"plan.acceptance[{i}].priority: must or should")
    lower = " ".join(x.get("text", "").lower() for x in acc)
    for k, m in enumerate(spec.get("must_have") or []):
        if m.lower() not in lower:
            old = next((x for x in acc if x.get("id") == f"m{k + 1}" and x.get("from") == "spec.must_have"), None)
            if old is not None:                        # the request's item was reworded: update it, never a twin id
                old["text"] = m
                norm.append(f"acceptance: m{k + 1}'s text updated from spec.must_have ({m!r}); check its 'how'")
                continue
            acc.append({"id": f"m{k + 1}", "text": m, "how": "visual", "priority": "must", "from": "spec.must_have"})
            norm.append(f"acceptance: added m{k + 1} from spec.must_have ({m!r}); give it the right 'how'")
    for k, m in enumerate(spec.get("must_not") or []):
        if f"not {m}".lower() not in lower and m.lower() not in lower:
            acc.append({"id": f"n{k + 1}", "text": f"not: {m}", "how": "visual", "priority": "must",
                        "from": "spec.must_not"})
            norm.append(f"acceptance: added n{k + 1} from spec.must_not ({m!r})")
    if not any(x.get("priority") == "must" for x in acc):
        err.append("plan.acceptance: no 'must' item (the pass criterion is one)")
    if spec.get("pass_criterion") and not any(x.get("from") == "spec.pass_criterion" or
                                              spec["pass_criterion"].lower() in x.get("text", "").lower()
                                              for x in acc):
        acc.append({"id": "p1", "text": spec["pass_criterion"], "how": "morante", "priority": "must",
                    "from": "spec.pass_criterion"})
        norm.append("acceptance: added p1, the spec's pass criterion (how: morante)")
    for i, q in enumerate(plan.get("open_questions") or []):
        if len(q.get("options") or []) < 2 or not q.get("default"):
            err.append(f"plan.open_questions[{i}]: every candidate as an option, and your default")
    for i, alt in enumerate(plan.get("alternatives") or []):
        if len(alt.get("options") or []) < 2 or not alt.get("choice") or not alt.get("why"):
            err.append(f"plan.alternatives[{i}]: two options or more, the choice and why")
    return err, warn, norm


def md_table(rows, cols):
    out = ["| " + " | ".join(c for c, _ in cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join(str(f(r) if callable(f) else r.get(f, "")).replace("|", "/")
                                     for _, f in cols) + " |")
    return out


def plan_md(plan, spec):
    held = lambda j: " · ".join(f"{d} {j.get('held', {}).get(d, '')}" for d in ("+x", "-x", "+y", "-y", "+z", "-z"))
    out = [f"# {spec.get('design')} · plan", "",
           "Generated from `plan.json` by `tools/rounds.py validate`: edit the JSON, never this page.", "",
           f"**{plan.get('summary', '')}**", "",
           f"Level {spec.get('level')} · purpose: {spec.get('purpose', '')} · pass: {spec.get('pass_criterion', '')}",
           "", "## Part list", ""]
    out += md_table(plan.get("parts", []), [("Part", "name"), ("Role", "role"), ("Why separate", "why_separate"),
                                            ("g", "grams"), ("Print orientation", "print_orient")])
    if plan.get("joints"):
        out += ["", "## Joint table", ""]
        out += md_table(plan["joints"], [("Joint", "name"), ("Parts", lambda j: f"{j.get('a')} ↔ {j.get('b')}"),
                                         ("Type", "type"), ("Held", held), ("Fit", "fit"), ("In from", "in_from"),
                                         ("Apart by", "apart_by")])
    if plan.get("assembly"):
        out += ["", "## Assembly sequence", ""]
        out += md_table([dict(s, n=i + 1) for i, s in enumerate(plan["assembly"])],
                        [("Step", "n"), ("Part", "part"), ("From", "from"), ("Hand or tool", "tool"),
                         ("Already in", "already"), ("How you know", "check")])
    if plan.get("alternatives"):
        out += ["", "## Alternatives", ""]
        for alt in plan["alternatives"]:
            out.append(f"- **{alt.get('topic')}**: {' / '.join(alt.get('options', []))} → **{alt.get('choice')}**, "
                       f"{alt.get('why')}")
    out += ["", "## Acceptance", ""]
    out += md_table(plan.get("acceptance", []), [("Id", "id"), ("Item", "text"), ("How", "how"),
                                                 ("Check", "check"), ("Priority", "priority")])
    if plan.get("open_questions"):
        out += ["", "## Open questions", ""]
        for q in plan["open_questions"]:
            out.append(f"- {q.get('q')} Options: {' / '.join(q.get('options', []))}. Default: {q.get('default')}")
    if plan.get("diagram"):
        out += ["", "## Diagram", "", f"<img src=\"{plan['diagram']}\" alt=\"Plan diagram\">"]
    return "\n".join(out) + "\n"


def cmd_validate(a):
    ws = os.path.abspath(a.ws)
    spec, plan = jload(os.path.join(ws, "spec.json")), jload(os.path.join(ws, "plan.json"))
    if spec is None:
        print(f"ERROR no spec.json in {ws}: run init first")
        return 2
    if plan is None:
        print(f"ERROR no plan.json in {ws}: copy cad/_template/plan.json and fill it")
        return 2
    e1, w1 = check_spec(spec, ws)
    e2, w2, norm = check_plan(plan, spec)
    err, warn = e1 + e2, w1 + w2
    print(("FAIL" if err else "PASS") + f" plan of {spec.get('design')} ({spec.get('level')}): "
          f"{len(err)} errors, {len(warn)} warnings")
    for x in err:
        print(f"  ERROR {x}")
    for x in warn:
        print(f"  WARN  {x}")
    for x in norm:
        print(f"  NORM  {x}")
    if not err:
        plan["_validated"] = digest([os.path.join(ws, "spec.json")]) + ":" + hashlib.sha256(
            json.dumps({k: v for k, v in plan.items() if k != "_validated"}, sort_keys=True).encode()).hexdigest()[:12]
        jsave(os.path.join(ws, "plan.json"), plan)
        with open(os.path.join(ws, "design-plan.md"), "w") as f:
            f.write(plan_md(plan, spec))
        print(f"  wrote {os.path.join(ws, 'design-plan.md')}")
    return 1 if err else 0


def plan_is_valid(ws):
    plan = jload(os.path.join(ws, "plan.json")) or {}
    v = plan.get("_validated")
    if not v:
        return False
    now = digest([os.path.join(ws, "spec.json")]) + ":" + hashlib.sha256(
        json.dumps({k: x for k, x in plan.items() if k != "_validated"}, sort_keys=True).encode()).hexdigest()[:12]
    return v == now


# ---------------------------------------------------------------- check (the gates)

def run_gate(g, ws, out_dir):
    name = g.get("name", g.get("kind"))
    if g["kind"] == "cad_verify":
        js = os.path.join(out_dir, f"{name}.json")
        cmd = [sys.executable, os.path.join(TOOLS, "cad_verify.py"), expand(g["spec"], ws), "--json", js,
               "--out", os.path.join(out_dir, f"{name}.txt")] + list(g.get("args", []))
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=g.get("timeout", 1800))
        res = jload(js)
        if res is None:
            return {"name": name, "kind": "cad_verify", "verdict": "ERROR", "partial": False, "fails": [],
                    "checks": {}, "tail": (p.stdout + p.stderr)[-1500:]}
        return {"name": name, "kind": "cad_verify", "verdict": res["verdict"], "partial": res["partial"],
                "fails": res["fail_lines"], "warns": res["warn_lines"][:20], "checks": res["checks"],
                "tail": p.stdout[-1500:]}
    cmd = g["cmd"].replace("{ws}", ws).replace("{root}", ROOT)
    p = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=g.get("timeout", 900))
    text = p.stdout + p.stderr
    fails = []
    if g.get("fail_regex"):
        fails = [ln.strip() for ln in text.splitlines() if re.search(g["fail_regex"], ln)]
    verdict = "ERROR" if p.returncode not in (0, *g.get("ok_codes", [])) else ("FAIL" if fails else "PASS")
    return {"name": name, "kind": "command", "verdict": verdict, "partial": bool(g.get("partial")), "fails": fails,
            "checks": {}, "tail": text[-2500:]}


def cmd_check(a, out_dir=None):
    ws = os.path.abspath(a.ws)
    spec = jload(os.path.join(ws, "spec.json"))
    if spec is None:
        print(f"ERROR no spec.json in {ws}")
        return None
    out_dir = out_dir or os.path.join(ws, "rounds", "_check")
    os.makedirs(out_dir, exist_ok=True)
    gates = [run_gate(g, ws, out_dir) for g in spec.get("gates", [])]
    verdict = "ERROR" if any(g["verdict"] == "ERROR" for g in gates) else \
        "FAIL" if any(g["verdict"] in ("FAIL", "PARTIAL FAIL") for g in gates) else "PASS"
    res = {"verdict": verdict, "src": digest(src_files(ws, spec)), "gates": gates,
           "at": datetime.datetime.now().isoformat(timespec="seconds")}
    jsave(os.path.join(out_dir, "gates.json"), res)
    print(f"{verdict} gates of {spec.get('design')}: " + "; ".join(f"{g['name']} {g['verdict']}" +
                                                                  (" (partial)" if g["partial"] else "")
                                                                  for g in gates) or "no gates")
    for g in gates:
        for ln in g["fails"][:15]:
            print(f"  {g['name']}: {short(ln)}")
        if g["verdict"] == "ERROR":
            print(f"  {g['name']} could not run:\n" + "\n".join("    " + x for x in g["tail"].splitlines()[-12:]))
    print(f"  gates: {os.path.join(out_dir, 'gates.json')}")
    return res


# ---------------------------------------------------------------- round (snapshot, views, brief)

def silhouette_iou(mask_a, mask_b, size=256):
    """IoU of two silhouettes (white = object), each cropped to its own bounding box and scaled to one square, so
    framing and image size do not count; the aspect ratio does (it is drawn into the square unstretched)."""
    import numpy as np
    from PIL import Image

    def norm(path):
        im = np.asarray(Image.open(path).convert("L")) > 127
        ys, xs = np.nonzero(im)
        if not len(xs):
            return np.zeros((size, size), bool)
        crop = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        h, w = crop.shape
        s = size / max(h, w)
        img = Image.fromarray(crop.astype(np.uint8) * 255).resize((max(1, round(w * s)), max(1, round(h * s))))
        out = np.zeros((size, size), bool)
        arr = np.asarray(img) > 127
        y0, x0 = (size - arr.shape[0]) // 2, (size - arr.shape[1]) // 2
        out[y0:y0 + arr.shape[0], x0:x0 + arr.shape[1]] = arr
        return out
    a, b = norm(mask_a), norm(mask_b)
    union = (a | b).sum()
    return float((a & b).sum() / union) if union else 0.0


def judge_criteria(rub, measured):
    """The rubric's criteria the judge scores (measured ones are filled by code, or dropped when not measured)."""
    return [c for c in rub["criteria"] if c.get("kind") != "measured"], \
        [c for c in rub["criteria"] if c.get("kind") == "measured" and c["id"] in measured]


def brief_md(spec, plan, gates, rub, images, measured, n):
    crit, meas = judge_criteria(rub, measured)
    acc = [x for x in plan.get("acceptance", []) if x.get("how") in ("visual", "measure") and not (x.get("how") == "measure" and x.get("gate"))]
    out = [f"# Judge brief · {spec['design']} · round r{n:02d}", "",
           "You judge pictures of a 3D-printed robot design against its request and its reference. You never see "
           "the code. Everything you may use is in this file and the images listed below.", "",
           "## The request", "", f"- Level: {spec['level']} (N0 simple shapes, N1 real-looking parts, N2 printable)",
           f"- Purpose: {spec.get('purpose', '')}"]
    out += [f"- Must have: {m}" for m in spec.get("must_have", [])]
    out += [f"- Must not: {m}" for m in spec.get("must_not", [])]
    out += [f"- Left out on purpose (approved): `{e['part']}`: {e['value']}; do not count its absence against the "
            f"design" for e in spec.get("exceptions", []) if e.get("kind") == "drop"]
    out += ["", "## The plan (digest)", "", plan.get("summary", "")]
    out += [f"- `{p['name']}`: {p.get('role', '')}" for p in plan.get("parts", [])]
    out += ["", "## Images", ""]
    out += [f"- {lab}: `{p}`" for lab, p in images]
    out += ["", "## Measured facts (computed by code: do not re-estimate them)", ""]
    out += [f"- {k}: {v:.3f}" for k, v in measured.items()]
    for g in gates.get("gates", []):
        out.append(f"- gate `{g['name']}`: {g['verdict']}" + (" (partial)" if g["partial"] else ""))
        out += [f"  - {ln}" for ln in g["fails"][:10]]
        if g["kind"] == "command":
            out += ["  ```", *("  " + ln for ln in g["tail"].strip("\n").splitlines()[-25:]), "  ```"]
    out += ["", "## How to judge", "", rub.get("extra_instructions", "").strip(), "", "## Criteria (score each 0..1)",
            ""]
    for c in crit:
        out.append(f"### `{c['id']}` · {c['title']} (weight {c['weight']})")
        out.append(c["description"].strip())
        out += [f"- {k}: {v}" for k, v in c["anchors"].items()]
        out.append("")
    if meas:
        out.append("Measured criteria (not yours): " + ", ".join(c["id"] for c in meas))
    out += ["", "## Defect checklist (answer every id, present true/false)", ""]
    out += [f"- `{d['id']}`: {d['text']}" for d in rub.get("defects", [])]
    out += ["", "## Acceptance items (verified true only when an image or a measured fact proves it)", ""]
    out += [f"- `{x['id']}` ({x['priority']}): {x['text']}" for x in acc] or ["- none for the judge"]
    shape = {"criteria": {c["id"]: {"score": 0.0, "evidence": "image + where"} for c in crit},
             "summary": "two sentences", "strengths": ["..."],
             "issues": [{"target": "part name or overall", "kind": "shape|proportion|missing|artefact|other",
                         "severity": "major|minor", "evidence": "image + where"}],
             "improvement_plan": [{"priority": 1, "target": "part name", "instruction": "imperative, concrete",
                                   "expected_gain": "which criterion, about how much"}],
             "acceptance": {x["id"]: {"verified": False, "evidence": "..."} for x in acc},
             "defects": {d["id"]: {"present": False, "evidence": ""} for d in rub.get("defects", [])}}
    out += ["", "## Return exactly this JSON (every key), written to `judgment.json` in this folder", "", "```json",
            json.dumps(shape, indent=1, ensure_ascii=False), "```", ""]
    return "\n".join(out)


def cmd_round(a):
    ws, n = os.path.abspath(a.ws), int(a.n)
    spec, plan = jload(os.path.join(ws, "spec.json")), jload(os.path.join(ws, "plan.json"))
    if spec is None or plan is None:
        print("ERROR spec.json and plan.json first")
        return 2
    if not plan_is_valid(ws):
        print("ERROR plan.json is not validated as it stands: run validate until PASS (a changed plan is a re-plan: "
              "the rounds start over)")
        return 2
    d = rdir(ws, n)
    if os.path.exists(os.path.join(d, "judgment.json")) and not a.force:
        print(f"ERROR {d} is already judged: the next round is r{n + 1:02d} (--force repacks it)")
        return 2
    os.makedirs(d, exist_ok=True)
    srcd = os.path.join(d, "src")
    shutil.rmtree(srcd, ignore_errors=True)
    files = src_files(ws, spec) + [os.path.join(ws, "plan.json")]
    snaps = []
    for p in files:
        snap = snap_name(p, ws)
        dst = os.path.join(srcd, snap)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(p, dst)
        snaps.append({"path": os.path.relpath(p, ROOT), "snap": snap})
    gates = cmd_check(a, out_dir=d)
    if gates is None:
        return 2
    if gates["verdict"] == "ERROR":
        print(f"ERROR round r{n:02d} stopped: a gate could not run; fix it and run round {n} again")
        return 2
    if gates["verdict"] == "FAIL" and spec.get("judge", {}).get("enabled") and not a.force:
        print(f"FAIL round r{n:02d} not packed for the judge: fix the gate failures above first (each caps the score "
              f"at 0.60; a judge call on them is wasted). --force packs it anyway")
        return 1
    images, measured = [], {}
    for i, r in enumerate(spec.get("references", [])):
        p = expand(r["image"], ws)
        if os.path.exists(p):
            dst = os.path.join(d, f"reference-{i}{os.path.splitext(p)[1]}")
            shutil.copy2(p, dst)
            images.append((f"REFERENCE {i}: {r.get('label', '')}", dst))
    v = spec.get("views", {})
    if v.get("cmd"):
        out = os.path.join(d, "views.png")
        cmd = v["cmd"].replace("{out}", out).replace("{ws}", ws).replace("{root}", ROOT).replace("{dir}", d)
        p = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=v.get("timeout", 900))
        made = [x.replace("{out}", out).replace("{dir}", d) for x in v.get("images", ["{out}"])]
        if p.returncode or not all(os.path.exists(x) for x in made):
            print(f"ERROR views command failed:\n{(p.stdout + p.stderr)[-1500:]}")
            return 2
        images += [(f"VIEW {k}: {os.path.basename(x)}", x) for k, x in enumerate(made)]
        for k, m in enumerate(v.get("masks", [])):
            mp, ref = m["mask"].replace("{dir}", d), spec["references"][m.get("ref", 0)].get("mask")
            if ref and os.path.exists(mp) and os.path.exists(expand(ref, ws)):
                measured["silhouette_iou"] = silhouette_iou(mp, expand(ref, ws))
    jsave(os.path.join(d, "round.json"), {"n": n, "src": gates["src"], "files": snaps,
                                          "images": images, "measured": measured,
                                          "at": datetime.datetime.now().isoformat(timespec="seconds")})
    if not spec.get("judge", {}).get("enabled"):
        print(f"PASS round r{n:02d} packed without a judge ({gates['verdict']} gates): run score {n}")
        return 0
    rub = rubric(spec["judge"].get("rubric", "looks"))
    with open(os.path.join(d, "brief.md"), "w") as f:
        f.write(brief_md(spec, plan, gates, rub, images, measured, n))
    pics = ", ".join(p for _, p in images)
    print(f"PASS round r{n:02d} packed ({gates['verdict']} gates): {d}")
    print(f"JUDGE INSTRUCTION: Judge the round in {d}: read {os.path.join(d, 'brief.md')} and every image ({pics}) "
          f"in one step, then write {os.path.join(d, 'judgment.json')} exactly as the brief says and reply only "
          f"'wrote <path>'. (Agent definition: ~/.claude/agents/looks-judge.md.)")
    return 0


# ---------------------------------------------------------------- score

def short(s, n=240):
    return s if len(s) <= n else s[:n] + " …"


def clamp(x):
    return max(0.0, min(1.0, float(x)))


def score_round(spec, plan, gates, rub, judgment, measured):
    """The arithmetic: weighted criteria − defect penalties, then every cap (gates, defects, acceptance, floors)."""
    caps, notes, improve = [], [], []
    for g in gates.get("gates", []):
        if g["verdict"] == "ERROR":
            caps.append((0.0, f"gate {g['name']} could not run"))
        elif g["verdict"] in ("FAIL", "PARTIAL FAIL"):
            caps.append((rub.get("gate_fail_cap", 0.6), f"gate {g['name']} FAIL"))
            improve += [f"[gate/{g['name']}] {short(ln)}" for ln in g["fails"][:8]]
        elif g["partial"] and spec.get("level") == "N2":
            caps.append((rub.get("gate_partial_cap", 0.85), f"gate {g['name']} only partial"))
    if judgment is None:                                   # no judge: the gates and the code-checked items decide
        overall, crit_scores, floors = 1.0, {}, []
        defects, jacc = {}, {}
    else:
        crit_scores, floors = {}, []
        wsum = tot = 0.0
        for c in rub["criteria"]:
            if c.get("kind") == "measured":
                if c["id"] not in measured:
                    notes.append(f"{c['id']} not measured: weight dropped")
                    continue
                s = clamp(eval_map(c.get("map", {}), measured[c["id"]]))
            else:
                s = clamp((judgment.get("criteria", {}).get(c["id"]) or {}).get("score", 0.0))
            crit_scores[c["id"]] = s
            wsum += c["weight"]
            tot += c["weight"] * s
            if c.get("floor") is not None and s < c["floor"]:
                floors.append(c["id"])
                caps.append((rub.get("floor_cap", 0.6), f"{c['id']} {s:.2f} under its floor {c['floor']}"))
        overall = tot / wsum if wsum else 0.0
        defects = judgment.get("defects", {})
        for dfn in rub.get("defects", []):
            if (defects.get(dfn["id"]) or {}).get("present"):
                overall -= dfn.get("penalty", 0.0)
                if dfn.get("cap") is not None:
                    caps.append((dfn["cap"], f"defect {dfn['id']}"))
        jacc = judgment.get("acceptance", {})
    acc_rows, must, ok_must = [], 0, 0
    for x in plan.get("acceptance", []):
        how, state = x.get("how"), "pending"
        if how == "verify":
            st = [g["checks"].get(x.get("check")) for g in gates.get("gates", []) if g["kind"] == "cad_verify"]
            st = [s for s in st if s]
            full = all(not g["partial"] for g in gates.get("gates", []) if g["kind"] == "cad_verify")
            state = "verified" if st and full and all(s["fail"] == 0 for s in st) else \
                "failed" if any(s["fail"] for s in st) else "pending"
        elif how == "measure" and x.get("gate"):             # code answers: the named gate's verdict, not the judge
            st = [g["verdict"] for g in gates.get("gates", []) if g["name"] == x["gate"]]
            state = "verified" if st == ["PASS"] else "failed" if st and st[0] in ("FAIL", "PARTIAL FAIL") else \
                "pending"
        elif how in ("visual", "measure") and judgment is not None:
            state = "verified" if (jacc.get(x["id"]) or {}).get("verified") else "failed"
        acc_rows.append((x["id"], x["priority"], how, state, x["text"]))
        if x["priority"] == "must" and how not in ("morante", "print"):
            must += 1
            ok_must += state == "verified"
            if state != "verified":
                improve.append(f"[acceptance/{x['id']}] {x['text']} ({state})")
    if must and ok_must < must:
        caps.append((0.6 + 0.4 * ok_must / must, f"must acceptance {ok_must}/{must} verified"))
    for f in floors:
        improve.append(f"[floor/{f}] raise {f} over its floor")
    if judgment is not None:
        for it in sorted(judgment.get("improvement_plan", []), key=lambda i: i.get("priority", 9))[:6]:
            improve.append(f"[judge/{it.get('target')}] {it.get('instruction')} ({it.get('expected_gain', '')})")
    overall = clamp(overall)
    raw = overall
    for c, why in caps:
        overall = min(overall, c)
    thr = (spec.get("judge") or {}).get("pass_threshold", rub.get("pass_threshold", 0.75))  # Morante may set a design's own
    passed = overall >= thr and not floors and \
        all(g["verdict"] == "PASS" for g in gates.get("gates", []))
    return {"overall": round(overall, 3), "raw": round(raw, 3), "passed": passed,
            "caps": [f"{c:.2f} {why}" for c, why in caps if c < raw + 1e-9], "criteria": crit_scores,
            "acceptance": acc_rows, "improvement": improve, "notes": notes, "judged": judgment is not None}


def eval_map(m, x):
    """Piecewise-linear map of a measured value to 0..1 from anchor points {"0.85": 1.0, "0.27": 0.1}."""
    pts = sorted((float(k), float(v)) for k, v in m.items()) or [(0.0, 0.0), (1.0, 1.0)]
    if x <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


def cmd_score(a):
    ws, n = os.path.abspath(a.ws), int(a.n)
    d = rdir(ws, n)
    spec, plan = jload(os.path.join(ws, "spec.json")), jload(os.path.join(d, "src", "plan.json"))
    gates, rnd = jload(os.path.join(d, "gates.json")), jload(os.path.join(d, "round.json"))
    if None in (spec, plan, gates, rnd):
        print(f"ERROR round r{n:02d} is not packed: run round {n}")
        return 2
    judged = spec.get("judge", {}).get("enabled")
    judgment = jload(os.path.join(d, "judgment.json")) if judged else None
    if judged and judgment is None:
        print(f"ERROR no judgment.json in {d}: hand the JUDGE INSTRUCTION to a fresh looks-judge first")
        return 2
    rub = rubric(spec.get("judge", {}).get("rubric", "looks")) if judged else {"pass_threshold": 0.75}
    res = score_round(spec, plan, gates, rub, judgment, rnd.get("measured", {}))
    jsave(os.path.join(d, "score.json"), res)
    print(f"{'PASS' if res['passed'] else 'FAIL'} r{n:02d} overall {res['overall']:.2f}"
          + (f" (raw {res['raw']:.2f}, capped)" if res["caps"] else "") + ("" if res["judged"] else " (no judge)"))
    for c in res["caps"]:
        print(f"  cap   {c}")
    if res["criteria"]:
        print("  criteria: " + ", ".join(f"{k} {v:.2f}" for k, v in res["criteria"].items()))
    for i, pr, how, st, txt in res["acceptance"]:
        print(f"  acc   {i} {pr:6s} {how:8s} {st:9s} {txt[:90]}")
    for x in res["notes"]:
        print(f"  note  {x}")
    print("improvement list (the next refine round makes exactly these, gate items first):" if res["improvement"]
          else "improvement list: empty")
    for x in res["improvement"]:
        print(f"  - {x}")
    print(f"  images: " + ", ".join(p for _, p in rnd.get("images", [])))
    return 0 if res["passed"] else 1


# ---------------------------------------------------------------- status and best

def rounds_of(ws):
    out = []
    for d in sorted(glob.glob(os.path.join(ws, "rounds", "r[0-9][0-9]"))):
        out.append((int(os.path.basename(d)[1:]), jload(os.path.join(d, "score.json")),
                    jload(os.path.join(d, "gates.json"))))
    return out


def best_round(rs):
    scored = [(s["overall"], s["passed"], -n, n) for n, s, _ in rs if s]
    return max(scored)[3] if scored else None


def cmd_status(a):
    ws = os.path.abspath(a.ws)
    spec = jload(os.path.join(ws, "spec.json")) or {}
    rs = rounds_of(ws)
    if not rs:
        print(f"PASS no rounds yet in {ws}")
        return 0
    b = best_round(rs)
    print(f"PASS {spec.get('design')}: {len(rs)} rounds, refine rounds asked {spec.get('refine_rounds', 0)}; "
          f"best r{b:02d}" if b is not None else "PASS no round scored yet")
    print("| Round | Gates | Score | Passed | Caps |\n|---|---|---|---|---|")
    falls = 0
    prev = None
    for n, s, g in rs:
        print(f"| r{n:02d} | {g['verdict'] if g else '—'} | {s['overall']:.2f} | {'yes' if s['passed'] else 'no'} | "
              f"{'; '.join(s['caps']) or '—'} |" if s else f"| r{n:02d} | {g['verdict'] if g else '—'} | — | — | — |")
        if s and prev is not None:
            falls = falls + 1 if s["overall"] < prev else 0
        prev = s["overall"] if s else prev
    done = len(rs) - 1 >= spec.get("refine_rounds", 0)
    last = rs[-1][1]
    if last and last["passed"] and not last["improvement"]:
        print("STOP: passed with an empty improvement list")
    elif falls >= 2:
        print("STOP: the score fell two rounds running; the deliverable is the best round")
    elif done:
        print("STOP: the refine rounds Morante asked for are done")
    else:
        print(f"next: refine round r{len(rs):02d} makes exactly the last score's improvement list")
    return 0


def cmd_best(a):
    ws = os.path.abspath(a.ws)
    b = best_round(rounds_of(ws))
    if b is None:
        print("ERROR no scored round")
        return 2
    rnd = jload(os.path.join(rdir(ws, b), "round.json"))
    back = []
    for f in rnd["files"]:
        if f["snap"] == "plan.json":
            continue
        shutil.copy2(os.path.join(rdir(ws, b), "src", f["snap"]), os.path.join(ROOT, f["path"]))
        back.append(f["path"])
    print(f"PASS restored r{b:02d}'s source ({', '.join(back)}); now build and run check so out/ and images/ match "
          f"it")
    return 0


# ---------------------------------------------------------------- ready to print

def spec_names(path):
    """What a cad_verify spec declares at module level, read without running it (building is slow): name -> AST
    value, and how many literal {"hardware": True, ...} parts lack a "label"."""
    tree = ast.parse(open(path).read())
    names = {t.id: node.value for node in tree.body if isinstance(node, ast.Assign)
             for t in node.targets if isinstance(t, ast.Name)}
    unlabelled = 0
    for d in ast.walk(tree):
        if isinstance(d, ast.Dict):
            pairs = [(k.value, v) for k, v in zip(d.keys, d.values) if isinstance(k, ast.Constant)]
            hw = any(k == "hardware" and isinstance(v, ast.Constant) and v.value is True for k, v in pairs)
            unlabelled += hw and "label" not in [k for k, _ in pairs]
    return names, unlabelled


def _missing(kit_html):
    """Lines the workshop kit could not fill: «MISSING:» (English kit) or «FALTA:» (Spanish)."""
    return kit_html.count("MISSING:") + kit_html.count("FALTA:")


def ready_items(plan, rs, verify_txt, names, unlabelled, fit_status, kit_html, coupons):
    """The ready-to-print checklist as (state, text): PASS, FAIL, or HAND (only a person or an agent's reply can
    tell). Pure: the tests feed it the files' contents."""
    out = []
    b = best_round(rs)
    if b is None:
        out.append(("FAIL", "no scored round: run round and score first"))
    else:
        s, last = {n: sc for n, sc, _ in rs}[b], rs[-1][0]
        out.append(("PASS" if b == last else "FAIL", f"r{b:02d} is the best round" +
                    ("" if b == last else f", not the last (r{last:02d}): run best, then check")))
        gate = [x for x in s["improvement"] if x.startswith("[gate/")]
        out.append(("FAIL" if gate else "PASS", f"gate items in its score: {len(gate)}"))
        musts = [i for i, pr, how, st, _ in s["acceptance"]
                 if pr == "must" and how not in ("morante", "print") and st != "verified"]
        out.append(("FAIL" if musts else "PASS", "must acceptance unverified: " + (", ".join(musts) or "none")))
    first = (verify_txt or "").splitlines()[:1]
    out.append(("PASS" if first and first[0].startswith("cad_verify: PASS") else "FAIL", "verify-result.txt: " +
                (first[0] if first else "missing (full run with --out <design>/verify-result.txt)")))
    for k, need, may_be_empty in (("JOINTS", "every joint of the joint table", False),
                                  ("MARKS", "every gear and phased part", True),
                                  ("MEASURE", "what to check with the caliper", False)):
        v = names.get(k)
        empty = isinstance(v, ast.Dict) and not v.keys or isinstance(v, ast.List) and not v.elts
        out.append(("FAIL" if v is None or (empty and not may_be_empty) else "PASS",
                    f"{k} " + ("missing" if v is None else "empty" if empty else "declared") + f" ({need})"))
    lab = names.get("LABELS")
    es = isinstance(lab, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == "es" for k in lab.keys)
    out.append(("PASS" if es else "FAIL", 'LABELS["es"] ' + ("declared" if es else "missing")))
    out.append(("FAIL" if unlabelled else "PASS", f"hardware parts without a label: {unlabelled}"))
    used = sorted({j["fit"].split(".")[-1] for j in plan.get("joints", []) if j.get("fit")})
    assumed = [f for f in used if fit_status.get(f) == "assumed"]
    out.append(("PASS" if not assumed else "HAND" if coupons else "FAIL",
                "assumed fits: " + (", ".join(assumed) or "none") +
                (" (this print is their coupon)" if assumed and coupons else
                 " (print their coupons first, or pass --coupons)" if assumed else "")))
    out.append(("FAIL", "kit: not given or not found (--kit kits/<NN-step>/kit.html)") if kit_html is None
               else ("FAIL" if _missing(kit_html) else "PASS", f"kit MISSING/FALTA: {_missing(kit_html)}"))
    out.append(("HAND", "design-reviewer APPROVE at the pre-print gate; every WARN explained in design-review.md"))
    out.append(("HAND", "print-plater PASS, grams and hours known"))
    return out


def cmd_ready(a):
    ws = os.path.abspath(a.ws)
    spec, plan = jload(os.path.join(ws, "spec.json")), jload(os.path.join(ws, "plan.json"))
    if spec is None or plan is None:
        print(f"ERROR {ws} has no spec.json or plan.json")
        return 2
    gate = next((g for g in spec.get("gates", []) if g.get("kind") == "cad_verify"), None)
    if gate is None:
        print("ERROR no cad_verify gate in spec.json: N0 and N1 are not printed")
        return 2
    try:
        names, unlabelled = spec_names(expand(gate["spec"], ws))
    except (OSError, SyntaxError) as e:
        print(f"ERROR cannot read the verify spec: {e}")
        return 2
    sys.path.insert(0, ROOT)
    from cad import fits
    status = {k: v.status for k, v in vars(fits).items() if type(v).__name__ == "Fit"}
    vt = os.path.join(ws, "verify-result.txt")
    items = ready_items(plan, rounds_of(ws), open(vt).read() if os.path.exists(vt) else None, names, unlabelled,
                        status, open(a.kit).read() if a.kit and os.path.exists(a.kit) else None, a.coupons)
    fails = sum(st == "FAIL" for st, _ in items)
    print(("FAIL" if fails else "PASS") + f" ready to print: {fails} missing" +
          ("" if fails else "; confirm the HAND items, then «imprime»"))
    for st, t in items:
        print(f"  {st:4s}  {t}")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init", help="write spec.json (once)")
    p.add_argument("ws")
    p.add_argument("--level", required=True, choices=LEVELS)
    p.add_argument("--purpose", required=True)
    p.add_argument("--pass-criterion")
    p.add_argument("--must-have", action="append")
    p.add_argument("--must-not", action="append")
    p.add_argument("--ref", action="append", help="reference image, e.g. {root}/cad/carcass-jenscolt/images/jenscolt-photo-1.jpg")
    p.add_argument("--rounds", type=int, default=0, help="refine rounds Morante asked for (default 0: one round)")
    p.add_argument("--mesh", action="append", help="a conversion: PART=reference.stl (repo-relative), once per part")
    p.add_argument("--edit", action="store_true", help="conversion of an organic part: also the build.py --edit gate")
    p = sub.add_parser("except", help="record an exception Morante approved for one part, with his reason")
    p.add_argument("ws")
    p.add_argument("part", help="the part (its fidelity gate is fidelity-<part>)")
    p.add_argument("--reason", required=True, help="Morante's reason, in his words")
    p.add_argument("--p95", type=float, help="this part's own p95 limit (mm)")
    p.add_argument("--max", type=float, help="this part's own max limit (mm)")
    p.add_argument("--judge", type=float, help="the design's own pass threshold for the looks judge")
    p.add_argument("--drop", action="append", help="a detail of the reference left out on purpose")
    for name in ("validate", "check", "status", "best"):
        sub.add_parser(name).add_argument("ws")
    for name in ("round", "score"):
        p = sub.add_parser(name)
        p.add_argument("ws")
        p.add_argument("n")
        if name == "round":
            p.add_argument("--force", action="store_true")
    p = sub.add_parser("ready", help="the ready-to-print checklist, from the files")
    p.add_argument("ws")
    p.add_argument("--kit", help="the workshop kit.html for this print")
    p.add_argument("--coupons", action="store_true", help="this print is the coupons for the assumed fits")
    a = ap.parse_args()
    fn = {"init": cmd_init, "except": cmd_except, "validate": cmd_validate, "check": cmd_check, "round": cmd_round, "score": cmd_score,
          "status": cmd_status, "best": cmd_best, "ready": cmd_ready}[a.cmd]
    rc = fn(a)
    if a.cmd == "check":  # cmd_check returns the gates (cmd_round reuses them), or None when it could not run
        rc = 2 if rc is None or rc["verdict"] == "ERROR" else 1 if rc["verdict"] == "FAIL" else 0
    return rc


if __name__ == "__main__":
    sys.exit(main())
