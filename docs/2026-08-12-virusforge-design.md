# VirusForge — Tasarım Dokümanı (Design Spec)

**Sürüm:** 1.0 · **Tarih:** 2026-08-12
**Konum:** `/home/ali/VirusForge/` · **GitHub:** `github.com/aliarslan47/VirusForge`
**Kaynak spec:** `viral_phage_bacteriophage_antigravity_spec_v3.md` (v3, registry düzeltildi)

---

## 1. Amaç ve Kapsam

VirusForge, **RNA ve DNA virüslerinin** (izole virüs + bakteriyofaj) tam genom biyoinformatiğini uçtan uca yapan, modüler, teknoloji-bağımsız, bilimsel olarak izlenebilir ve yeniden üretilebilir bir platformdur.

- **Girdi:** short-read / long-read / hybrid / hazır assembly (FASTQ/FASTA).
- **Çıktı:** her modül için standardize edilmiş tablolar + görseller + native çıktılar + provenance + nihai rapor.
- **Felsefe:** genel viral hat her uygun virüste çalışır; bakteriyofaj tespit edilirse phage-specific modüller **ek olarak** aktive olur (genel hattın yerine geçmez). RNA virüsleri için reference-based/consensus + varyant/quasispecies yolu devreye girer.

## 2. Kimlik ve İzolasyon (KURAL)

VirusForge, **BacForge**'un kanıtlanmış mimari **desenini** izler ama tamamen **ayrı ve izole**dir:

- Her şey `/home/ali/VirusForge/` içinde: kendi Python paketi `virusforge/`, kendi `environment.yml` (ayrı conda env), kendi `pyproject.toml`, kendi `config/ databases/ runs/ samples/`.
- Kod/araç paylaşımı = **kopyala-uyarla (vendor)**; asla `import bacforge` değil. Symlink yok, ortak env yok, ortak paket yok.
- BacForge'a hiçbir şey yazılmaz; VirusForge BacForge'dan hiçbir dosya okumaz/import etmez.

## 3. Mimari

### 3.1 Dizin yapısı
```
/home/ali/VirusForge/
├── virusforge/                 # Python paketi
│   ├── cli.py                  # python3 -m virusforge.cli run ...
│   ├── config.py               # YAML config + override
│   ├── detect.py               # V00: read-tipi + genom-tipi + kimya tanıma
│   ├── util.py                 # find_long_reads, sha256, run_cmd, ...
│   ├── provenance.py           # tool+ver+db+param+timestamp+SHA zinciri
│   ├── registry.py             # merkezi tool/DB metadata (sürüm, repo, DOI)
│   ├── modules/                # her modül ayrı klasör (Vxx)
│   └── report/                 # HTML/JSON rapor motoru
├── config/          # default.yaml + örnek config'ler
├── databases/       # checkv/ genomad/ pharokka/ phabox/ inphared/ vadr/ ...
├── setup/           # DB indirme scriptleri
├── runs/            # 20260812_HHMMSS_<mode>/ (zaman damgalı, silinmez)
├── samples/         # girdi örnekleri
├── docs/            # bu doküman + registry
├── legacy/          # eski R betiği (arşiv, kullanılmıyor)
├── environment.yml · pyproject.toml · README.md · DURUM.md
```

### 3.2 Modül çıktı sözleşmesi
Her modül standart klasörler üretir:
`01_input/ 02_work/ 03_native_outputs/ 04_standardized/ 05_statistics/ 06_visualization/ 07_logs/ 08_metadata/` + `Vxx_summary.json`.
Native tool çıktısı **değiştirilmeden** saklanır. Frontend/rapor doğrudan native formata bağımlı olmaz; normalized JSON/TSV üzerinden çalışır.

### 3.3 Durum kodları
`PASS · WARNING · FAIL · NOT_APPLICABLE · SKIPPED`. Dürüstlük zorunlu: sahte/sabit sonuç yok, sessiz PASS yok, tool uyuşmazlığı gizlenmez, uydurma DOI yok.

### 3.4 Provenance
`RESULT → sample → input SHA256 → module → tool+version → database+version → command+params → container/env → timestamp → output SHA256`. Eski run silinmez; yeni `run_id` ile saklanır.

## 4. Girdi Yönlendirme (V00)

Read uzunluğu dağılımı + paired-end ilişkisi + FASTQ header ile: `SHORT_READ / LONG_READ / HYBRID / ASSEMBLY_INPUT`. Dosya adı tek başına karar vermez; kullanıcı override edebilir. Genom-tipi (`DNA / RNA / ssDNA / dsDNA / ssRNA± / dsRNA`, `SEGMENTED?`) metadata + downstream identification'dan belirlenir.

```
                 V00 AUTO-DETECT
                       │
     ┌─────────────────┼──────────────────┐
   SHORT             LONG               HYBRID
     │                 │                   │
FastQC+fastp     NanoPlot+chopper    short QC + long QC
     │                 │                   │
   [genom-tipi dallanması: DNA de novo / RNA de novo / RNA reference-based]
```

