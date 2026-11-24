"""Workshop kit: everything Morante needs at the bench for one print-and-assemble step, in one page for the phone.

Made before every print that Morante will assemble or measure, from the design's cad_verify spec (parts, assembly
order, fasteners, marks, measurements) plus a short notes file the documenter writes. Kits live in the repo, in
English, under kits/<NN-step>/ (kit.html plus its PNGs, linked; GitHub Pages serves them). The page always has the
same sections, so nothing has to be asked for again:

  1. What this tests        what this print is for, and what result means it works
  2. What to print          each plate: what it is for, grams, hours; and what not to print yet
  3. What you need          every printed part (also those from earlier plates) and every screw, pin and nut with its
                            exact size and count, from the spec; the tools
  4. Assembly               one big picture per step (tools/figures.py), what to do and how to know it is right,
                            the alignment marks of that step
  5. Measure                a drawing per measurement: where the caliper goes, the expected value and tolerance
  6. What to film           shots and angles for the build log

Anything the notes leave out shows as a red MISSING line (FALTA in Spanish) instead of disappearing, so a missing
piece is seen before the kit reaches Morante.

Notes file (JSON, in the kit's language), all keys optional (the old Spanish keys titulo, que_prueba, funciona_si,
imprimir/placa/para_que/gramos/horas, no_imprimir_aun, herramientas, piezas_previas, pasos, comprobar, grabar, mesa,
cuando are still read):
    {"title": "...", "tests": "...", "works_if": "...",
     "print": [{"plate": "print/x.3mf", "what_for": "...", "grams": 12, "hours": 1.5}],
     "not_yet": ["..."], "tools": ["1.5 mm hex key", "caliper"],
     "earlier_parts": ["red fork from plate legs-forks-v1"],
     "steps": {"<part name>": "what to do"}, "check": {"<part name>": "how to know it is right"},
     "record": ["..."], "bench": {"+X": "up", "+Z": "toward"},
     "when": {"<MEASURE what>": "when it is measured"}}
"bench": where the model axes point on the bench (up/down/toward/away/left/right; the spec's BENCH_POSE does the same
and wins): a bench step then reads «on the bench: down» instead of «in from the +X side». MEASURE's "when" is shown
per measurement (when_<lang>, or notes "when", or the "when" as given); none: a MISSING line.
Spec fields used (see cad_verify.py and figures.py): PARTS (with "label" for hardware, e.g. "M2×6 Allen", and
"label_<lang>" when the kit's language differs),
ASSEMBLY, ACCESS, MARKS, MEASURE, LABELS[lang] (part names; without them the file names are used).

    python3 tools/workshop_kit.py <spec.py> kits/<NN-step> --notes kits/<NN-step>/notes.json [--lang en] [--embed]
    → <out dir>/kit.html plus the PNGs (linked; --embed puts them inside the page, one file to send)
"""
import argparse
import base64
import collections
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figures  # noqa: E402
from cad_verify import load_meshes, load_spec  # noqa: E402

CSS = """body{font:17px/1.45 -apple-system,system-ui,sans-serif;margin:0 auto;max-width:760px;padding:16px;color:#1a1a1a;
background:#fff}h1{font-size:1.5em;margin:.2em 0}h2{font-size:1.2em;border-bottom:2px solid #1a1a1a;margin-top:1.6em}
img{width:100%;height:auto;border:1px solid #ddd;border-radius:6px}table{border-collapse:collapse;width:100%}
td,th{border-bottom:1px solid #ddd;padding:6px 4px;text-align:left;vertical-align:top}.falta{color:#c0392b;
font-weight:bold}.paso{border:1px solid #ccc;border-radius:8px;padding:10px;margin:14px 0}.n{display:inline-block;
background:#1a1a1a;color:#fff;border-radius:50%;width:1.8em;height:1.8em;text-align:center;line-height:1.8em;
font-weight:bold;margin-right:.4em}.ok{color:#1e7e34}.mark{background:#fff3cd;padding:2px 6px;border-radius:4px}"""


