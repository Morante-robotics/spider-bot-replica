#!/usr/bin/env python3
"""Planar leg-mechanism simulator: foot path of a crank-driven walking leg, and numbers to compare legs.

Three candidate legs, all driven by one crank turning at constant speed:
  - toy:    crank + one bent leg that slides through a fixed pivot (inverted slider-crank), as in walking toys;
  - klann:  Klann's linkage (US patent 6,260,862), bar lengths from DIY Walkers, scaled so the crank = 3;
  - jansen: Theo Jansen's Strandbeest leg ("holy numbers", crank = 15).
Each leg is scaled so that its foot touches the ground HIP_HEIGHT mm below the crank axle, then measured over one
crank turn, measured over the half turn each leg carries the body (two groups of 4 legs, cranks 180° apart): stride, how much
the body rises and falls (bob), whether the foot slips backwards, how even the foot speed is; plus step height,
crank radius, size of the leg and number of moving parts.

Also: `fourbar()` solves a four-bar linkage and `grashof()` says whether its shortest link can turn fully.

Usage:
    python3 legs.py [--hip 55] [--png foot-paths.png] [--gif legs.gif]

Needs numpy and matplotlib (pip install numpy matplotlib; pillow for the GIF).
"""
import argparse

import numpy as np

HIP_HEIGHT = 55.0      # mm, crank axle above the ground (body bottom ≈ 46 mm at 120 % scale)
STEPS = 720            # crank positions per turn


# ---------- geometry helpers ----------

def circles(p0, r0, p1, r1):
    """The two intersections of circle (p0, r0) and circle (p1, r1), or None if they do not meet."""
    d = np.linalg.norm(p1 - p0)
    if d > r0 + r1 or d < abs(r0 - r1) or d == 0:
        return None
    a = (r0 ** 2 - r1 ** 2 + d ** 2) / (2 * d)
    h = np.sqrt(max(r0 ** 2 - a ** 2, 0))
    m = p0 + a * (p1 - p0) / d
    perp = np.array([-(p1 - p0)[1], (p1 - p0)[0]]) / d
    return m + h * perp, m - h * perp


def pick(options, near):
    """Of two candidate points, the one closest to `near` (keeps the linkage on the same branch)."""
    return min(options, key=lambda p: np.linalg.norm(p - near))


def rot(v, deg):
    t = np.radians(deg)
    return np.array([np.cos(t) * v[0] - np.sin(t) * v[1], np.sin(t) * v[0] + np.cos(t) * v[1]])


def unit(v):
    return v / np.linalg.norm(v)


# ---------- four-bar ----------

def grashof(ground, crank, coupler, rocker):
    """Grashof check: s + l <= p + q means the shortest link can make full turns."""
    links = sorted([ground, crank, coupler, rocker])
    s, p, q, l = links
    kind = "crank-rocker" if min(links) == crank and s + l <= p + q else (
        "Grashof (shortest link turns fully)" if s + l <= p + q else "non-Grashof (no link turns fully)")
    return s + l <= p + q, f"s + l = {s + l:g}, p + q = {p + q:g}: {kind}"


def fourbar(O, P, crank, coupler, rocker, theta, guess):
    """Crank O-A, coupler A-B, rocker P-B. Returns A, B for crank angle theta (rad)."""
    A = O + crank * np.array([np.cos(theta), np.sin(theta)])
    s = circles(A, coupler, P, rocker)
    return (A, None) if s is None else (A, pick(s, guess))


# ---------- legs (all in their own units, scaled later) ----------

class Leg:
    name = ""
    crank = 1.0
    parts = 0          # moving parts per leg, the shared crank not counted
    pivots = 0         # pin joints per leg

    def solve(self, theta, prev):
        """Joint positions (dict name -> xy) for crank angle theta; prev = previous solution (branch tracking)."""
        raise NotImplementedError

    def bars(self):
        """Pairs (or longer chains) of joint names drawn as bars."""
        raise NotImplementedError


class Toy(Leg):
    """Crank pin A carries the inner end of a rigid bent leg that slides and turns in a fixed sleeve P
    (inverted slider-crank). Knee K = A + u * TO_KNEE along u = direction A->P; foot F = K + rotate(u, BEND) * SHIN.
    One part per leg."""
    # Geometry from a random search (4000 tries) for the longest stride with body bob <= 3 mm, so that this simple
    # leg is compared at its best and not with made-up numbers.
    name, crank, parts, pivots = "toy (crank + sliding leg)", 6.7, 1, 2
    O = np.array([0.0, 0.0])
    P = np.array([-21.6, 1.1])      # sleeve / ball joint on the body edge
    TO_KNEE, BEND, SHIN = 28.6, 98.0, 48.9

    def solve(self, theta, prev):
        A = self.O + self.crank * np.array([np.cos(theta), np.sin(theta)])
        u = unit(self.P - A)
        K = A + u * self.TO_KNEE
        F = K + rot(u, self.BEND) * self.SHIN
        return dict(O=self.O, A=A, P=self.P, K=K, F=F)

    def bars(self):
        return [("O", "A"), ("A", "K", "F")]

    def ground(self):
        return ["O", "P"]


