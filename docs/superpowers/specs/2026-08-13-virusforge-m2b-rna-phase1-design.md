# VirusForge — M2-B RNA-Virüs Yolu · FAZ 1

## Context
VirusForge şu an DNA/faj genomiğini uçtan uca yapıyor (M1 platform + M2-A + M3). Paketin kimliği
"RNA + DNA tüm virüsler" ama **RNA yolu henüz yok** (tasarımda kararlı, kodda iskelet yok, araçlar
registry'de değil). Bu plan RNA yolunun **Faz 1**'ini ekler: RNA/DNA yönlendirme + RNA assembly/konsensus
(referans-tabanlı iVar **veya** de novo rnaviralSPAdes) + VADR anotasyon + DNA/faj-özel modüllerin RNA'da
dürüstçe N/A dönmesi. Gerçek doğrulama: ENA'dan SARS-CoV-2 amplikon (Illumina ARTIC). Faz 2 (ayrı) =
iVar/LoFreq varyant/quasispecies, Faz 1'in ürettiği BAM üzerinden.

Kullanıcı kararları: veri=SARS-CoV-2 amplikon; kapsam=fazlı (Faz 1 assembly/konsensus+VADR, Faz 2 varyant);
assembly=ikisi de (referans varsa iVar konsensus, yoksa rnaviralSPAdes).

## Temel mimari karar
**Yeni modül numarası YOK, renumber YOK — tüm RNA mantığı mevcut modüllerin İÇİNDE dallanır.** Bu, kod
tabanının değişmezine uyar (`pipeline.py:22`: "mode→modül eşlemesi yok, her modül kendi içinde dallanır")
ve `DEFAULT_MODULES` / `PIPELINE_STEPS` / render `section()` çağrıları / i18n / `test_e2e_dryrun._CORE` /
"V10=son" garantisini kırmaz. VADR, V06'nın (Genome Annotation) RNA dalı olur; hizalama+iVar konsensus V02'nin
(Assembly) RNA dalı olur.

**Kritik sıralama kısıtı:** V02 (assembly) V04'ten (geNomad taksonomi) ÖNCE koşar → geNomad-tabanlı
auto-molekül assembly'yi süremez. **Faz 1'de RNA yolu açık `--molecule rna` ile tetiklenir** (amplikon zaten
referans girdisi gerektirdiği için dürüst ve yeterli). Auto-türetme (Riboviria) yalnız aşağı-akış N/A'ları için.

## Kapsam
**Faz 1 DAHİL:** molekül ekseni (is_rna + config/CLI), V02 RNA assembly (rnaviralSPAdes de novo + referans-tabanlı
minimap2/samtools/ivar konsensus, BAM artifact), V03 RNA QC (BAM kapsama), V06 VADR anotasyon, V05/V07/V08/V09
RNA'da N/A, rapor RNA bölümleri (tr+en), registry/config/CLI, tam TDD, SARS-CoV-2 gerçek doğrulama.
**Faz 1 HARİÇ (Faz 2):** iVar variants + LoFreq quasispecies varyant çağırma; lineage (Pangolin/Nextclade).

## Uygulama (dosya bazlı)

### 1. Molekül ekseni — `virusforge/module.py`
`is_phage` (module.py:23) yanına `is_rna(ctx)`: (a) `config.get(cfg,"general.molecule","auto")` dna/rna ise
otorite (V02 dahil tüm modüllere açık); (b) auto ise `ctx.results["V04"].taxonomy`'de `"riboviria"` → RNA.

### 2. `virusforge/cli.py` + `config/default.yaml`
- CLI `run`'a `--molecule {auto,dna,rna}` → `cfg["general"]["molecule"]` (mevcut `--mode` plumbing'i, cli.py:15).
- `default.yaml`: `general.molecule: auto`; `tools.rna` bloğu (`reference`, `primer_bed`, `conda_env: vf_rna`,
  `conda_bin`, `ivar_min_depth: 10`, `ivar_min_freq: 0.5`); `tools.vadr` bloğu (`db: databases/vadr`,
  `model: sarscov2`, `conda_env: vf_vadr`, `conda_bin`).

