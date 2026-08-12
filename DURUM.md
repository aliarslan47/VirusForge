# DURUM — VirusForge

> "Nerede kaldık" anlık görüntüsü. `/clear` öncesi ve anlamlı her durakta güncellenir.

**Konum:** `/home/ali/VirusForge/` · **GitHub:** `github.com/aliarslan47/VirusForge`
**Kimlik:** Forge ailesinin virüs/faj üyesi (kardeşler: BacForge=bakteri, Vaxforge). BacForge deseniyle aynı ama **tamamen izole** (ayrı paket/env, `import bacforge` YOK).
**Son güncelleme:** 2026-08-12

## Ne oldu (2026-08-12)
- Repo `Phage-Compare-Mini-Pipeline` → **VirusForge** yeniden adlandırıldı (GitHub API teyitli); remote güncellendi. Eski R betiği `legacy/`e taşındı (temel değil).
- Kaynak spec (`viral_phage_bacteriophage_antigravity_spec_v3.md`) denetlendi:
  - **Tool Registry doğrulandı** — 6 ölü/yanlış repo (CheckV/chklovski, Prodigal-gv/RiversLab, iPHoP/Roux-SGLab, RaFAH/coevoeco, PhageTerm/source-data, VIRIDIC/rega-cev) + 2 fork/ayna (vConTACT2, MAFFT) düzeltildi.
  - Fazlalıklar belirlendi (şemsiye araç içindekiler ayrı kurulmayacak; çoklu-identifier/host opsiyonel).
- **Kapsam RNA + DNA tüm virüsler** olarak genişletildi. 2026 makalelerinden 2 gerçek ekleme doğrulandı: **INPHARED** (faj referans DB) + **phold** (yapısal annotation). RNA yolu: rnaviralSPAdes/iVar + **VADR** + **iVar/LoFreq**.
- **Tasarım dokümanı yazıldı:** `docs/2026-08-12-virusforge-design.md` (mimari + doğrulanmış registry + milestone planı).

## Şu an nerede kaldık
- **Brainstorming/tasarım TAMAM, kullanıcı onayladı** ("buna başlayalım"). Tasarım dokümanı repo'da.
- **SIRADA:** kullanıcı spec'i gözden geçirir → sonra **implementasyon planı** (writing-plans) → M1 iskeleti (`virusforge/` paketi + V00–V08,V19 modül klasörleri + environment.yml + cli).

## Milestone planı
- **M1** — DNA/faj çekirdek (short+long+hybrid): V00→V01→V03→V04→V05→V06→V07→V08→V19. Yalın set (geNomad, Pharokka, PhaBOX, CheckV, Mash+INPHARED, SPAdes/Flye/Unicycler).
- **M2** — RNA-virüs yolu + zenginleştirme (V09–V13, +phold, VADR, iVar/LoFreq).
- **M3** — karşılaştırmalı/filo/görsel (V15–V18) + metavirome + plugin lineage (Pangolin/Nextclade/IRMA).
