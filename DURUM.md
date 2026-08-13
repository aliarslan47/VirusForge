# DURUM — VirusForge

> "Nerede kaldık" anlık görüntüsü. `/clear` öncesi ve anlamlı her durakta güncellenir.

**Konum:** `/home/ali/VirusForge/` · **GitHub:** `github.com/aliarslan47/VirusForge`
**Kimlik:** Forge ailesinin virüs/faj üyesi (kardeşler: BacForge=bakteri, Vaxforge). BacForge deseniyle aynı ama **tamamen izole** (ayrı paket/env, `import bacforge` YOK).
**Son güncelleme:** 2026-08-13

## Ne oldu (2026-08-12)
- Repo `Phage-Compare-Mini-Pipeline` → **VirusForge** yeniden adlandırıldı (GitHub API teyitli); remote güncellendi. Eski R betiği `legacy/`e taşındı (temel değil).
- Kaynak spec (`viral_phage_bacteriophage_antigravity_spec_v3.md`) denetlendi:
  - **Tool Registry doğrulandı** — 6 ölü/yanlış repo (CheckV/chklovski, Prodigal-gv/RiversLab, iPHoP/Roux-SGLab, RaFAH/coevoeco, PhageTerm/source-data, VIRIDIC/rega-cev) + 2 fork/ayna (vConTACT2, MAFFT) düzeltildi.
  - Fazlalıklar belirlendi (şemsiye araç içindekiler ayrı kurulmayacak; çoklu-identifier/host opsiyonel).
- **Kapsam RNA + DNA tüm virüsler** olarak genişletildi. 2026 makalelerinden 2 gerçek ekleme doğrulandı: **INPHARED** (faj referans DB) + **phold** (yapısal annotation). RNA yolu: rnaviralSPAdes/iVar + **VADR** + **iVar/LoFreq**.
- **Tasarım dokümanı yazıldı:** `docs/2026-08-12-virusforge-design.md` (mimari + doğrulanmış registry + milestone planı).

## 2026-08-12 — KISA OKUMA UÇTAN-UCA DOĞRULANDI (T7, 9/9 PASS)
Gerçek ENA verisi `ERR3804828` (Escherichia phage T7, Illumina MiSeq). conda env `virusforge` + DB'ler indirildi (CheckV 6.4G, geNomad 1.4G, Pharokka 1.8G, INPHARED 187M, PhaBOX 1.6G). **Tüm 9 modül PASS**, sonuçlar doğru:
- V04: 45.451 bp / 7 contig; **CheckV %100 comp, %0 cont, Complete**
- V05 geNomad: Caudoviricetes;**Autographiviridae** ✅
- V06 Mash+INPHARED: en yakın **V01146** (T7 ref) dist 0.0036 → cins Teseptimavirus ✅
- V07 Pharokka: **76 CDS** (head&packaging 14, DNA/RNA metab 16, tail 5, lysis 3)
- V08 PhaBOX: **virulent** + **Studiervirinae** ✅
- V19: BacForge-tarzı HTML rapor + provenance

**Çözülen 3 gerçek bug:** (1) Pharokka parser contig-başına satırları topluyor (60→doğru); (2) env diamond 0.9.10→2.2.5 (CheckV DIAMOND); (3) PhaBOX pandas-3 `'singleton'` hatası → izole `vf_phabox` env (pandas 2.3) + `conda run`. Ayrıca CLI `--resume` + resume artifact geri-yükleme eklendi.

## 2026-08-13 — M2-A (V08 AMR) + TAM RENUMBER (BOŞLUKSUZ V00–V09)
Brainstorm→spec→plan→TDD ile faj zenginleştirme eklendi, sonra kullanıcı kararıyla sadeleştirildi +
kodlar boşluksuz hale getirildi.
- **KALDIRILANLAR (kullanıcı kararı):**
  - **Host (RaFAH) + Termini (PhageTerm):** araçları bioconda/pypi'da yok, dağıtım kanalları
    (SourceForge 403, Pasteur GitLab klon bozuk) bu ortamdan erişilemedi → tamamen silindi + `vf_rafah` env.
  - **Domain (phold):** `vf_phold` env 25GB (15GB DB) çok yer kaplıyordu → env + modül + tüm referanslar silindi.
- **TAM RENUMBER (boşluksuz):** V03→V02, V04→V03, V05→V04, V06→V05, V07→V06, V08→V07, V11→**V08 (AMR)**,
  V19→**V09 (rapor)**. Token-tabanlı script + git mv; dosya adları/sınıf adları/kod stringleri/dirname/
  rapor referansları hepsi tutarlı. **Yeni sıra: V00→V01→V02→V03→V04→V05→V06→V07→V08→V09 (10 modül, sıfır boşluk).**
