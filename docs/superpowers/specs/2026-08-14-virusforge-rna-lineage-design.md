# VirusForge — RNA Soy/Klad Tayini (V12 Lineage) Tasarımı

**Tarih:** 2026-08-14
**Milestone:** M2-B RNA yolu — Faz 3 (lineage)
**Durum:** Onaylandı (brainstorm), plan bekliyor

## Amaç

RNA virüslerinde konsensüs genomundan **soy hattı / klad** tayini. Klinik/epidemiyolojik
yorumun son halkası: V02 konsensüs → V06 VADR anotasyon → V11 varyant → **V12 soy tayini**.

DNA/faj yolunda anlamı yoktur → `NOT_APPLICABLE` (V11 deseniyle aynı). Yeni bir modüldür;
mevcut bir slota dallanmaz çünkü soy tayininin DNA karşılığı yoktur.

## Kararlar (kullanıcı onaylı)

1. **Araçlar: Pangolin + Nextclade (ikisi de).** Bağımsız, paralel; biri hata verirse diğeri
   devam eder (sessiz-hata yok, WARNING).
   - **Pangolin** — SARS-CoV-2 PANGO soy hattı (ör. `BA.2.86`), scorpio, conflict, QC.
   - **Nextclade** — klad + Nextclade_pango + QC + mutasyon; dataset ile çok-patojen kapasite.
2. **Kapsam:** SARS-CoV-2 öncelikli doğrulanır (mevcut ENA `ERR11728561` konsensüsü). Nextclade
   dataset config'ten seçilir → ileride grip/RSV/mpox genişleyebilir. İlk sürüm SARS-CoV-2.
3. **Env:** ayrı izole conda env'leri — `vf_pangolin` + `vf_nextclade` (vf_amr/vf_lofreq deseni).

## Girdi / Çıktı

- **Girdi:** V02'nin ürettiği konsensüs FASTA (`ivar consensus` çıktısı; zaten `ctx.artifacts["V02"]`
  içinde + `restore_artifacts` ile resume dayanıklı) + `module.is_rna(ctx)` True.
  Konsensüs yoksa (de novo yol, referanssız) → `NOT_APPLICABLE` (dürüst atlama).
- **Pangolin çıktısı:** `pangolin <consensus.fa> --outfile lineage_report.csv` → CSV →
  `parse_pangolin` → `{lineage, conflict, scorpio_call, qc_status, note, version, pango_version}`.
- **Nextclade çıktısı:** `nextclade run -D <dataset_dir> --output-tsv nextclade.tsv <consensus.fa>` →
  TSV → `parse_nextclade` → `{clade, nextclade_pango, qc_overall, total_substitutions,
  total_missing, total_aa_substitutions}`.
- `metrics.lineage = {pangolin: {...}, nextclade: {...}}` → report.json.

## Yerleşim

- **Modül:** `virusforge/modules/v12_lineage.py` → `class V12Lineage(Module)`; `code="V12"`,
  standart 8-klasör çıktı; parser fonksiyonları modül-düzeyinde (test edilebilir).
- **pipeline.py:** `DEFAULT_MODULES` → `… V08Amr, V09Comparative, V11VariantCall, V12Lineage, V10Report`.
  (V12, V11'den sonra, V10 rapor öncesi — V11'in V09↔V10 arasına yerleştirilmesiyle tutarlı.)
- **Rapor sırası:** `v10_report._ORDER` ve `references.PIPELINE_STEPS` → …V11 → V12 → V10.

## Config / Registry

```
tools.pangolin.conda_env = vf_pangolin
tools.pangolin.cmd = pangolin komut şablonu
tools.nextclade.conda_env = vf_nextclade
tools.nextclade.dataset = "sars-cov-2"        # dataset adı
tools.nextclade.dataset_dir = databases/nextclade/sars-cov-2   # indirilmiş dataset
tools.nextclade.run_cmd = nextclade run komut şablonu
```

- `registry` → pangolin (repo cov-lineages/pangolin, DOI) + nextclade (repo nextstrain/nextclade, DOI).
- `tools.py` → `pangolin_cmd(...)` ve `nextclade_run_cmd(...)` komut kurucular (`_conda_wrap`).

## Rapor (V10, çift-dilli)

Yeni **"V12 — Soy/Klad Tayini"** bölümü:
- Özet stat kartları: **Soy (Pangolin)** + **Klad (Nextclade)**.
- **Pangolin tablosu:** Soy hattı · Scorpio · Conflict · QC · Not · Sürüm.
- **Nextclade tablosu:** Klad · Nextclade PANGO · QC · Toplam subst. · Eksik (N) · AA subst.
- i18n: `report/i18n.py` EN sözlüğüne V12 anahtarları; `render_html`/`render_comparison`
  choke-point çevirisi. TR varsayılan; soy/klad adları (BA.2.86 vb.) bilimsel terim → çevrilmez.
- DNA/faj yolunda gri **N/A pill** (mevcut desen; V05/V07/V08/V09 gibi).

## Hata yönetimi (sessiz-hata yok)

- Konsensüs yok → `NOT_APPLICABLE` (net sebep).
- Pangolin başarısız ama Nextclade başarılı (veya tersi) → tamamlanan yazılır, eksik olan WARNING;
  modül `WARNING` döner, pipeline durmaz.
- Her ikisi de başarısız → `WARNING` (rapor gerisi üretilir).
- Nextclade dataset dizini yoksa → net WARNING (kurulum talimatı loga).

## Test (TDD)

`tests/test_v12_lineage.py` (+ mevcut dosyalara eklemeler):
1. `is_applicable`: rna+konsensüs → çalışır; dna → N/A; rna ama konsensüs yok → N/A.
2. `parse_pangolin`: örnek CSV → doğru alanlar; boş/eksik sütun toleransı.
3. `parse_nextclade`: örnek TSV → doğru alanlar; yeni/eski sütun adı toleransı.
4. `pangolin_cmd` / `nextclade_run_cmd`: doğru komut + conda_env wrap.
5. V12 dispatch: rna yolunda iki araç çağrılır (mock), metrics üretilir.
6. N/A guard: dna yolunda araçlar çağrılmaz.
7. render V12 bölümü tr + en (başlık + tablo + stat çevirisi; EN'e ham TR sızmaz).
8. e2e RNA: pipeline'da V12 sırada (V11→V12→V10).

Hedef: ~154 → ~164 pytest yeşil.

## Env kurulumu

- `vf_pangolin`: `pangolin` + `pangolin-data` (bioconda).
- `vf_nextclade`: `nextclade` (bioconda) + `nextclade dataset get --name sars-cov-2
  --output-dir databases/nextclade/sars-cov-2`.

## Gerçek doğrulama

Mevcut SARS-CoV-2 konsensüsü (ENA `ERR11728561`, Faz 1 çıktısı `--resume`) üzerinde:
- Pangolin bir PANGO soyu atar (veya QC nedeniyle unassigned → dürüstçe raporlanır).
- Nextclade bir klad + Nextclade_pango + QC atar; %1 N maskesi tolere edilir.
- V12 rapor bölümü TR+EN; DNA/faj koşusunda N/A pill korunur.

## Kapsam dışı (bu faz)

- IRMA (grip segment-assembly) — ayrı, ileride.
- Nextclade çok-patojen dataset otomatik seçimi (patojen tespitinden) — config-manuel yeterli.
- Soy-tabanlı epidemiyolojik yorum/trend — kapsam dışı.
