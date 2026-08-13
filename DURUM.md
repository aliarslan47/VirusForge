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

## 2026-08-13 — M2-A FAJ ZENGİNLEŞTİRME TAMAM + T7'de DOĞRULANDI
Brainstorm→spec (`docs/superpowers/specs/2026-08-13-...-m2a-...-design.md`)→plan→TDD ile 4 yeni modül:
**V09 host** (RaFAH/iPHoP config-seçmeli) · **V11 AMR** (AMRFinderPlus) · **V12 termini** (PhageTerm) ·
**V13 domain** (phold). Hepsi faj-koşullu (`is_phage`); pipeline `…V08→V09→V11→V12→V13→V19`.
- **Ön koşul çözüldü:** V07 artık pharokka çıktısını artifact yayınlıyor (`_protein_faa`=phanotate.faa,
  pharokka.faa DEĞİL) + `restore_artifacts` → V11/V13 resume'da besleniyor.
- **İzole conda env deseni** (phabox gibi): `tools.<araç>.conda_env` → `vf_amr`/`vf_rafah`/`vf_phageterm`/
  `vf_phold`; çalışan `virusforge` env'i korunur.
- **20 yeni pytest (toplam 63 yeşil).** registry+references+config+render güncel (4 yeni amaca-özel tablo).
- **T7 `--resume` GERÇEK DOĞRULAMA (9/9 modül tutarlı):** V00–V08 atlandı, V09–V13+V19 koştu.
  - **V11 PASS (gerçek):** AMRFinderPlus v4.2.7, 76 proteinde **0 AMR** (litik faj için doğru). input=protein.
  - **V13 PASS (gerçek):** phold v1.2.6 (DB 15GB kuruldu), bilinmeyen **30→27** (yapı-tabanlı 3 CDS fonksiyon).
  - **V09/V12 WARNING (dürüst):** RaFAH+PhageTerm bioconda/pypi'da YOK, kaynak kurulumu bu oturumda
    yapılamadı → net "env yok" hatası (uydurma yok). Env adları config'te hazır; araçlar kurulunca çalışır.
  - Rapor 2.6MB, 4 yeni tablo + gerçek değerler; V19 yeniden üretildi.
- **Gerçek-veri bug'ı yakalandı+düzeltildi:** AMRFinderPlus **v4.x sütun adları** değişmiş
  (Type/Element symbol/% Coverage of reference) — parser v3+v4 uyumlu yapıldı (sessiz-hata önlendi).
- **Kurulu env'ler:** `vf_amr` (AMRFinderPlus+DB), `vf_phold` (phold+15GB DB). Kurulamayan: RaFAH, PhageTerm.

## Şu an nerede kaldık
- **M1 İSKELETİ KURULDU + TEST GEÇTİ (2026-08-12).** `virusforge/` paketi tam: config, util, provenance, Module tabanı + 8 standart klasör + durum kodları, registry (doğrulanmış repo'lar), detect (V00), V01–V08 + V19 modülleri, tools.py (komut kurucular), pipeline (moda göre yönlendirme + resume), CLI (`run`/`info`), HTML rapor motoru.
- **43 pytest yeşil** (config/util/provenance/module/registry/detect/parsers/tools/pipeline/e2e-dryrun). Sentetik fixture'larla; gerçek veri indirilmedi.
- **CLI smoke:** araçsız bile uçtan uca koşuyor — V00 PASS, V19 PASS (rapor+provenance), diğerleri dürüstçe WARNING, V08 NOT_APPLICABLE. Çökme yok.
- Commit'ler yerelde (push için gh auth bekliyor): d647cc5 (çekirdek), 19144d4 (tam hat).
- **2026-08-12 (akşam): RAPOR PROFESYONELLEŞTİRİLDİ.** BacForge-tarzı: numaralı/isimli 12 Tablo + 4 Şekil (pipeline akışı, Mash-mesafe grafiği, **circular genom haritası**, fonksiyonel kategori grafiği), Genel Bakış kartları, araç+sürüm+DOI tablosu. Genom haritası V07'de **otomatik** üretiliyor (pharokka_plotter gömüldü → `06_visualization/genome_map.png`). Rapor artifact olarak yayımlandı: https://claude.ai/code/artifact/0541885b-ce14-4011-87db-6eecc212b819. Kullanıcı geri bildirimi bellekte: **otonom çalış, görseller dahil her şeyi kendin üret+denetle** ([[feedback_otonom_denetim]]).
- **M2-A faj zenginleştirme kod+doğrulama TAMAM (2026-08-13, üstteki bölüm).**
- **SIRADA seçenekleri:**
  1. **RaFAH + PhageTerm kaynak kurulumu** → V09 host + V12 termini gerçek doğrulaması (T7 için **DTR** beklenen — bilinen doğru). İkisi de bioconda/pypi'da yok: RaFAH GitHub `felipehcoutinho/RaFAH` (HMMER+prodigal+model), PhageTerm GitLab `vlegrand/ptv` (py3). Env'ler `vf_rafah`/`vf_phageterm` config'te hazır; kurulunca modüller dokunmadan çalışır.
  2. **long + hybrid** yolları (`samples/T7_long/…ont.fastq.gz` indi) — `conda install -n virusforge -c bioconda flye medaka unicycler nanoplot`.
  3. **M2-B RNA-virüs yolu** ayrı spec (rnaviralSPAdes/iVar + VADR + iVar/LoFreq + V05 RNA yönlendirme).
- **Env'ler:** `virusforge` (ana) · `vf_phabox` (pandas 2.3) · `vf_amr` (AMRFinderPlus) · `vf_phold` (phold+15GB DB). DB'ler `databases/` (checkv/genomad/pharokka/inphared/phabox).

## Milestone planı
- **M1** — DNA/faj çekirdek (short+long+hybrid): V00→V01→V03→V04→V05→V06→V07→V08→V19. Yalın set (geNomad, Pharokka, PhaBOX, CheckV, Mash+INPHARED, SPAdes/Flye/Unicycler).
- **M2** — RNA-virüs yolu + zenginleştirme (V09–V13, +phold, VADR, iVar/LoFreq).
- **M3** — karşılaştırmalı/filo/görsel (V15–V18) + metavirome + plugin lineage (Pangolin/Nextclade/IRMA).
