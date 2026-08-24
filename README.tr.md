# VirusForge

RNA ve DNA virüsleri ile bakteriyofajların tüm-genom analizi için modüler, uçtan uca bir pipeline — ham okumalardan tek, kendine yeten çift dilli bir HTML rapora.

[![Pipeline DAG](https://img.shields.io/badge/pipeline-DAG-0d6b8f)](https://aliarslan47.github.io/VirusForge/pipeline_architecture.html)
[![molecule](https://img.shields.io/badge/molecule-DNA%20%C2%B7%20RNA-2f8f5b)](https://aliarslan47.github.io/VirusForge/pipeline_architecture.html)
[![reads](https://img.shields.io/badge/reads-short%20%C2%B7%20long%20%C2%B7%20hybrid-c07211)](https://aliarslan47.github.io/VirusForge/pipeline_architecture.html)

**Türkçe** · [English](README.md)

## Nedir?

VirusForge, Forge ailesinin virüs/faj üyesidir — BacForge (bakteri) ve RNAForge (bulk RNA-seq) ile aynı mimari, ancak ayrı ve izole bir kurulum. Ham okumaları tek komutla biyolojiye taşır ve çift dilli (TR+EN), kendine yeten bir HTML raporla sonlanır.

## Ne yapar?

VirusForge kısa-okuma, uzun-okuma, hibrit ve önceden-assemble edilmiş girdileri otomatik algılar ve kalite kontrolünden nihai rapora kadar işler. Molekül tipine göre dallanır (`--molecule` seçeneği ya da geNomad'ın Riboviria algısı); okuma tipi ayrı, dik bir eksendir:

- **DNA virüsü / faj**: de novo assembly (SPAdes/Flye/Unicycler) → parlatma + CheckV → geNomad ID → Mash/INPHARED taksonomi → Pharokka anotasyon → PhaBOX karakterizasyon → AMRFinderPlus → karşılaştırmalı/filogeni (BLAST · IQ-TREE2 · taxmyPHAGE).
- **RNA virüsü**: referans-temelli iVar konsensüs → kapsam QC → VADR anotasyon → iVar/LoFreq varyant & quasispecies → Nextclade soy/klad. SARS-CoV-2 verisinde doğrulandı.

Tasarımı gereği dürüst: değer yoksa `WARNING`, modül yola uymuyorsa `NOT_APPLICABLE`; sabit-kodlu ya da uydurma sonuç yok; tam girdi→araç→veritabanı→komut→çıktı köken zinciri.

Etkileşimli çift dilli düğüm grafiği: **[render edilmiş diyagram](https://aliarslan47.github.io/VirusForge/pipeline_architecture.html)**.

## Kurulum

```bash
git clone https://github.com/aliarslan47/VirusForge.git
cd VirusForge

conda env create -f environment.yml
conda activate virusforge
pip install -e .

# Veritabanları (CheckV, geNomad, Pharokka, INPHARED, PhaBOX)
bash setup/get_databases.sh
```

## Kullanım

```bash
# kurulu araç sürümleri
python -m virusforge.cli info

# örnek: samples/<id>/ (kısa: *_R1/_R2 · uzun: tek ONT fastq · assembly: *.fasta)
python -m virusforge.cli run --sample samples/T7_short --out runs --threads 8

# çıktı: runs/<zaman>_<mod>/report.html
```

## Modüller

Her modül molekül tipine göre dallanır; yola uymayan modül `NOT_APPLICABLE` döner.

| Kod | Modül | DNA / faj yolu | RNA virüsü yolu |
|:---:|---|---|---|
| V00 | Girdi & Algılama | ortak: okuma tipi + molekül (geNomad / `--molecule`) | ortak |
| V01 | Okuma QC | ortak: fastp · FastQC · NanoPlot · filtlong · MultiQC | ortak |
| V02 | Assembly / Konsensüs | SPAdes · Flye · Unicycler | iVar konsensüs · rnaviralSPAdes |
| V03 | Parlatma & Kalite | Medaka · QUAST · CheckV | QUAST · kapsam |
| V04 | Viral Tanımlama | ortak: geNomad (doğrulama + taksonomi) | ortak |
| V05 | Taksonomi & Referans | Mash + INPHARED · NJ ağacı | Yok |
| V06 | Genom Anotasyonu | Pharokka + dairesel harita | VADR + gen haritası |
| V07 | Faj Karakterizasyonu | PhaBOX (PhaMer/PhaGCN/PhaTYP) | Yok |
| V08 | AMR & Virülans | AMRFinderPlus | Yok |
| V09 | Karşılaştırmalı & Filogeni | BLAST · MAFFT · IQ-TREE2 · taxmyPHAGE | Yok |
| V10 | Varyant & Quasispecies | Yok | iVar varyant + LoFreq |
| V11 | Soy / Klad | Yok | Nextclade |
| V12 | Rapor & Dışa Aktarım | ortak: çift dilli (TR+EN) HTML + köken | ortak |

Tam araç kaydı (DOI'lerle), örnek run'lar ve depo yapısı `docs/` içindedir.

---

Forge ailesi: [RNAForge](https://github.com/aliarslan47/RNAForge) (bulk RNA-seq) · [BacForge](https://github.com/aliarslan47/BacForge) (bakteri) · **VirusForge** (virüs/faj) · [MicrobiomeForge](https://github.com/aliarslan47/MicrobiomeForge) (mikrobiyom) · [Vaxforge](https://github.com/aliarslan47/Vaxforge) (ters aşılama) · [ImmForge](https://github.com/aliarslan47/ImmForge) (bağışıklık simülasyonu) · [PipelineForge](https://github.com/aliarslan47/PipelineForge) (DAG üreticisi). [MIT](LICENSE) lisansı altında.
