"""The Spider-Bot's CAD designs as one package, so a design takes another's numbers by importing its build.py (one
source per number), never by copying a value or loading a file by its path.

Every script (build.py, verify.py, checks, figures) starts with the repo root on sys.path:

    ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    sys.path.insert(0, ROOT)
    from cad import design, fits
    C = design("crankshafts")            # cad/crankshafts/build.py
    B = design("gear-train-test")        # its own build.py too, so it is loaded once under one name

Design folders are kebab-case (gear-train-test), which an import statement cannot spell; design() imports them by
name. Each module is loaded once per process, whoever asks for it first.
"""
import importlib


def design(name):
    """The build.py of design folder cad/<name>/, as a module."""
    return importlib.import_module(f"cad.{name}.build")
