#!/usr/bin/env python3
"""Exploded view of the test frame with its screws: which screw goes where.

Usage:
    python3 screws_figure.py [--lang es|en]      # images/test-frame-screws[-es].png

Reads the STLs written by build.py and uses the renderer of onshape_figures.py.
"""
import argparse
import os

import numpy as np
import trimesh

import build as B
import onshape_figures as F

TXT = {
    "es": dict(top="M3×10 desde arriba + tuerca bajo el brazo:\nla tuerca lo fija al brazo, la punta\nentra 3 mm en la horquilla y gira ahí",
               bottom="M3×10 desde abajo + tuerca sobre el brazo:\nigual que el de arriba",
               pin="Tornillo M3×16 a través\nde horquilla y pata",
               nut="Tuerca M3", crank="Tapa: dos lengüetas bajan por las ranuras\ny sujetan el eje; 2 × M3×12 a tuercas\nmetidas en los bloques del marco",
               ball="La bola entra en el tubo",
               arm="Brazos del marco: agujero\npasante Ø{hole}", title="Marco de prueba: tornillos (despiece)",
               fork_title="La horquilla, de cerca", keep_title="La tapa del cigüeñal",
               knut="La tuerca entra por la ranura\ndel bloque, desde fuera", ftop="Agujero ciego arriba (Ø{hole})",
               fbot="Agujero ciego abajo (Ø{hole})", fside="Agujero pasante (Ø{hole})"),
    "en": dict(top="M3×10 from above + nut under the arm:\nthe nut locks it to the arm, its tip\ngoes 3 mm into the fork and turns there",
               bottom="M3×10 from below + nut on the arm:\nsame as the top one",
               pin="M3×16 screw through\nfork and leg",
               nut="M3 nut", crank="Keeper: two tongues go down the slots\nand hold the shaft; 2 × M3×12 into nuts\npushed into the frame's end blocks",
               ball="The ball goes into the tube",
               arm="Frame arms: Ø{hole}\nthrough hole", title="Test frame: screws (exploded)",
               fork_title="The fork, close up", keep_title="The shaft keeper",
               knut="The nut slides into the\nblock's slot from outside", ftop="Blind hole on top (Ø{hole})",
               fbot="Blind hole underneath (Ø{hole})", fside="Through hole (Ø{hole})"),
}
STEEL, NUT = (120, 125, 135), (90, 95, 105)


# Hole sizes come from build.py, so the labels follow any change of clearance.
HOLE = f"{B.SCREW + B.CLR_STEEL:.1f}"
TXT = {lang: {k: v.replace("{hole}", HOLE) for k, v in t.items()} for lang, t in TXT.items()}

def screw(head_at, into, length):
    """Socket-head M3 screw: head outside at head_at, shank pointing along `into`."""
    d = B.unit(into)
    shank = trimesh.creation.cylinder(1.5, length, sections=24)
    shank.apply_translation([0, 0, length / 2])
    head = trimesh.creation.cylinder(2.75, 3.0, sections=24)
    head.apply_translation([0, 0, -1.5])
    m = trimesh.util.concatenate([shank, head])
    m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], d))
    m.apply_translation(head_at)
    return m.triangles


