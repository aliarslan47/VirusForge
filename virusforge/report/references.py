"""M1 araç referansları (repo doğrulanmış, DOI gerçek). Sürüm RUNTIME'da tespit edilir (uydurma YOK)."""

# (registry_key, görünen ad, amaç, repo, doi)
TOOL_REFERENCES = [
    ("fastqc", "FastQC", "Short-read kalite kontrolü", "https://github.com/s-andrews/FastQC", None),
    ("fastp", "fastp", "Ultra-hızlı FASTQ ön-işleme", "https://github.com/OpenGene/fastp", "10.1093/bioinformatics/bty560"),
    ("nanoplot", "NanoPlot", "Uzun-okuma QC görselleştirme", "https://github.com/wdecoster/NanoPlot", "10.1093/bioinformatics/bty149"),
    ("filtlong", "Filtlong", "Uzun-okuma kalite filtresi", "https://github.com/rrwick/Filtlong", "10.5281/zenodo.1037300"),
    ("multiqc", "MultiQC", "QC raporlarını birleştirme", "https://github.com/MultiQC/MultiQC", "10.1093/bioinformatics/btw354"),
    ("spades", "SPAdes", "De novo short-read assembler", "https://github.com/ablab/spades", "10.1089/cmb.2012.0021"),
    ("flye", "Flye", "De novo long-read assembler", "https://github.com/mikolmogorov/Flye", "10.1038/s41587-019-0072-8"),
    ("unicycler", "Unicycler", "Hybrid assembly", "https://github.com/rrwick/Unicycler", "10.1371/journal.pcbi.1005595"),
    ("medaka", "Medaka", "ONT consensus cilası", "https://github.com/nanoporetech/medaka", None),
    ("quast", "QUAST", "Assembly kalite değerlendirme", "https://github.com/ablab/quast", "10.1093/bioinformatics/btt086"),
    ("checkv", "CheckV", "Viral genom tamlık & kontaminasyon", "https://bitbucket.org/berkeleylab/checkv", "10.1038/s41587-020-00774-7"),
    ("genomad", "geNomad", "Viral dizi tanıma & taksonomi", "https://github.com/apcamargo/genomad", "10.1038/s41587-023-01953-y"),
    ("mash", "Mash", "Hızlı genom mesafesi (en yakın referans)", "https://github.com/marbl/Mash", "10.1186/s13059-016-0997-x"),
    ("inphared", "INPHARED", "Faj referans veritabanı (Mash sketch, ICTV)", "https://github.com/RyanCook94/inphared", "10.1089/phage.2021.0007"),
    ("pharokka", "Pharokka", "Bakteriyofaj genom annotation", "https://github.com/gbouras13/pharokka", "10.1093/bioinformatics/btac776"),
    ("phabox", "PhaBOX", "Faj karakterizasyon (PhaMer/PhaGCN/PhaTYP)", "https://github.com/KennthShang/PhaBOX", "10.1093/bioadv/vbad101"),
    ("amrfinderplus", "AMRFinderPlus", "AMR / virülans / stres geni taraması", "https://github.com/ncbi/amr", "10.1038/s41598-021-91456-0"),
]

# Rapor bölüm sırası ve modül adları
PIPELINE_STEPS = [
    ("V00", "Girdi & Otomatik Tespit", "auto-detect"),
    ("V01", "Okuma Kalitesi & Ön-İşleme", "FastQC / fastp / NanoPlot"),
    ("V02", "Viral Genom Assembly", "SPAdes / Flye / Unicycler"),
    ("V03", "Cilalama & Genom Kalitesi", "Medaka / QUAST / CheckV"),
    ("V04", "Viral Dizi Tanıma", "geNomad"),
    ("V05", "Taksonomi & En Yakın Referanslar", "Mash + INPHARED"),
    ("V06", "Genom Annotation", "Pharokka"),
    ("V07", "Faj-Özel Karakterizasyon", "PhaBOX"),
    ("V08", "AMR & Virülans", "AMRFinderPlus"),
    ("V09", "Nihai Rapor & Export", "VirusForge"),
]