# Fixed text of the page, per language
TXT = {
    "en": {"title": "Workshop kit", "missing": "MISSING", "s1": "1 · What this tests", "works": "Works if:",
           "m_tests": "what this print tests", "m_works": "what result means it works",
           "s2": "2 · What to print", "th_print": ("Plate", "What for", "g", "h"),
           "m_print": "plates to print, what for, grams and hours", "not_yet": "Do not print yet:",
           "s3": "3 · What you need", "printed": "Printed parts", "earlier": "Also, from earlier prints:",
           "hw": "Hardware", "m_label": "exact size (PARTS[...]['label']) of: ", "tools": "Tools:", "m_tools": "tools",
           "s4": "4 · Assembly", "exploded": "Every part, with its step number:",
           "m_step": "what to do in step {}", "mark": "Mark:", "m_check": "how to know step {} is right",
           "m_order": "assembly order (ASSEMBLY in the spec)", "s5": "5 · Measure",
           "nothing": "Nothing to measure in this step (no MEASURE in the spec).", "th_meas": ("Measurement", "When"),
           "m_when": "when it is measured", "s6": "6 · What to film",
           "m_record": "which photos and videos to take, and from which angle",
           "files": ("exploded.png", "measure.png", "step")},
    "es": {"title": "Paquete de taller", "missing": "FALTA", "s1": "1 · Qué se prueba", "works": "Funciona si:",
           "m_tests": "qué prueba esta impresión", "m_works": "qué resultado significa que funciona",
           "s2": "2 · Qué imprimir", "th_print": ("Placa", "Para qué", "g", "h"),
           "m_print": "placas a imprimir, para qué, gramos y horas", "not_yet": "No imprimir todavía:",
           "s3": "3 · Qué necesitas", "printed": "Piezas impresas", "earlier": "Además, de impresiones anteriores:",
           "hw": "Tornillería", "m_label": "medida exacta (PARTS[...]['label']) de: ", "tools": "Herramientas:",
           "m_tools": "herramientas", "s4": "4 · Montaje", "exploded": "Todas las piezas, con su número de paso:",
           "m_step": "qué hacer en el paso {}", "mark": "Marca:", "m_check": "cómo saber que el paso {} está bien",
           "m_order": "orden de montaje (ASSEMBLY en el spec)", "s5": "5 · Medir",
           "nothing": "Nada que medir en este paso (sin MEASURE en el spec).", "th_meas": ("Medida", "Cuándo"),
           "m_when": "cuándo se mide", "s6": "6 · Qué grabar",
           "m_record": "qué fotos y vídeos hacer, y desde qué ángulo",
           "files": ("despiece.png", "medir.png", "paso")},
}
# Old Spanish note keys → the English ones
ALIASES = {"titulo": "title", "que_prueba": "tests", "funciona_si": "works_if", "imprimir": "print",
           "no_imprimir_aun": "not_yet", "herramientas": "tools", "piezas_previas": "earlier_parts", "pasos": "steps",
           "comprobar": "check", "grabar": "record", "mesa": "bench", "cuando": "when"}
PLATE_ALIASES = {"placa": "plate", "para_que": "what_for", "gramos": "grams", "horas": "hours"}


def read_notes(path):
    raw = json.load(open(path)) if path else {}
    notes = {ALIASES.get(k, k): v for k, v in raw.items()}
    notes["print"] = [{PLATE_ALIASES.get(k, k): v for k, v in p.items()} for p in notes.get("print", [])]
    return notes


