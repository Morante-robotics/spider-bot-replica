"""Spider-Bot robot at S 0.70 (plan.json): the shells and legs (shells.py) and the drive inside them (interior.py,
written by its own designer: when it is missing, only the shells are built and this says so).

    ../../.venv/bin/python build.py [--part base] [--fine]
Outputs out/<part>.step and .stl, robot frame (legs in their neutral pose; verify.py carries them per pose).
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import timebudget
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
from cad import common
import shells as SH
OUT = SH.OUT

def main():
    a = common.part_args(__doc__, SH.PARTS)
    t0 = time.time()
    for n in a.part or list(SH.PARTS):
        timebudget.reset(n)                                   # each part its own 40 s (a whole build is many parts)
        t = time.time(); sh = SH.PARTS[n](); common.export(n, sh, OUT, fine=a.fine)
        print(f"    {n}: {len(sh.solids())} solid(s), valid {sh.is_valid}, {time.time() - t:.1f} s", flush=True)
    try:
        import interior
    except ImportError:
        print("interior.py missing: shells only")
    else:
        if not a.part: timebudget.reset("interior"); interior.write_all()
    print(f"build {time.time() - t0:.1f} s")

if __name__ == "__main__":
    main()
