"""Rapor çift-dilli (TR varsayılan + EN). Tam-string eşlemesi (over-match yok):
bilinmeyen string olduğu gibi döner. Bilimsel/araç terimleri (PHROG, taksonomi, enum) çevrilmez."""

# Türkçe etiket → İngilizce (tam string). Veri/HTML/bilimsel terimler sözlükte YOK → değişmez.
EN = {
    # başlık / UI
    "VirusForge — Viral / Faj Genom Analiz Raporu": "VirusForge — Viral / Phage Genome Analysis Report",
    "Genel Bakış": "Overview", "Tablo": "Table", "Şekil": "Figure",
    "Veri yok / analiz uygulanmadı.": "No data / analysis not performed.",
    "Örnek": "Sample", "Sekans tipi": "Sequencing type",
    "Alan": "Field", "Değer": "Value", "Metrik": "Metric", "Kategori": "Category",
    "Gen sayısı": "Gene count", "Düzey": "Level", "Sınıf": "Class", "Kimlik": "Identity",
    "Kapsam": "Coverage", "Gen": "Gene", "Tür": "Species", "Accession": "Accession",
    "Mash mesafesi": "Mash distance", "~Benzerlik": "~Similarity",
    "% Kimlik": "% Identity", "% Kapsam": "% Coverage",
    # kartlar
    "Genom uzunluğu": "Genome length", "Tamlık (CheckV)": "Completeness (CheckV)",
    "Kontaminasyon": "Contamination", "Gen (CDS)": "Genes (CDS)", "Yaşam tarzı": "Lifestyle",
    # genel bakış tablo
    "Analiz özeti — temel bulgular": "Analysis summary — key findings",
    "Viral doğrulama (geNomad)": "Viral confirmation (geNomad)", "Taksonomi": "Taxonomy",
    "Alt-familya (PhaGCN)": "Subfamily (PhaGCN)", "En yakın referans (Mash)": "Closest reference (Mash)",
    "Yaşam tarzı (PhaTYP)": "Lifestyle (PhaTYP)", "Genom kalitesi (CheckV)": "Genome quality (CheckV)",
    "VirusForge modül akışı ve modül durumları (yeşil=PASS, turuncu=WARNING, kırmızı=FAIL, gri=N/A).":
        "VirusForge module flow and statuses (green=PASS, orange=WARNING, red=FAIL, grey=N/A).",
    # bölüm başlıkları
    "Input & Otomatik Tespit": "Input & Auto-Detection",
    "Okuma Kalitesi & Ön-İşleme (fastp)": "Read Quality & Preprocessing (fastp)",
    "Viral Genom Assembly": "Viral Genome Assembly",
    "Cilalama & Genom Kalitesi (QUAST + CheckV)": "Polishing & Genome Quality (QUAST + CheckV)",
    "Viral Dizi Tanıma (geNomad)": "Viral Sequence Identification (geNomad)",
    "Taksonomi & En Yakın Referanslar": "Taxonomy & Closest References",
    "Genom Annotation (Pharokka)": "Genome Annotation (Pharokka)",
    "Faj-Özel Karakterizasyon (PhaBOX)": "Phage-Specific Characterization (PhaBOX)",
    "AMR & Virülans (AMRFinderPlus)": "AMR & Virulence (AMRFinderPlus)",
    "Karşılaştırmalı Tanımlama & Filogeni": "Comparative Identification & Phylogeny",
    # tablo başlıkları
    "Girdi tespiti": "Input detection", "Okuma kalite metrikleri": "Read quality metrics",
    "Assembly": "Assembly", "Assembly kalite metrikleri (QUAST)": "Assembly quality metrics (QUAST)",
    "Viral genom tamlık & kontaminasyon (CheckV)": "Viral genome completeness & contamination (CheckV)",
    "Viral dizi tanıma özeti": "Viral identification summary",
    "En yakın referans genomlar (Mash + INPHARED/ICTV)": "Closest reference genomes (Mash + INPHARED/ICTV)",
    "Annotation özeti (Pharokka)": "Annotation summary (Pharokka)",
    "Fonksiyonel kategori dağılımı (PHROGs)": "Functional category distribution (PHROGs)",
    "Faj yaşam tarzı & taksonomi (PhaBOX)": "Phage lifestyle & taxonomy (PhaBOX)",
    "AMR / virülans / stres gen sayıları": "AMR / virulence / stress gene counts",
    "Saptanan genler (AMRFinderPlus)": "Detected genes (AMRFinderPlus)",
    "Tanımlama — en yakın kayıt (BLAST, online virus DB)": "Identification — closest hit (BLAST, online virus DB)",
    "ICTV sınıflandırma": "ICTV classification",
    "En yakın 5 tür (ağaç/ICTV referans seti)": "Closest 5 species (tree/ICTV reference set)",
    # satır etiketleri
    "Belirlenen sekans tipi": "Detected sequencing type", "Ortalama okuma uzunluğu": "Mean read length",
    "Karar kaynağı": "Decision source", "Ham okuma": "Raw reads", "Temiz okuma": "Clean reads",
    "Tutulma oranı": "Retention rate", "Q30 oranı": "Q30 rate", "GC içeriği": "GC content",
    "Uzun-okuma ort. uzunluk": "Long-read mean length", "Uzun-okuma N50": "Long-read N50",
    "Assembler": "Assembler", "Taslak genom": "Draft genome", "Toplam uzunluk": "Total length",
    "Contig sayısı": "Contig count", "En büyük contig": "Largest contig",
    "Tamlık": "Completeness", "CheckV kalitesi": "CheckV quality", "Değerlendirilen contig": "Evaluated contig",
    "Viral mi?": "Viral?", "Viral dizi sayısı": "Viral sequence count",
    "En yüksek virus skoru": "Highest virus score", "Toplam CDS": "Total CDS",
    "PhaTYP skoru": "PhaTYP score", "Soy hattı": "Lineage", "Virülans": "Virulence", "Stres": "Stress",
    "En yakın kayıt": "Closest hit", "Familya (geNomad)": "Family (geNomad)",
    "Alt-familya (PhaBOX)": "Subfamily (PhaBOX)", "Cins (taxmyPHAGE)": "Genus (taxmyPHAGE)",
    "Tür (taxmyPHAGE)": "Species (taxmyPHAGE)",
    # şekil altyazıları (statik)
    "En yakın referanslara Mash mesafesi (küçük = daha yakın).":
        "Mash distance to closest references (smaller = closer).",
    "Fonksiyonel kategorilere göre gen dağılımı.": "Gene distribution by functional category.",
    "Pharokka circular genom haritası — CDS (renk = PHROG fonksiyonel kategorisi), tRNA, GC içeriği ve GC-skew.":
        "Pharokka circular genome map — CDS (color = PHROG functional category), tRNA, GC content and GC-skew.",
    "Filogenetik ağaç — örnek ve en yakın akrabaları (MAFFT + IQ-TREE2).":
        "Phylogenetic tree — sample and its closest relatives (MAFFT + IQ-TREE2).",
    # na mesajları
    "Bakteriyofaj karakterizasyonu uygulanmadı.": "Bacteriophage characterization not performed.",
    "AMR / virülans geni saptanmadı — fajlarda beklenen sonuç.":
        "No AMR / virulence gene detected — expected result for phages.",
    "AMR taraması uygulanmadı.": "AMR screening not performed.",
    "BLAST tanımlaması yapılmadı (ağ/DB?).": "BLAST identification not performed (network/DB?).",
    # araçlar bölümü
    "Araçlar, Sürümler & Bilimsel Referanslar": "Tools, Versions & Scientific References",
    "Araç": "Tool", "Sürüm": "Version", "Amaç": "Purpose", "Depo": "Repository",
    # karşılaştırma raporu
    "VirusForge — Çoklu-Örnek Karşılaştırma": "VirusForge — Multi-Sample Comparison",
    "örnek karşılaştırıldı": "samples compared", "Örnekler": "Samples",
    "Ortak Filogenetik Ağaç": "Combined Phylogenetic Tree",
    "Örnekler-Arası Benzerlik": "Between-Sample Similarity",
    "Genom": "Genome", "Cins (ICTV)": "Genus (ICTV)", "Tür (ICTV)": "Species (ICTV)", "Familya": "Family",
    "Örneklerin (ve varsa akrabaların) ortak ML ağacı — kim kiminle kümeleniyor.":
        "Combined ML tree of samples (and relatives if any) — who clusters with whom.",
    "İkili genom % kimliği (yerel blastn; yüksek = koyu).":
        "Pairwise genome % identity (local blastn; high = dark).",
    # clinker interaktif synteny (M3 Faz 2)
    "İnteraktif Gen-Kümesi Synteny (clinker)": "Interactive Gene-Cluster Synteny (clinker)",
    "genom hizalandı": "genomes aligned",
    "interaktif clinker görselini aç": "open interactive clinker figure",
    "Anotasyonsuz (atlanan) örnekler": "Samples without annotation (skipped)",
}


def t(s, lang="tr"):
    """Etiketi seçili dile çevir. lang!='en' → olduğu gibi; bilinmeyen → olduğu gibi (over-match yok)."""
    if lang == "en" and isinstance(s, str):
        return EN.get(s, s)
    return s
