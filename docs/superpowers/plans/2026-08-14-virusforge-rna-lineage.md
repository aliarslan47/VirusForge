# V12 RNA Soy/Klad Tayini (Pangolin + Nextclade) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** RNA konsensüs genomundan soy hattı (Pangolin PANGO) + klad (Nextclade) tayini yapan V12 modülünü ekle; DNA/faj'da NOT_APPLICABLE.

**Architecture:** V11 varyant modülüyle birebir aynı desen — RNA-only yeni modül, V02'nin ürettiği konsensüs FASTA'yı (`ctx.artifacts["V02"]["draft"]`) tüketir, iki aracı bağımsız/paralel çalıştırır (biri düşerse diğeri devam eder, sessiz-hata yok), sonuçları çift-dilli rapora yansıtır. Araçlar izole conda env'lerinde (`vf_pangolin`, `vf_nextclade`) `conda run` ile sarılır.

**Tech Stack:** Python 3, pytest, Pangolin (cov-lineages), Nextclade (nextstrain), conda, mevcut VirusForge modül/tools/report/i18n altyapısı.

**Spec:** `docs/superpowers/specs/2026-08-14-virusforge-rna-lineage-design.md`

## Global Constraints

- **İzolasyon:** `import bacforge` YOK; VirusForge tamamen bağımsız paket.
- **Sessiz-hata yasak:** her hata WARNING/log ile yüksek sesle; yutulan exception yok ([[feedback_gurultulu_hata]]).
- **Env izolasyonu:** araçlar `conda run -n <env>` (`_conda_wrap`) ile; çalışan `virusforge` env'i korunur.
- **RNA-only:** V12 yalnız `is_rna(ctx)` True iken çalışır; DNA/faj → `Status.NOT_APPLICABLE`.
- **Çift-dilli rapor:** TR varsayılan; EN çevirisi `report/i18n.py` sözlüğünden; soy/klad adları (BA.2.86 vb.) bilimsel terim → çevrilmez.
- **Kod stili:** mevcut modüllerin Türkçe docstring/yorum yoğunluğuna ve V11 desenine uy.
- **Modül kodu = "V12"**; rapor sırası V11 → V12 → V10.

---

### Task 1: Parser fonksiyonları (`parse_pangolin`, `parse_nextclade`)

Saf fonksiyonlar; dosyadan okur, sözlük döner. Önce bunlar çünkü araçsız test edilebilir.

**Files:**
- Create: `virusforge/modules/v12_lineage.py` (yalnız iki parser + import'lar bu task'ta)
- Test: `tests/test_v12_lineage.py`

