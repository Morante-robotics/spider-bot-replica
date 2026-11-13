"""Workshop kit: everything Morante needs at the bench for one print-and-assemble step, in one page for the phone.

Made before every print that Morante will assemble or measure, from the design's cad_verify spec (parts, assembly
order, fasteners, marks, measurements) plus a short notes file the documenter writes in Spanish. The page always has
the same sections, so nothing has to be asked for again:

  1. Qué se prueba          what this print is for, and what result means it works
  2. Qué imprimir           each plate: what it is for, grams, hours; and what not to print yet
  3. Qué necesitas          every printed part (also those from earlier plates) and every screw, pin and nut with its
                            exact size and count, from the spec; the tools
  4. Montaje                one big picture per step (tools/figures.py), what to do and how to know it is right,
                            the alignment marks of that step
  5. Medir                  a drawing per measurement: where the caliper goes, the expected value and tolerance
  6. Qué grabar             shots and angles for the build log

Anything the notes leave out shows as a red «FALTA» line instead of disappearing, so a missing piece is seen before
the kit reaches Morante.

Notes file (JSON, Spanish), all keys optional:
    {"titulo": "...", "que_prueba": "...", "funciona_si": "...",
     "imprimir": [{"placa": "print/x.3mf", "para_que": "...", "gramos": 12, "horas": 1.5}],
     "no_imprimir_aun": ["..."], "herramientas": ["destornillador Allen 2,5", "calibre"],
     "piezas_previas": ["horquilla roja de la placa legs-forks-v1"],
     "pasos": {"<part name>": "qué hacer"}, "comprobar": {"<part name>": "cómo sé que está bien"},
     "grabar": ["..."]}
Spec fields used (see cad_verify.py and figures.py): PARTS (with "label" for hardware, e.g. "M3×12 Allen"), ASSEMBLY,
ACCESS, MARKS, MEASURE, LABELS["es"].

    python3 tools/workshop_kit.py <spec.py> <out dir> --notes kit-notes-es.json
    → <out dir>/kit.html (one file, images inside) plus the PNGs
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


def esc(s):
    return html.escape(str(s))


def falta(what):
    return f'<p class="falta">FALTA: {esc(what)}</p>'


def img(path):
    with open(path, "rb") as f:
        return f'<img src="data:image/png;base64,{base64.b64encode(f.read()).decode()}">'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("outdir")
    ap.add_argument("--notes", help="kit notes in Spanish (JSON)")
    args = ap.parse_args()
    spec = load_spec(args.spec)
    meshes = load_meshes(spec, args.spec)
    notes = json.load(open(args.notes)) if args.notes else {}
    os.makedirs(args.outdir, exist_ok=True)
    L = lambda n: figures.label(spec, n, "es")  # noqa: E731
    seq = list(getattr(spec, "ASSEMBLY", []))
    marks = getattr(spec, "MARKS", {})
    out = [f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
           f"<title>{esc(notes.get('titulo', 'Paquete de taller'))}</title><style>{CSS}</style>",
           f"<h1>{esc(notes.get('titulo', 'Paquete de taller'))}</h1>"]

    out.append("<h2>1 · Qué se prueba</h2>")
    out.append(f"<p>{esc(notes['que_prueba'])}</p>" if notes.get("que_prueba") else falta("qué prueba esta impresión"))
    out.append(f"<p><b>Funciona si:</b> {esc(notes['funciona_si'])}</p>" if notes.get("funciona_si")
               else falta("qué resultado significa que funciona"))

    out.append("<h2>2 · Qué imprimir</h2>")
    if notes.get("imprimir"):
        out.append("<table><tr><th>Placa</th><th>Para qué</th><th>g</th><th>h</th></tr>" + "".join(
            f"<tr><td>{esc(p.get('placa', ''))}</td><td>{esc(p.get('para_que', ''))}</td>"
            f"<td>{esc(p.get('gramos', '?'))}</td><td>{esc(p.get('horas', '?'))}</td></tr>"
            for p in notes["imprimir"]) + "</table>")
    else:
        out.append(falta("placas a imprimir, para qué, gramos y horas"))
    if notes.get("no_imprimir_aun"):
        out.append("<p><b>No imprimir todavía:</b></p><ul>" +
                   "".join(f"<li>{esc(x)}</li>" for x in notes["no_imprimir_aun"]) + "</ul>")

    out.append("<h2>3 · Qué necesitas</h2>")
    printed = [n for n, p in spec.PARTS.items() if not p.get("hardware")]
    hw = collections.Counter(p.get("label", n) for n, p in spec.PARTS.items() if p.get("hardware"))
    unlabeled = [n for n, p in spec.PARTS.items() if p.get("hardware") and "label" not in p]
    out.append("<p><b>Piezas impresas</b></p><ul>" + "".join(f"<li>{esc(L(n))}</li>" for n in printed) + "</ul>")
    for x in notes.get("piezas_previas", []):
        out.append(f"<p>Además, de impresiones anteriores: {esc(x)}</p>")
    out.append("<p><b>Tornillería</b></p><table>" + "".join(f"<tr><td>{c} ×</td><td>{esc(k)}</td></tr>"
                                                           for k, c in sorted(hw.items())) + "</table>")
    if unlabeled:
        out.append(falta("medida exacta (PARTS[...]['label']) de: " + ", ".join(unlabeled)))
    out.append("<p><b>Herramientas:</b> " + esc(", ".join(notes["herramientas"])) + "</p>" if notes.get("herramientas")
               else falta("herramientas"))

    out.append("<h2>4 · Montaje</h2>")
    ex = figures.exploded(spec, meshes, os.path.join(args.outdir, "despiece.png"), lang="es")
    if ex:
        out.append("<p>Todas las piezas, con su número de paso:</p>" + img(ex))
    pics = figures.step_pictures(spec, meshes, args.outdir, lang="es")
    for k, ((n, d), pic) in enumerate(zip(seq, pics)):
        how = figures.WORDS["es"]["first"] if d is None else figures.direction_words(d, "es")
        out.append(f'<div class="paso"><p><span class="n">{k + 1}</span><b>{esc(L(n))}</b> · {esc(how)}</p>')
        out.append(img(pic))
        out.append(f"<p>{esc(notes['pasos'][n])}</p>" if n in notes.get("pasos", {})
                   else (falta(f"qué hacer en el paso {k + 1}") if d is not None else ""))
        if n in marks:
            out.append(f'<p><span class="mark">Marca: {esc(marks[n])}</span></p>')
        out.append(f'<p class="ok">✓ {esc(notes["comprobar"][n])}</p>' if n in notes.get("comprobar", {})
                   else (falta(f"cómo saber que el paso {k + 1} está bien") if d is not None else ""))
        out.append("</div>")
    if not seq:
        out.append(falta("orden de montaje (ASSEMBLY en el spec)"))

    out.append("<h2>5 · Medir</h2>")
    ms = figures.measure_sheet(spec, meshes, os.path.join(args.outdir, "medir.png"), lang="es")
    out.append(img(ms) if ms else "<p>Nada que medir en este paso (sin MEASURE en el spec).</p>")

    out.append("<h2>6 · Qué grabar</h2>")
    out.append("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in notes["grabar"]) + "</ul>" if notes.get("grabar")
               else falta("qué fotos y vídeos hacer, y desde qué ángulo"))

    page = os.path.join(args.outdir, "kit.html")
    with open(page, "w") as f:
        f.write("\n".join(out))
    n_falta = sum(s.count('class="falta"') for s in out)
    print(page)
    print(f"{n_falta} FALTA" if n_falta else "complete")
    sys.exit(1 if n_falta else 0)


if __name__ == "__main__":
    main()