def esc(s):
    return html.escape(str(s))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("outdir")
    ap.add_argument("--notes", help="kit notes (JSON) in the kit's language")
    ap.add_argument("--lang", default="en", choices=sorted(TXT))
    ap.add_argument("--embed", action="store_true", help="images inside the page (one file to send); default: linked")
    args = ap.parse_args()
    lang, T = args.lang, TXT[args.lang]
    spec = load_spec(args.spec)
    meshes = load_meshes(spec, args.spec)
    notes = read_notes(args.notes)
    if notes.get("bench") and not hasattr(spec, "BENCH_POSE"):
        spec.BENCH_POSE = notes["bench"]    # bench steps read as seen on the bench (the spec's own BENCH_POSE wins)
    os.makedirs(args.outdir, exist_ok=True)
    L = lambda n: figures.label(spec, n, lang)  # noqa: E731

    def falta(what):
        return f'<p class="falta">{T["missing"]}: {esc(what)}</p>'

    def img(path):
        if not args.embed:
            return f'<img src="{esc(os.path.relpath(path, args.outdir))}" loading="lazy">'
        with open(path, "rb") as f:
            return f'<img src="data:image/png;base64,{base64.b64encode(f.read()).decode()}">'

    from cad_verify import steps
    seq = steps(spec)           # a step may move a tuple of parts as one body, or be done on the bench
    marks = getattr(spec, "MARKS", {})
    title = notes.get("title", T["title"])
    out = [f"<!doctype html><html lang={lang}><meta charset=utf-8>"
           f"<meta name=viewport content='width=device-width,initial-scale=1'>"
           f"<title>{esc(title)}</title><style>{CSS}</style>", f"<h1>{esc(title)}</h1>"]

    out.append(f"<h2>{T['s1']}</h2>")
    out.append(f"<p>{esc(notes['tests'])}</p>" if notes.get("tests") else falta(T["m_tests"]))
    out.append(f"<p><b>{T['works']}</b> {esc(notes['works_if'])}</p>" if notes.get("works_if") else falta(T["m_works"]))

    out.append(f"<h2>{T['s2']}</h2>")
    if notes.get("print"):
        out.append("<table><tr>" + "".join(f"<th>{h}</th>" for h in T["th_print"]) + "</tr>" + "".join(
            f"<tr><td>{esc(p.get('plate', ''))}</td><td>{esc(p.get('what_for', ''))}</td>"
            f"<td>{esc(p.get('grams', '?'))}</td><td>{esc(p.get('hours', '?'))}</td></tr>"
            for p in notes["print"]) + "</table>")
    else:
        out.append(falta(T["m_print"]))
    if notes.get("not_yet"):
        out.append(f"<p><b>{T['not_yet']}</b></p><ul>" + "".join(f"<li>{esc(x)}</li>" for x in notes["not_yet"])
                   + "</ul>")

    out.append(f"<h2>{T['s3']}</h2>")
    printed = [n for n, p in spec.PARTS.items() if not p.get("hardware")]
    hw = collections.Counter(p.get(f"label_{lang}") or p.get("label", n) for n, p in spec.PARTS.items() if p.get("hardware"))
    unlabeled = [n for n, p in spec.PARTS.items() if p.get("hardware") and "label" not in p]
    out.append(f"<p><b>{T['printed']}</b></p><ul>" + "".join(f"<li>{esc(L(n))}</li>" for n in printed) + "</ul>")
    for x in notes.get("earlier_parts", []):
        out.append(f"<p>{T['earlier']} {esc(x)}</p>")
    out.append(f"<p><b>{T['hw']}</b></p><table>" + "".join(f"<tr><td>{c} ×</td><td>{esc(k)}</td></tr>"
                                                         for k, c in sorted(hw.items())) + "</table>")
    if unlabeled:
        out.append(falta(T["m_label"] + ", ".join(unlabeled)))
    out.append(f"<p><b>{T['tools']}</b> " + esc(", ".join(notes["tools"])) + "</p>" if notes.get("tools")
               else falta(T["m_tools"]))

    out.append(f"<h2>{T['s4']}</h2>")
    f_ex, f_ms, f_step = T["files"]
    ex = figures.exploded(spec, meshes, os.path.join(args.outdir, f_ex), lang=lang)
    if ex:
        out.append(f"<p>{T['exploded']}</p>" + img(ex))
    pics = figures.step_pictures(spec, meshes, args.outdir, lang=lang, prefix=f_step)
    for k, (st, pic) in enumerate(zip(seq, pics)):
        d = st["d"]
        # notes are keyed by the part, or for a sub-assembly by «a + b + c» (else its first part's note)
        n = " + ".join(st["names"])
        if n not in notes.get("steps", {}) and n not in notes.get("check", {}):
            n = st["names"][0]
        how = figures.step_words(st, spec, lang)
        name = " + ".join(L(x) for x in st["names"])
        out.append(f'<div class="paso"><p><span class="n">{k + 1}</span><b>{esc(name)}</b> · {esc(how)}</p>')
        out.append(img(pic))
        out.append(f"<p>{esc(notes['steps'][n])}</p>" if notes.get("steps", {}).get(n)
                   else (falta(T["m_step"].format(k + 1)) if d is not None else ""))
        if n in marks:
            out.append(f'<p><span class="mark">{T["mark"]} {esc(marks[n])}</span></p>')
        out.append(f'<p class="ok">✓ {esc(notes["check"][n])}</p>' if notes.get("check", {}).get(n)
                   else (falta(T["m_check"].format(k + 1)) if d is not None else ""))
        out.append("</div>")
    if not seq:
        out.append(falta(T["m_order"]))

    out.append(f"<h2>{T['s5']}</h2>")
    ms = figures.measure_sheet(spec, meshes, os.path.join(args.outdir, f_ms), lang=lang)
    out.append(img(ms) if ms else f"<p>{T['nothing']}</p>")
    if ms:
        # when each one is taken: MEASURE's "when_<lang>", else notes["when"][what], else the "when" as given
        out.append("<table><tr>" + "".join(f"<th>{h}</th>" for h in T["th_meas"]) + "</tr>")
        for k, mz in enumerate(spec.MEASURE):
            w = mz.get(f"when_{lang}") or notes.get("when", {}).get(mz["what"]) or mz.get("when")
            nm = esc(f"{k + 1}. {mz.get('what_' + lang, mz['what'])}")
            out.append(f"<tr><td>{nm}</td><td>{esc(w)}</td></tr>" if w
                       else f'<tr><td>{nm}</td><td class="falta">{T["missing"]}: {T["m_when"]}</td></tr>')
        out.append("</table>")

    out.append(f"<h2>{T['s6']}</h2>")
    out.append("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in notes["record"]) + "</ul>" if notes.get("record")
               else falta(T["m_record"]))

    page = os.path.join(args.outdir, "kit.html")
    with open(page, "w") as f:
        f.write("\n".join(out))
    n_falta = sum(s.count('class="falta"') for s in out)
    print(page)
    print(f"{n_falta} {T['missing']}" if n_falta else "complete")
    sys.exit(1 if n_falta else 0)


if __name__ == "__main__":
    main()
