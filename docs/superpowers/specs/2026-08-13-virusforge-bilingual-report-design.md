# VirusForge — Çift-Dilli TR+EN Rapor Tasarımı (Item 3)

> Tarih: 2026-08-13 · Durum: onaylandı (kullanıcı) · Kapsam: rapor sistemi TR+EN.

## 1. Amaç
Her koşu **iki rapor** üretsin: `report.html` (Türkçe, varsayılan) + `report_en.html` (İngilizce). Üstte
dil geçiş linki. Karşılaştırma raporu da aynı (`comparison_report.html` + `_en`).

## 2. Mekanizma
- **`virusforge/report/i18n.py`**: `T = {"anahtar": {"tr": "...", "en": "..."}}` + `t(key, lang="tr")`
  (bilinmeyen anahtar → anahtarın kendisi, sessiz çökme yok).
- **`render.py`**: `render_html(report, run_dir=None, lang="tr")`; tüm kullanıcı-etiketleri `t(...)`'den geçer.
  Aynı şekilde `render_comparison(data, lang="tr")`.
- **Dil linki:** rapor üstünde `report.html ⇄ report_en.html` geçişi (basit `<a>`).

## 3. Çevrilenler vs çevrilmeyenler
- **Çevrilir (benim etiketlerim):** başlıklar, tablo başlıkları, sütun adları (Alan/Değer/Metrik/Kategori…),
  kart etiketleri, şekil altyazıları, notlar, bölüm adları.
- **ÇEVRİLMEZ (standart/araç çıktısı):** PHROG kategorileri, taksonomi (Latince), araç enum değerleri
  (virulent, High-quality, Complete), pipeline şeması modül adları (zaten İngilizce), accession/DOI.

## 4. Çıktı
- `v10_report.py`: `report.html` = render_html(lang="tr"), `report_en.html` = render_html(lang="en").
- `compare.py`: `comparison_report.html` (tr) + `comparison_report_en.html` (en).
- İkisi de charset'li (`_document`).

## 5. Test
- `t(key,lang)` birim testi (tr/en dönüş + bilinmeyen anahtar → key).
- `render_html(lang="en")` smoke: İngilizce başlık ("Overview" gibi) var, charset var, çökmez.
- `render_html(lang="tr")` hâlâ Türkçe (regresyon).
- Mevcut 94 test yeşil kalır (varsayılan lang="tr").

## 6. Doğrulama
T7 hibrit run: `report.html` Türkçe + `report_en.html` İngilizce üretilir; ikisinde de aynı veri, doğru dil,
charset (mojibake yok), dil linki çalışır.

## 7. Kabul kriterleri
1. Her koşu 2 rapor (tr+en) üretir; karşılaştırma da 2 rapor.
2. Tüm benim etiketlerim çevrilir; standart/araç terimleri korunur.
3. Dil geçiş linki. charset ikisinde de.
4. Yeni pytest'ler + mevcut testler yeşil (varsayılan tr).
