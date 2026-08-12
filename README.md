# VirusForge

> Forge ailesinin virüs/faj üyesi — **RNA ve DNA virüslerinin** (izole virüs + bakteriyofaj) tam genom biyoinformatiğini uçtan uca yapan modüler platform. Kardeşler: [BacForge] (bakteri), [Vaxforge].

## Ne yapar

Short-read / long-read / hybrid / hazır assembly girdilerini otomatik tanır; V00–V19 modülleriyle: QC → assembly → viral tamlık → identification → taksonomi → annotation → (faj ise) karakterizasyon/host/lifestyle → varyant/quasispecies (RNA) → karşılaştırmalı genomik → filogenomik → rapor. Bakteriyofaj tespit edilirse phage-specific modüller **ek** olarak devreye girer; RNA virüslerinde reference-based/consensus + varyant yolu aktifleşir.

- **Dürüstlük:** sahte/sabit sonuç yok, uydurma DOI yok, tool uyuşmazlığı gizlenmez. Durumlar: `PASS/WARNING/FAIL/NOT_APPLICABLE/SKIPPED`.
- **İzlenebilirlik:** her sonuç tool+DB sürümü ve parametreleriyle yeniden üretilebilir (provenance zinciri).
- **İzolasyon:** BacForge deseniyle aynı çizgide ama tamamen ayrı paket/env/kurulum.

## Durum

Tasarım aşaması. Bkz. **[docs/2026-08-12-virusforge-design.md](docs/2026-08-12-virusforge-design.md)** (mimari + doğrulanmış tool registry + milestone planı) ve **[DURUM.md](DURUM.md)**.

## Milestone'lar

- **M1** — DNA/faj çekirdek, 3 okuma tipi (short+long+hybrid): V00–V08 + V19.
- **M2** — RNA-virüs yolu (rnaviralSPAdes/iVar, VADR, iVar+LoFreq) + zenginleştirme (V09–V13).
- **M3** — karşılaştırmalı/filo/görsel (V15–V18) + metavirome + plugin lineage.

*Lisans: [LICENSE](LICENSE)*
