# VirusForge

> Forge ailesinin virüs/faj üyesi — [BacForge] (bakteri) ve [RNAForge] (RNA-seq) ile aynı çizgide, hafif ve dış-araç gerektirmeyen bir karşılaştırmalı genomik aracı.

---

**TR:**
VirusForge, iki faj/virüs genom seti arasındaki gen dizisi karşılaştırmalarını kolaylaştırmak için hazırlanmış hafif bir R pipeline'ıdır.
Pipeline, gen kümelerini (clusters) ve farklı okuma çerçevelerindeki (reading frames) amino asit dizilerini analiz eder, istatistiksel özetler çıkarır ve benzersiz "anchor" noktalarını tespit eder.
Amaç, hızlı ve küçük ölçekli faj karşılaştırma çalışmaları için pratik bir çözüm sunmaktır. **BLAST/minimap2 gibi dış araç gerektirmez.**

**ENG:**
VirusForge is a lightweight R pipeline designed to facilitate gene sequence comparisons between two different phage/virus genome sets.
The pipeline analyzes gene clusters and amino acid sequences in different reading frames, generates statistical summaries, and detects unique "anchor" points.
It provides a practical solution for quick, small-scale phage comparison studies. **No external tools (BLAST/minimap2) required.**

---

## Şu an ne yapıyor (mevcut mini-pipeline)

Girdi: iki genom için FASTA + GFF (GenBank opsiyonel). Çıktı: `results/` altında tablolar ve görseller.

1. **Temel istatistikler** — genom uzunluğu, GC%, CDS/gene/tRNA sayıları
2. **QC barplot'lar** — uzunluk, GC, CDS/tRNA
3. **Circular haritalar** — CDS, GC%, kümülatif GC-skew (circlize)
4. **Alignment-free k-mer (K=6) kosinüs benzerliği**
5. **Product-bazlı Jaccard** (GFF/GB annotasyonundan)
6. **6-çerçeve AA 5-mer anchor + genoPlotR synteny** (BLAST'sız)

## Gereken R paketleri

`Biostrings`, `rtracklayer`, `seqinr`, `genoPlotR`, `circlize`, `tidyverse`

## Çalıştırma

`Phage Genome Comparison Tool.R` içindeki `data_dir` yolunu kendi FASTA/GFF klasörüne göre ayarlayıp betiği çalıştır.

---

*Lisans: bkz. [LICENSE](LICENSE)*
