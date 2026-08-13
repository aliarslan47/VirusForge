# VirusForge — M3 Faz 2: clinker İnteraktif Synteny Tasarımı

> Tarih: 2026-08-13 · Durum: onaylandı (kullanıcı "yap") · Kapsam: `virusforge compare`'e clinker.

## 1. Amaç
`virusforge compare`'e **çok-genomlu interaktif** gen-kümesi hizalaması ekle (clinker v0.0.32). Mevcut
V09 statik-SVG synteny (örnek-vs-1-ref) olduğu gibi kalır; clinker onu tamamlar, değiştirmez.

## 2. Yerleşim & env kararı
- **Yerleşim:** `compare` komutu (çok-örnek). clinker'ın asıl gücü çok-genom; GenBank'lar zaten hazır.
- **Env:** mevcut `ali-clinker` (saf araç, BacForge koduna bağımlılık yok). config `tools.clinker.conda_env`.

## 3. Akış (data flow)
```
run_dirs → her run'ın pharokka.gbk (V06_GENOME_ANNOTATION/03_native_outputs/pharokka/pharokka.gbk)
         → work/clinker/<run_adı>.gbk olarak evele (clinker küme etiketi = örnek adı)
         → conda run -n ali-clinker clinker <gbk...> -p clinker.html
         → clinker.html (compare çıktı dizinine KARDEŞ dosya; gömülmez)
         → comparison_report.html + _en.html içinden relatif LİNK
```

## 4. Bileşenler
- **`tools.py`** — `clinker_cmd(gbks, out_html, conda_env, extra=None)`: `conda run -n <env> clinker <gbk...>
  -p <out_html>` komutunu kurar. Payload olarak liste döndürür (mevcut `*_cmd` deseni).
- **`compare.py`**
  - `stage_genbanks(run_dirs, work_dir)` → her run'ın `pharokka.gbk`'ını `work/<run_adı>.gbk` olarak
    kopyalar; gbk'ı olmayan run atlanır (hangisi atlandığı döndürülür). Evrilen (staged) gbk yol listesi döner.
  - `build_clinker(run_dirs, out_dir, cfg)` → stage_genbanks + clinker koştur → `out_dir/clinker.html` üret.
    Dönüş: `{"html": "clinker.html", "n_genomes": k, "skipped": [...]}` veya None (yetersiz/başarısız).
  - `run_compare` → GenBank'lı ≥2 örnek varsa `build_clinker` çağır; sonucu `data["clinker"]`'e koy.
- **`report/render.py`** `render_comparison` — `data.get("clinker")` varsa yeni bölüm:
  başlık "İnteraktif Gen-Kümesi Synteny (clinker)" + `clinker.html`'e relatif `<a>` link + kaç genom notu.
  i18n'den çevrili (tr+en).
- **`report/i18n.py`** — yeni bölüm etiketleri (başlık, link metni, not, yetersiz-genom mesajı).

## 5. Hata yönetimi (sessiz-hata YASAK — bkz. feedback_gurultulu_hata)
- Bir run'da `pharokka.gbk` yok → o örnek clinker'dan düşer, `skipped`'e eklenir (rapora yansır).
- Evrilen gbk < 2 → clinker atlanır; rapor bölümü dürüst "yetersiz anotasyonlu genom (≥2 gerekir)" mesajı.
- clinker sıfır-dışı çıkış / `clinker.html` üretilmez → `build_clinker` None döner; rapor clinker bölümünü
  atlar (uyarı notu), geri kalan comparison raporu üretilir. safe_run + log dosyası.

## 6. Test (TDD)
1. `clinker_cmd` doğru komut kurar (gbk'lar sırayla, `-p out_html`, `conda run -n ali-clinker`).
2. `stage_genbanks` gbk'ı olan run'ları örnek-adıyla eveler; gbk'sız run'ı `skipped`'e koyar.
3. `build_clinker` 2 minik gerçek gbk ile `clinker.html` üretir (ali-clinker gerçek koşu; küçük veri).
4. `build_clinker` <2 gbk → None (dürüst atlama).
5. `render_comparison` clinker link'i içerir (data["clinker"] varsa); tr + en.
6. Mevcut 102 test yeşil kalır.

## 7. Gerçek doğrulama
2+ gerçek T7 run (short + hybrid) ile `virusforge compare` → `clinker.html` açılır, gen-kümesi hizalaması
gösterir (T7'ler ~%100 benzer → yoğun bağlantı), link iki rapordan da çalışır, dürüst notlar tutarlı.

## 8. Kabul kriterleri
1. `compare` ≥2 anotasyonlu genomda `clinker.html` üretir + iki rapordan linkler.
2. Statik-SVG synteny (V09) bozulmaz.
3. Eksik/yetersiz/başarısız durumlar dürüst not, sessiz hata yok.
4. Yeni pytest'ler + mevcut 102 test yeşil.
5. `ali-clinker` env kullanılır (yeni env kurulmaz).
