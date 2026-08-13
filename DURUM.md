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

## Şu an nerede kaldık
- **M1 İSKELETİ KURULDU + TEST GEÇTİ (2026-08-12).** `virusforge/` paketi tam: config, util, provenance, Module tabanı + 8 standart klasör + durum kodları, registry (doğrulanmış repo'lar), detect (V00), V01–V08 + V19 modülleri, tools.py (komut kurucular), pipeline (moda göre yönlendirme + resume), CLI (`run`/`info`), HTML rapor motoru.
- **43 pytest yeşil** (config/util/provenance/module/registry/detect/parsers/tools/pipeline/e2e-dryrun). Sentetik fixture'larla; gerçek veri indirilmedi.
- **CLI smoke:** araçsız bile uçtan uca koşuyor — V00 PASS, V19 PASS (rapor+provenance), diğerleri dürüstçe WARNING, V08 NOT_APPLICABLE. Çökme yok.
- Commit'ler yerelde (push için gh auth bekliyor): d647cc5 (çekirdek), 19144d4 (tam hat).
- **2026-08-12 (akşam): RAPOR PROFESYONELLEŞTİRİLDİ.** BacForge-tarzı: numaralı/isimli 12 Tablo + 4 Şekil (pipeline akışı, Mash-mesafe grafiği, **circular genom haritası**, fonksiyonel kategori grafiği), Genel Bakış kartları, araç+sürüm+DOI tablosu. Genom haritası V07'de **otomatik** üretiliyor (pharokka_plotter gömüldü → `06_visualization/genome_map.png`). Rapor artifact olarak yayımlandı: https://claude.ai/code/artifact/0541885b-ce14-4011-87db-6eecc212b819. Kullanıcı geri bildirimi bellekte: **otonom çalış, görseller dahil her şeyi kendin üret+denetle** ([[feedback_otonom_denetim]]).
- **M2-A (V08 AMR) + tam renumber TAMAM (2026-08-13, üstteki bölüm). Host/termini/domain kaldırıldı.**
- **SIRADA seçenekleri:**
  1. **long + hybrid** yolları (`samples/T7_long/…ont.fastq.gz` indi) — `conda install -n virusforge -c bioconda flye medaka unicycler nanoplot`.
  2. **M2-B RNA-virüs yolu** ayrı spec (rnaviralSPAdes/iVar + VADR + iVar/LoFreq + RNA yönlendirme).
- **Env'ler:** `virusforge` (ana) · `vf_phabox` (pandas 2.3) · `vf_amr` (AMRFinderPlus). DB'ler `databases/` (checkv/genomad/pharokka/inphared/phabox).

## Milestone planı (güncel numaralandırma — boşluksuz)
- **M1** — DNA/faj çekirdek (short+long+hybrid): V00→V01→V02→V03→V04→V05→V06→V07(+**M2-A V08 AMR**)→V09 rapor. Set: geNomad, Pharokka, PhaBOX, CheckV, Mash+INPHARED, SPAdes/Flye/Unicycler, AMRFinderPlus.
- **M2-B** — RNA-virüs yolu (rnaviralSPAdes/iVar + VADR + iVar/LoFreq + RNA yönlendirme) → yeni modüller V10+.
- **M3** — karşılaştırmalı/filo/görsel + metavirome + plugin lineage (Pangolin/Nextclade/IRMA) → V11+.