## 5. RNA vs DNA yolları

| Modül | DNA / faj yolu | RNA yolu |
|---|---|---|
| V03 Assembly | SPAdes / Flye / Unicycler | rnaviralSPAdes/coronaSPAdes **veya** reference-based consensus (iVar) |
| V07 Annotation | Pharokka (+phold) | **VADR** (NCBI viral) / VAPiD |
| V08/V10/V12 | phage char / lifestyle / termini | **NOT_APPLICABLE** |
| V14 Variants | opsiyonel | **kritik**: iVar + LoFreq (quasispecies) |
| V17 Phylo | MAFFT+IQ-TREE2 | + lineage (Pangolin/Nextclade/IRMA — plugin) |

## 6. Tool Registry (doğrulanmış, düzeltilmiş)

`✓` = çekirdek/önerilen · `(opt)` = opsiyonel (default kapalı) · etiket: okuma/genom tipi.
**Şemsiye araçlar** parantez içindekileri kendi içinde koşturur — ayrı kurulmaz.

| Modül | Araç | Rol | Durum | Repo (doğrulanmış) |
|---|---|---|---|---|
| V01 | FastQC | short QC | ✓ | github.com/s-andrews/FastQC |
| V01 | fastp | short trim | ✓ | github.com/OpenGene/fastp |
| V01 | NanoPlot | long QC | ✓ | github.com/wdecoster/NanoPlot |
| V01 | Filtlong/chopper | long filtre | ✓ | github.com/rrwick/Filtlong |
| V01/V18 | MultiQC | birleştirme | ✓ | github.com/MultiQC/MultiQC |
| V01 | SortMeRNA | rRNA temizliği [RNA] | (opt) | github.com/sortmerna/sortmerna |
| V02 | minimap2 | host hizalama | ✓ | github.com/lh3/minimap2 |
| V02 | Bowtie2 | short host | ✓ | github.com/BenLangmead/bowtie2 |
| V02 | SAMtools | BAM işleme | ✓ | github.com/samtools/samtools |
| V02 | STAR/HISAT2 | host transkriptom [RNA] | (opt) | github.com/alexdobin/STAR |
| V02 | Kraken2 | taksonomik tarama | (opt) | github.com/DerrickWood/kraken2 |
| V03 | SPAdes | DNA short assembly | ✓ | github.com/ablab/spades |
| V03 | Flye | DNA long assembly | ✓ | github.com/mikolmogorov/Flye |
| V03 | Unicycler | DNA hybrid assembly | ✓ | github.com/rrwick/Unicycler |
| V03 | rnaviralSPAdes/coronaSPAdes | RNA de novo | ✓ | (SPAdes modu) ablab/spades |
| V03 | iVar | RNA reference consensus | ✓ | github.com/andersen-lab/ivar |
| V04 | Racon | long cila | ✓ | github.com/lbcb-sci/racon |
| V04 | Medaka | ONT cila | ✓ | github.com/nanoporetech/medaka |
| V04 | QUAST | assembly metrik | ✓ | github.com/ablab/quast |
| V04 | **CheckV** | viral tamlık/kontaminasyon | ✓ | **bitbucket.org/berkeleylab/checkv** |
| V05 | **geNomad** | viral identification+tax | ✓ | github.com/apcamargo/genomad |
| V05 | VirSorter2 | identification (consensus) | (opt) | github.com/jiarong/VirSorter2 |
| V05 | VIBRANT | identification + AMG | (opt) | github.com/AnantharamanLab/VIBRANT |
| V05 | palmscan/palmID | RdRP tespiti [RNA] | (opt) | github.com/rcedgar/palmscan |
| V06 | Mash | en yakın referans | ✓ | github.com/marbl/Mash |
| V06 | **INPHARED** | faj referans DB | ✓ | github.com/RyanCook94/inphared |
| V06 | RefSeq Viral + BLAST | RNA/genel referans | ✓ | (NCBI) |
| V06 | sourmash | MinHash (alt) | (opt) | github.com/sourmash-bio/sourmash |
| V07 | **Pharokka** (PHANOTATE+Prodigal-gv+tRNAscan-SE+MMseqs2) | faj annotation | ✓ | github.com/gbouras13/pharokka |
| V07 | **phold** | yapısal annotation (2026) | (opt) | github.com/gbouras13/phold |
| V07 | **VADR** | RNA/genel viral annotation | ✓ | github.com/ncbi/vadr |
| V07 | VAPiD | alt genel annotation | (opt) | github.com/rcs333/VAPiD |
| V07 | Cenote-Taker3 | geniş virüs keşfi | (opt) | github.com/mtisza1/Cenote-Taker3 |
| V08 | **PhaBOX** (PhaMer/PhaGCN/PhaTYP/PhaVIP) | faj karakterizasyon | ✓ | github.com/KennthShang/PhaBOX |
| V09 | **iPHoP** (RaFAH+CRISPR+BLAST içinde) | host prediction | ✓ | **bitbucket.org/srouxjgi/iphop** |
| V09 | CHERRY | host (2025 benchmark) | (opt) | github.com/KennthShang/CHERRY |
| V10 | PhaTYP (PhaBOX) / BACPHLIP | lifestyle | ✓ / (opt) | github.com/adamhockenberry/bacphlip |
| V11 | AMRFinderPlus | AMR | ✓ | github.com/ncbi/amr |
| V11 | ABRicate | AMR/virülans | ✓ | github.com/tseemann/abricate |
| V11 | CARD/RGI | AMR | (opt) | github.com/arpcard/rgi |
| V12 | PhageTerm (PTV) | termini/packaging | ✓ | gitlab.pasteur.fr/vlegrand/ptv |
| V13 | DIAMOND | homoloji | ✓ | github.com/bbuchfink/diamond |
| V13 | MMseqs2 | arama/kümeleme | ✓ | github.com/soedinglab/MMseqs2 |
| V13 | HMMER | profil | ✓ | github.com/EddyRivasLab/hmmer |
| V13 | InterProScan | derin domain (ağır) | (opt) | github.com/ebi-pf-team/interproscan |
| V14 | BCFtools | varyant | ✓ | github.com/samtools/bcftools |
| V14 | **iVar** | RNA consensus+varyant | ✓ | github.com/andersen-lab/ivar |
| V14 | **LoFreq** | düşük-frekans/quasispecies | ✓ | github.com/CSB5/lofreq |
| V14 | snpEff / V-pipe | varyant annot / quasispecies | (opt) | github.com/pcingola/SnpEff |
| V15 | clinker | synteny | ✓ | github.com/gamcil/clinker |
| V16 | VIRIDIC | intergenomik % [DNA] | ✓ | rhea.icbm.uni-oldenburg.de/viridic |
| V16 | vConTACT2 | gen-paylaşım ağı (legacy) | (opt) | bitbucket.org/MAVERICLab/vcontact2 |
| V17 | MAFFT | hizalama | ✓ | mafft.cbrc.jp (Katoh) |
| V17 | IQ-TREE2 | ağaç | ✓ | github.com/iqtree/iqtree2 |
| V17 | TreeTime | zamansal | (opt) | github.com/neherlab/treetime |
| Plugin | Pangolin/Nextclade/IRMA | RNA lineage | (opt) | github.com/cov-lineages/pangolin |
| GLOBAL | Nextflow (ileride) | orkestrasyon | (opt) | github.com/nextflow-io/nextflow |