def nut(at, axis):
    m = trimesh.creation.cylinder(3.2, 2.4, sections=6)
    m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], B.unit(axis)))
    m.apply_translation(at)
    return m.triangles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="es")
    t = TXT[ap.parse_args().lang]
    sfx = "-es" if ap.parse_args().lang == "es" else ""

    frame, crank, leg, pivot = F.mesh("test-frame"), F.mesh("crankshaft-2"), F.mesh("leg-middle-right"), F.mesh("pivot")
    ps = F.pose(np.radians(30))
    P = np.array(ps["pivot"][1], float)
    Rp = ps["pivot"][0]
    ey = Rp[:, 1]                                            # fork's screw axis (horizontal, across the leg)
    _, win_y, _, h = B.yoke_size()
    half_w = win_y / 2 + B.YOKE_WALL
    ex = 16.0                                                # how far the screws are pulled out

    gap = B.NUT_T + 0.4
    top_head = P + [0, 0, h / 2 + gap + 3.0 + ex]
    bot_head = P - [0, 0, h / 2 + gap + 3.0 + ex]
    top_nut = P + [0, 0, h / 2 + 0.4 + B.NUT_T / 2 + ex / 2]
    bot_nut = P - [0, 0, h / 2 + 0.4 + B.NUT_T / 2 + ex / 2]
    pin_head = P - ey * (half_w + ex)
    nut_at = P + ey * (half_w + 1.2 + ex)
    sh = np.array([B.CX, F.Y_SH, F.Z_SH])
    zt = F.Z_SH + 6
    kup = 14.0                                               # keeper pulled up
    keeper = F.mesh("test-frame-keeper") + [0, 0, kup]
    kparts = []
    for sy in (1, -1):
        ys = F.Y_SH + sy * B.KEEP_SCREW_Y
        kparts += [(screw([B.CX, ys, zt + 4 + kup + 8], [0, 0, -1], 12), STEEL),
                   (nut([B.CX, ys + sy * 9, zt - 5.5], [0, 0, 1]), NUT)]
    parts = kparts + [(keeper, F.COL["slider"]),
             (frame, F.COL["frame"]), (F.tf(crank, *ps["crank"]), F.COL["crank"]),
             (F.tf(pivot, *ps["pivot"]), F.COL["pivot"]), (F.tf(leg, *ps["leg"]), F.COL["leg"]),
             (screw(top_head, [0, 0, -1], 10), STEEL), (screw(bot_head, [0, 0, 1], 10), STEEL),
             (nut(top_nut, [0, 0, 1]), NUT), (nut(bot_nut, [0, 0, 1]), NUT),
             (screw(pin_head, ey, 16), STEEL), (nut(nut_at, ey), NUT)]
    lines = [("line", [top_head, P + [0, 0, h / 2]]), ("line", [bot_head, P - [0, 0, h / 2]]),
             ("line", [[B.CX, F.Y_SH + B.KEEP_SCREW_Y, zt + 4 + kup + 8], [B.CX, F.Y_SH + B.KEEP_SCREW_Y, zt]]),
             ("line", [[B.CX, F.Y_SH - B.KEEP_SCREW_Y, zt + 4 + kup + 8], [B.CX, F.Y_SH - B.KEEP_SCREW_Y, zt]]),
             ("line", [pin_head, nut_at])]
    labels = [(t["top"], top_head + [0, 0, 3], (-190, -30)), (t["bottom"], bot_head - [0, 0, 3], (-190, 30)),
              (t["pin"], pin_head, (-170, 40)), (t["nut"], nut_at, (110, -40)),
              (t["arm"], P + [0, 6, h / 2 + 2.0], (150, -80)),
              (t["ball"], ps["A"], (40, 150))]
    mid = (P + sh) / 2 + [12, 0, -5]
    img = F.render(parts, -35, 18, mid, 120, size=(1100, 760), marks=lines, labels=labels, title=t["title"])

    # the fork alone, with its three holes
    fz = YH = h
    fk = F.render([(pivot, F.COL["pivot"])], -40, 20, [0, 0, 0], 40, size=(520, 760),
                  marks=[("circle", ([0, 0, YH / 2], [0, 0, 1], (B.SCREW + B.CLR) / 2)),
                         ("circle", ([0, -half_w, 0], [0, 1, 0], (B.SCREW + B.CLR) / 2))],
                  labels=[(t["ftop"], [0, 0, YH / 2], (40, -120)), (t["fbot"], [0, 0, -YH / 2], (40, 150)),
                          (t["fside"], [0, -half_w, 0], (-60, 120))], title=t["fork_title"])
    # close-up of the shaft and its keeper
    kc = sh + [0, 0, 8]
    kp = F.render(parts, -35, 22, kc, 52, size=(620, 760), marks=lines[2:4],
                  labels=[(t["crank"], sh + [0, 0, 6 + kup + 4], (60, -150)),
                          (t["knut"], [B.CX, F.Y_SH - B.KEEP_SCREW_Y - 9, zt - 5.5], (-40, 170))],
                  title=t["keep_title"])
    out = os.path.join(F.HERE, "images", f"test-frame-screws{sfx}.png")
    F.row([img, kp, fk], out)


if __name__ == "__main__":
    main()