### 3. `virusforge/tools.py` (saf `*_cmd`, gerekli olanlar `_conda_wrap`'li)
`rnaviralspades_cmd` (`spades.py --rnaviral`), `minimap2_cmd` (`-ax sr`), `samtools_sort_cmd`,
`samtools_index_cmd`, `samtools_coverage_cmd` (stdout), `samtools_mpileup_cmd`, `ivar_trim_cmd` (vf_rna),
`ivar_consensus_cmd` (vf_rna, stdin'den mpileup), `vadr_cmd` (`v-annotate.pl --mdir --mkey`, vf_vadr).

### 4. `virusforge/util.py`
`run_pipe(cmd1, cmd2, out_path, log_path)` — iki-süreç Popen pipe (`samtools mpileup | ivar consensus`;
mevcut run_cmd/run_redirect shell-pipe desteklemez). RuntimeError deseni run_cmd ile aynı.

### 5. `virusforge/modules/v02_assembly.py` — RNA dalı
- **De novo:** `select_assembler`'a RNA dalı → `tools.rnaviralspades_cmd(...)`, `(cmd, out/"contigs.fasta")`.
- **Referans-tabanlı** (`tools.rna.reference` varsa): `V02Assembly.run` içinde `_run_reference_consensus()`
  helper (çok-adım, select_assembler dışı): minimap2 → (primer_bed varsa) ivar trim → samtools sort/index →
  `run_pipe(mpileup, ivar consensus)` → consensus.fa. Yayınla `ctx.artifacts["V02"]={"draft":consensus,
  "bam":sorted.bam,"reference":ref}`; BAM `04_standardized/`'a kopyalanır (Faz 2). `restore_artifacts` BAM'i geri yükler.

### 6. `virusforge/modules/v06_annotate.py` — VADR RNA dalı
`run()` başında `is_rna(ctx)` → VADR (`tools.vadr_cmd`), değilse mevcut Pharokka. Modül-seviye
`parse_vadr(out_dir)` → `{pass, n_pass, n_fail, alerts, features}` (pass/fail tbl + alt list). metrics +
`annotation_summary.json`.

### 7. `virusforge/modules/v03_polish_qc.py` — RNA QC dalı
`is_rna(ctx)`: Medaka+CheckV atla; V02 BAM'inden `samtools_coverage` → `parse_samtools_coverage`
(`breadth_pct, mean_depth`); QUAST korunur. Status breadth eşiğiyle (>%90 @ depth≥10 → PASS).

### 8. N/A guard'ları
`v05_taxonomy`, `v09_comparative` `run()` başına açık `is_rna(ctx)` → `NOT_APPLICABLE` (INPHARED faj DB /
taxmyPHAGE faj RNA'da anlamsız). V07/V08 zaten is_phage=False ile N/A (netlik için is_rna guard eklenebilir).

### 9. Rapor — `virusforge/report/render.py` + `report/i18n.py` + `report/references.py`
Kod-key'li section gövdeleri molekül-duyarlı: V02 (referans-tabanlı konsensus vs de novo + referans accession),
V03 (RNA'da kapsama tablosu + `_svg_hbar` bar), V06 (VADR pass/fail + alert + feature tablosu). V05/V07/V08/V09
NOT_APPLICABLE döndüğünden mevcut gri-pill + boş-tablo otomatik N/A. Yeni TR etiketleri i18n `EN` sözlüğüne
(çift-dilli korunur). `references.py`: PIPELINE_STEPS V06 alt-başlığı "Pharokka / VADR"; TOOL_REFERENCES'a
iVar/VADR/minimap2/samtools.

### 10. `virusforge/data/registry.yaml` + `cli.py` info
`ivar` (github.com/andersen-lab/ivar, doi 10.1186/s13059-018-1618-7), `vadr` (github.com/ncbi/vadr,
doi 10.1186/s12859-020-3537-3). minimap2/samtools zaten kayıtlı. `cmd_info` tuple'ına (cli.py:37) yeni adlar.

## Test (TDD sırası)
Saf fonksiyonlar önce → dispatch → modül-koşum → e2e. Her adım kırmızı-gör-yeşil:
1. `test_module.py`: `is_rna` (override rna/dna, auto Riboviria, default dna).
2. `test_util.py`: `run_pipe` (pipe + hata yükseltme).
3. `test_tools.py`: rnaviralspades/minimap2/samtools*/ivar*/vadr komut kurucuları (conda_wrap env'leri).
4. `test_parsers.py`: `parse_vadr`, `parse_samtools_coverage` (fixture).
5. `test_v02.py`: RNA-ref-yok → rnaviralspades dispatch; RNA-ref-var → run_cmd/run_pipe monkeypatch, BAM+consensus+reference artifact.
6. V06 RNA dalı (VADR çağrısı) + DNA dalı hâlâ Pharokka.
7. N/A testleri: V05/V07/V08/V09 is_rna guard → NOT_APPLICABLE (test_comparative.py:162 deseni).
8. `test_e2e_dryrun.py`: yeni `test_rna_pipeline` (molecule=rna+reference, tüm araç no-op mock, `_CORE`
   değişmez; assert BAM artifact + VADR yolu + N/A statüleri + report.html RNA bölümleri).

## Doğrulama (gerçek, ENA SARS-CoV-2 ARTIC)
1. ENA'dan Illumina ARTIC amplikon run'ı (R1/R2 + eşleşen ARTIC primer BED → `tools.rna.primer_bed`).
2. Referans NC_045512.2 (Wuhan-Hu-1, 29903 bp) efetch → `tools.rna.reference`. İzole env'ler: `vf_rna`
   (minimap2/samtools/ivar), `vf_vadr` (VADR + sarscov2 modeli).
3. `virusforge run --sample <dir> --molecule rna --config rna.yaml`.
4. Beklenen: V02 iVar konsensus ~29.9 kb, breadth >%95 @ depth≥10; V03 kapsama; V06 VADR PASS (sarscov2);
   V04 taxonomy Riboviria; V05/V07/V08/V09 = NOT_APPLICABLE (gri); rapor çift-dilli, konsensus+kapsama+VADR
   pass, DNA/faj bölümleri tutarlı N/A. `pytest -q` tümü yeşil.

## Riskler
- **VADR env/DB:** vf_vadr (Infernal/BLAST) ağır; Faz 1 için yalnız sarscov2 modeli indir.
- **iVar pipe:** `run_pipe` helper şart (ivar consensus mpileup'ı yalnız stdin'den okur).
- **Amplikon primer bias:** doğru konsensus için `ivar trim` (primer BED) gerekir; BED yoksa WARNING ile devam.
- **Faj-DB yanılması:** is_rna guard V05/V09'u WARNING değil açık NOT_APPLICABLE yapmalı (dürüstlük).
- **Molekül sıralama:** geNomad V02 sonrası → Faz 1 açık `--molecule rna` gerektirir (dokümante et).
- **Araç erişilebilirliği:** Herhangi bir araç bioconda/pypi'da yoksa (M2-A'daki RaFAH/PhageTerm/phold dersi)
  modül yazılmaz; kurulum başarısızsa kapsam sadeleştirilir + kullanıcıya bildirilir.

## Sonraki adım
Onay sonrası: bu tasarımı `docs/superpowers/specs/2026-08-13-virusforge-m2b-rna-phase1-design.md`'e yaz +
commit → writing-plans ile task-bazlı uygulama planı → TDD ile uygula → SARS-CoV-2 gerçek doğrulama → DURUM+bellek.
