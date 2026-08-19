# VirusForge

A modular, end-to-end pipeline for whole-genome analysis of RNA and DNA viruses and bacteriophages.

[![Pipeline DAG](https://img.shields.io/badge/pipeline-DAG-0d6b8f)](https://aliarslan47.github.io/VirusForge/pipeline_architecture.html)
[![molecule](https://img.shields.io/badge/molecule-DNA%20%C2%B7%20RNA-2f8f5b)](https://aliarslan47.github.io/VirusForge/pipeline_architecture.html)
[![reads](https://img.shields.io/badge/reads-short%20%C2%B7%20long%20%C2%B7%20hybrid-c07211)](https://aliarslan47.github.io/VirusForge/pipeline_architecture.html)

[Türkçe](README.md) · English

---

VirusForge auto-detects short-read, long-read, hybrid and pre-assembled inputs and processes them from
quality control to a final report with a single command. It branches by molecule type: for bacteriophages
and DNA viruses it runs Pharokka, PhaBOX, AMR and comparative/phylogenetic modules; for RNA viruses it runs
reference-based consensus, VADR annotation, variant/quasispecies calling, and Nextclade lineage/clade
assignment. The RNA path has been validated on SARS-CoV-2 data.

VirusForge follows the same architectural pattern as BacForge (bacteria) and Vaxforge, but is a separate,
isolated installation.

## Pipeline

`V00`–`V01` are shared by both paths. After the molecule decision (the `--molecule` option or geNomad's
Riboviria detection), the DNA/phage and RNA branches split and rejoin at the `V12` report. Read type
(short/long/hybrid/assembly) is a separate, orthogonal axis. Interactive bilingual diagram:
[**rendered diagram**](https://aliarslan47.github.io/VirusForge/pipeline_architecture.html) · source: `docs/pipeline_architecture.html`.

```mermaid
flowchart TB
    IN([FASTQ / FASTA]) --> V00[V00 · Input + Detect]
    V00 --> V01[V01 · Read QC<br/>fastp·NanoPlot·filtlong]
    V01 --> MOL{molecule?}

    MOL -->|DNA / phage| D02[V02 · Assembly<br/>SPAdes·Flye·Unicycler]
    D02 --> D03[V03 · Polishing + QC<br/>Medaka·QUAST·CheckV]
    D03 --> D04[V04 · Viral ID<br/>geNomad]
    D04 --> D05[V05 · Taxonomy<br/>Mash+INPHARED]
    D05 --> D06[V06 · Annotation<br/>Pharokka + map]
    D06 --> D07[V07 · Phage Charact.<br/>PhaBOX]
    D07 --> D08[V08 · AMR<br/>AMRFinderPlus]
    D08 --> D09[V09 · Comparative<br/>BLAST·IQ-TREE2·taxmyPHAGE]
    D09 --> V12

    MOL -->|RNA| R02[V02 · Consensus<br/>iVar·rnaviralSPAdes]
    R02 --> R03[V03 · Quality + Coverage<br/>QUAST·samtools depth]
    R03 --> R04[V04 · Viral ID<br/>geNomad → Riboviria]
    R04 --> R06[V06 · Annotation<br/>VADR + gene map]
    R06 --> R10[V10 · Variants<br/>iVar+LoFreq]
    R10 --> R11[V11 · Lineage/Clade<br/>Nextclade]
    R11 --> V12

    V12[V12 · Report + Export<br/>TR+EN HTML + provenance] --> OUT([HTML + JSON + Provenance])

    classDef dna fill:#e7f0f5,stroke:#0d6b8f,color:#14181d;
    classDef rna fill:#f7ecdb,stroke:#c07211,color:#14181d;
    classDef sh  fill:#e6f0ed,stroke:#3f8a7d,color:#14181d;
    class D02,D03,D05,D06,D07,D08,D09 dna;
    class R02,R03,R06,R10,R11 rna;
    class V00,V01,D04,R04,V12 sh;
```

## Modules

Each module branches on molecule type; a module that does not fit that path returns `NOT_APPLICABLE`.

| Code | Module | DNA / phage path | RNA virus path |
|:---:|---|---|---|
| V00 | Input & Detect | shared: read type + molecule (geNomad Riboviria / `--molecule`) | shared |
| V01 | Read QC | shared: fastp · FastQC · NanoPlot · filtlong · MultiQC | shared |
| V02 | Assembly / Consensus | SPAdes · Flye · Unicycler (de novo) | iVar consensus (ref) · rnaviralSPAdes |
| V03 | Polishing & Quality | Medaka · QUAST · CheckV | QUAST · coverage (samtools depth) |
| V04 | Viral Identification | shared: geNomad (viral confirmation + taxonomy) | shared |
| V05 | Taxonomy & References | Mash + INPHARED · NJ tree | N/A (phage-specific) |
| V06 | Genome Annotation | Pharokka + circular genome map | VADR + gene map |
| V07 | Phage Characterization | PhaBOX (PhaMer/PhaGCN/PhaTYP) | N/A |
| V08 | AMR & Virulence | AMRFinderPlus | N/A |
| V09 | Comparative & Phylogeny | BLAST · MAFFT · IQ-TREE2 · taxmyPHAGE · VIRIDIC · synteny | N/A |
| V10 | Variants & Quasispecies | N/A (RNA-specific) | iVar variants + LoFreq (type/effect/gene) |
| V11 | Lineage / Clade | N/A (RNA-specific) | Nextclade (clade + PANGO lineage + QC) |
| V12 | Report & Export | shared: bilingual (TR+EN) HTML report + provenance | shared |

## Installation

```bash
git clone https://github.com/aliarslan47/VirusForge.git
cd VirusForge

conda env create -f environment.yml
conda activate virusforge
pip install -e .

# Databases (CheckV, geNomad, Pharokka, INPHARED, PhaBOX)
bash setup/get_databases.sh
```

## Usage

```bash
# Installed tool versions
python -m virusforge.cli info

# Sample: samples/<id>/  (short: *_R1/_R2, long: single ONT fastq, assembly: *.fasta)
python -m virusforge.cli run --sample samples/T7_short --out runs --threads 8

# Output: runs/<timestamp>_<mode>/report.html
```

## Example: *Escherichia phage* T7 (short-read)

Real ENA data (`ERR3804828`, Illumina MiSeq). All modules on the DNA/phage path PASS; V10/V11 (RNA) are
N/A for this sample.

| Analysis | Result |
|---|---|
| Genome quality (CheckV) | 100% complete · 0% contamination · Complete |
| Assembly (QUAST) | 45,451 bp · largest contig 40,659 bp · N50 40,659 |
| Viral ID (geNomad) | Caudoviricetes; Autographiviridae (score 0.98) |
| Closest reference (Mash) | `V01146` (T7 reference) · distance 0.0036 |
| Annotation (Pharokka) | 76 CDS |
| Lifestyle (PhaBOX) | virulent · subfamily Studiervirinae |

## Tool registry

Each tool's official repository and publication were verified; versions are detected at runtime and DOIs
are the publication source. Full list: [`docs/2026-08-12-virusforge-design.md`](docs/2026-08-12-virusforge-design.md).

| Tool | Role | DOI |
|---|---|---|
| [fastp](https://github.com/OpenGene/fastp) | Read preprocessing | 10.1093/bioinformatics/bty560 |
| [SPAdes](https://github.com/ablab/spades) | Assembly | 10.1089/cmb.2012.0021 |
| [CheckV](https://bitbucket.org/berkeleylab/checkv) | Viral completeness/contamination | 10.1038/s41587-020-00774-7 |
| [geNomad](https://github.com/apcamargo/genomad) | Viral ID & taxonomy | 10.1038/s41587-023-01953-y |
| [Mash](https://github.com/marbl/Mash) + [INPHARED](https://github.com/RyanCook94/inphared) | Closest reference | 10.1186/s13059-016-0997-x |
| [Pharokka](https://github.com/gbouras13/pharokka) | Phage annotation | 10.1093/bioinformatics/btac776 |
| [PhaBOX](https://github.com/KennthShang/PhaBOX) | Phage characterization | 10.1093/bioadv/vbad101 |
| [VADR](https://github.com/ncbi/vadr) | RNA virus annotation | 10.1186/s12859-020-3537-3 |
| [Nextclade](https://github.com/nextstrain/nextclade) | Clade + lineage assignment | 10.21105/joss.03773 |

## Roadmap

- [x] M1 — DNA/phage core; short, long, hybrid and assembly inputs validated on T7 data
- [x] M2-A — phage enrichment: V08 AMR & virulence (AMRFinderPlus)
- [x] M3 — V09 comparative & phylogeny; multi-sample `compare` and clinker
- [x] M2-B — RNA virus path (iVar consensus, VADR, V10 variants, V11 Nextclade); validated on SARS-CoV-2
- [ ] Optional: RNA de novo validation · metavirome · additional detection tools (virsorter2/vibrant/kraken2)

## Repository layout

```
virusforge/   Python package (modules · tools · pipeline · report · registry)
config/       default and user YAML
databases/    downloaded databases   (git-ignored)
runs/         timestamped runs       (git-ignored)
samples/      input samples          (git-ignored)
docs/         design docs and plans
setup/        database download scripts
```

## Principles

- Isolation: separate package, separate environment, no cross-imports.
- Honesty: `WARNING` when there is no value, `NOT_APPLICABLE` when it does not apply; no hard-coded or fabricated results.
- Traceability: input SHA → tool + version → database + version → command → output SHA chain (`provenance.json`).

## License

[MIT](LICENSE). Forge family: BacForge (bacteria) · Vaxforge · VirusForge (virus/phage).
