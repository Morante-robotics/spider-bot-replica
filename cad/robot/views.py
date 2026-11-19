"""Judge views (spec.views.cmd): the robot in n1_render's four views (3/4, front, side, below-front), no labels on the
robot. Usage (repo root): uv run python cad/robot/views.py <out.png>

PLAN stage: the N1 meshes at S 0.65 (the approved look; the inside is hidden by the opaque body, so no boxes are
drawn). Round r00, first task: draw the N2 parts from out/*.stl instead (body, base, legs posed by n1.carry).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [HERE, os.path.join(ROOT, "cad", "mockup"), os.path.join(ROOT, "tools")]
import n1  # noqa: E402
import n1_render  # noqa: E402
import probes as P  # noqa: E402

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    R = n1.run(P.p_at(P.S_FIX))
    R["bx"] = {}                        # nothing inside is visible from outside
    n1_render.render(out, R, pose=0, lang="es")
    print("wrote", out)
