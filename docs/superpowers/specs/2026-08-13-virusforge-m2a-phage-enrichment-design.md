# VirusForge M2-A — Faj Zenginleştirme Tasarımı (V09, V11, V12, V13)

> Tarih: 2026-08-13 · Durum: onaylandı (kullanıcı) · Kapsam: M2'nin faj-zenginleştirme yarısı
> Kardeş yarım (ayrı spec): M2-B RNA-virüs yolu (rnaviralSPAdes/iVar + VADR + iVar/LoFreq).

## 1. Amaç ve bağlam

M1 faj çekirdek hattı kısa okumada uçtan-uca doğrulandı (T7, 9/9 PASS): V00→V01→V03→V04→V05→
V06→V07→V08→V19. M2-A bu **çalışan faj hattının üzerine biner** ve dört zenginleştirme modülü ekler:
konak tahmini, AMR/virülans taraması, genom uçları (termini) tespiti, yapısal/domain annotation.

**Kural — izolasyon:** BacForge deseni izlenir ama tamamen ayrı (`import bacforge` yok). Kod paylaşımı
= kopyala-uyarla. Mevcut M1 sözleşmesine (`Module` tabanı, 8 standart klasör, `safe_run`, summary.json,
resume) birebir uyulur; yeni desen icat edilmez.

**Doğruluk ve dürüstlük:** Araç kuruluysa gerçek sonuç; kurulu değil/çökerse `WARNING` + log —
asla uydurma çıktı. Faj değilse `NOT_APPLICABLE` (V08 deseni).

## 2. Mimari

Pipeline'a `V08`'den sonra, `V19`'dan önce dört yeni `Module` alt-sınıfı eklenir. Yeni varsayılan sıra:

```
V00 → V01 → V03 → V04 → V05 → V06 → V07 → V08 → V09 → V11 → V12 → V13 → V19
```

`virusforge/pipeline.py` içindeki `DEFAULT_MODULES` listesi güncellenir (V19 en sonda kalır).
Numaralandırma spec'e sadıktır (V10/V14–V18 M2-B/M3'e ayrılmıştır; boşluklar kasıtlı).

Her modül `virusforge/modules/vNN_*.py` dosyasında, mevcut modüllerle aynı iskelet:
- `make_dirs(ctx.run_dir)` → 8 standart alt-klasör
- upstream veriyi `ctx.results` / `latest_genome(ctx)` / `ctx.artifacts` üzerinden alır
- komut `tools.py`'deki saf fonksiyonla kurulur, `safe_run(cmd, log)` ile koşar
- native çıktı `03_native_outputs/`, standart JSON `04_standardized/`, summary `write_summary(...)`
- `ctx.results[self.code] = metrics` ile aşağı-akışa (V19 rapor) veri geçer
- `restore_artifacts` (gerekirse) resume için diskten geri yükler

### 2.1 Faj-koşulluluk (ortak yardımcı)

Dört modül de yalnız fajlarda anlamlı. V08'deki kontrol tekrarlanmak yerine `module.py`'ye küçük bir
yardımcı eklenir:

```python
def is_phage(ctx) -> bool:
    v05 = ctx.results.get("V05", {})
    tax = (v05.get("taxonomy") or "").lower()
    return bool(v05.get("is_viral")) and ("caudo" in tax or "phage" in tax or not tax)
```

Faj değilse modül `NOT_APPLICABLE` döndürür (genel viral hat kesilmez, yalnız bu modül atlanır).

## 3. Modül tanımları

### V09 — Host / Konak Tahmini
- **Dosya:** `modules/v09_host.py` · **dirname:** `V09_HOST_PREDICTION`
- **Araç:** config `tools.host.method` → `rafah` (varsayılan) | `iphop` (opsiyonel/ileri)
- **Girdi:** `latest_genome(ctx)` (V04 cilalı > V03 draft)
- **RaFAH:** `RaFAH.py --predict --genomes_list <genome> --file_prefix <out>` → `*_Host_Predictions.tsv`
  parse: tahmin edilen host taksonu + skor.
- **iPHoP:** `iphop predict --fa <genome> --out_dir <out> --db_dir <db>` → `Host_prediction_to_genus_*.csv`
  parse: host cinsi + güven skoru + yöntem. DB dev ortamında indirilmez (opsiyonel).
- **Standart çıktı:** `04_standardized/host_prediction.json`
  `{method, predicted_host, rank, confidence, raw_row}`
- **Durum:** faj değil→N/A; araç yok/çöker→WARNING; parse başarılı→PASS

