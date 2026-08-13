# VirusForge — Çoklu-Örnek Karşılaştırma Tasarımı (M3+ Item 2)

> Tarih: 2026-08-13 · Durum: onaylandı (kullanıcı) · Kapsam: birden çok tamamlanmış koşuyu karşılaştıran ayrı komut.

## 1. Amaç
Birden fazla ayrı örnek (her biri tek virüs/faj, kendi V00→V10 koşusu bitmiş) **birlikte** karşılaştırılsın:
ortak filogenetik ağaç + örnekler-arası benzerlik matrisi + ICTV özet tablosu. Soru: "dizelediğim örnekler
birbirleriyle nasıl akraba?". Per-örnek V-modülleri (V00–V10) **dokunulmaz**; bu ayrı bir CLI komutu.

## 2. Mimari
- **`virusforge/compare.py`** — karşılaştırma orkestrasyonu (saf fonksiyonlar + `run_compare()`).
- **CLI:** yeni `compare` alt-komutu — `virusforge compare <run1> <run2> … --out <dizin>`.
- **`virusforge/report/render.py`** — yeni `render_comparison(data)` (mevcut `_svg_tree`/`_svg_matrix` +
  charset'li HTML iskeleti yeniden kullanılır).
- Araçlar mevcut: MAFFT, IQ-TREE2, blastn (yerel), hepsi `virusforge` env. Ağ gerektirmez.

## 3. Akış
```
girdi: tamamlanmış run dizinleri (her birinde V03…/viral_genome.fasta)
  ↓ her run'dan topla: genom fasta + örnek adı + ICTV (V09) + taksonomi (V04) + genom uzunluğu
  ↓ tüm genomları tek fasta'ya (header = örnek adı; salt-sayısal temizle)
  ├─ MAFFT --adjustdirection → IQ-TREE2 (ML + bootstrap) → ORTAK AĞAÇ (Newick)
  └─ yerel all-vs-all blastn (makeblastdb + blastn) → ikili % kimlik → BENZERLİK MATRİSİ
  ↓ render_comparison → comparison_report.html
```

## 4. Fonksiyonlar (compare.py)
- `collect_samples(run_dirs) -> list[dict]`: her run için `{name, genome_path, ictv, taxonomy, length}`
  (genom = `V03_POLISHING_VIRAL_QC/04_standardized/viral_genome.fasta`; ICTV = V09 comparative.json;
  taksonomi = V04; ad = run dizin adı ya da örnek adı). Genomu olmayan run atlanır (loglanır).
- `build_combined_fasta(samples, out_fasta)`: örnek genomlarını tek fasta'ya birleştir (header=örnek adı).
- `pairwise_identity_matrix(fasta, work) -> (labels, matrix)`: makeblastdb + all-vs-all blastn →
  NxN % kimlik matrisi (köşegen=100). Parser: `parse_blastn_identity(tsv)`.
- `run_compare(run_dirs, out_dir, cfg)`: yukarıdaki akışı koşar; comparison_report.html + comparison.json yazar.

## 5. Çıktı — comparison_report.html
- **Tablo:** örnekler (ad · genom uzunluğu · ICTV cins/tür · taksonomi)
- **Şekil:** ortak filogenetik ağaç (`_svg_tree`) — hangi örnek hangisiyle kümeleniyor
- **Şekil:** örnekler-arası benzerlik matrisi ısı-haritası (`_svg_matrix`)
- `comparison.json`: örnekler + newick + matris (yeniden üretilebilirlik)
- **charset'li HTML** (Türkçe mojibake yok — render_html ile aynı iskelet).

## 6. Dürüstlük / hata
- < 2 geçerli genom → WARNING (karşılaştırma anlamsız), açık mesaj.
- MAFFT/IQ-TREE2/blastn yok → o alt-çıktı atlanır, dürüst not; komut çökmez.
- Genomu olmayan / bozuk run atlanır + loglanır (sessiz yutma yok).

## 7. Test
- `parse_blastn_identity` birim testi (sentetik blastn tsv → matris).
- `collect_samples` birim testi (sahte run dizin yapısı → toplanan alanlar).
- `build_combined_fasta` (header=örnek adı, sayısal-temizleme).
- `render_comparison` smoke (sentetik veri → HTML çöker mez, charset var).
- `run_compare` araçsız ortamda dürüst WARNING (mekanizma).

## 8. Doğrulama
- 4 T7 run'ı (short/long/hybrid/assembly) = 4 örnek → matris ~%99+ hepsi (aynı genom), ağaç sıkı küme.
- Anlamlı dallanma için ref_cache'teki akrabalar (V01146=T7, EU734174=phage13a, …) ek örnek olarak →
  T7 örnekleri bir kladda, phage13a ayrı dalda; matris T7'ler ~%99, phage13a ~%95.

## 9. Kabul kriterleri
1. `virusforge compare <run'lar> --out <dizin>` çalışır; comparison_report.html + comparison.json üretir.
2. Ortak ağaç + benzerlik matrisi + örnek tablosu; charset'li (Türkçe doğru).
3. <2 genom / araç yok → dürüst WARNING, çökme yok.
4. Yeni pytest'ler + mevcut 87 test yeşil.
5. 4 T7 run + akraba ile gerçek doğrulama: T7'ler kümelenir, akraba ayrı dal.

## 10. Kapsam dışı (sonra)
- Örneklerin closest-ref'lerini de ağaca katma (şimdilik yalnız örnekler + isteğe bağlı elle akraba)
- Çift-dilli rapor (Item 3, ayrı) · metavirome (tek örnek çok virüs — ayrı, farklı iş)
