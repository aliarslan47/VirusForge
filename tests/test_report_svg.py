"""Rapor görselleri: filogenetik ağaç dendrogram + benzerlik matrisi ısı-haritası (bağımsız SVG)."""
from virusforge.report.render import _svg_tree, _svg_matrix


def test_svg_tree_contains_taxa():
    svg = _svg_tree("(sample:0.001,(V01146:0.002,EU734174:0.04)95:0.01);")
    assert svg.startswith("<svg") and "sample" in svg and "V01146" in svg


def test_svg_tree_empty_is_safe():
    assert "na" in _svg_tree("")


def test_svg_matrix_renders_cells():
    svg = _svg_matrix(["s", "A"], [[100.0, 96.0], [96.0, 100.0]])
    assert svg.startswith("<svg") and "96" in svg