- **M2-A kalan = V08 AMR & Virülans (AMRFinderPlus).** Faj-koşullu (`is_phage`).
- **Ön koşul:** V06 (annotate) pharokka çıktısını artifact yayınlıyor (`_protein_faa`=phanotate.faa) +
  `restore_artifacts` → V08 AMR proteinlerle beslenir.
- **İzole conda env:** `tools.amrfinder.conda_env=vf_amr`; çalışan `virusforge` env korunur.
- **53 pytest yeşil** (e2e-dryrun tam pipeline dahil).
- **T7 gerçek doğrulama:** V08 AMR = AMRFinderPlus v4.2.7, 76 proteinde **0 AMR** (litik faj için doğru).
  **Gerçek-veri bug'ı:** AMRFinderPlus **v4.x sütun adları** değişmiş (Type/Element symbol/% Coverage of
  reference) — parser v3+v4 uyumlu (sessiz-hata önlendi). Taze T7 koşusu yeni kodlarla üretiliyor.
- **Kurulu env'ler:** `vf_amr` (AMRFinderPlus+DB). Silinen: `vf_rafah`, `vf_phold`, `databases/rafah`.

## 2026-08-13 — LONG-OKUMA YOLU GERÇEK-VERİ DOĞRULANDI (T7 ONT, 10/10 PASS)
Gerçek ENA `SRR30401542` (T7 ONT, 25.351 okuma, ort. Q10.4). İzole `vf_long` env (Flye/Medaka/
NanoPlot/filtlong; conda_env deseni, `virusforge` env korunur). **10/10 modül PASS, biyoloji kısa-
okumayla tutarlı:** Autographiviridae, en yakın T7 V01146 (0.0009), **virulent**, **0 AMR**, CheckV
**%96.8 High-quality** tek contig. (CDS 54 vs short 76 — long Q10 konsensüs artık hatası, beklenen.)
**3 gerçek bug bulundu+düzeltildi (gerçek-veri doğrulamasının değeri):**
1. **Kimya:** Q10.4 verisinde `--nano-hq` yanlış → `resolve_chemistry(mean_qual)`: Q<13 → r9 (--nano-raw).
2. **Flye `--meta`:** küçük+ultra-derin (1616x) fajda `--meta` olmadan "No disjointigs assembled" çöküşü.
3. **Junk contig:** Flye 5 contig (ana 1911x + 4 junk 3-22x host/kimera) → sahte AMR + yanlış yaşam tarzı;
   `filter_contigs_by_coverage` (max*0.1 altı elenir) → temiz tek-genom.
Medaka kimyaya-duyarlı model (R9→r941_min_sup_g507). **62 pytest yeşil.**

## 2026-08-13 — HYBRID YOLU DOĞRULANDI → M1 PLATFORM KAPSAMI TAMAM (short+long+hybrid)
Hibrit örnek `samples/T7_hybrid` (short R1/R2 + long ONT symlink). Unicycler `vf_long`'a kuruldu.
**10/10 PASS, üç okuma tipinin EN İYİ sonucu:** tek contig, CheckV **%100 Complete High-quality**,
**40.532 bp** (tam T7, DTR uçları dahil), **60 CDS (=T7 ref NC_001604)**, Autographiviridae,
en yakın V01146 (0.0010), **virulent**, **0 AMR**. **2 gerçek hibrit-bug bulundu+düzeltildi:**
1. **Unicycler sayısal header** `>1` → PhaBOX pandas 'int64/object merge Accession' çöküşü →
   `sanitize_contig_names` (salt-sayısal → contig_<n>).
2. **Medaka hibrit'i bozuyordu:** Unicycler zaten short-düzeltmeli; R9/Q10 ONT medaka'sı hata geri
   sokuyordu (CDS 76→55) → Medaka **yalnız saf LONG_READ**. **64 pytest yeşil.**
**MILESTONE 1 PLATFORM KAPSAMI TAMAM: short✅ + long✅ + hybrid✅ + assembly_input✅** (hepsi T7 gerçek-veri, tutarlı biyoloji).

