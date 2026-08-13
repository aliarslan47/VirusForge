# VirusForge — M2-B RNA-Virüs Yolu · FAZ 2 (Varyant & Quasispecies)

## Context
Faz 1 (tamam, commit 4e78463) RNA yolunu ekledi: yönlendirme + referans-tabanlı iVar konsensus + VADR +
faj modüllerinin N/A'sı; SARS-CoV-2 ARTIC amplikonuyla doğrulandı (konsensus 29859 bp, kapsama %98.88).
Faz 1 **BAM artifact** (`ctx.artifacts["V02"]["bam"]` = `V02_.../04_standardized/aligned_sorted.bam` +
`.bai`) ve referansı üretip saklıyor. Faz 2 bu BAM üzerinden **varyant çağırma + quasispecies** analizini
ekler: konsensus-seviyesi + düşük-frekanslı (intra-host) varyantlar. Bu, SARS-CoV-2 gibi RNA virüslerinde
kritik (kaynak tasarım: "V14 iVar + LoFreq quasispecies **kritik**"). Lineage (Pangolin/Nextclade) kapsam
dışı (sonraki iş).

Kullanıcı kararları: **yeni V11 modülü** (varyant çağırmanın DNA karşılığı yok → kendi modülü, DNA'da N/A);
kapsam **sadece varyant/quasispecies** (iVar variants + LoFreq).

## Temel karar
Faz 1 mevcut modüllere dallandı çünkü RNA analizleri DNA-eşlenikli slotlara (assembly/annotation/QC) oturdu.
Varyant çağırmanın böyle bir eşleniği YOK → **yeni `V11VariantCall` modülü** (`v11_variants.py`), DEFAULT_MODULES'a
V09 ile V10-rapor arasına eklenir. Rapor (V10) son çalışmaya devam eder. DNA/faj yolunda + BAM yoksa (de novo
RNA, referanssız) → `NOT_APPLICABLE`. **iVar variants vf_rna'da; LoFreq izole yeni `vf_lofreq` env.**

## Uygulama (dosya bazlı)

### 1. Yeni modül — `virusforge/modules/v11_variants.py`
`V11VariantCall(Module)`: code="V11", dirname="V11_VARIANT_CALLING". `run()`:
- Guard: `not is_rna(ctx)` → NOT_APPLICABLE. `bam = ctx.artifacts["V02"].get("bam")` yoksa → NOT_APPLICABLE
  (dürüst not: "referans-tabanlı BAM yok — de novo RNA'da varyant çağrılmaz").
- **iVar variants** (vf_rna, pipe): `util.run_pipe(samtools_mpileup_cmd(ref,bam), ivar_variants_cmd(prefix, min_q, min_freq))`
  → `prefix.tsv`. (`samtools_mpileup_cmd` Faz 1'de var; iVar variants mpileup'ı stdin'den okur — konsensusla aynı desen.)
  GFF verilirse (`tools.rna.gff`, opsiyonel) iVar'a `-g gff -r ref` → AA/codon etkisi; yoksa nükleotid-seviye.
- **LoFreq** (vf_lofreq): `lofreq_call_cmd(ref, bam, out_vcf)` → `lofreq call -f ref -o out.vcf bam` (BAM+`.bai` V02'den).
- Parser'lar (modül-seviye): `parse_ivar_variants(tsv)` → [{pos,ref,alt,freq,depth,(aa)}]; `parse_lofreq_vcf(vcf)`
  → [{pos,ref,alt,af,dp}].
- Metrics: `{"ivar_variants":[...], "lofreq_variants":[...], "n_total", "n_consensus" (freq≥0.5),
  "n_minor" (freq<0.5 = quasispecies/intra-host), "quasispecies": n_minor>0}`. Standardize JSON + summary.
- Status: PASS (varyant tablosu üretildi), araç hatası → WARNING (sessiz yok).

### 2. `virusforge/tools.py`
- `ivar_variants_cmd(out_prefix, min_q=20, min_freq=0.03, gff=None, ref=None, conda_env, conda_bin)` →
  `ivar variants -p <prefix> -q <q> -t <freq> [-g gff -r ref]`, `_conda_wrap(..., stream=True)` (pipe 2. komut).
- `lofreq_call_cmd(ref, bam, out_vcf, min_cov=10, conda_env, conda_bin)` →
  `lofreq call --min-cov <n> -f <ref> -o <vcf> <bam>`, `_conda_wrap`.

### 3. Pipeline & rapor entegrasyonu (yeni modül kancaları)
- `pipeline.py`: import + `DEFAULT_MODULES`'a `V09Comparative, V11VariantCall, V10Report` sırası.
- `modules/v10_report.py`: `_ORDER`'a `"V11"` ekle (V09'dan sonra → rapor bölümü sırası).
- `report/references.py`: `PIPELINE_STEPS`'e `("V11","Variant & Quasispecies Calling","iVar variants + LoFreq")`
  V10'dan ÖNCE (diyagramda V09→V11→V10; numara-sıra kozmetik, çalışma sırası doğru).
- `report/render.py`: V11 bölümü — varyant tablosu (Poz/Ref/Alt/Frekans/Derinlik/[AA]) + quasispecies özeti
  (toplam/konsensus/minör varyant sayısı). DNA'da NOT_APPLICABLE → mevcut gri-pill otomatik.
- `report/i18n.py`: yeni TR etiketleri (Varyant, Frekans, Konsensus varyant, Minör (intra-host) varyant,
  Quasispecies, Alt/Ref, Pozisyon) → EN.

### 4. config + registry + CLI
- `config/default.yaml`: `tools.rna.gff: ""` (opsiyonel AA), `tools.rna.ivar_var_min_q: 20`,
  `ivar_var_min_freq: 0.03`; `tools.lofreq: {conda_env: vf_lofreq, conda_bin, min_cov: 10}`.
- `data/registry.yaml`: `lofreq` (repo github.com/CSB5/lofreq, version_cmd, doi 10.1093/nar/gks918). iVar zaten var.
- `cli.py` `cmd_info` tuple'ına `lofreq`.
- **Env kurulumu:** `conda create -n vf_lofreq -c bioconda -c conda-forge lofreq` (2.1.5 mevcut; izole).

### 5. Test (TDD sırası)
1. `test_tools.py`: `ivar_variants_cmd` (mpileup pipe, `-t` freq, opsiyonel `-g`), `lofreq_call_cmd` (`-f -o`, vf_lofreq).
2. `test_parsers.py`: `parse_ivar_variants` (iVar tsv fixture: ALT_FREQ sütunu), `parse_lofreq_vcf` (VCF AF/DP fixture).
3. `test_v11.py`: RNA+BAM → varyant metrikleri (run_pipe/run_cmd monkeypatch, tsv/vcf üret); DNA → NOT_APPLICABLE;
   RNA+BAM-yok → NOT_APPLICABLE.
4. `test_report_svg.py`: render V11 varyant tablosu + quasispecies (tr+en).
5. `test_e2e_dryrun.py`: RNA e2e'ye V11 dahil (`_CORE`'a "V11"); DNA e2e'de V11 = N/A summary.
6. Mevcut 145 test yeşil kalır.

## Doğrulama (gerçek, Faz 1 BAM'i üzerinden)
Aynı SARS-CoV-2 örneği (`samples/CoV2_ERR11728561`, Faz 1 BAM'i mevcut) `--molecule rna` ile yeniden koş
(veya `--resume`). Beklenen: iVar + LoFreq varyant tabloları; SARS-CoV-2 soy-tanımlayıcı mutasyonlar
(konsensus-seviyesi, freq≈1.0) + birkaç minör (intra-host) varyant; quasispecies özeti; V11 rapor bölümü
çift-dilli; DNA T7 run'ında V11 = N/A. `pytest -q` tümü yeşil.

## Riskler
- **LoFreq env:** vf_lofreq izole (vf_rna'ya eklemek htslib çakışması riski — Faz 1'de görüldü). Ayrı env güvenli.
- **BAM/BAI kalıcılığı:** V02 `aligned_sorted.bam` + `.bai` 04_standardized'da (LoFreq .bai ister) — resume'da korunur.
- **iVar variants pipe:** konsensustaki `run_pipe` + `--no-capture-output` deseni aynen; iVar variants mpileup'ı
  stdin'den okur.
- **De novo RNA'da BAM yok** → V11 dürüstçe N/A (varyant çağırma referans+hizalama gerektirir).
- **GFF opsiyonel:** yoksa nükleotid-seviye varyant (AA etkisi yok) — Faz 2 için yeterli; AA sonra eklenebilir.

## Sonraki adım
Onay → spec (`docs/superpowers/specs/2026-08-14-virusforge-m2b-rna-phase2-design.md`) + commit → TDD uygula →
vf_lofreq kur → SARS-CoV-2 gerçek doğrulama → DURUM+bellek → push. Sonra: lineage (Pangolin/Nextclade), M3.
