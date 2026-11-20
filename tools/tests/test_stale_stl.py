"""cad_verify.stale: an exported STL older than its design's build.py (or a shared module) is stale."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import cad_verify  # noqa: E402


def test_stale(tmp_path, monkeypatch):
    monkeypatch.setattr(cad_verify, "SHARED", [])
    (tmp_path / "out").mkdir()
    stl, build = tmp_path / "out" / "a.stl", tmp_path / "build.py"
    stl.write_text("solid a\nendsolid a\n")
    build.write_text("# model\n")
    os.utime(stl, (100, 100))
    os.utime(build, (200, 200))
    assert cad_verify.stale(str(stl)) == ["build.py"]
    os.utime(stl, (300, 300))
    assert cad_verify.stale(str(stl)) == []


def test_no_build(tmp_path):
    (tmp_path / "out").mkdir()
    stl = tmp_path / "out" / "a.stl"
    stl.write_text("solid a\nendsolid a\n")
    assert cad_verify.stale(str(stl)) == []
