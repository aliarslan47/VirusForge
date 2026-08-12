# DURUM — VirusForge

> Bu dosya "nerede kaldık" anlık görüntüsüdür. `/clear` öncesi ve anlamlı her durakta güncellenir.

**Konum:** `/home/ali/VirusForge/`
**GitHub:** `github.com/aliarslan47/Phage-Compare-Mini-Pipeline` → **VirusForge** olarak yeniden adlandırılacak (kullanıcı girişi bekleniyor)
**Kimlik:** Forge ailesinin virüs/faj üyesi (kardeşler: BacForge = bakteri, RNAForge = RNA-seq)
**Son güncelleme:** 2026-08-12

## Ne var
- Tek dosyalık R pipeline: `Phage Genome Comparison Tool.R` (~15 KB)
- Dış araç gerektirmeyen (BLAST/minimap2 yok) faj karşılaştırması: temel istatistik, QC barplot, circular harita, k-mer kosinüs, product Jaccard, 6-çerçeve AA 5-mer synteny anchor
- Örnek senaryo: T4 vs T7 (Enterobacteria phage)

## Şu an nerede kaldık
- **2026-08-12: Repo VirusForge olarak yerelde kuruldu.** Public repo tam geçmişiyle `/home/ali/VirusForge`'a klonlandı; README VirusForge markasına çevrildi; DURUM.md + .gitignore eklendi.
- **Bekleyen:** GitHub tarafında repo adının `VirusForge` yapılması (kullanıcının gh oturumu / settings sayfası gerekli), sonra yerel commit'lerin push'u.

## Sıradaki muhtemel işler
- GitHub rename + remote URL güncelleme + push
- (isteğe bağlı) R betiğini T4/T7'ye sabit yerine parametreli hale getirme (herhangi iki genom)
- (isteğe bağlı) Forge ailesi çizgisinde milestone planı
