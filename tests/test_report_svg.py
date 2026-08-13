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


def test_structural_summary_classifies_phrog():
    from virusforge.report.render import _structural_summary
    fns = {"CDS": 60, "head and packaging": 10, "connector": 1, "tail": 3,
           "DNA, RNA and nucleotide metabolism": 12, "lysis": 3,
           "moron, auxiliary metabolic gene and host takeover": 4, "other": 3,
           "integration and excision": 0, "transcription regulation": 0,
           "unknown function": 24, "tRNAs": 0, "CARD_AMR_Genes": 0}
    s = _structural_summary(fns)
    assert s["structural"] == 14        # 10 + 1 + 3 (head&packaging + connector + tail)
    assert s["non_structural"] == 22    # 12 + 3 + 4 + 3 (+ 0 + 0)
    assert s["unknown"] == 24           # unknown function; CDS/tRNA/AMR sayaçları HARİÇ


def test_render_html_structural_vs_nonstructural_table():
    from virusforge.report.render import render_html
    rep = {"sample": "T7", "mode": "HYBRID", "run_id": "r", "modules": [
        {"code": "V06", "status": "PASS", "metrics": {"cds": 60, "functions": {
            "head and packaging": 10, "connector": 1, "tail": 3,
            "DNA, RNA and nucleotide metabolism": 12, "lysis": 3, "other": 3,
            "moron, auxiliary metabolic gene and host takeover": 4, "unknown function": 24}}}]}
    tr = render_html(rep, lang="tr")
    en = render_html(rep, lang="en")
    assert "Yapısal" in tr and "Yapısal olmayan" in tr and "14" in tr
    assert "Structural" in en and "Non-structural" in en and "Yapısal olmayan" not in en


def test_render_html_v05_mash_tree_figure():
    # V05 (Taksonomi & En Yakın Referanslar) bölümüne Mash-mesafe ağacı figürü (tr+en)
    from virusforge.report.render import render_html
    nwk = "(sample:0.0002,(V01146:0.001,EU734174:0.04):0.01);"
    rep = {"sample": "T7", "mode": "HYBRID", "run_id": "r", "modules": [
        {"code": "V05", "status": "PASS", "metrics": {"closest_10": [
            {"accession": "V01146", "mash_dist": 0.001}]}},
        {"code": "V09", "status": "PASS", "metrics": {"tree": {"mash_newick": nwk}}}]}
    tr = render_html(rep, lang="tr")
    en = render_html(rep, lang="en")
    assert "Mash-mesafe ağacı" in tr and "<svg" in tr and "V01146" in tr
    assert "Mash-distance tree" in en and "Mash-mesafe ağacı" not in en


def test_lifestyle_label_lytic_lysogenic():
    from virusforge.report.render import _lifestyle_label
    assert "litik" in _lifestyle_label("virulent", "tr").lower()
    assert "lizojenik" in _lifestyle_label("temperate", "tr").lower()
    assert "lytic" in _lifestyle_label("virulent", "en").lower()
    assert "lysogenic" in _lifestyle_label("temperate", "en").lower()
    assert "virulent" in _lifestyle_label("virulent", "tr")   # ham PhaTYP enum korunur
    assert _lifestyle_label("—", "tr") == "—"                  # bilinmeyen → olduğu gibi


def test_break_lineage_wraps_long_taxonomy():
    from virusforge.report.render import _break_lineage
    lin = "acellular root:Viruses;realm:Duplodnaviria;class:Caudoviricetes;subfamily:Studiervirinae"
    out = _break_lineage(lin)
    assert "<wbr>" in out and "brk" in out           # her ';' sonrası kırılma noktası + kaydırma sınıfı
    assert "Studiervirinae" in out                    # içerik korunur
    assert "mdash" in _break_lineage("")               # boş → em-dash (çökmez)


def test_render_html_shows_lytic_and_wraps_lineage():
    from virusforge.report.render import render_html
    rep = {"sample": "T7", "mode": "HYBRID", "run_id": "r", "modules": [
        {"code": "V07", "status": "PASS", "metrics": {
            "lifestyle": {"TYPE": "virulent", "PhaTYPScore": "1.0"},
            "taxonomy": {"Lineage": "class:Caudoviricetes;subfamily:Studiervirinae"}}}]}
    tr = render_html(rep, lang="tr")
    en = render_html(rep, lang="en")
    assert "litik" in tr and "lytic" in en           # yaşam tarzı yorumu
    assert "brk" in tr and "<wbr>" in tr             # soy hattı kaydırılabilir (taşmaz)


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
