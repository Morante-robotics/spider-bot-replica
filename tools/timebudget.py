"""Time budget of a build (plan-velocidad, Phase 0): any build command over CAD_BUDGET seconds (env, default 60; 0 = off) is a bug.

    timebudget.start()                     # once per process (common.part_args does it): the watchdog thread
    with timebudget.stage("base_keel", cold=True): ...   # a stage: its time is logged, > 10 s warns, the watchdog names it

The watchdog is a daemon thread: past the budget it prints the [TIME] line and ends the process with exit code 3
(os._exit: an OCCT call cannot be interrupted from Python). Every cold/warm stage appends a row
`date,command,part,stage,seconds,cold|warm` to <repo>/out/build-times.csv (gitignored).
"""
import contextlib
import datetime
import os
import sys
import threading
import time

BUDGET = float(os.environ.get("CAD_BUDGET", "60"))
WARN = 10.0
CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out", "build-times.csv")
_T0 = time.time()
_cur = {"stage": "(start)", "t": _T0}
_started = []


def _command():
    return " ".join([os.path.basename(os.path.dirname(os.path.abspath(sys.argv[0]))) + "/" + os.path.basename(sys.argv[0])] + sys.argv[1:])


def _part():
    a = sys.argv
    return ",".join(a[i + 1] for i, x in enumerate(a[:-1]) if x == "--part") or "all"


def _watch():
    while True:
        time.sleep(0.25)
        el = time.time() - _T0
        if el > BUDGET:
            print(f"[TIME] {_command()} over {BUDGET:g} s in stage {_cur['stage']} ({el:.0f} s): a bug, see plan-velocidad", flush=True)
            os._exit(3)


def reset(stage="(start)"):
    """a new budget from now: a build of several parts gives each part its own CAD_BUDGET."""
    global _T0
    _T0 = time.time(); _cur["stage"], _cur["t"] = stage, _T0


def start():
    if _started or BUDGET <= 0:
        return
    _started.append(1)
    threading.Thread(target=_watch, daemon=True).start()


def log(stage, seconds, cold):
    try:
        os.makedirs(os.path.dirname(CSV), exist_ok=True)
        with open(CSV, "a") as f:
            f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S},{_command().replace(',', ' ')},{_part()},{stage},{seconds:.2f},{'cold' if cold else 'warm'}\n")
    except OSError:
        pass
    if cold:
        print(f"    [time] {stage}: {seconds:.1f} s cold", flush=True)
        if seconds > WARN:
            print(f"[TIME] WARN stage {stage} took {seconds:.1f} s (> {WARN:g} s)", flush=True)


@contextlib.contextmanager
def stage(name):
    """Name the running stage for the watchdog; a stage that ends by itself is logged by the caller via log()."""
    prev = _cur["stage"]
    _cur["stage"] = name
    try:
        yield
    finally:
        _cur["stage"] = prev
