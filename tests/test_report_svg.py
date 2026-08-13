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


def test_i18n_t():
    from virusforge.report.i18n import t
    assert t("Genel Bakış", "en") == "Overview"
    assert t("Genel Bakış", "tr") == "Genel Bakış"          # varsayılan TR değişmez
    assert t("bilinmeyen_XYZ", "en") == "bilinmeyen_XYZ"     # over-match yok


def test_render_html_english():
    from virusforge.report.render import render_html
    rep = {"sample": "T7", "mode": "HYBRID", "run_id": "r", "modules": []}
    en = render_html(rep, lang="en")
    tr = render_html(rep, lang="tr")
    assert "Overview" in en and "Analysis Report" in en          # İngilizce etiketler
    assert "Genel Bakış" in tr and "Genel Bakış" not in en       # TR regresyon yok
    assert 'charset="utf-8"' in en.lower()


def test_report_has_utf8_charset():
    # Türkçe harflerin bozulmaması için charset bildirimi ŞART (kalıcı çözüm)
    from virusforge.report.render import render_html
    h = render_html({"sample": "T7", "mode": "HYBRID", "run_id": "r", "modules": []})
    assert "<!DOCTYPE html>" in h
    assert 'charset="utf-8"' in h.lower() or "charset='utf-8'" in h.lower()
    assert "<head" in h and "</head>" in h and "<body" in h
