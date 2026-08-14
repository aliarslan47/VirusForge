<div align="center">

# 🧬 VirusForge

**RNA & DNA virüslerinin ve bakteriyofajların tam genom biyoinformatiği için modüler, uçtan-uca analiz platformu**

[![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-2e9e6b)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-181%20passing-brightgreen)](tests/)
[![Milestone](https://img.shields.io/badge/M1·M2·M3-DNA%20%2B%20RNA%20doğrulandı%20✓-0d6b8f)](docs/)
[![Forge Family](https://img.shields.io/badge/Forge%20ailesi-BacForge%20·%20Vaxforge-6b7682)](#)

</div>

---

VirusForge; short-read, long-read, hybrid ve hazır-assembly girdilerini **otomatik tanıyıp** kalite kontrolünden nihai rapora kadar tek komutla işler. **Bakteriyofaj/DNA virüs** tespit edilirse phage-özel modüller (Pharokka, PhaBOX, AMR, karşılaştırmalı/filogeni) devreye girer; **RNA virüsleri** için reference-based konsensüs + VADR anotasyon + varyant/quasispecies + soy/klad (Nextclade) yolu **çalışır ve SARS-CoV-2 ile doğrulanmıştır** (M2-B tamam).

BacForge (bakteri) ve Vaxforge'un kardeşi olan bu platform, aynı mimari deseni izler ama **tamamen izole** bir kurulumdur.

## ✨ Öne çıkanlar

- **Otomatik yönlendirme** — kullanıcıdan seçim istemeden read-tipi (short/long/hybrid/assembly) ve genom-tipi (DNA/RNA) tespiti
- **Dürüst çıktı** — sahte/sabit sonuç yok, uydurma DOI yok, araç uyuşmazlığı gizlenmez; durumlar `PASS · WARNING · FAIL · NOT_APPLICABLE · SKIPPED`
- **İzlenebilir & yeniden üretilebilir** — her sonuç tool + veritabanı sürümü ve parametreleriyle `provenance.json`'a kaydedilir
- **Profesyonel rapor** — numaralı tablolar/şekiller, **circular genom haritası**, fonksiyonel dağılım grafikleri, araç+DOI referansları (self-contained HTML)
- **Doğrulanmış araç kaydı** — her aracın resmî deposu tek tek kontrol edildi (6 hatalı/ölü repo düzeltildi)

## 🔬 Pipeline

Tek pipeline, iki yol: `V00`–`V01` ortak; molekül kararından sonra (`--molecule` / geNomad Riboviria)
DNA/faj ve RNA virüs dalları ayrılır ve `V12` raporunda birleşir. Okuma tipi (short/long/hybrid/assembly)
buna dik ayrı bir eksendir. Etkileşimli çift-dilli şema: [`docs/pipeline_architecture.html`](docs/pipeline_architecture.html).

```mermaid
flowchart TB
    IN([FASTQ / FASTA]) --> V00[V00 · Girdi + Tespit]
    V00 --> V01[V01 · Okuma QC<br/>fastp·NanoPlot·filtlong]
    V01 --> MOL{molekül?}

    MOL -->|DNA / faj| D02[V02 · Assembly<br/>SPAdes·Flye·Unicycler]
    D02 --> D03[V03 · Cilalama + QC<br/>Medaka·QUAST·CheckV]
    D03 --> D04[V04 · Viral Tanıma<br/>geNomad]
    D04 --> D05[V05 · Taksonomi<br/>Mash+INPHARED]
    D05 --> D06[V06 · Anotasyon<br/>Pharokka + harita]
    D06 --> D07[V07 · Faj Karakter.<br/>PhaBOX]
    D07 --> D08[V08 · AMR<br/>AMRFinderPlus]
    D08 --> D09[V09 · Karşılaştırmalı<br/>BLAST·IQ-TREE2·taxmyPHAGE]
    D09 --> V12

    MOL -->|RNA| R02[V02 · Konsensüs<br/>iVar·rnaviralSPAdes]
    R02 --> R03[V03 · Kalite + Kapsama<br/>QUAST·samtools depth]
    R03 --> R04[V04 · Viral Tanıma<br/>geNomad → Riboviria]
    R04 --> R06[V06 · Anotasyon<br/>VADR + gen haritası]
    R06 --> R10[V10 · Varyant<br/>iVar+LoFreq]
    R10 --> R11[V11 · Soy/Klad<br/>Nextclade]
    R11 --> V12

    V12[V12 · Rapor + Export<br/>TR+EN HTML + provenance] --> OUT([HTML + JSON + Provenance])

    classDef dna fill:#e7f0f5,stroke:#0d6b8f,color:#14181d;
    classDef rna fill:#f7ecdb,stroke:#c07211,color:#14181d;
    classDef sh  fill:#e6f0ed,stroke:#3f8a7d,color:#14181d;
    class D02,D03,D05,D06,D07,D08,D09 dna;
    class R02,R03,R06,R10,R11 rna;
    class V00,V01,D04,R04,V12 sh;
```

## 🧩 Modüller

Her modül molekül tipine göre kendi içinde dallanır; o yola uymayan modül dürüstçe **N/A** döner.

| Kod | Modül | DNA / faj yolu | RNA virüs yolu |
|:---:|---|---|---|
| **V00** | Girdi & Tespit | ↔ **ortak** — okuma tipi + molekül (geNomad Riboviria / `--molecule`) | ↔ |
| **V01** | Okuma QC | ↔ **ortak** — fastp · FastQC · NanoPlot · filtlong · MultiQC | ↔ |
| **V02** | Assembly / Konsensüs | SPAdes · Flye · Unicycler *(de novo)* | iVar konsensüs (ref) · rnaviralSPAdes |
| **V03** | Cilalama & Kalite | Medaka · QUAST · CheckV | QUAST · kapsama (samtools depth) |
| **V04** | Viral Tanıma | ↔ **ortak** — geNomad (viral doğrulama + taksonomi) | ↔ |
| **V05** | Taksonomi & Referans | Mash + INPHARED · NJ ağaç | *N/A — faj-özel* |
| **V06** | Genom Anotasyon | Pharokka + circular genom haritası | VADR + gen haritası |
| **V07** | Faj Karakterizasyonu | PhaBOX (PhaMer/PhaGCN/PhaTYP) | *N/A* |
| **V08** | AMR & Virülans | AMRFinderPlus | *N/A* |
| **V09** | Karşılaştırmalı & Filogeni | BLAST · MAFFT · IQ-TREE2 · taxmyPHAGE · VIRIDIC · synteny | *N/A* |
| **V10** | Varyant & Quasispecies | *N/A — RNA'ya özel* | iVar variants + LoFreq (tür/etki/gen) |
| **V11** | Soy / Klad Tayini | *N/A — RNA'ya özel* | Nextclade (klad + PANGO soyu + QC) |
| **V12** | Rapor & Export | ↔ **ortak** — çift-dilli (TR+EN) HTML rapor + provenance | ↔ |

## 🚀 Kurulum

```bash
git clone https://github.com/aliarslan47/VirusForge.git
cd VirusForge

# İzole conda ortamı
conda env create -f environment.yml
conda activate virusforge
pip install -e .

# Veritabanları (CheckV, geNomad, Pharokka, INPHARED, PhaBOX)
bash setup/get_databases.sh
```

## 💻 Kullanım

```bash
# Kurulu araç sürümlerini gör
python -m virusforge.cli info

# Örneği koy: samples/<id>/  (short: *_R1/_R2, long: tek ONT fastq, assembly: *.fasta)
python -m virusforge.cli run --sample samples/T7_short --out runs --threads 8

# → runs/<zaman>_<mod>/report.html  (self-contained profesyonel rapor)
```

## 📊 Örnek sonuç — *Escherichia phage* T7 (short-read, doğrulandı)

Gerçek ENA verisi (`ERR3804828`, Illumina MiSeq) ile **DNA/faj yolu tüm modüller PASS** (V10/V11 RNA modülleri bu örnekte N/A):

| Analiz | Sonuç |
|---|---|
| Genom kalitesi (CheckV) | **%100 tam · %0 kontaminasyon · Complete** |
| Assembly (QUAST) | 45.451 bp · en büyük contig 40.659 bp · N50 40.659 |
| Viral tanıma (geNomad) | Caudoviricetes; **Autographiviridae** (skor 0.98) |
| En yakın referans (Mash) | `V01146` (T7 referansı) · mesafe 0.0036 |
| Annotation (Pharokka) | **76 CDS** · head&packaging 14 · DNA/RNA metab. 16 |
| Yaşam tarzı (PhaBOX) | **virulent** · alt-familya **Studiervirinae** |

📄 **Örnek rapor:** [canlı görüntüle](https://claude.ai/code/artifact/0541885b-ce14-4011-87db-6eecc212b819)

## 🧪 Doğrulanmış araç kaydı (çekirdek)

| Araç | Rol | DOI |
|---|---|---|
| [fastp](https://github.com/OpenGene/fastp) | Read ön-işleme | 10.1093/bioinformatics/bty560 |
| [SPAdes](https://github.com/ablab/spades) | Assembly | 10.1089/cmb.2012.0021 |
| [CheckV](https://bitbucket.org/berkeleylab/checkv) | Viral tamlık/kontaminasyon | 10.1038/s41587-020-00774-7 |
| [geNomad](https://github.com/apcamargo/genomad) | Viral tanıma & taksonomi | 10.1038/s41587-023-01953-y |
| [Mash](https://github.com/marbl/Mash) + [INPHARED](https://github.com/RyanCook94/inphared) | En yakın referans | 10.1186/s13059-016-0997-x |
| [Pharokka](https://github.com/gbouras13/pharokka) | Faj annotation | 10.1093/bioinformatics/btac776 |
| [PhaBOX](https://github.com/KennthShang/PhaBOX) | Faj karakterizasyon | 10.1093/bioadv/vbad101 |

> Tam kayıt: [`docs/2026-08-12-virusforge-design.md`](docs/2026-08-12-virusforge-design.md) · Sürümler runtime'da tespit edilir, DOI'ler yayın kaynağıdır — **uydurma yok**.

## 🗺️ Yol haritası

- [x] **M1** — DNA/faj çekirdek · **short + long + hybrid + assembly T7 gerçek-veri doğrulandı** (platform kapsamı tam)
- [x] **M2-A** — faj zenginleştirme: **V08 AMR & virülans (AMRFinderPlus)** · T7 doğrulandı
- [x] **M3** — **V09 karşılaştırmalı & filogeni** (BLAST + IQ-TREE2 + taxmyPHAGE ICTV + VIRIDIC + synteny) · çoklu-örnek `compare` + clinker · T7 doğrulandı
- [x] **M2-B** — **RNA-virüs yolu** (iVar konsensüs · VADR · V10 iVar/LoFreq varyant · V11 Nextclade soy/klad) · **SARS-CoV-2 gerçek-veri doğrulandı** (XBB.1.5.52)
- [ ] Sıradaki (opsiyonel): RNA de novo (referanssız) doğrulama · metavirome · tespit araçları (virsorter2/vibrant/kraken2) · RNA lineage eklentileri (IRMA)

## 📁 Yapı

```
virusforge/        Python paketi (modules/ · tools · pipeline · report · registry)
config/            varsayılan + kullanıcı YAML
databases/         indirilen DB'ler         (git'e girmez)
runs/              zaman-damgalı koşular     (git'e girmez)
samples/           girdi örnekleri           (git'e girmez)
docs/              tasarım dokümanı + plan
setup/             DB indirme scriptleri
```

## 🧭 İlkeler

**İzolasyon** — VirusForge, BacForge'un mimari desenini izler ama ayrı paket/env/kurulumdur; çapraz-import yoktur.
**Dürüstlük** — değer yoksa WARNING, uygun değilse NOT_APPLICABLE; asla uydurma/sabit sonuç.
**İzlenebilirlik** — input SHA → tool+sürüm → DB+sürüm → komut → çıktı SHA zinciri.

---

<div align="center">
<sub>Forge ailesi · BacForge (bakteri) · Vaxforge · <b>VirusForge</b> (virüs/faj)</sub>
</div>

*Lisans: [MIT](LICENSE)*