**Not:** CheckV, iPHoP, PhageTerm, VIRIDIC, MAFFT GitHub'da değil (Bitbucket/GitLab/web) — kurulum yöntemleri farklı.

## 7. Milestone Planı

- **M1 — DNA/faj çekirdek (3 okuma tipi):** V00→V01→V03→V04→V05→V06→V07→V08→V19. Tek izolat faj; short+long+hybrid. Yalın set: fastp/FastQC/MultiQC, NanoPlot/Filtlong, SPAdes/Flye/Unicycler, Racon/Medaka, QUAST, CheckV, geNomad, Mash+INPHARED, Pharokka, PhaBOX. Gerçek örnekte uçtan uca (exit 0, dürüst durumlar).
- **M2 — RNA-virüs yolu + zenginleştirme:** RNA assembly (rnaviralSPAdes / reference-based iVar), VADR annotation, V14 (iVar+LoFreq), V09 host (iPHoP/CHERRY), V10 lifestyle, V11 AMR, V12 termini, V13 functional (+phold).
- **M3 — karşılaştırmalı/filo + görsel + genişleme:** V15 synteny, V16 comparative (VIRIDIC), V17 phylo (MAFFT+IQ-TREE2), V18 toplu istatistik/görsel; metavirome (V30A–F); plugin lineage (Pangolin/Nextclade/IRMA).

## 8. Tasarım İlkeleri — "olmamalı" (kural)

1. Yanlış/fork repo → yok (registry doğrulandı).
2. Şemsiye aracın içindekini ayrı kurmak → yok (Pharokka/PhaBOX/iPHoP içindekiler).
3. Zorunlu çoklu-identifier / çoklu-host tool → yok; varsayılan yalın, gerisi opsiyonel.
4. Ağır DB'ler (iPHoP, InterProScan, Kraken2) M1'de zorunlu → yok.
5. Zorunlu/agresif host-removal → yok (CRISPR host sinyalini korur).
6. VirusForge↔BacForge ortak kurulum/import → yok (izolasyon).
7. Fabrikasyon/stub/sabit sonuç/uydurma DOI/gizli tool-uyuşmazlığı → yok.

## 9. Ertelenenler / Açık Konular
- Metavirome (V30A–F) → M3.
- Plugin engine (SARS/HIV/HBV/flu lineage araçları) → M3, RNA yolunun üstüne.
- Segmented genom motoru (influenza) → M2/M3 arası, RNA yoluyla.
