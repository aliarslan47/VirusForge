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


def test_svg_synteny_renders():
    from virusforge.report.render import _svg_synteny
    top = [{"gene": "A", "start": 1, "end": 500, "strand": "+", "function": "tail"},
           {"gene": "C", "start": 600, "end": 900, "strand": "-", "function": "lysis"}]
    bottom = [{"gene": "B", "start": 1, "end": 500, "strand": "+", "function": "tail"}]
    svg = _svg_synteny(top, bottom, [("A", "B")], "sample", "T7 ref")
    assert svg.startswith("<svg") and "sample" in svg and "T7 ref" in svg


def test_svg_synteny_empty_safe():
    from virusforge.report.render import _svg_synteny
    assert "na" in _svg_synteny([], [], [], "a", "b")


def test_report_has_utf8_charset():
    # Türkçe harflerin bozulmaması için charset bildirimi ŞART (kalıcı çözüm)
    from virusforge.report.render import render_html
    h = render_html({"sample": "T7", "mode": "HYBRID", "run_id": "r", "modules": []})
    assert "<!DOCTYPE html>" in h
    assert 'charset="utf-8"' in h.lower() or "charset='utf-8'" in h.lower()
    assert "<head" in h and "</head>" in h and "<body" in h
