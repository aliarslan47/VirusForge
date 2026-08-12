# VirusForge M1 (DNA/faj çekirdek) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** VirusForge M1 — izole bakteriyofaj için short/long/hybrid uçtan-uca çekirdek hattı (V00→V01→V03→V04→V05→V06→V07→V08→V19), BacForge deseninde ama tamamen izole.

**Architecture:** Python paketi `virusforge/`. Her modül ortak `Module` taban sınıfından türer, standart çıktı klasörleri + `Vxx_summary.json` üretir, dürüst durum kodu döndürür. CLI modülleri okuma-tipine göre yönlendirir. Harici araçlar conda env'de; wrapper'lar komut kurar + native çıktıyı korur + normalized JSON/TSV üretir.

**Tech Stack:** Python 3.11, conda (env `virusforge`), pytest, PyYAML. Araçlar: fastp/FastQC/MultiQC, NanoPlot/Filtlong, SPAdes/Flye/Unicycler, Racon/Medaka/QUAST/CheckV, geNomad, Mash+INPHARED, Pharokka, PhaBOX.

## Global Constraints
- İzolasyon: `import bacforge` YASAK; BacForge'a hiçbir yazma/okuma yok. Ayrı conda env `virusforge`.
- Python paket adı `virusforge`; CLI `python3 -m virusforge.cli`.
- Dürüstlük: sabit/sahte sonuç yok; değer yoksa WARNING/NOT_APPLICABLE; tool uyuşmazlığı gizlenmez; uydurma DOI yok.
- Native çıktı `03_native_outputs/` altında değiştirilmeden saklanır.
- Her modül çıktısı: `01_input 02_work 03_native_outputs 04_standardized 05_statistics 06_visualization 07_logs 08_metadata` + `Vxx_summary.json`.
- Durum kodları: `PASS WARNING FAIL NOT_APPLICABLE SKIPPED`.
- Test verisi İNDİRİLMEZ (kullanıcı sağlayacak); testler sentetik fixture kullanır.
- Anlamlı her task sonunda commit.

---

### Task 1: Paket iskeleti + config yükleyici

**Files:**
- Create: `pyproject.toml`, `environment.yml`, `virusforge/__init__.py`, `virusforge/config.py`, `config/default.yaml`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `config.load_config(path: str | None) -> dict` — default.yaml'ı yükler, kullanıcı YAML'ı ile derin-merge eder (override). `config.get(cfg, "tools.spades.threads", default)` nokta-yollu erişim.

