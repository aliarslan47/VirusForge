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


def test_render_html_lang_attr_reflects_lang():
    # <html lang> gerçek dili yansıtmalı (erişilebilirlik + doğru dil bildirimi)
    from virusforge.report.render import render_html
    rep = {"sample": "T7", "mode": "HYBRID", "run_id": "r", "modules": []}
    assert "<html lang='en'>" in render_html(rep, lang="en")
    assert "<html lang='tr'>" in render_html(rep, lang="tr")


def test_render_html_language_switch_link():
    # Dil-geçiş linki: TR raporundan report_en.html'e, EN raporundan report.html'e
    from virusforge.report.render import render_html
    rep = {"sample": "T7", "mode": "HYBRID", "run_id": "r", "modules": []}
    tr = render_html(rep, lang="tr")
    en = render_html(rep, lang="en")
    assert "report_en.html" in tr and "English" in tr
    assert "report.html" in en and "Türkçe" in en


def test_render_html_gene_annotation_table():
    # V06 anotasyon bölümünde her CDS için gen listesi tablosu (tr + en)
    from virusforge.report.render import render_html
    rep = {"sample": "T7", "mode": "HYBRID", "run_id": "r", "modules": [
        {"code": "V06", "status": "PASS", "metrics": {"cds": 2, "genes": [
            {"gene": "X_CDS_0001", "start": "891", "stop": "1", "strand": "-",
             "product": "internal virion protein", "phrog": "1339", "category": "head and packaging"},
            {"gene": "X_CDS_0002", "start": "4374", "stop": "1990", "strand": "+",
             "product": "tail protein", "phrog": "457", "category": "tail"}]}}]}
    tr = render_html(rep, lang="tr")
    en = render_html(rep, lang="en")
    # locus + ürün + PHROG her iki dilde de görünür (veri çevrilmez)
    assert "X_CDS_0001" in tr and "internal virion protein" in tr and "1339" in tr
    assert "Gen anotasyon listesi" in tr
    assert "X_CDS_0002" in en and "tail protein" in en
    assert "Gene annotation list" in en and "Gen anotasyon listesi" not in en


def test_render_html_english_na_and_tools():
    # na-mesajları + Araçlar bölümü başlığı da İngilizce'ye çevrilmeli (ham TR sızmasın)
    from virusforge.report.render import render_html
    en = render_html({"sample": "T7", "mode": "HYBRID", "run_id": "r", "modules": []}, lang="en")
    assert "Bacteriophage characterization not performed." in en
    assert "AMR screening not performed." in en
    assert "BLAST identification not performed" in en
    assert "Tools, Versions & Scientific References" in en
    # ham Türkçe sızmamalı
    assert "uygulanmadı" not in en and "Araçlar, Sürümler" not in en