## 2026-08-13 — ASSEMBLY_INPUT doğrulandı + rapor dil kararı
- **ASSEMBLY_INPUT** (hazır genom girdisi): `samples/T7_assembly` (hibrit T7 assembly'si). V01 N/A (okuma QC yok),
  V02 fasta→draft (+sayısal-header temizleme, PhaBOX güvenliği), V03 QUAST/CheckV (medaka yok). Sonuç: temiz T7
  (CheckV %100 HQ, Autographiviridae, 60 CDS, virulent, 0 AMR). **4. girdi modu da doğrulandı.**
- **Rapor dil kararı (kullanıcı):** pipeline şeması **İngilizce** kalır (modül adları); bölüm içerikleri Türkçe.
  Rapor bug'ları düzeltildi: assembler adı (conda-yolu değil), sürüm tespiti `_parse_version` (uyarı/yardım
  çöpü atılır). **İLERİDE: rapor sistemi TR+ENG çift-dilli olacak** (henüz değil).

## 2026-08-13 — M3 FAZ 1: V09 KARŞILAŞTIRMALI TANIMLAMA & FİLOGENİ TAMAM + T7 DOĞRULANDI
Brainstorm→spec→plan(8 task)→TDD. Yeni **V09 Comparative** modülü (rapor V09→**V10**'a kaydı). Akış:
online blastn(-remote) → en yakın 5 tür → efetch → MAFFT+IQ-TREE2 ağaç + taxmyPHAGE ICTV cins/tür.
**BLAST=tanımlama, ICTV=verdikt** (best-hit'ten türetilmez). **79 pytest yeşil.**
- **T7 hibrit gerçek doğrulama (V09 PASS, 11/11 modül):**
  - **ICTV (taxmyPHAGE):** cins **Teseptimavirus**, tür **Teseptimavirus T7** (=Escherichia virus T7);
    örnek vs V01146 %98.25 intergenomic → ICTV %95 tür eşiği üstü; "cins düzeyinde tutarlı".
  - **Ağaç:** örnek V01146 (T7 ref) ile yan yana (dal 0.0002); Autographiviridae T7-benzeri klad.
- **Task 8'de 4 gerçek-veri bug bulundu+düzeltildi:**
  1. **iqtree binary** `iqtree` (v3.1.3), `iqtree2` değil → config `iqtree_bin`.
  2. **blastn -remote bu ortamdan NCBI Blast4'e ERİŞEMİYOR** (bloklu, SF/GitLab gibi) → **timeout(120s) +
     V05 (yerel Mash+INPHARED) fallback**: online BLAST birincil kalır, erişilemezse V05 akrabaları ağaç referansı.
  3. **mafft `--adjustdirection`**: ters-tümleyen genom → sahte uzun dal (2.1→0.0002) düzeltildi.
  4. **taxmyPHAGE DB** kurulumu (`taxmyphage install` → VMR + BLAST DB). ICTV yerel VIRIDIC, online gerektirmez.
- **M3 GÖRSEL TAM (Part A+B):**
  - **VIRIDIC benzerlik ısı-haritası** (taxmyPHAGE üretir → rapora gömülü).
  - **Gen-düzeni SYNTENY** (özel statik SVG): clinker interaktif-HTML bağımsız rapora girmediğinden kendi
    üretimimiz — en yakın ref'i pharokka ile annotate + örnek proteinleri ref'e **yerel blastp** (ağsız) →
    homolog gen çiftleri → gen okları (PHROG fonksiyon renkli) + bağlantı çizgileri. **T7: 60 genden 59'u
    homolog** (örnek vs V01146=T7 ref, neredeyse tam synteny). **86 pytest yeşil.**
  - **V09 tam kapsam:** BLAST tanımlama + IQ-TREE2 ağaç + taxmyPHAGE ICTV + VIRIDIC heatmap + synteny.
- **Kurulu:** blast, iqtree(v3), taxmyphage(+DB), mafft✅, efetch✅ (hepsi `virusforge` env).
- **NOT:** online BLAST bu ortamda bloklu; V05 fallback ile ağaç+ICTV yine üretiliyor. Ağ erişimli
  ortamda online BLAST birincil çalışır (kod hazır). Spec/plan: `docs/superpowers/{specs,plans}/2026-08-13-*m3*`.

## 2026-08-13 — RAPOR CHARSET KÖK-ÇÖZÜM + ÇOKLU-ÖRNEK KARŞILAŞTIRMA (Item 2)
- **Türkçe mojibake KALICI çözüldü:** rapor `<meta charset="utf-8">`siz üretiliyordu → tarayıcı UTF-8'i
  Latin-1 okuyup harfleri bozuyordu (Örnek→Ã–rnek). `render_html`+`render_comparison` artık düzgün HTML
  iskeleti (`_document` helper) sarıyor. TDD kilitli (`test_report_has_utf8_charset`). 4 rapor da yenilendi ✅.
- **Item 2 — Çoklu-örnek karşılaştırma (`virusforge compare`):** ayrı komut, tamamlanmış run'ları alır →
  ortak MAFFT+IQ-TREE2 ağaç + yerel all-vs-all blastn benzerlik matrisi + ICTV özet tablosu → charset'li
  `comparison_report.html`. `compare.py` + CLI `compare` alt-komutu. **Doğrulandı:** 4 T7 run %100, EU734174
  (phage13a) %94.4 (farklı tür/aynı cins). **94 pytest yeşil.** Spec: `docs/superpowers/specs/2026-08-13-*compare*`.
- **Item 3 — ÇİFT-DİLLİ RAPOR TAMAM ✅** (kullanıcı seçimi = **iki dosya**: `report.html` tr +
  `report_en.html` en, üstte dil linki). `report/i18n.py` (EN sözlüğü + `t()`), `render_html(lang=)` +
  `render_comparison(lang=)` choke-point çevirisi (table/section/stat/figure + başlık/Genel Bakış/header +
  na-mesajları + Araçlar bölümü). TR varsayılan değişmez; bilimsel terimler (PHROG/taksonomi/enum) korunur.
  **YARIN KALAN 4 madde bitti:** (1) na-mesajları + Araçlar bölümü çevirisi `L()`'e bağlandı; (2) dil-geçiş
  nav linki (`_lang_switch`: EN→Türkçe, TR→English); (3) `v10_report.py` + `compare.py` DUAL çıktı (tr+en);
  (4) T7 gerçek doğrulama. `_document(lang=)` → `<html lang=>` gerçek dili yansıtır. **102 pytest yeşil**
  (+6 yeni: lang attr, dil linki, comparison EN, v10 dual, compare dual, na/tools EN).
  **T7 hibrit gerçek doğrulama:** report.html (TR) + report_en.html (EN) üretildi; doğru lang, charset,
  çalışan dil linki, mojibake yok, Autographiviridae/virulent korundu. Spec: `docs/.../2026-08-13-*bilingual*`.
## 2026-08-13 — M3 FAZ 2: clinker İNTERAKTİF SYNTENY TAMAM + T7 DOĞRULANDI
Brainstorm→spec→plan→TDD. `virusforge compare`'e **çok-genomlu interaktif** gen-kümesi hizalaması eklendi.
- **Yerleşim (kullanıcı kararı):** `compare` komutu (çok-örnek); clinker'ın asıl gücü çok-genom, GenBank'lar hazır.
- **Env (kullanıcı kararı):** mevcut `ali-clinker` (v0.0.32) yeniden kullanıldı (saf araç, yeni env kurulmadı);
  config `tools.clinker.conda_env`.
- **Akış:** her run'ın `V06_.../pharokka/pharokka.gbk`'ı → `stage_genbanks` örnek-adıyla evele → `build_clinker`
  `conda run -n ali-clinker clinker <gbk...> -p clinker.html` → **portable clustermap HTML** (gömülmez) →
  `render_comparison` iki rapordan (tr+en) relatif link. Statik-SVG synteny (V09) korunur; clinker tamamlar.
- **Hata yönetimi (sessiz yok):** gbk'sız run dürüst `skipped`; <2 anotasyonlu genom veya clinker hatası → None
  (bölüm atlanır, rapor gerisi üretilir).
- **107 pytest yeşil** (+5: `clinker_cmd`, `stage_genbanks` evele/skip, `<2→None`, render link tr+en,
  **gerçek clinker koşusu** minik gbk→clustermap HTML).
- **T7 gerçek doğrulama:** short+hybrid `compare` → `clinker.html` (666KB portable clustermap, iki genom),
  iki rapor da linkli+çevrili, EN'e ham TR sızmadı. Spec: `docs/.../2026-08-13-*clinker*`.

## 2026-08-13 — V06 GEN ANOTASYON TABLOSU (her CDS) EKLENDİ + T7 DOĞRULANDI
Kullanıcı isteği: anotasyon bölümüne her gen için satır olan tablo. `v06_annotate.parse_cds_genes`
(`pharokka_cds_final_merged_output.tsv` → gene/start/stop/strand/product(annot)/phrog/category) →
V06.run `metrics.genes` (report.json'a girer) → render V06 bölümü **"Gen anotasyon listesi (her CDS)"**
tablosu (# · Gen · Başlangıç · Bitiş · Yön · Ürün · PHROG · Kategori); TSV yoksa atlanır. i18n tr+en.
**109 pytest yeşil** (+2). T7 hibrit: 60 CDS satırı iki raporda da, EN'e ham TR sızmadı. commit a6fe5ad.

## Şu an nerede kaldık (özet)
- **SIRADA (asıl işler):** **M2-B RNA yolu** (rnaviralSPAdes/iVar + VADR + iVar/LoFreq).
- **DÜŞÜK ÖNCELİK / opsiyonel:** rapor-cilalama listesinin Item 4'ü = opsiyonel tespit araçları
  (virsorter2/vibrant/kraken2) → config'te var, modül yok. (NOT: "short/long/hybrid" ayrı bir eksen = M1
  platform kapsamı, çoktan TAMAM; Item numaraları rapor-cilalama fazına aittir, okuma tipiyle ilgisiz.)

## Şu an nerede kaldık
- **M1 İSKELETİ KURULDU + TEST GEÇTİ (2026-08-12).** `virusforge/` paketi tam: config, util, provenance, Module tabanı + 8 standart klasör + durum kodları, registry (doğrulanmış repo'lar), detect (V00), V01–V08 + V19 modülleri, tools.py (komut kurucular), pipeline (moda göre yönlendirme + resume), CLI (`run`/`info`), HTML rapor motoru.
- **43 pytest yeşil** (config/util/provenance/module/registry/detect/parsers/tools/pipeline/e2e-dryrun). Sentetik fixture'larla; gerçek veri indirilmedi.
- **CLI smoke:** araçsız bile uçtan uca koşuyor — V00 PASS, V19 PASS (rapor+provenance), diğerleri dürüstçe WARNING, V08 NOT_APPLICABLE. Çökme yok.
- Commit'ler yerelde (push için gh auth bekliyor): d647cc5 (çekirdek), 19144d4 (tam hat).
- **2026-08-12 (akşam): RAPOR PROFESYONELLEŞTİRİLDİ.** BacForge-tarzı: numaralı/isimli 12 Tablo + 4 Şekil (pipeline akışı, Mash-mesafe grafiği, **circular genom haritası**, fonksiyonel kategori grafiği), Genel Bakış kartları, araç+sürüm+DOI tablosu. Genom haritası V07'de **otomatik** üretiliyor (pharokka_plotter gömüldü → `06_visualization/genome_map.png`). Rapor artifact olarak yayımlandı: https://claude.ai/code/artifact/0541885b-ce14-4011-87db-6eecc212b819. Kullanıcı geri bildirimi bellekte: **otonom çalış, görseller dahil her şeyi kendin üret+denetle** ([[feedback_otonom_denetim]]).
- **M2-A (V08 AMR) + tam renumber TAMAM (2026-08-13, üstteki bölüm). Host/termini/domain kaldırıldı.**
- **M1 PLATFORM KAPSAMI TAMAM (short+long+hybrid, T7 doğrulandı) + M2-A V08 AMR (2026-08-13).**
- **SIRADA:** **M2-B RNA-virüs yolu** (ayrı spec): rnaviralSPAdes/iVar + VADR + iVar/LoFreq + V04'te RNA
  yönlendirme → yeni modüller V10+. (RNA doğrulama verisi gerekir; ör. SARS-CoV-2/HIV.)
- **Env'ler:** `virusforge` (ana) · `vf_phabox` (pandas 2.3) · `vf_amr` (AMRFinderPlus) · `vf_long` (Flye/Medaka/NanoPlot/filtlong/unicycler). DB'ler `databases/`.
- **Run dizinleri:** `runs/*_short_read` · `*_long_read` · `*_hybrid` (üçü de doğrulanmış).

## Milestone planı (güncel numaralandırma — boşluksuz)
- **M1** — DNA/faj çekirdek (short+long+hybrid): V00→V01→V02→V03→V04→V05→V06→V07(+**M2-A V08 AMR**)→V09 rapor. Set: geNomad, Pharokka, PhaBOX, CheckV, Mash+INPHARED, SPAdes/Flye/Unicycler, AMRFinderPlus.
- **M2-B** — RNA-virüs yolu (rnaviralSPAdes/iVar + VADR + iVar/LoFreq + RNA yönlendirme) → yeni modüller V10+.
- **M3** — karşılaştırmalı/filo/görsel + metavirome + plugin lineage (Pangolin/Nextclade/IRMA) → V11+.