- [ ] **Step 1:** `tests/test_config.py` — `test_load_defaults()` (default threads okunur), `test_user_override()` (kullanıcı YAML default'u ezer), `test_dotted_get_missing_returns_default()`.
- [ ] **Step 2:** Testi çalıştır, FAIL (modül yok).
- [ ] **Step 3:** `config/default.yaml` (threads, tools.* placeholder yok — gerçek varsayılanlar: `general.threads: 8`, `general.memory_gb: 32`, her araç için alt anahtar). `config.py`: `load_config`, derin-merge, `get` nokta-yollu.
- [ ] **Step 4:** `pytest tests/test_config.py -v` → PASS.
- [ ] **Step 5:** `environment.yml` (kanal: conda-forge, bioconda; paketler: python=3.11, pytest, pyyaml, fastp, fastqc, multiqc, nanoplot, filtlong, spades, flye, unicycler, racon, medaka, quast, checkv, genomad, mash, pharokka; phabox pip/ayrı not). `pyproject.toml` (name=virusforge, scripts). Commit.

### Task 2: util + provenance

**Files:**
- Create: `virusforge/util.py`, `virusforge/provenance.py`
- Test: `tests/test_util.py`, `tests/test_provenance.py`

**Interfaces:**
- Produces:
  - `util.sha256(path) -> str`
  - `util.run_cmd(cmd: list[str], cwd, log_path) -> CompletedProcess` (stdout/stderr log'a; hata → RuntimeError yüksek sesle)
  - `util.find_long_reads(sample_dir) -> Path|None` (ONT işareti; R1/R2 dışla — BacForge dersi)
  - `util.find_short_reads(sample_dir) -> tuple[Path,Path]|None` (R1/R2)
  - `provenance.record(module, tool, version, db, db_version, cmd, params, input_sha, output_sha) -> dict` ve `provenance.write(run_dir, records)`

- [ ] **Step 1:** `test_util.py`: `test_sha256_known_value()` (sentetik dosya), `test_find_long_reads_excludes_R1()` (R1.fastq long seçilmemeli), `test_run_cmd_raises_on_failure()`. `test_provenance.py`: `test_record_has_all_fields()`.
- [ ] **Step 2:** FAIL.
- [ ] **Step 3:** `util.py` + `provenance.py` implement.
- [ ] **Step 4:** PASS.
- [ ] **Step 5:** Commit.

### Task 3: Module taban sınıfı + çıktı sözleşmesi

**Files:**
- Create: `virusforge/module.py`
- Test: `tests/test_module.py`

**Interfaces:**
- Produces: `class Module` — `name`, `code` (Vxx), `run(ctx) -> ModuleResult`. Yardımcılar: `make_dirs(run_dir)` (8 standart klasör), `write_summary(status, metrics, provenance)`; `ModuleResult(status: Status, summary_path, metrics: dict)`. `Status` enum: PASS/WARNING/FAIL/NOT_APPLICABLE/SKIPPED.

- [ ] **Step 1:** `test_module.py`: `test_make_dirs_creates_8_folders()`, `test_write_summary_json_has_status_and_provenance()`, `test_status_enum_values()`.
- [ ] **Step 2:** FAIL.
- [ ] **Step 3:** `module.py` implement (soyut `run`, dirs, summary yazımı, Status enum).
- [ ] **Step 4:** PASS.
- [ ] **Step 5:** Commit.

### Task 4: registry (tool/DB metadata)

**Files:**
- Create: `virusforge/registry.py`, `virusforge/data/registry.yaml`
- Test: `tests/test_registry.py`

**Interfaces:**
- Produces: `registry.tool(name) -> dict` (version_cmd, repo, doi?, db?). Doğrulanmış repo adresleri (tasarım dokümanı Bölüm 6). `registry.detect_version(name) -> str|None` (araç kuruluysa sürüm; değilse None, uydurma YOK).

- [ ] **Step 1:** `test_registry.py`: `test_known_tools_present()` (checkv repo = bitbucket.org/berkeleylab/checkv), `test_unknown_tool_raises()`, `test_detect_version_missing_returns_none()`.
- [ ] **Step 2:** FAIL.
- [ ] **Step 3:** `registry.yaml` (Bölüm 6 registry — doğrulanmış repo/DOI) + `registry.py`.
- [ ] **Step 4:** PASS.
- [ ] **Step 5:** Commit.

### Task 5: V00 — Input & Auto-Detection

**Files:**
- Create: `virusforge/modules/v00_input.py`, `virusforge/detect.py`
- Test: `tests/test_detect.py`

**Interfaces:**
- Consumes: util.find_short/long_reads.
- Produces: `detect.detect_mode(sample_dir) -> {"mode": SHORT_READ|LONG_READ|HYBRID|ASSEMBLY_INPUT, "evidence": {...}}`. Karar: read uzunluk dağılımı + paired ilişki + header (dosya adı tek başına DEĞİL). Kullanıcı override (`config general.mode`). `V00.run` → `data_type.json`, `read_statistics.tsv`, `checksums.sha256`.

- [ ] **Step 1:** `test_detect.py`: sentetik FASTQ fixture'ları (kısa ~150bp paired → SHORT; uzun ~5kb tek → LONG; ikisi birden → HYBRID; .fasta → ASSEMBLY). `test_detect_short/long/hybrid/assembly()`, `test_config_override_wins()`.
- [ ] **Step 2:** FAIL.
- [ ] **Step 3:** `detect.py` (uzunluk histogramı eşikleri; header ipuçları) + `v00_input.py` (summary + checksums).
- [ ] **Step 4:** PASS.
- [ ] **Step 5:** Commit.

### Task 6: CLI + orchestrator

**Files:**
- Create: `virusforge/cli.py`, `virusforge/pipeline.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: Module alt sınıfları, detect_mode.
- Produces: `pipeline.run(sample_dir, out_root, config) -> run_dir` — `runs/<ts>_<mode>/` oluşturur, V00 sonrası moda göre modül sırasını seçer, her modülü çalıştırır, resume (bitmiş modül atlanır — Kapatma Dayanıklılığı), 10 sn heartbeat log. `cli.py`: `run --sample --out --config`, `info`.
- **Not:** ts (timestamp) `Date.now` yerine `os.environ`/config'den değil — Python'da `datetime` serbest; ama testte sabit ts enjekte edilebilir (`clock` parametresi).

- [ ] **Step 1:** `test_pipeline.py`: sahte iki modül (biri PASS biri WARNING) ile `test_run_creates_run_dir_and_runs_in_order()`, `test_resume_skips_completed()`, `test_mode_selects_module_sequence()`.
- [ ] **Step 2:** FAIL.
- [ ] **Step 3:** `pipeline.py` + `cli.py` implement (modül registry: V00,V01,V03,V04,V05,V06,V07,V08,V19).
- [ ] **Step 4:** PASS.
- [ ] **Step 5:** Commit.

### Task 7: V01 — Read QC (tool-wrapper şablonu)

**Files:**
- Create: `virusforge/modules/v01_qc.py`, `virusforge/tools.py`
- Test: `tests/test_v01.py`

**Interfaces:**
- Consumes: Module, run_cmd, mode.
- Produces: `tools.fastp_cmd(r1,r2,out) -> list[str]`, `tools.nanoplot_cmd(long,out)`, `tools.multiqc_cmd(dir,out)`; `v01.parse_fastp_json(path) -> {raw_reads, clean_reads, q30, gc, ...}`; `v01.parse_nanoplot(path) -> {mean_len, read_n50, ...}`. `V01.run` moda göre kol seçer, native çıktı korunur, `04_standardized/qc_metrics.json`.

- [ ] **Step 1:** `test_v01.py`: `test_fastp_cmd_has_r1_r2_and_json()`, `test_parse_fastp_json()` (fixture fastp JSON), `test_parse_nanoplot()` (fixture), `test_run_long_uses_nanoplot_branch()` (run_cmd mock).
- [ ] **Step 2:** FAIL.
- [ ] **Step 3:** `tools.py` (komut kuruculardan başla) + `v01_qc.py` (parse + branch + summary).
- [ ] **Step 4:** PASS.
- [ ] **Step 5:** Commit.

### Task 8: V03 — Assembly (routing)

**Files:** Create `virusforge/modules/v03_assembly.py`; extend `tools.py`; Test `tests/test_v03.py`
**Interfaces:** Produces `tools.spades_cmd`, `tools.flye_cmd(chem)`, `tools.unicycler_cmd`; `V03.run` moda göre assembler seçer → canonical `04_standardized/draft_viral_genome.fasta`. ONT kimya (R9/R10) config/header'dan → Flye modu + Medaka modeli (V04'e taşınır).
- [ ] **Step 1:** `test_v03.py`: `test_short_selects_spades()`, `test_hybrid_selects_unicycler()`, `test_long_selects_flye_with_chem()`, `test_missing_long_raises()` (boş long guard — sessiz PASS yasak).
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS. **Step 5:** Commit.

### Task 9: V04 — Polishing + Genome Quality

**Files:** Create `virusforge/modules/v04_polish_qc.py`; extend `tools.py`; Test `tests/test_v04.py`
**Interfaces:** `tools.racon_cmd`, `tools.medaka_cmd(model)`, `tools.quast_cmd`, `tools.checkv_cmd`; `V04.parse_checkv(quality_summary.tsv) -> {completeness, contamination, checkv_quality}`, `parse_quast(report.tsv) -> {n50, length, contigs, gc}`. long ise Racon+Medaka cila; canonical `viral_genome.fasta`. Değer yoksa WARNING (sabit sayı YOK).
- [ ] **Step 1:** `test_v04.py`: `test_parse_checkv_fixture()`, `test_parse_quast_fixture()`, `test_long_runs_racon_medaka()`, `test_no_checkv_value_sets_warning()`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS. **Step 5:** Commit.

### Task 10: V05 — Viral Identification (geNomad)

**Files:** Create `virusforge/modules/v05_identify.py`; extend `tools.py`; Test `tests/test_v05.py`
**Interfaces:** `tools.genomad_cmd(fasta, db, out)`; `V05.parse_genomad(summary) -> {is_viral, virus_score, taxonomy, provirus}`. Tool uyuşmazlığı (opsiyonel VirSorter2/VIBRANT açıksa) gizlenmez → `04_standardized/viral_identification.json` içinde her aracın verdiği ayrı.
- [ ] **Step 1:** `test_v05.py`: `test_genomad_cmd()`, `test_parse_genomad_fixture()`, `test_disagreement_recorded_not_hidden()`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS. **Step 5:** Commit.

### Task 11: V06 — Taxonomy + Closest References (Mash + INPHARED)

**Files:** Create `virusforge/modules/v06_taxonomy.py`; extend `tools.py`, `setup/`; Test `tests/test_v06.py`
**Interfaces:** `tools.mash_dist_cmd(query, inphared_sketch, out)`; `V06.parse_mash(dist.tsv) -> closest_10 [{accession, taxonomy, mash_dist, ...}]` (accession'a göre DEDUP — BacForge dersi). `setup/get_inphared.sh` (DB indirici, kullanıcı çalıştırır).
- [ ] **Step 1:** `test_v06.py`: `test_mash_cmd()`, `test_parse_mash_dedup_by_accession()`, `test_empty_hits_sets_warning()`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS. **Step 5:** Commit.

### Task 12: V07 — Annotation (Pharokka)

**Files:** Create `virusforge/modules/v07_annotate.py`; extend `tools.py`; Test `tests/test_v07.py`
**Interfaces:** `tools.pharokka_cmd(fasta, db, out, threads)`; `V07.parse_pharokka(cds_functions.tsv, gbk) -> {cds, trna, functional_counts, ...}`. Identifier integrity: `locus_tag/gene/product/protein_id` ayrı tutulur (locus_tag gene yerine yazılmaz; bilinmeyen product NULL). PHANOTATE/Prodigal-gv/tRNAscan-SE Pharokka içinde — ayrı çağırma YOK.
- [ ] **Step 1:** `test_v07.py`: `test_pharokka_cmd()`, `test_parse_pharokka_fixture()`, `test_identifier_integrity_no_locustag_as_gene()`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS. **Step 5:** Commit.

### Task 13: V08 — Phage-Specific Characterization (PhaBOX)

**Files:** Create `virusforge/modules/v08_phage_char.py`; extend `tools.py`; Test `tests/test_v08.py`
**Interfaces:** `tools.phabox_cmd(fasta, db, out)`; `V08.parse_phabox(...) -> {phamer, phagcn_taxonomy, phatyp_lifestyle, structural_genes}`. Faj değilse (V05'ten) → NOT_APPLICABLE.
- [ ] **Step 1:** `test_v08.py`: `test_phabox_cmd()`, `test_parse_phabox_fixture()`, `test_non_phage_sets_not_applicable()`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS. **Step 5:** Commit.

### Task 14: V19 — Final Report + Export

**Files:** Create `virusforge/modules/v19_report.py`, `virusforge/report/render.py`; Test `tests/test_v19.py`
**Interfaces:** `V19.run` tüm `Vxx_summary.json`'ları toplar → `report.html` + `report.json` + `provenance.json`. Analiz çalıştı ama bulgu yoksa bölüm silinmez → `Detected: 0 / completed`. Rapor sırası tasarım dokümanındaki gibi. Frontend native formata bağımlı değil (yalnız normalized JSON).
- [ ] **Step 1:** `test_v19.py`: `test_collects_all_summaries()`, `test_zero_findings_section_kept()`, `test_report_json_has_provenance()`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS. **Step 5:** Commit.

### Task 15: Uçtan-uca dry-run + smoke iskele

**Files:** Create `tests/test_e2e_dryrun.py`, `samples/README.md`
**Interfaces:** run_cmd mock'lanmış halde tüm hattın moda göre doğru modül sırasını üretmesi + her modülün summary yazması. Gerçek araçlı smoke, kullanıcının vereceği örnekle yapılacak (ayrı adım).
- [ ] **Step 1:** `test_e2e_dryrun.py`: `test_short_pipeline_runs_all_modules_in_order()` (araçlar mock; her modül PASS/uygun durum). `samples/README.md`: örnek koyma talimatı.
- [ ] **Step 2:** FAIL. **Step 3:** iskeleti tamamla. **Step 4:** PASS. **Step 5:** Commit.

---

## Self-Review notu
- Spec kapsamı: V00–V08 + V19 tümü task'lı ✓. RNA/M2, V09–V18/M3 kapsam dışı (sonraki plan).
- Placeholder yok; her task testli + komut/parse hedefli.
- Tip tutarlılığı: `Status`, `ModuleResult`, `detect_mode`, `tools.*_cmd`, `parse_*` adları task'lar arası tutarlı.
- Gerçek araçlı E2E, DB indirme + kullanıcı örneği gerektirir → Task 15 sonrası ayrı doğrulama adımı.
