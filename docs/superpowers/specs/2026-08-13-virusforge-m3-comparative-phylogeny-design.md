# VirusForge M3 Faz 1 — Karşılaştırmalı Tanımlama & Filogeni Tasarımı

> Tarih: 2026-08-13 · Durum: onaylandı (kullanıcı) · Kapsam: M3'ün ilk modülü (comparative + phylo)
> Sonraki faz (ayrı spec): clinker synteny, çoklu-örnek karşılaştırma, metavirome.

## 1. Amaç ve bağlam

M1 (4 girdi modu: short/long/hybrid/assembly_input) + M2-A (V08 AMR) T7'de doğrulandı. Bu modül
"bu virüs **ne** ve en yakın akrabaları **kim**" sorusunu karşılaştırmalı yanıtlar:
- **BLAST tanımlama** (online virus DB) → en yakın kayıt + en yakın 5 tür (downstream referans seti)
- **ICTV sınıflandırma** → familya/alt-familya (mevcut geNomad/PhaBOX) + cins/tür (taxmyPHAGE/VIRIDIC)
- **Filogenetik ağaç** (örnek + 5 akraba)

**Tasarım ilkesi:** BLAST'ı **en-yakın-tür seçmek + tanımlama** için kullan; ICTV taksonomiyi ondan
**türetme** (ICTV geNomad/PhaBOX/taxmyPHAGE'den gelir — best-hit ≠ ICTV eşiği). Böylece ICTV yanlış olmaz.

## 2. Mimari

Yeni modül **V09 Karşılaştırmalı Tanımlama & Filogeni** (`v09_comparative.py`), V08'den sonra eklenir.
**Rapor V09→V10'a kayar** (rapor her zaman en son — mevcut numaralandırma kuralı). Yeni sıra:
`V00→V01→V02→V03→V04→V05→V06→V07→V08→V09→V10`.

Modül **viral örneklerde** koşar (V04 is_viral). **Runtime ağ gerekir** (blastn -remote + efetch);
ağ yok / araç yok / yeterli hit yoksa dürüst **WARNING** (asla uydurma).

## 3. Akış

```
örnek contig'ler (latest_genome: V03 > V02)
   │
   ├─(1) blastn -remote -db ref_viruses_rep_genomes    [ONLINE, DB indirmesi YOK]
   │        → en yakın hitler → tür başına tekilleştir → top-5 tür (accession + %kimlik/kapsam)
   │
   ├─(2) efetch → 5 türün TAM genomu (databases/ref_cache/ önbellek; çekilemeyeni atla+logla)
   │
   ├─(3) MAFFT (tüm-genom hizalama: örnek + 5) → IQ-TREE2 (ML + UFBoot bootstrap, model-otomatik)
   │        → Newick ağaç → SVG dendrogram (midpoint köklendirme)
   │
   └─(4) taxmyPHAGE (VIRIDIC algoritması: örnek+5 arası all-vs-all YEREL BLASTn → intergenomic %kimlik;
            ICTV eşiği %95 tür / %70 cins; ICTV VMR'dan cins/tür ADI) → cins/tür + benzerlik matrisi
```

**İki BLAST ayrı:** (1) online = en yakın 5'i **bulma**; (4) yerel (taxmyPHAGE içi) = 6 genom arası **% matrisi**.

## 4. Çıktılar

- `04_standardized/comparative.json`:
  `{blast_top_hit:{accession,species,identity,coverage}, closest_species:[5×{accession,species,identity}],
    ictv:{family,subfamily,genus,species,method}, tree_newick, nearest_sibling, bootstrap,
    similarity_matrix:[[...]], viridic_clusters}`
- Native: blast tsv, hizalama, `.treefile`, taxmyPHAGE çıktısı
- Görsel (`06_visualization/`): filogenetik ağaç SVG + benzerlik matrisi ısı-haritası (bağımsız inline SVG)

## 5. Rapor (V10) — karşılaştırmalı sunum

`references.py PIPELINE_STEPS` + `v10_report._ORDER` + `render.py` güncellenir (yeni V09 bölümü):
- **Tablo — Tanımlama (BLAST):** en yakın kayıt · tür · %kimlik · %kapsam
- **Tablo — ICTV sınıflandırma:** familya/alt-familya (geNomad/PhaBOX) + **cins/tür (taxmyPHAGE)** yan yana
- **Şekil — Filogenetik ağaç** (örnek + 5 akraba, bootstrap değerleri)
- **Şekil — Benzerlik matrisi** ısı-haritası (VIRIDIC intergenomic %)
- Not: BLAST = "en yakın eşleşme" etiketiyle; ICTV = resmi verdikt (karışmaz)

## 6. Araçlar / env / registry

Registry'ye eklenecek (gerçek repo + DOI + version_cmd):
- `blast` (blastn; online `-remote` — DB indirmesi yok) · `mafft` ✅ (kurulu) · `iqtree2` (kurulacak)
- `taxmyphage` (VIRIDIC + ICTV VMR) · `efetch` ✅ (kurulu, Entrez Direct)

Env: iqtree2 + taxmyphage `virusforge` env'ine (hafif) ya da izole `vf_phylo` (implementasyonda karar;
mafft/blast/efetch zaten `virusforge`'da). VMR/DB indirmesi: taxmyPHAGE kendi küçük ICTV VMR'ını çeker.

Config (`tools.comparative`): `blast_db: ref_viruses_rep_genomes`, `n_closest: 5`, `min_hits: 3`,
`ref_cache: databases/ref_cache`, `conda_env` (gerekirse).

## 7. Dürüstlük / hata yönetimi

- Ağ yok / blastn -remote başarısız → WARNING (tanımlama yapılamadı)
- < `min_hits` (3) tür bulunursa → ağaç/VIRIDIC atlanır, WARNING (yeterli akraba yok)
- efetch başarısız accession'lar atlanır + loglanır
- Araç (iqtree2/taxmyphage) kurulu değilse → WARNING (o alt-analiz atlanır, diğerleri devam)

## 8. Test stratejisi

Mevcut sentetik-fixture deseni (gerçek araç/ağ gerektirmez):
- Parser birim testleri: `parse_blast_hits` (tsv → top-N tür, tür-dedup), `parse_iqtree` (Newick → sibling/bootstrap),
  `parse_taxmyphage` (çıktı → cins/tür), similarity-matrix parse
- Modül koşumu: araçsız/ağsız ortamda dürüst WARNING; viral-değil → koşmaz
- SVG üreteçleri (ağaç dendrogram, matris ısı-haritası) saf fonksiyon + test
- Pipeline: yeni sıra (V09 comparative + V10 report); e2e-dryrun yeni modüllerle çöker mez

## 9. Gerçek-veri doğrulaması (T7)

- **BLAST:** en yakın = T7-benzeri fajlar (Autographiviridae)
- **ICTV (taxmyPHAGE):** cins **Teseptimavirus**, tür **Escherichia virus T7**
- **Ağaç:** örnek T7, **V01146 (T7 ref) ile aynı dalda**, yüksek bootstrap
- **Matris:** örnek vs T7 ref ≈ %95+ (aynı tür); diğer T7-benzerleri %70-95 (aynı cins/farklı tür)

## 10. Kapsam dışı (sonraki fazlar)
- clinker (gen-düzeni synteny görseli) — annotated genbank gerektirir
- Çoklu-örnek / metavirome karşılaştırma · offline yerel BLAST DB opsiyonu
- Çift-dilli TR+ENG rapor ([[reminder_virusforge_bilingual_report]])

## 11. Kabul kriterleri
1. V09 modülü M1 sözleşmesine uyar (8 klasör, summary, N/A/WARNING dürüstlüğü, ağ-yoksa çökmez).
2. Rapor V10'a kayar; PIPELINE_STEPS + _ORDER + render tutarlı.
3. Registry'ye araçlar gerçek repo/DOI/version_cmd ile eklenir.
4. Yeni pytest'ler + mevcut 66 test yeşil.
5. T7 gerçek koşu: BLAST T7-benzeri, ICTV Teseptimavirus/Escherichia virus T7, ağaç V01146 ile küme.
6. Her anlamlı durakta commit + push.