**Interfaces:**
- Produces: `parse_pangolin(csv_path) -> dict` alanlar: `lineage, conflict, scorpio_call, qc_status, note, version, pango_version` (eksik sütun → "" veya None; dosya boş → `{}`).
- Produces: `parse_nextclade(tsv_path) -> dict` alanlar: `clade, nextclade_pango, qc_overall, total_substitutions, total_missing, total_aa_substitutions` (eksik → "" / None; dosya boş → `{}`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_v12_lineage.py
from pathlib import Path
from virusforge.modules.v12_lineage import parse_pangolin, parse_nextclade


def test_parse_pangolin(tmp_path):
    csv = tmp_path / "lineage_report.csv"
    csv.write_text(
        "taxon,lineage,conflict,ambiguity_score,scorpio_call,scorpio_support,"
        "scorpio_conflict,scorpio_notes,version,pangolin_version,scorpio_version,"
        "constellation_version,is_designated,qc_status,qc_notes,note\n"
        "sample,BA.2.86,0.0,,Omicron (BA.2-like),0.9,0.0,,PUSHER-v1.25,4.3.1,"
        "0.3.19,v0.1.12,True,pass,,Assigned from designation hash.\n")
    r = parse_pangolin(csv)
    assert r["lineage"] == "BA.2.86"
    assert r["scorpio_call"] == "Omicron (BA.2-like)"
    assert r["qc_status"] == "pass"
    assert r["pango_version"] == "4.3.1"
    assert "designation" in r["note"]


def test_parse_pangolin_missing_columns(tmp_path):
    csv = tmp_path / "min.csv"
    csv.write_text("taxon,lineage,qc_status\nsample,B.1.1.7,pass\n")
    r = parse_pangolin(csv)
    assert r["lineage"] == "B.1.1.7"
    assert r["scorpio_call"] == ""
    assert r["qc_status"] == "pass"


def test_parse_nextclade(tmp_path):
    tsv = tmp_path / "nextclade.tsv"
    tsv.write_text(
        "index\tseqName\tclade\tNextclade_pango\tqc.overallStatus\t"
        "totalSubstitutions\ttotalMissing\ttotalAminoacidSubstitutions\n"
        "0\tsample\t23I\tBA.2.86\tgood\t72\t305\t45\n")
    r = parse_nextclade(tsv)
    assert r["clade"] == "23I"
    assert r["nextclade_pango"] == "BA.2.86"
    assert r["qc_overall"] == "good"
    assert r["total_substitutions"] == 72
    assert r["total_missing"] == 305
    assert r["total_aa_substitutions"] == 45


def test_parse_nextclade_empty(tmp_path):
    tsv = tmp_path / "empty.tsv"
    tsv.write_text("index\tseqName\tclade\n")
    assert parse_nextclade(tsv) == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ali/VirusForge && python -m pytest tests/test_v12_lineage.py -q`
Expected: FAIL — `ModuleNotFoundError: virusforge.modules.v12_lineage` / import error.

- [ ] **Step 3: Write minimal implementation**

```python
# virusforge/modules/v12_lineage.py
"""V12 — Soy/Klad Tayini (RNA yolu, Faz 3).

RNA virüs konsensüs genomundan soy hattı (Pangolin PANGO) + klad (Nextclade) tayini.
V02'nin ürettiği konsensüs FASTA (`ctx.artifacts["V02"]["draft"]`) üzerinden. İki araç bağımsız
çalışır (biri düşse diğeri devam, sessiz-hata yok). DNA/faj yolunda veya konsensüs yoksa N/A.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .. import tools, util
from ..config import get
from ..module import Context, Module, ModuleResult, Status, is_rna, safe_run


def _int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def parse_pangolin(csv_path) -> dict:
    """Pangolin lineage_report.csv → tek örnek satırı özeti. Boş/başlıksız → {}."""
    p = Path(csv_path)
    if not p.exists():
        return {}
    with open(p, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return {}
    r = rows[0]
    return {
        "lineage": (r.get("lineage") or "").strip(),
        "conflict": (r.get("conflict") or "").strip(),
        "scorpio_call": (r.get("scorpio_call") or "").strip(),
        "qc_status": (r.get("qc_status") or "").strip(),
        "note": (r.get("note") or "").strip(),
        "version": (r.get("version") or "").strip(),
        "pango_version": (r.get("pangolin_version") or "").strip(),
    }


def parse_nextclade(tsv_path) -> dict:
    """Nextclade TSV → tek örnek satırı özeti. Veri satırı yoksa → {}."""
    p = Path(tsv_path)
    if not p.exists():
        return {}
    with open(p, newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if not rows:
        return {}
    r = rows[0]
    return {
        "clade": (r.get("clade") or "").strip(),
        "nextclade_pango": (r.get("Nextclade_pango") or "").strip(),
        "qc_overall": (r.get("qc.overallStatus") or "").strip(),
        "total_substitutions": _int(r.get("totalSubstitutions")),
        "total_missing": _int(r.get("totalMissing")),
        "total_aa_substitutions": _int(r.get("totalAminoacidSubstitutions")),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ali/VirusForge && python -m pytest tests/test_v12_lineage.py -q`
Expected: PASS (4 test).

- [ ] **Step 5: Commit**

```bash
git add virusforge/modules/v12_lineage.py tests/test_v12_lineage.py
git commit -m "feat(v12): pangolin+nextclade parser fonksiyonları"
```

---

### Task 2: Tool komut kurucular + registry kayıtları

**Files:**
- Modify: `virusforge/tools.py` (dosya sonuna iki fonksiyon)
- Modify: `virusforge/data/registry.yaml` (iki kayıt)
- Test: `tests/test_v12_lineage.py`

**Interfaces:**
- Produces: `tools.pangolin_cmd(consensus, out_csv, threads=4, conda_env=None, conda_bin="conda") -> list[str]`
- Produces: `tools.nextclade_run_cmd(consensus, dataset_dir, out_tsv, conda_env=None, conda_bin="conda") -> list[str]`
- Consumes: `tools._conda_wrap(cmd, conda_env, conda_bin, stream=False)` (mevcut).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_v12_lineage.py  (ekle)
from virusforge import tools
from virusforge import registry


def test_pangolin_cmd():
    cmd = tools.pangolin_cmd("cons.fa", "out.csv", threads=4, conda_env="vf_pangolin")
    assert cmd[:4] == ["conda", "run", "-n", "vf_pangolin"]
    assert "pangolin" in cmd
    assert "cons.fa" in cmd
    assert "--outfile" in cmd and "out.csv" in cmd


def test_nextclade_run_cmd():
    cmd = tools.nextclade_run_cmd("cons.fa", "db/sc2", "nc.tsv", conda_env="vf_nextclade")
    assert cmd[:4] == ["conda", "run", "-n", "vf_nextclade"]
    assert "nextclade" in cmd and "run" in cmd
    assert "-D" in cmd and "db/sc2" in cmd
    assert "--output-tsv" in cmd and "nc.tsv" in cmd
    assert "cons.fa" in cmd


def test_registry_has_lineage_tools():
    assert registry.tool("pangolin")["repo"]
    assert registry.tool("nextclade")["repo"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ali/VirusForge && python -m pytest tests/test_v12_lineage.py -q -k "cmd or registry"`
Expected: FAIL — `AttributeError: module 'virusforge.tools' has no attribute 'pangolin_cmd'`.

- [ ] **Step 3: Write minimal implementation**

`virusforge/tools.py` sonuna ekle:

```python
def pangolin_cmd(consensus, out_csv, threads=4, conda_env=None, conda_bin="conda"):
    """Pangolin PANGO soy tayini: pangolin <consensus.fa> --outfile <out.csv>."""
    return _conda_wrap(["pangolin", str(consensus), "--outfile", str(out_csv),
                        "-t", str(threads)], conda_env, conda_bin)


def nextclade_run_cmd(consensus, dataset_dir, out_tsv, conda_env=None, conda_bin="conda"):
    """Nextclade klad/mutasyon/QC: nextclade run -D <dataset_dir> --output-tsv <tsv> <consensus>."""
    return _conda_wrap(["nextclade", "run", "-D", str(dataset_dir),
                        "--output-tsv", str(out_tsv), str(consensus)], conda_env, conda_bin)
```

`virusforge/data/registry.yaml` sonuna ekle:

```yaml
pangolin:
  repo: https://github.com/cov-lineages/pangolin
  version_cmd: ["pangolin", "--version"]
  doi: "10.1038/s41564-020-0770-5"
nextclade:
  repo: https://github.com/nextstrain/nextclade
  version_cmd: ["nextclade", "--version"]
  doi: "10.21105/joss.03773"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ali/VirusForge && python -m pytest tests/test_v12_lineage.py -q -k "cmd or registry"`
Expected: PASS (3 test).

- [ ] **Step 5: Commit**

```bash
git add virusforge/tools.py virusforge/data/registry.yaml tests/test_v12_lineage.py
git commit -m "feat(v12): pangolin/nextclade komut kurucu + registry kaydı"
```

---

### Task 3: V12Lineage modülü (run + N/A guard'ları)

**Files:**
- Modify: `virusforge/modules/v12_lineage.py` (sınıf ekle)
- Test: `tests/test_v12_lineage.py`

**Interfaces:**
- Produces: `class V12Lineage(Module)` — `code = "V12"`, `name = "Soy/Klad Tayini"`. `run(ctx) -> ModuleResult`. `metrics` yapısı: `{"pangolin": {...}, "nextclade": {...}, "problems": [...]}`. Konsensüs yok veya DNA → `Status.NOT_APPLICABLE`. Her iki araç düşerse → `Status.WARNING`. Kısmi başarı → `WARNING`, tam → `PASS`.
- Consumes: `ctx.artifacts["V02"]["draft"]` (konsensüs FASTA), `is_rna(ctx)`, `tools.pangolin_cmd`, `tools.nextclade_run_cmd`, `parse_pangolin`, `parse_nextclade`, `safe_run`.
- `ctx.results["V12"] = metrics` (rapora girer).

Not: Module tabanının `code`/`name` sınıf attribute'ları, `make_dirs`, `write_summary`, `module_dir` metodları V11 ile aynı imzada kullanılır — V11'i (`virusforge/modules/v11_variants.py`) şablon al.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_v12_lineage.py  (ekle)
import types
from virusforge.modules.v12_lineage import V12Lineage
from virusforge.module import Status


def _ctx(tmp_path, molecule="rna", draft=True):
    """Minimal sahte Context: run_dir + cfg + artifacts + results."""
    cons = tmp_path / "cons.fa"
    if draft:
        cons.write_text(">sample\n" + "ACGT" * 50 + "\n")
    cfg = {"general": {"molecule": molecule},
           "tools": {"pangolin": {"conda_env": "vf_pangolin"},
                     "nextclade": {"conda_env": "vf_nextclade",
                                   "dataset_dir": str(tmp_path / "db")}}}
    return types.SimpleNamespace(
        run_dir=tmp_path, cfg=cfg,
        artifacts={"V02": {"draft": str(cons)} if draft else {}},
        results={},
    )


def test_v12_not_applicable_dna(tmp_path):
    res = V12Lineage().run(_ctx(tmp_path, molecule="dna"))
    assert res.status == Status.NOT_APPLICABLE


def test_v12_not_applicable_no_consensus(tmp_path):
    res = V12Lineage().run(_ctx(tmp_path, molecule="rna", draft=False))
    assert res.status == Status.NOT_APPLICABLE


def test_v12_runs_both_tools(tmp_path, monkeypatch):
    from virusforge.modules import v12_lineage as mod

    calls = []

    def fake_safe_run(cmd, log_path):
        calls.append(cmd)
        # pangolin CSV / nextclade TSV çıktısını simüle et
        if "pangolin" in cmd:
            out = [c for c in cmd if str(c).endswith(".csv")][0]
            Path(out).write_text("taxon,lineage,qc_status\nsample,BA.2.86,pass\n")
        else:
            idx = cmd.index("--output-tsv")
            Path(cmd[idx + 1]).write_text(
                "index\tseqName\tclade\tNextclade_pango\tqc.overallStatus\n0\ts\t23I\tBA.2.86\tgood\n")
        return None

    monkeypatch.setattr(mod, "safe_run", fake_safe_run)
    res = V12Lineage().run(_ctx(tmp_path, molecule="rna"))
    assert res.status == Status.PASS
    assert res.metrics["pangolin"]["lineage"] == "BA.2.86"
    assert res.metrics["nextclade"]["clade"] == "23I"
    assert len(calls) == 2  # iki araç da çağrıldı
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ali/VirusForge && python -m pytest tests/test_v12_lineage.py -q -k "v12"`
Expected: FAIL — `ImportError: cannot import name 'V12Lineage'`.

- [ ] **Step 3: Write minimal implementation**

`virusforge/modules/v12_lineage.py` içine (parser'ların altına) ekle:

```python
class V12Lineage(Module):
    code = "V12"
    name = "Soy/Klad Tayini"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        if not is_rna(ctx):
            m = {"note": "DNA/faj yolu — soy/klad tayini uygulanmadı"}
            return ModuleResult(Status.NOT_APPLICABLE,
                                self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m), m)
        v02 = ctx.artifacts.get("V02", {}) or {}
        cons = v02.get("draft")
        if not cons or not Path(cons).exists():
            m = {"note": "konsensüs genom yok (de novo/referanssız) — soy tayini yapılamaz"}
            return ModuleResult(Status.NOT_APPLICABLE,
                                self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m), m)

        metrics: dict = {}
        problems: list[str] = []
        native = dirs["03_native_outputs"]

        # Pangolin (izole vf_pangolin env)
        pcsv = native / "lineage_report.csv"
        err = safe_run(tools.pangolin_cmd(cons, pcsv,
                                          get(ctx.cfg, "tools.pangolin.threads", 4),
                                          get(ctx.cfg, "tools.pangolin.conda_env", None),
                                          get(ctx.cfg, "tools.pangolin.conda_bin", "conda")),
                       dirs["07_logs"] / "pangolin.log")
        pang = parse_pangolin(pcsv)
        if pang:
            metrics["pangolin"] = pang
        elif err:
            problems.append(f"Pangolin: {err[:120]}")
        else:
            problems.append("Pangolin: soy atanmadı")

        # Nextclade (izole vf_nextclade env)
        dataset_dir = get(ctx.cfg, "tools.nextclade.dataset_dir", "")
        if not dataset_dir or not Path(dataset_dir).exists():
            problems.append(f"Nextclade: dataset dizini yok ({dataset_dir}); "
                            "`nextclade dataset get` ile indir")
        else:
            ntsv = native / "nextclade.tsv"
            err = safe_run(tools.nextclade_run_cmd(cons, dataset_dir, ntsv,
                                                   get(ctx.cfg, "tools.nextclade.conda_env", None),
                                                   get(ctx.cfg, "tools.nextclade.conda_bin", "conda")),
                           dirs["07_logs"] / "nextclade.log")
            nc = parse_nextclade(ntsv)
            if nc:
                metrics["nextclade"] = nc
            elif err:
                problems.append(f"Nextclade: {err[:120]}")
            else:
                problems.append("Nextclade: klad atanmadı")

        if "pangolin" not in metrics and "nextclade" not in metrics:
            metrics["error"] = "; ".join(problems) or "soy/klad üretilmedi"
            return ModuleResult(Status.WARNING,
                                self.write_summary(ctx.run_dir, Status.WARNING, metrics), metrics)
        if problems:
            metrics["problems"] = problems
        (dirs["04_standardized"] / "lineage.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False))
        ctx.results[self.code] = metrics
        status = Status.PASS if not problems else Status.WARNING
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, metrics), metrics)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ali/VirusForge && python -m pytest tests/test_v12_lineage.py -q`
Expected: PASS (tüm V12 testleri).

- [ ] **Step 5: Commit**

```bash
git add virusforge/modules/v12_lineage.py tests/test_v12_lineage.py
git commit -m "feat(v12): V12Lineage modülü (pangolin+nextclade, N/A guard'ları)"
```

---

### Task 4: Pipeline'a V12 bağla + config default'ları

**Files:**
- Modify: `virusforge/pipeline.py` (import + `DEFAULT_MODULES`)
- Modify: `virusforge/config.py` (varsayılan `tools.pangolin` / `tools.nextclade` — mevcut default deseni neyse ona uy)
- Test: `tests/` (e2e dryrun testi — mevcut e2e testine V12 sıra kontrolü ekle veya yeni)

**Interfaces:**
- Consumes: `V12Lineage`.
- Produces: `DEFAULT_MODULES` sırası `… V08Amr, V09Comparative, V11VariantCall, V12Lineage, V10Report`.

Not: `config.py`'da `tools.rna`/`tools.lofreq` default'larının nasıl tanımlandığını (Task başlangıcında) `grep -n "pangolin\|lofreq\|def get\|DEFAULTS\|setdefault" virusforge/config.py` ile teyit et; aynı mekanizmayla `tools.pangolin.conda_env=vf_pangolin`, `tools.nextclade.conda_env=vf_nextclade`, `tools.nextclade.dataset="sars-cov-2"`, `tools.nextclade.dataset_dir="databases/nextclade/sars-cov-2"` ekle. Eğer default'lar kod içi `get(cfg, key, default)` ile veriliyorsa (yaml default dosyası yoksa) ayrı ekleme gerekmez — modül zaten fallback veriyor; bu durumda bu adımı atla ve sadece pipeline bağla.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_v12_lineage.py  (ekle)
def test_v12_in_default_pipeline_order():
    from virusforge.pipeline import DEFAULT_MODULES
    from virusforge.modules.v11_variants import V11VariantCall
    from virusforge.modules.v12_lineage import V12Lineage
    from virusforge.modules.v10_report import V10Report
    names = [m.__name__ if isinstance(m, type) else type(m).__name__ for m in DEFAULT_MODULES]
    assert "V12Lineage" in names
    # V11 → V12 → V10 sırası
    assert names.index("V11VariantCall") < names.index("V12Lineage") < names.index("V10Report")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ali/VirusForge && python -m pytest tests/test_v12_lineage.py -q -k "default_pipeline"`
Expected: FAIL — `V12Lineage not in names`.

- [ ] **Step 3: Write minimal implementation**

`virusforge/pipeline.py`:

```python
from .modules.v12_lineage import V12Lineage
```

`DEFAULT_MODULES` listesinde `V11VariantCall,` ile `V10Report` arasına `V12Lineage,` ekle:

```python
    V08Amr, V09Comparative, V11VariantCall, V12Lineage, V10Report,
```

(Config default'ları için yukarıdaki Not'a göre gerekiyorsa `config.py`'a ekle; gerekmiyorsa atla.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ali/VirusForge && python -m pytest tests/test_v12_lineage.py -q -k "default_pipeline"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add virusforge/pipeline.py virusforge/config.py tests/test_v12_lineage.py
git commit -m "feat(v12): pipeline DEFAULT_MODULES'a V12 (V11→V12→V10) + config default"
```

---

### Task 5: Rapor entegrasyonu (sıra + references + render bölümü + i18n)

**Files:**
- Modify: `virusforge/modules/v10_report.py:11` (`_ORDER`)
- Modify: `virusforge/report/references.py` (`TOOL_REFERENCES` + `PIPELINE_STEPS`)
- Modify: `virusforge/report/render.py` (V11 bölümünden sonra V12 bölümü)
- Modify: `virusforge/report/i18n.py` (V12 EN anahtarları)
- Test: `tests/test_v12_lineage.py`

**Interfaces:**
- Consumes: `M["V12"]` metrics (`pangolin`, `nextclade`), `section()`, `table()`, `L()`, `_esc()` (render.py mevcut helper'ları).
- Produces: raporda "V12 — Soy/Klad Tayini" bölümü (TR) / "Lineage / Clade Assignment" (EN).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_v12_lineage.py  (ekle)
from virusforge.report.render import render_html


def _report_with_v12():
    return {
        "sample": "sample", "run_dir": ".", "modules": {},
        "results": {
            "V12": {"pangolin": {"lineage": "BA.2.86", "qc_status": "pass",
                                 "scorpio_call": "", "conflict": "0.0",
                                 "note": "", "pango_version": "4.3.1"},
                    "nextclade": {"clade": "23I", "nextclade_pango": "BA.2.86",
                                  "qc_overall": "good", "total_substitutions": 72,
                                  "total_missing": 305, "total_aa_substitutions": 45}},
        },
    }


def test_render_v12_tr():
    html = render_html(_report_with_v12(), lang="tr")
    assert "Soy/Klad" in html or "Soy Hattı" in html
    assert "BA.2.86" in html      # bilimsel terim korunur
    assert "23I" in html


def test_render_v12_en_no_raw_tr():
    html = render_html(_report_with_v12(), lang="en")
    assert "BA.2.86" in html
    # EN raporda ham TR başlık sızmamalı
    assert "Soy/Klad Tayini" not in html
    assert "Lineage" in html or "Clade" in html
```

Not: `render_html`'in beklediği `report` sözlük yapısını (modules/results anahtarları) Task başında mevcut bir geçen testten (`grep -n "render_html(" tests/`) doğrula; yukarıdaki iskeleti gerçeğe uydur.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/ali/VirusForge && python -m pytest tests/test_v12_lineage.py -q -k "render_v12"`
Expected: FAIL — "Soy/Klad" HTML'de yok.

- [ ] **Step 3: Write minimal implementation**

(a) `virusforge/modules/v10_report.py:11` — `_ORDER` sonuna `"V12"` ekle:

```python
_ORDER = ["V00", "V01", "V02", "V03", "V04", "V05", "V06", "V07", "V08", "V09", "V11", "V12"]
```

(b) `virusforge/report/references.py` — `TOOL_REFERENCES` listesine ekle:

```python
    ("pangolin", "Pangolin", "SARS-CoV-2 PANGO soy tayini", "https://github.com/cov-lineages/pangolin", "10.1038/s41564-020-0770-5"),
    ("nextclade", "Nextclade", "Klad/mutasyon/QC (çok-patojen)", "https://github.com/nextstrain/nextclade", "10.21105/joss.03773"),
```

`PIPELINE_STEPS` içinde `("V11", …)` ile `("V10", …)` arasına ekle:

```python
    ("V12", "Lineage / Clade Assignment", "Pangolin + Nextclade"),
```

(c) `virusforge/report/render.py` — V11 bölümünü ekleyen `p.append(section("V11", …))` satırından hemen sonra:

```python
    # V12 — Soy/Klad Tayini (RNA yolu; DNA'da NOT_APPLICABLE → gri pill otomatik)
    lin = M.get("V12", {}) or {}
    if lin.get("pangolin") or lin.get("nextclade"):
        v12body = ""
        pg = lin.get("pangolin") or {}
        if pg:
            v12body += table(L("Pangolin — PANGO soy hattı"), [L("Metrik"), L("Değer")], [
                [L("Soy hattı"), _esc(pg.get("lineage") or "—")],
                [L("Scorpio"), _esc(pg.get("scorpio_call") or "—")],
                [L("Conflict"), _esc(pg.get("conflict") or "—")],
                [L("QC"), _esc(pg.get("qc_status") or "—")],
                [L("Not"), _esc(pg.get("note") or "—")],
                [L("Sürüm"), _esc(pg.get("pango_version") or "—")],
            ])
        nc = lin.get("nextclade") or {}
        if nc:
            v12body += table(L("Nextclade — klad & mutasyon"), [L("Metrik"), L("Değer")], [
                [L("Klad"), _esc(nc.get("clade") or "—")],
                [L("Nextclade PANGO"), _esc(nc.get("nextclade_pango") or "—")],
                [L("QC"), _esc(nc.get("qc_overall") or "—")],
                [L("Toplam substitüsyon"), _esc(nc.get("total_substitutions"))],
                [L("Eksik (N)"), _esc(nc.get("total_missing"))],
                [L("AA substitüsyon"), _esc(nc.get("total_aa_substitutions"))],
            ])
        p.append(section("V12", L("Soy/Klad Tayini"), v12body))
```

(d) `virusforge/report/i18n.py` — EN sözlüğüne ekle (mevcut sözlük deseniyle):

```python
    "Soy/Klad Tayini": "Lineage / Clade Assignment",
    "Pangolin — PANGO soy hattı": "Pangolin — PANGO lineage",
    "Nextclade — klad & mutasyon": "Nextclade — clade & mutations",
    "Soy hattı": "Lineage",
    "Scorpio": "Scorpio",
    "Conflict": "Conflict",
    "Not": "Note",
    "Klad": "Clade",
    "Nextclade PANGO": "Nextclade PANGO",
    "Toplam substitüsyon": "Total substitutions",
    "Eksik (N)": "Missing (N)",
    "AA substitüsyon": "Amino-acid substitutions",
```

(Zaten mevcut olanları — "Metrik", "Değer", "QC", "Sürüm" — tekrar ekleme; `grep` ile teyit et.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/ali/VirusForge && python -m pytest tests/test_v12_lineage.py -q`
Expected: PASS (tüm dosya). Sonra tam suite: `python -m pytest -q` — 154 önceki + yeni testler yeşil.

- [ ] **Step 5: Commit**

```bash
git add virusforge/modules/v10_report.py virusforge/report/references.py virusforge/report/render.py virusforge/report/i18n.py tests/test_v12_lineage.py
git commit -m "feat(v12): rapor entegrasyonu (sıra+references+render+i18n tr/en)"
```

---

### Task 6: Env kurulumu + SARS-CoV-2 gerçek doğrulama

Bu task kod değil; izole env'leri kurar ve V12'yi gerçek konsensüs üzerinde çalıştırır. Deliverable = geçen gerçek koşu + güncellenmiş DURUM/bellek.

**Files:**
- Modify: `DURUM.md` (V12 bölümü)
- Modify: bellek `virusforge-project.md` + `MEMORY.md` satırı

- [ ] **Step 1: Env'leri kur**

```bash
conda create -y -n vf_pangolin -c bioconda -c conda-forge pangolin pangolin-data
conda create -y -n vf_nextclade -c bioconda -c conda-forge nextclade
conda run -n vf_nextclade nextclade dataset get --name sars-cov-2 --output-dir /home/ali/VirusForge/databases/nextclade/sars-cov-2
```

Doğrula:
```bash
conda run -n vf_pangolin pangolin --version
conda run -n vf_nextclade nextclade --version
```
Expected: sürüm satırları (çöp değil).

- [ ] **Step 2: Mevcut SARS-CoV-2 konsensüsünü bul**

```bash
find /home/ali/VirusForge/runs -name "draft_viral_genome.fasta" -path "*ERR11728561*" 2>/dev/null
```
Faz 1 RNA run'ının V02 `04_standardized/draft_viral_genome.fasta`'sı. Yoksa `--resume` ile Faz 1'i tekrar üret (spec'teki komut).

- [ ] **Step 3: V12'yi resume ile çalıştır**

```bash
cd /home/ali/VirusForge && conda run -n virusforge python -m virusforge run \
  --molecule rna --resume runs/<ERR11728561 run dizini>
```
Beklenen: V12 PASS (veya QC nedeniyle unassigned → dürüst raporlanır); `report.html` + `report_en.html` içinde "V12 — Soy/Klad Tayini" bölümü; Pangolin soyu + Nextclade kladı; DNA koşusunda N/A pill korunur.

- [ ] **Step 4: DNA regresyon — N/A doğrula**

```bash
cd /home/ali/VirusForge && conda run -n virusforge python -m virusforge run --resume runs/<T7 hybrid run>
```
Beklenen: V12 NOT_APPLICABLE (gri pill), T7 raporu bozulmadan üretilir.

- [ ] **Step 5: Tam suite + commit**

```bash
cd /home/ali/VirusForge && conda run -n virusforge python -m pytest -q
git add -A && git commit -m "test(v12): SARS-CoV-2 gerçek doğrulama + DURUM/bellek güncel" && git push
```
Expected: tüm testler yeşil; DURUM.md V12 bölümü + bellek güncel.

---

## Self-Review

**1. Spec coverage:**
- Pangolin + Nextclade ikisi de → Task 2/3 ✅
- SARS-CoV-2 öncelikli + dataset config → Task 4/6 ✅
- Ayrı env (vf_pangolin/vf_nextclade) → Task 6 + config ✅
- Girdi = V02 konsensüs draft, yoksa N/A → Task 3 ✅
- Yerleşim V12, V11→V12→V10 → Task 4/5 ✅
- Config/registry → Task 2/4 ✅
- Rapor çift-dilli + N/A pill → Task 5 ✅
- Hata yönetimi (kısmi/tam başarısız, sessiz-hata yok) → Task 3 ✅
- Testler (parse/cmd/dispatch/N/A/render/e2e) → Task 1-5 ✅
- Env kurulum + gerçek doğrulama → Task 6 ✅

**2. Placeholder scan:** Somut kod/test her adımda mevcut; "TBD" yok. Task 4/5'teki "grep ile teyit et" notları gerçek belirsizliği (mevcut config/report yapısının runtime detayı) çözmek için yönlendirme — executor mevcut kalıbı okuyup uygular.

**3. Type consistency:** `parse_pangolin`/`parse_nextclade` alan adları Task 1'de tanımlı, Task 3 (metrics) ve Task 5 (render) aynı anahtarları kullanır (`lineage/scorpio_call/qc_status/note/pango_version`, `clade/nextclade_pango/qc_overall/total_substitutions/total_missing/total_aa_substitutions`). `metrics["pangolin"]`/`metrics["nextclade"]` sözlük yapısı Task 3↔5 tutarlı. `V12Lineage.code="V12"` her yerde tutarlı.
