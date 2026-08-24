# VirusForge

A modular, end-to-end pipeline for whole-genome analysis of RNA and DNA viruses and bacteriophages — from raw reads to a single, self-contained bilingual HTML report.

[![Pipeline DAG](https://img.shields.io/badge/pipeline-DAG-0d6b8f)](https://aliarslan47.github.io/VirusForge/pipeline_architecture.html)
[![molecule](https://img.shields.io/badge/molecule-DNA%20%C2%B7%20RNA-2f8f5b)](https://aliarslan47.github.io/VirusForge/pipeline_architecture.html)
[![reads](https://img.shields.io/badge/reads-short%20%C2%B7%20long%20%C2%B7%20hybrid-c07211)](https://aliarslan47.github.io/VirusForge/pipeline_architecture.html)

[Türkçe](README.tr.md) · **English**

## What is it?

VirusForge is the virus/phage member of the Forge family — same architecture as BacForge (bacteria) and RNAForge (bulk RNA-seq), but a separate, isolated installation. It takes raw reads to biology in a single command and ends with a bilingual (TR+EN), self-contained HTML report.

## What it does

VirusForge auto-detects short-read, long-read, hybrid and pre-assembled inputs and processes them from quality control to a final report. It branches by molecule type (the `--molecule` option or geNomad's Riboviria detection); read type is a separate, orthogonal axis:

- **DNA virus / phage**: de novo assembly (SPAdes/Flye/Unicycler) → polishing + CheckV → geNomad ID → Mash/INPHARED taxonomy → Pharokka annotation → PhaBOX characterization → AMRFinderPlus → comparative/phylogeny (BLAST · IQ-TREE2 · taxmyPHAGE).
- **RNA virus**: reference-based iVar consensus → coverage QC → VADR annotation → iVar/LoFreq variants & quasispecies → Nextclade lineage/clade. Validated on SARS-CoV-2 data.

Honest by design: `WARNING` when there is no value, `NOT_APPLICABLE` when a module does not fit the path; no hard-coded or fabricated results; full input→tool→database→command→output provenance chain.

Interactive bilingual node-graph: **[rendered diagram](https://aliarslan47.github.io/VirusForge/pipeline_architecture.html)**.

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
# installed tool versions
python -m virusforge.cli info

# sample: samples/<id>/ (short: *_R1/_R2 · long: single ONT fastq · assembly: *.fasta)
python -m virusforge.cli run --sample samples/T7_short --out runs --threads 8

# output: runs/<timestamp>_<mode>/report.html
```

## Modules

Each module branches on molecule type; a module that does not fit the path returns `NOT_APPLICABLE`.

| Code | Module | DNA / phage path | RNA virus path |
|:---:|---|---|---|
| V00 | Input & Detect | shared: read type + molecule (geNomad / `--molecule`) | shared |
| V01 | Read QC | shared: fastp · FastQC · NanoPlot · filtlong · MultiQC | shared |
| V02 | Assembly / Consensus | SPAdes · Flye · Unicycler | iVar consensus · rnaviralSPAdes |
| V03 | Polishing & Quality | Medaka · QUAST · CheckV | QUAST · coverage |
| V04 | Viral Identification | shared: geNomad (confirmation + taxonomy) | shared |
| V05 | Taxonomy & References | Mash + INPHARED · NJ tree | N/A |
| V06 | Genome Annotation | Pharokka + circular map | VADR + gene map |
| V07 | Phage Characterization | PhaBOX (PhaMer/PhaGCN/PhaTYP) | N/A |
| V08 | AMR & Virulence | AMRFinderPlus | N/A |
| V09 | Comparative & Phylogeny | BLAST · MAFFT · IQ-TREE2 · taxmyPHAGE | N/A |
| V10 | Variants & Quasispecies | N/A | iVar variants + LoFreq |
| V11 | Lineage / Clade | N/A | Nextclade |
| V12 | Report & Export | shared: bilingual (TR+EN) HTML + provenance | shared |

Full tool registry (with DOIs), example runs and the repository layout live in `docs/`.

---

Forge family: **VirusForge** (virus/phage) · [BacForge](https://github.com/aliarslan47/BacForge) (bacteria) · [RNAForge](https://github.com/aliarslan47/RNAForge) (bulk RNA-seq) · [PipelineForge](https://github.com/aliarslan47/PipelineForge) (DAG generator). Licensed under [MIT](LICENSE).
