import os
import sys

import trimesh

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import mesh_ref  # noqa: E402


def test_same_mesh_is_zero():
    s = trimesh.creation.icosphere(subdivisions=4, radius=10)
    res = mesh_ref.compare(s, s, n=3000)
    assert res["part_to_ref"]["max"] < 1e-6 and res["ref_to_part"]["max"] < 1e-6


def test_offset_sphere_reads_its_offset():
    a = trimesh.creation.icosphere(subdivisions=5, radius=10.0)
    b = trimesh.creation.icosphere(subdivisions=5, radius=10.5)
    res = mesh_ref.compare(a, b, n=3000)
    for way in ("part_to_ref", "ref_to_part"):
        assert abs(res[way]["mean"] - 0.5) < 0.05


def test_missing_feature_shows_one_way_only():
    box = trimesh.creation.box((20, 20, 20))
    bump = trimesh.creation.box((4, 4, 6))
    bump.apply_translation((0, 0, 12))
    ref = trimesh.util.concatenate([box, bump])
    res = mesh_ref.compare(box, ref, n=4000)
    assert res["part_to_ref"]["max"] < 1e-6          # everything the part has is in the reference
    assert res["ref_to_part"]["max"] > 4.0           # the bump the part lacks is found


def test_cli_gate_lines(tmp_path, capsys):
    a = trimesh.creation.icosphere(subdivisions=4, radius=10.0)
    b = trimesh.creation.icosphere(subdivisions=4, radius=13.0)   # 3 mm off: over the default p95
    pa, pb = tmp_path / "a.stl", tmp_path / "b.stl"
    a.export(pa)
    b.export(pb)
    assert mesh_ref.main(["compare", str(pa), str(pb), "--samples", "2000"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("FAIL fidelity")
    assert mesh_ref.main(["compare", str(pa), str(pa), "--samples", "2000"]) == 0
    assert capsys.readouterr().out.startswith("PASS fidelity")


def test_source_check_finds_mesh_reads_only(tmp_path):
    b = tmp_path / "build.py"
    b.write_text('import trimesh\nm = load("x.stl")\n# spideybot_L_leg1.stl, the reference\n'
                 'export_stl(s, os.path.join(OUT, f"{name}.stl"), tolerance=0.02)\nshape = Mesher().read(p)\n')
    assert [n for n, _ in mesh_ref.source_check(b)] == [1, 2, 5]


def test_views_writes_reference_and_design(tmp_path):
    s = trimesh.creation.icosphere(subdivisions=2, radius=10)
    p = tmp_path / "s.stl"
    s.export(p)
    assert mesh_ref.main(["views", str(tmp_path / "ref.png"), "--ref", str(p)]) == 0
    assert mesh_ref.main(["views", str(tmp_path / "v.png"), "--ref", str(p), "--parts", str(p),
                          "--edits", str(tmp_path / "e.png"), f"{p}=same"]) == 0
    assert all((tmp_path / f).exists() for f in ("ref.png", "v.png", "e.png"))


def test_visible_drops_a_hidden_inside():
    outer = trimesh.creation.box((20, 20, 20))
    inner = trimesh.creation.box((4, 4, 4))                   # a block hidden inside: never seen from outside
    m = trimesh.util.concatenate([outer, inner])
    v = mesh_ref.visible(m, "all", n=60)
    assert abs(v.area - outer.area) < 1e-6
    res = mesh_ref.compare(outer, m, n=3000, view="all")
    assert res["ref_to_part"]["max"] < 1e-6                  # the hidden block no longer counts against the part
