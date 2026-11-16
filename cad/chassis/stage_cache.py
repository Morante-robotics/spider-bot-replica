"""Moved to tools/stage_cache.py (shared by every design); kept so `from stage_cache import Stages` still works here.
The shared module is registered as `stage_cache` itself, so pickled stage results keep resolving their classes."""
import importlib.util
import os
import sys

_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools", "stage_cache.py")
_spec = importlib.util.spec_from_file_location("stage_cache", _p)
_m = importlib.util.module_from_spec(_spec)
sys.modules["stage_cache"] = _m
_spec.loader.exec_module(_m)
Stages = _m.Stages