class Klann(Leg):
    """Klann's patent geometry (DIY Walkers joint map, crank = 3): crank O-A; bar A-M-K bent 12.8° at M, rocker
    M-P2; leg U-K-F (10.04 + 10.04, bent 30° at the knee K), rocker U-P1."""
    name, crank, parts, pivots = "Klann", 3.0, 4, 6
    O, P1, P2 = np.array([10.0, 10.0]), np.array([7.4, 16.9]), np.array([3.4, 8.03])
    AM, MK, BEND_M, MP2, UK, KF, BEND_K, UP1 = 6.6, 5.84, 12.8, 3.59, 10.04, 10.04, 30.0, 5.79
    START = dict(M=np.array([1.3, 10.5]), U=np.array([2.1, 18.5]), F=np.array([-6.4, 1.1]))  # read off the plan

    def solve(self, theta, prev):
        prev = prev or self.START
        A = self.O + self.crank * np.array([np.cos(theta), np.sin(theta)])
        s = circles(A, self.AM, self.P2, self.MP2)
        if s is None:
            return None
        M = pick(s, prev["M"])
        d = unit(M - A)
        K = min((M + rot(d, b) * self.MK for b in (self.BEND_M, -self.BEND_M)),
                key=lambda k: np.linalg.norm(k - prev.get("K", M + d * self.MK)))
        s = circles(K, self.UK, self.P1, self.UP1)
        if s is None:
            return None
        U = pick(s, prev["U"])
        e = unit(K - U)
        F = min((K + rot(e, b) * self.KF for b in (self.BEND_K, -self.BEND_K)),
                key=lambda f: np.linalg.norm(f - prev["F"]))
        return dict(O=self.O, A=A, M=M, K=K, U=U, F=F, P1=self.P1, P2=self.P2)

    def bars(self):
        return [("O", "A"), ("A", "M", "K"), ("M", "P2"), ("U", "K", "F"), ("U", "P1")]

    def ground(self):
        return ["O", "P1", "P2"]


class Jansen(Leg):
    """Strandbeest leg, Jansen's numbers: a=38 b=41.5 c=39.3 d=40.1 e=55.8 f=39.4 g=36.7 h=65.7 i=49 j=50 k=61.9
    l=7.8 m=15 (crank). Crank O-A, frame pivot B; triangle B-C-E (B-C = b, B-E = d, C-E = e), bars E-F (f)
    and B-D (c), triangle D-F-G (D-F = g, F-G = h, D-G = i; foot G)."""
    name, crank, parts, pivots = "Jansen", 15.0, 7, 10
    a, b, c, d, e, f, g, h, i, j, k, l = 38, 41.5, 39.3, 40.1, 55.8, 39.4, 36.7, 65.7, 49, 50, 61.9, 7.8
    O = np.array([0.0, 0.0])
    B = np.array([-38.0, -7.8])

    def solve(self, theta, prev):
        A = self.O + self.crank * np.array([np.cos(theta), np.sin(theta)])
        up, down, left = np.array([0, 1e3]), np.array([0, -1e3]), np.array([-1e3, 0])
        prev = prev or {}
        s = circles(A, self.j, self.B, self.b)
        C = pick(s, prev.get("C", up)) if s else None
        s = circles(A, self.k, self.B, self.c)
        D = pick(s, prev.get("D", down)) if s else None
        if C is None or D is None:
            return None
        s = circles(self.B, self.d, C, self.e)
        E = pick(s, prev.get("E", left + up))
        s = circles(E, self.f, D, self.g)
        F = pick(s, prev.get("F", left))
        s = circles(F, self.h, D, self.i)
        G = pick(s, prev.get("G", down))
        return dict(O=self.O, A=A, B=self.B, C=C, D=D, E=E, F=F, G=G)

    def bars(self):
        return [("O", "A"), ("A", "C"), ("A", "D"), ("B", "C", "E", "B"), ("B", "D"), ("E", "F"),
                ("D", "F", "G", "D")]

    def ground(self):
        return ["O", "B"]


FOOT = {"toy (crank + sliding leg)": "F", "Klann": "F", "Jansen": "G"}


def run(leg, steps=STEPS):
    """Solve a full crank turn. Returns list of joint dicts in mm, scaled so the foot reaches HIP_HEIGHT below O."""
    sols, prev = [], None
    # Klann/Jansen read best starting from their drawn position; go round once to settle the branch, then record
    thetas = np.linspace(0, 2 * np.pi, steps, endpoint=False)
    if isinstance(leg, Klann):
        thetas = thetas + np.radians(151.7)
    for _ in range(2):
        sols = []
        for t in thetas:
            s = leg.solve(t, prev)
            if s is None:
                raise RuntimeError(f"{leg.name}: linkage locks at {np.degrees(t):.0f}°")
            sols.append(s)
            prev = s
    foot = FOOT[leg.name]
    low = min(s[foot][1] for s in sols)
    O = sols[0]["O"]
    scale = HIP_HEIGHT / (O[1] - low)
    return [{k: (v - O) * scale for k, v in s.items()} for s in sols], scale