### V11 — AMR + Virülans
- **Dosya:** `modules/v11_amr.py` · **dirname:** `V11_AMR_VIRULENCE`
- **Araç:** AMRFinderPlus (primary, BacForge tutarlı). abricate/VFDB = config-hook (varsayılan kapalı, YAGNI).
- **Girdi:** V07 pharokka protein FAA'sı (varsa) → `amrfinder -p <faa>`; yoksa genom → `amrfinder -n <genome>`.
  Pharokka çıktısındaki protein dosyası `ctx.artifacts["V07"]` veya native output'tan bulunur.
- **DB:** `tools.amrfinder.db` (varsayılan AMRFinderPlus kurulum DB'si; `amrfinder -u` ile güncellenir).
- **Standart çıktı:** `04_standardized/amr_virulence.json`
  `{amr_genes:[...], virulence_genes:[...], stress_genes:[...], counts:{...}}`
  (AMRFinderPlus `Element type` sütunu: AMR / VIRULENCE / STRESS)
- **Durum:** faj değil→N/A; araç yok/çöker→WARNING; 0 gen bulunması normal→PASS (boş liste geçerli sonuç)

### V12 — Genom Uçları / Termini
- **Dosya:** `modules/v12_termini.py` · **dirname:** `V12_TERMINI`
- **Araç:** PhageTerm
- **Girdi:** ham paired-end okuma (V00/V01 kısa okuma) + assembly (`latest_genome`).
  **Long-only örnekte `NOT_APPLICABLE`** (PhageTerm paired-end kısa okuma gerektirir; mode `long` ise atla).
- **Komut:** `PhageTerm.py -f <R1> -r <R2> -s <genome> --report_title <name>` → `*_PhageTerm_report.pdf/.csv`
  parse: termini tipi (DTR / cohesive cos / pac / headful / unknown) + pozisyon.
- **Standart çıktı:** `04_standardized/termini.json` `{termini_type, left, right, method}`
- **Durum:** long-only ya da paired okuma yok→N/A; faj değil→N/A; çöker→WARNING; parse→PASS

### V13 — Yapısal / Domain Annotation
- **Dosya:** `modules/v13_domain.py` · **dirname:** `V13_DOMAIN_ANNOTATION`
- **Araç:** phold (zaten registry'de). pharokka GenBank çıktısını tüketir.
- **Girdi:** V07 pharokka çıktı dizini (GenBank/GFF). `phold run -i <pharokka.gbk> -o <out> [-d db]`
  (ya da `phold predict` + `phold compare`). ProstT5/Foldseek ile yapı-tabanlı fonksiyon ataması.
- **Standart çıktı:** `04_standardized/domain_annotation.json`
  `{annotated_cds, functional_categories:{...}, structural_hits, unknown_before, unknown_after}`
  (phold'un fonksiyona-atadığı CDS sayısı — pharokka'nın "hypothetical"lerini azaltır)
- **Görsel:** phold plot üretirse `06_visualization/`'a kopyalanır → V19 şekli.
- **Durum:** faj değil→N/A; pharokka çıktısı yok→WARNING; araç yok/çöker→WARNING; parse→PASS

## 4. Registry ve config değişiklikleri

### 4.1 `virusforge/data/registry.yaml` — eklenecek araçlar
- `rafah` — repo `github.com/felipehcoutinho/RaFAH`, version_cmd tespit edilecek
- `iphop` — repo `bitbucket.org/srouxjgi/iphop`, `iphop --version` (opsiyonel)
- `amrfinderplus` — repo `github.com/ncbi/amr`, `amrfinder --version`
- `abricate` — repo `github.com/tseemann/abricate`, `abricate --version` (opsiyonel)
- `phageterm` — repo `gitlab.pasteur.fr/vlegrand/ptv` (PhageTerm virtual), version_cmd tespit
- `phold` — zaten mevcut, dokunulmaz

Her giriş doğrulanmış gerçek repo + DOI + version_cmd içerir (uydurma yok; kurulumdan sonra
`detect_version` ile canlı teyit).

### 4.2 `config/default.yaml` — eklenecek anahtarlar
```yaml
tools:
  host:
    method: rafah              # rafah | iphop
    rafah_db: databases/rafah  # RaFAH kendi modelini taşır; gerekirse yol
    iphop_db: databases/iphop  # opsiyonel, dev'de indirilmez
  amrfinder:
    db: ""                     # boş=AMRFinderPlus varsayılan kurulum DB'si
    use_abricate: false        # opsiyonel VFDB/CARD hook
  phageterm:
    extra_args: ""
  phold:
    db: databases/phold        # phold DB (opsiyonel; yoksa varsayılan)
```
`optional.phold` zaten var; V13 için ayrıca `optional`'a bağımlı DEĞİL (M2-A çekirdeği).

### 4.3 `virusforge/tools.py` — eklenecek saf komut kurucular
`rafah_cmd`, `iphop_cmd`, `amrfinder_cmd(input, out, db, is_protein)`, `phageterm_cmd`,
`phold_cmd`. Mevcut fonksiyon deseniyle (liste döndürür, conda_env opsiyonu gerekirse) aynı.
İzole env gerekirse (phabox gibi) `conda run -n <env>` sarmalayıcı deseni tekrar kullanılır.

## 5. Rapor (V19) entegrasyonu

`virusforge/report/render.py` yeni modül summary'lerini okuyup numaralı tablolar üretir:
- **Tablo:** Konak tahmini (host, rütbe, güven, yöntem)
- **Tablo:** AMR/Virülans genleri (gen, tip, kimlik %, kapsam)
- **Tablo:** Termini tipi
- **Tablo:** Domain annotation özeti (fonksiyona-atanan CDS, kategori dağılımı, hypothetical azalması)
- **Şekil:** phold plot (varsa)

Rapor mevcut BacForge-tarzı motoru kullanır; modül yoksa/N/A ise ilgili bölüm dürüstçe atlanır
(sahte "SKIPPED" yok — V19'un kendi PASS mantığı korunur).

## 6. Test stratejisi

Mevcut sentetik-fixture desenini izler (gerçek araç gerektirmez):
- **Parser birim testleri:** her modülün parse fonksiyonu için örnek araç çıktısı fixture'ı
  (RaFAH TSV, AMRFinderPlus TSV, PhageTerm CSV, phold TSV) → beklenen JSON.
- **Modül dry-run:** araçsız ortamda modül WARNING/N/A ile dürüstçe döner, çökmez.
- **Faj-koşulluluk:** `is_phage` yardımcısı için pozitif/negatif testler.
- **Pipeline sırası:** `DEFAULT_MODULES` yeni sırayı içerir; e2e dry-run yeni modüllerle koşar.
- **Resume:** yeni modüller `is_done`/summary ile atlanır.
Hedef: mevcut 43 yeşil teste yeni testler eklenir, tümü yeşil kalır.

## 7. Gerçek veri doğrulaması

Aynı T7 kısa-okuma run'ında `--resume` ile V09–V13 eklenir (V00–V08 zaten bitmiş, atlanır):
```
conda install -n virusforge -c bioconda rafah amrfinderplus phageterm phold
amrfinder -u   # AMRFinderPlus DB
virusforge run <T7_sample> --resume --run-dir <mevcut_T7_run>
```
Beklenen biyoloji (T7 / Escherichia phage T7):
- V09: host = *Escherichia* (RaFAH)
- V11: T7'de AMR beklenmez (boş liste = geçerli PASS); virülans muhtemelen yok
- V12: T7 **DTR** (direct terminal repeat) beklenir — bilinen doğru sonuç
- V13: phold pharokka hypothetical'larının bir kısmını fonksiyona atar (unknown_after < unknown_before)

Sonuçlar dürüstçe raporlanır; T7 için bilinen doğrularla (özellikle V12 DTR) çapraz kontrol edilir.

## 8. Kapsam dışı (YAGNI / sonraki spec'ler)
- iPHoP tam DB indirme + doğrulama (opsiyonel bırakıldı; config ile açılır)
- abricate/VFDB çoklu-DB taraması (config-hook var, varsayılan kapalı)
- RNA-virüs yolu (V05 RNA yönlendirme, rnaviralSPAdes, VADR, iVar/LoFreq) → **M2-B ayrı spec**
- V10/V14–V18 (karşılaştırmalı/filo/görsel) → M3

## 9. Kabul kriterleri
1. V09/V11/V12/V13 modülleri M1 sözleşmesine uyar (8 klasör, summary, resume, N/A/WARNING dürüstlüğü).
2. Registry'ye 5 araç doğrulanmış repo/DOI/version_cmd ile eklenir.
3. config/default.yaml yeni anahtarları taşır; mevcut çalışan config bozulmaz.
4. Yeni pytest'ler + mevcut 43 test yeşil.
5. T7 `--resume` gerçek koşusu: V09–V13 çalışır, V12 DTR doğrulanır, rapor yeni tabloları içerir.
6. Her anlamlı durakta commit + push ([[feedback_kayit_al]]).