def metrics(leg, sols, scale):
    """Gait used here: two groups of 4 legs with cranks 180° apart, so each leg must carry the body for half a turn.
    Pick the half turn that contains the foot's lowest point (it is on the ground then) and is flattest; the body
    rises and falls by `bob` while the leg carries it."""
    foot = FOOT[leg.name]
    F = np.array([s[foot] for s in sols])
    n, half = len(F), len(F) // 2
    best, low = None, int(np.argmin(F[:, 1]))
    for start in range(low - half, low + 1):
        idx = (start + np.arange(half + 1)) % n
        bob = np.ptp(F[idx, 1])
        if best is None or bob < best[0]:
            best = (bob, idx)
    bob, idx = best
    xs = F[idx, 0]
    vx = np.diff(xs)
    stride = abs(xs[-1] - xs[0])
    allpts = np.array([p for s in sols for p in s.values()])
    return dict(
        name=leg.name,
        stride=stride,
        bob=bob,
        lift=F[:, 1].max() - F[:, 1].min(),
        backwards=bool((np.sign(vx) != np.sign(xs[-1] - xs[0])).any() and np.abs(vx[np.sign(vx) != np.sign(xs[-1] - xs[0])]).max() > 1e-3),
        evenness=np.abs(vx).max() / max(np.median(np.abs(vx)), 1e-9),
        crank=leg.crank * scale,
        width=np.ptp(allpts[:, 0]),
        height=np.ptp(allpts[:, 1]),
        parts=leg.parts,
        pivots=leg.pivots,
        stance=idx,
    )


def table(rows):
    out = ["| Leg | Stride per half turn (mm) | Body bob while walking (mm) | Step height (mm) "
           "| Foot slips back on the ground | Foot speed peak / median | Crank radius (mm) | Leg size W × H (mm) "
           "| Moving parts per leg | Pin joints per leg |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['name']} | {r['stride']:.0f} | {r['bob']:.1f} | {r['lift']:.0f} "
                   f"| {'yes' if r['backwards'] else 'no'} | {r['evenness']:.1f} | {r['crank']:.1f} "
                   f"| {r['width']:.0f} × {r['height']:.0f} | {r['parts']} | {r['pivots']} |")
    return "\n".join(out)


def draw(ax, leg, s, color):
    for chain in leg.bars():
        pts = np.array([s[n] for n in chain])
        ax.plot(pts[:, 0], pts[:, 1], "-o", color=color, lw=2, ms=3)
    for n in leg.ground():
        ax.plot(*s[n], "s", color="k", ms=6)


def main():
    global HIP_HEIGHT
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hip", type=float, default=HIP_HEIGHT, help="crank axle height above the ground (mm)")
    ap.add_argument("--png")
    ap.add_argument("--gif")
    args = ap.parse_args()
    HIP_HEIGHT = args.hip

    ok, why = grashof(ground=np.linalg.norm(Klann.O - Klann.P2), crank=3, coupler=Klann.AM, rocker=Klann.MP2)
    print(f"Klann's driving four-bar (frame O-P2, crank, bar A-M, rocker M-P2): {why}\n")

    legs = [Toy(), Klann(), Jansen()]
    results = [(leg, *run(leg)) for leg in legs]
    rows = [metrics(leg, sols, sc) for leg, sols, sc in results]
    print(table(rows))

    if args.png or args.gif:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        colors = ["#c0392b", "#2471a3", "#27ae60"]

        def frame(fig, axs, k):
            for ax, (leg, sols, _), r, col in zip(axs, results, rows, colors):
                ax.clear()
                F = np.array([s[FOOT[leg.name]] for s in sols])
                ax.plot(F[:, 0], F[:, 1], color=col, lw=1, alpha=0.6)
                ax.plot(F[r["stance"], 0], F[r["stance"], 1], color=col, lw=3.5, alpha=0.35)
                ax.axhline(-HIP_HEIGHT, color="#888", lw=1)
                draw(ax, leg, sols[k % len(sols)], col)
                ax.set_aspect("equal")
                ax.set_xlim(-110, 50)
                ax.set_ylim(-HIP_HEIGHT - 8, 60)
                ax.set_title(f"{leg.name}\nstride {r['stride']:.0f} mm · step {r['lift']:.0f} mm · "
                             f"bob {r['bob']:.1f} mm", fontsize=10)
                ax.grid(alpha=0.25)
                ax.set_xlabel("mm (crank axle at 0, 0)")

        fig, axs = plt.subplots(1, 3, figsize=(15, 5))
        if args.png:
            frame(fig, axs, 0)
            plt.tight_layout()
            fig.savefig(args.png, dpi=90)
            print(f"wrote {args.png}")
        if args.gif:
            from matplotlib.animation import FuncAnimation, PillowWriter
            n = 48
            anim = FuncAnimation(fig, lambda i: frame(fig, axs, i * STEPS // n), frames=n)
            plt.tight_layout()
            anim.save(args.gif, writer=PillowWriter(fps=16), dpi=60)
            print(f"wrote {args.gif}")


if __name__ == "__main__":
    main()
