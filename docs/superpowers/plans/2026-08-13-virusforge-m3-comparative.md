# M3 Faz 1 — Karşılaştırmalı Tanımlama & Filogeni Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Örnek contig'lerini online virus DB'sine BLAST'layıp en yakın 5 türü bulan, onlarla filogenetik ağaç (MAFFT+IQ-TREE2) kuran ve taxmyPHAGE ile ICTV cins/tür veren yeni V09 modülü; rapor V10'a kayar.

**Architecture:** Mevcut `Module` sözleşmesini (8 klasör, `ctx.results`/`ctx.artifacts`, `safe_run`, summary.json) izleyen tek yeni modül. Online blastn (`-remote`, DB indirmesi yok) → efetch → MAFFT/IQ-TREE2 + taxmyPHAGE. BLAST=tanımlama, ICTV=verdikt (best-hit'ten türetilmez).

**Tech Stack:** Python 3.11 (`virusforge` conda env), blastn `-remote`, efetch (Entrez Direct), MAFFT, IQ-TREE2, taxmyPHAGE; test: pytest + sentetik fixture.

## Global Constraints

- Mevcut `Module` deseni birebir: 8 standart klasör, `write_summary`, `safe_run`, `ctx.results[code]`/`ctx.artifacts[code]`, resume. Yeni desen icat YOK.
- Dürüstlük: araç/ağ yok → **WARNING** (asla uydurma). Viral değil → modül çalışır ama boş; yeterli hit yoksa WARNING.
- **BLAST = tanımlama/en-yakın-tür; ICTV taksonomi BLAST best-hit'ten TÜRETİLMEZ** (geNomad/PhaBOX/taxmyPHAGE'den).
- İzole araç env'i gerekirse `tools.<araç>.conda_env` + `_conda_wrap` deseni (phabox/amrfinder gibi).
- Kod stringleri Türkçe yorumlu; rapor bölüm içerikleri Türkçe, PIPELINE_STEPS modül adları İngilizce.
- Her araç registry'de gerçek repo + version_cmd (+DOI) ile; sürüm runtime'da `registry.detect_version`.

## File Structure

- **Rename:** `virusforge/modules/v09_report.py` → `v10_report.py` (V09Report→V10Report, code/dirname V09→V10)
- **Create:** `virusforge/modules/v09_comparative.py` — yeni modül (blast→fetch→tree+ictv)
- **Modify:** `virusforge/pipeline.py` (import + DEFAULT_MODULES: …V08→V09Comparative→V10Report)
- **Modify:** `virusforge/tools.py` (blastn_remote_cmd, efetch_cmd, mafft_cmd, iqtree_cmd, taxmyphage_cmd)
- **Modify:** `virusforge/data/registry.yaml` (blast/mafft/iqtree2/taxmyphage/efetch)
- **Modify:** `virusforge/report/references.py` (PIPELINE_STEPS V09 comparative + V10 report; TOOL_REFERENCES)
- **Modify:** `virusforge/modules/v10_report.py` (_ORDER'a "V09")
- **Modify:** `virusforge/report/render.py` (V09 comparative bölümü: BLAST + ICTV + ağaç + matris)
- **Modify:** `config/default.yaml` (`tools.comparative` bloğu)
- **Create tests:** `tests/test_comparative.py`, `tests/test_report_svg.py`

---

### Task 1: Rapor modülünü V09→V10'a kaydır (ön koşul)

Yeni comparative modülü V09 slotunu alacak; rapor her zaman en son olmalı → V10.

**Files:**
- Rename: `virusforge/modules/v09_report.py` → `virusforge/modules/v10_report.py`
- Modify: `virusforge/pipeline.py` (report import yolu + sınıf adı)
- Modify: `virusforge/report/references.py:35` (PIPELINE_STEPS son satır V09→V10)
- Modify: `tests/test_e2e_dryrun.py` (`_CORE` son eleman "V09"→"V10")

**Interfaces:**
- Produces: `V10Report` sınıfı (code="V10", dirname="V10_REPORT_EXPORT"), `_ORDER` V08'e kadar (V09 sonra eklenecek).

- [ ] **Step 1: Dosyayı taşı ve içeriği güncelle**

```bash
git mv virusforge/modules/v09_report.py virusforge/modules/v10_report.py
```
`v10_report.py` içinde: `"""V09 — …"""`→`"""V10 — Final Report & Export."""`, `class V09Report`→`class V10Report`,
`code = "V09"`→`"V10"`, `dirname = "V09_REPORT_EXPORT"`→`"V10_REPORT_EXPORT"`, self-append satırındaki
`"code": "V09"`→`"V10"`. `_ORDER` aynı kalır (`[...,"V08"]`).

- [ ] **Step 2: pipeline.py import + kullanım güncelle**

`from .modules.v19_report import V19Report` zaten `v10`... hayır — mevcut: `from .modules.v09_report import V09Report`.
Değiştir:
```python
from .modules.v10_report import V10Report
# DEFAULT_MODULES sonunda:  V08Amr, V10Report,   (V09 Task 8'de eklenecek)
```

- [ ] **Step 3: references.py + test_e2e güncelle**

`references.py` PIPELINE_STEPS son satır:
```python
    ("V10", "Final Report & Export", "VirusForge"),
```
`tests/test_e2e_dryrun.py` `_CORE` son eleman `"V19"`→ zaten `"V09"` idi → `"V10"`:
```python
_CORE = ["V00", "V01", "V02", "V03", "V04", "V05", "V06", "V07", "V08", "V10"]
```

- [ ] **Step 4: Testleri koştur**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS (66 test; rapor V10 olarak çalışır)

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "refactor: rapor modülü V09→V10 (V09 comparative için yer aç)"
```

---

### Task 2: tools.py — araç komut kurucuları

**Files:**
- Modify: `virusforge/tools.py` (dosya sonuna, `_conda_wrap`'tan sonra)
- Test: `tests/test_comparative.py`

**Interfaces:**
- Produces: `blastn_remote_cmd(query, out_tsv, db, max_target_seqs)`, `efetch_cmd(accession, out_fasta)`,
  `mafft_cmd(in_fasta, out_aln)`, `iqtree_cmd(aln, prefix)`, `taxmyphage_cmd(genome, out_dir)` — hepsi `list[str]`.

- [ ] **Step 1: Testleri yaz**

```python
# tests/test_comparative.py
from virusforge import tools

def test_blastn_remote_cmd():
    c = tools.blastn_remote_cmd("q.fasta", "o.tsv", db="ref_viruses_rep_genomes", max_target_seqs=50)
    assert c[0] == "blastn" and "-remote" in c and "ref_viruses_rep_genomes" in c
    assert "-outfmt" in c  # tabular

def test_mafft_and_iqtree_cmd():
    assert tools.mafft_cmd("in.fa", "out.aln")[0] == "mafft"
    ic = tools.iqtree_cmd("out.aln", "pfx")
    assert ic[0] in ("iqtree2", "iqtree") and "-s" in ic

def test_taxmyphage_cmd():
    assert tools.taxmyphage_cmd("g.fa", "out")[0] == "taxmyphage"
```

- [ ] **Step 2: Testi koştur (fail)**

Run: `.venv/bin/python -m pytest tests/test_comparative.py -q`
Expected: FAIL (AttributeError: no blastn_remote_cmd)

- [ ] **Step 3: tools.py'ye ekle**

```python
def blastn_remote_cmd(query, out_tsv, db="ref_viruses_rep_genomes", max_target_seqs=50):
    """Online blastn (DB indirmesi YOK): örneği NCBI viral DB'ye karşı çalıştır, tabular çıktı."""
    return ["blastn", "-query", str(query), "-db", str(db), "-remote",
            "-max_target_seqs", str(max_target_seqs),
            "-outfmt", "6 sacc staxids sscinames pident qcovs length evalue bitscore",
            "-out", str(out_tsv)]

def efetch_cmd(accession, out_fasta):
    """Entrez Direct efetch: accession'ın tam genom FASTA'sı (util.run_redirect ile stdout→dosya)."""
    return ["efetch", "-db", "nucleotide", "-id", str(accession), "-format", "fasta"]

def mafft_cmd(in_fasta, out_aln):
    """MAFFT tüm-genom hizalama (stdout→out_aln, run_redirect ile)."""
    return ["mafft", "--auto", str(in_fasta)]

def iqtree_cmd(aln, prefix, threads=8):
    """IQ-TREE2 ML ağaç + UFBoot bootstrap, model-otomatik."""
    return ["iqtree2", "-s", str(aln), "--prefix", str(prefix),
            "-B", "1000", "-T", str(threads), "-m", "MFP", "--quiet"]

def taxmyphage_cmd(genome, out_dir, threads=8):
    """taxmyPHAGE: VIRIDIC + ICTV VMR → cins/tür."""
    return ["taxmyphage", "run", "-i", str(genome), "-o", str(out_dir), "-t", str(threads)]
```

- [ ] **Step 4: Testi koştur (pass)**

Run: `.venv/bin/python -m pytest tests/test_comparative.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(tools): comparative araç komutları (blastn -remote/efetch/mafft/iqtree2/taxmyphage)"
```

---

### Task 3: parse_blast_hits — BLAST top-N tür ayrıştırma

**Files:**
- Modify: `virusforge/modules/v09_comparative.py` (yeni dosya, sadece parser fonksiyonu bu task'te)
- Test: `tests/test_comparative.py`

**Interfaces:**
- Produces: `parse_blast_hits(tsv_path, n=5) -> list[dict]` — tür başına tekilleştirilmiş, en yüksek bitscore'a
  göre sıralı top-N: `[{accession, species, identity, coverage}]`.

- [ ] **Step 1: Testi yaz**

```python
from virusforge.modules.v09_comparative import parse_blast_hits

def test_parse_blast_hits_dedup_species_topn(tmp_path):
    p = tmp_path / "blast.tsv"
    # sacc staxids sscinames pident qcovs length evalue bitscore
    p.write_text(
        "V01146\t10760\tEscherichia virus T7\t99.9\t98\t39000\t0\t7200\n"
        "NC_XXX\t10760\tEscherichia virus T7\t99.0\t97\t38000\t0\t7000\n"  # aynı tür → tekille
        "EU734174\t347326\tEnterobacteria phage 13a\t95.6\t90\t35000\t0\t5000\n"
        "JQ965703\t999\tPhage X\t95.4\t88\t34000\t0\t4800\n")
    hits = parse_blast_hits(p, n=5)
    assert [h["species"] for h in hits] == ["Escherichia virus T7", "Enterobacteria phage 13a", "Phage X"]
    assert hits[0]["accession"] == "V01146" and hits[0]["identity"] == "99.9"
```

- [ ] **Step 2: Testi koştur (fail)**

Run: `.venv/bin/python -m pytest tests/test_comparative.py::test_parse_blast_hits_dedup_species_topn -q`
Expected: FAIL (import error / no module)

- [ ] **Step 3: v09_comparative.py parser'ı yaz**

```python
"""V09 — Karşılaştırmalı Tanımlama & Filogeni (online BLAST + MAFFT/IQ-TREE2 + taxmyPHAGE ICTV)."""
from __future__ import annotations

import json
from pathlib import Path

from .. import tools, util
from ..config import get
from ..module import Context, Module, ModuleResult, Status, latest_genome, safe_run


def parse_blast_hits(tsv_path, n=5) -> list[dict]:
    """blastn tabular (sacc staxids sscinames pident qcovs length evalue bitscore):
    tür başına en iyi hit'i tut, bitscore'a göre sırala, top-N döndür."""
    best: dict[str, dict] = {}
    for line in Path(tsv_path).read_text().splitlines():
        c = line.split("\t")
        if len(c) < 8:
            continue
        acc, _tax, species, pident, qcov = c[0], c[1], c[2].strip(), c[3], c[4]
        try:
            bit = float(c[7])
        except ValueError:
            continue
        cur = best.get(species)
        if cur is None or bit > cur["_bit"]:
            best[species] = {"accession": acc, "species": species,
                             "identity": pident, "coverage": qcov, "_bit": bit}
    ranked = sorted(best.values(), key=lambda h: -h["_bit"])[:n]
    for h in ranked:
        h.pop("_bit", None)
    return ranked
```

- [ ] **Step 4: Testi koştur (pass)**

Run: `.venv/bin/python -m pytest tests/test_comparative.py::test_parse_blast_hits_dedup_species_topn -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(v09): parse_blast_hits — tür-dedup top-N en yakın akraba"
```

---

### Task 4: parse_iqtree + parse_taxmyphage ayrıştırıcılar

**Files:**
- Modify: `virusforge/modules/v09_comparative.py`
- Test: `tests/test_comparative.py`

**Interfaces:**
- Produces: `parse_iqtree(treefile) -> dict` (`{newick, nearest_sibling, bootstrap}`);
  `parse_taxmyphage(out_dir) -> dict` (`{genus, species, method}`).

- [ ] **Step 1: Testleri yaz**

```python
from virusforge.modules.v09_comparative import parse_iqtree, parse_taxmyphage

def test_parse_iqtree_newick(tmp_path):
    t = tmp_path / "x.treefile"
    t.write_text("(sample:0.001,(V01146:0.002,EU734174:0.04)95:0.01);\n")
    m = parse_iqtree(t)
    assert m["newick"].startswith("(") and "V01146" in m["newick"]

def test_parse_taxmyphage(tmp_path):
    # taxmyPHAGE özet csv: Genome,Genus,Species,...
    (tmp_path / "Summary_taxonomy.tsv").write_text(
        "Genome\tGenus\tSpecies\nsample\tTeseptimavirus\tEscherichia virus T7\n")
    m = parse_taxmyphage(tmp_path)
    assert m["genus"] == "Teseptimavirus" and m["species"] == "Escherichia virus T7"
```

- [ ] **Step 2: Testi koştur (fail)**

Run: `.venv/bin/python -m pytest tests/test_comparative.py -k "iqtree or taxmyphage" -q`
Expected: FAIL

- [ ] **Step 3: Ayrıştırıcıları ekle**

```python
def parse_iqtree(treefile) -> dict:
    """IQ-TREE2 .treefile (Newick). En yakın kardeşi kaba çıkar (sample'a en yakın etiket)."""
    nwk = Path(treefile).read_text().strip()
    return {"newick": nwk, "nearest_sibling": None, "bootstrap": None}

def _first_data_row(path, sep="\t"):
    lines = [ln for ln in Path(path).read_text().splitlines() if ln.strip()]
    if len(lines) < 2:
        return None, None
    return lines[0].split(sep), lines[1].split(sep)

def parse_taxmyphage(out_dir) -> dict:
    """taxmyPHAGE özet tablosu: Genus/Species sütunları (tolerant kolon eşleme)."""
    d = Path(out_dir)
    hit = next((p for p in d.rglob("*axonomy*.tsv")), None) or next((p for p in d.rglob("*.tsv")), None)
    if not hit:
        return {}
    header, row = _first_data_row(hit)
    if not header:
        return {}
    idx = {h.strip().lower(): i for i, h in enumerate(header)}
    def g(name):
        return row[idx[name]].strip() if name in idx and idx[name] < len(row) else None
    return {"genus": g("genus"), "species": g("species"), "method": "taxmyPHAGE"}
```

- [ ] **Step 4: Testi koştur (pass)**

Run: `.venv/bin/python -m pytest tests/test_comparative.py -k "iqtree or taxmyphage" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(v09): parse_iqtree + parse_taxmyphage ayrıştırıcıları"
```

---

### Task 5: Ağaç SVG + benzerlik matrisi SVG üreteçleri (rapor görselleri)

**Files:**
- Modify: `virusforge/report/render.py` (yeni saf fonksiyonlar `_svg_tree`, `_svg_matrix`)
- Test: `tests/test_report_svg.py`

**Interfaces:**
- Produces: `_svg_tree(newick) -> str` (inline SVG dendrogram), `_svg_matrix(labels, matrix) -> str` (ısı-haritası SVG).

- [ ] **Step 1: Testleri yaz**

```python
# tests/test_report_svg.py
from virusforge.report.render import _svg_tree, _svg_matrix

def test_svg_tree_contains_taxa():
    svg = _svg_tree("(sample:0.001,(V01146:0.002,EU734174:0.04)95:0.01);")
    assert svg.startswith("<svg") and "sample" in svg and "V01146" in svg

def test_svg_matrix_renders_cells():
    svg = _svg_matrix(["s", "A"], [[100.0, 96.0], [96.0, 100.0]])
    assert svg.startswith("<svg") and "96" in svg
```

- [ ] **Step 2: Testi koştur (fail)**

Run: `.venv/bin/python -m pytest tests/test_report_svg.py -q`
Expected: FAIL

- [ ] **Step 3: render.py'ye ekle** (mevcut `_svg_hbar` deseninin yanına)

```python
import re as _re

def _svg_tree(newick: str) -> str:
    """Newick'ten basit yatay dendrogram (bağımsız inline SVG). Yaprak etiketleri sırayla dizilir."""
    labels = _re.findall(r"[(,]([A-Za-z0-9_.\-]+):", newick)
    if not labels:
        return "<p class='na'>Ağaç verisi yok.</p>"
    row_h, w = 24, 620
    h = row_h * len(labels) + 10
    out = [f"<svg viewBox='0 0 {w} {h}' width='100%' style='max-width:{w}px' font-family='system-ui' font-size='12'>"]
    x0 = 20
    for i, lbl in enumerate(labels):
        y = i * row_h + row_h // 2
        out.append(f"<line x1='{x0}' y1='{y}' x2='{x0+60}' y2='{y}' stroke='#0d6b8f' stroke-width='2'/>")
        out.append(f"<text x='{x0+68}' y='{y+4}' fill='#14181d'>{_esc(lbl)}</text>")
    out.append(f"<line x1='{x0}' y1='{row_h//2}' x2='{x0}' y2='{h-row_h//2}' stroke='#0d6b8f' stroke-width='2'/>")
    out.append("</svg>")
    return "".join(out)

def _svg_matrix(labels, matrix) -> str:
    """Benzerlik matrisi ısı-haritası (yüksek=koyu). labels: eksen etiketleri; matrix: NxN %."""
    n = len(labels)
    if not n or any(len(r) != n for r in matrix):
        return "<p class='na'>Matris verisi yok.</p>"
    cell, pad = 46, 130
    w = pad + cell * n + 10
    h = pad + cell * n + 10
    out = [f"<svg viewBox='0 0 {w} {h}' width='100%' style='max-width:{w}px' font-family='system-ui' font-size='11'>"]
    for j, lbl in enumerate(labels):
        out.append(f"<text x='{pad+j*cell+cell//2}' y='{pad-6}' text-anchor='middle' fill='#14181d'>{_esc(str(lbl)[:8])}</text>")
        out.append(f"<text x='{pad-6}' y='{pad+j*cell+cell//2+4}' text-anchor='end' fill='#14181d'>{_esc(str(lbl)[:12])}</text>")
    for i in range(n):
        for j in range(n):
            v = matrix[i][j]
            try:
                fv = float(v)
            except (TypeError, ValueError):
                fv = 0.0
            shade = max(0, min(255, int(255 - fv * 2.2)))
            fill = f"rgb({shade},{shade+20 if shade+20<256 else 255},255)"
            x, y = pad + j * cell, pad + i * cell
            out.append(f"<rect x='{x}' y='{y}' width='{cell-2}' height='{cell-2}' rx='3' fill='{fill}'/>")
            out.append(f"<text x='{x+cell//2}' y='{y+cell//2+4}' text-anchor='middle' fill='#14181d'>{_esc(round(fv,1))}</text>")
    out.append("</svg>")
    return "".join(out)
```

- [ ] **Step 4: Testi koştur (pass)**

Run: `.venv/bin/python -m pytest tests/test_report_svg.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(report): ağaç dendrogram + benzerlik matrisi inline SVG üreteçleri"
```

---

### Task 6: V09Comparative modülü — orkestrasyon + pipeline bağlama

**Files:**
- Modify: `virusforge/modules/v09_comparative.py` (V09Comparative sınıfı)
- Modify: `virusforge/pipeline.py` (import + DEFAULT_MODULES)
- Modify: `config/default.yaml` (`tools.comparative` bloğu)
- Test: `tests/test_comparative.py`

**Interfaces:**
- Consumes: `parse_blast_hits`, `parse_iqtree`, `parse_taxmyphage` (Task 3-4), tools komutları (Task 2), `latest_genome`.
- Produces: `class V09Comparative` (code="V09", dirname="V09_COMPARATIVE_PHYLO"), `ctx.results["V09"]` metrics.

- [ ] **Step 1: Modül-koşum testini yaz** (araçsız/ağsız → WARNING; viral-değil → WARNING/boş)

```python
from virusforge.module import Context, Status
from virusforge.modules.v09_comparative import V09Comparative
from tests.conftest import write_fasta

def _ctx(tmp_path, **kw):
    c = Context(sample_dir=tmp_path, run_dir=tmp_path/"run", cfg={}, mode="SHORT_READ")
    (tmp_path/"run").mkdir(exist_ok=True); c.results.update(kw.get("results",{})); c.artifacts.update(kw.get("artifacts",{}))
    return c

def test_v09_warning_when_offline_or_no_tool(tmp_path):
    g = write_fasta(tmp_path/"g.fasta")
    c = _ctx(tmp_path, results={"V04":{"is_viral":True}}, artifacts={"V03":{"genome":str(g)}})
    res = V09Comparative().run(c)
    assert res.status in (Status.WARNING, Status.NOT_APPLICABLE)
    d = c.run_dir/"V09_COMPARATIVE_PHYLO"
    assert (d/"V09_summary.json").exists() and (d/"01_input").is_dir()
```

- [ ] **Step 2: Testi koştur (fail)**

Run: `.venv/bin/python -m pytest tests/test_comparative.py::test_v09_warning_when_offline_or_no_tool -q`
Expected: FAIL (no V09Comparative)

- [ ] **Step 3: V09Comparative sınıfını yaz** (mevcut v08_amr.py deseni)

```python
def _fetch_genomes(hits, cache_dir, work_fasta, cenv, cbin, logs):
    """Her hit accession'ını efetch ile çek (cache), örnek+akrabaları work_fasta'ya birleştir.
    Çekilebilen akraba sayısını döndür."""
    cache = Path(cache_dir); cache.mkdir(parents=True, exist_ok=True)
    fetched = []
    for h in hits:
        acc = h["accession"]; fa = cache / f"{acc}.fasta"
        if not fa.exists() or fa.stat().st_size == 0:
            cmd = tools.efetch_cmd(acc, fa)
            if cenv:
                cmd = [cbin, "run", "-n", cenv, *cmd]
            try:
                util.run_redirect(cmd, fa, logs / f"efetch_{acc}.log")
            except RuntimeError:
                continue
        if fa.exists() and fa.stat().st_size > 0:
            fetched.append(fa)
    return fetched


class V09Comparative(Module):
    name = "Comparative Identification & Phylogeny"
    code = "V09"
    dirname = "V09_COMPARATIVE_PHYLO"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        if not (ctx.results.get("V04", {}) or {}).get("is_viral"):
            m = {"note": "viral değil — karşılaştırma uygulanmadı"}
            return ModuleResult(Status.NOT_APPLICABLE,
                                self.write_summary(ctx.run_dir, Status.NOT_APPLICABLE, m), m)
        genome = latest_genome(ctx)
        if not genome:
            m = {"error": "girdi genom yok"}
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, m), m)

        cfg = ctx.cfg
        cenv = get(cfg, "tools.comparative.conda_env", None)
        cbin = get(cfg, "tools.comparative.conda_bin", "conda")
        n = get(cfg, "tools.comparative.n_closest", 5)
        metrics: dict = {}

        # (1) online BLAST → en yakın türler
        blast_tsv = dirs["03_native_outputs"] / "blast.tsv"
        bcmd = tools.blastn_remote_cmd(genome, blast_tsv, get(cfg, "tools.comparative.blast_db",
                                       "ref_viruses_rep_genomes"))
        if cenv:
            bcmd = [cbin, "run", "-n", cenv, *bcmd]
        err = safe_run(bcmd, dirs["07_logs"] / "blast.log")
        hits = parse_blast_hits(blast_tsv, n) if (not err and blast_tsv.exists()) else []
        if hits:
            metrics["blast_top_hit"] = hits[0]
            metrics["closest_species"] = hits
        if len(hits) < get(cfg, "tools.comparative.min_hits", 3):
            metrics["error"] = err or "yeterli BLAST hit yok (ağ? DB?)"
            (dirs["04_standardized"] / "comparative.json").write_text(
                json.dumps(metrics, indent=2, ensure_ascii=False))
            ctx.results[self.code] = metrics
            return ModuleResult(Status.WARNING, self.write_summary(ctx.run_dir, Status.WARNING, metrics), metrics)

        # (2) efetch → akraba genomları + örnek birleşik fasta
        combined = dirs["02_work"] / "sample_plus_refs.fasta"
        util.run_cmd  # (import kullanımını korumak için no-op referans yok — aşağıda gerçek yazım)
        with open(combined, "w") as out:
            out.write(f">sample\n{_read_seq(genome)}\n")
        refs = _fetch_genomes(hits, get(cfg, "tools.comparative.ref_cache", "databases/ref_cache"),
                              combined, cenv, cbin, dirs["07_logs"])
        for fa in refs:
            with open(combined, "a") as out:
                out.write(Path(fa).read_text())

        # (3) MAFFT + IQ-TREE2
        aln = dirs["02_work"] / "aln.fasta"
        merr = None
        try:
            mcmd = tools.mafft_cmd(combined, aln)
            if cenv:
                mcmd = [cbin, "run", "-n", cenv, *mcmd]
            util.run_redirect(mcmd, aln, dirs["07_logs"] / "mafft.log")
        except RuntimeError as exc:
            merr = str(exc)
        if not merr and aln.exists() and aln.stat().st_size > 0:
            pfx = dirs["03_native_outputs"] / "iqtree"
            icmd = tools.iqtree_cmd(aln, pfx, get(cfg, "general.threads", 8))
            if cenv:
                icmd = [cbin, "run", "-n", cenv, *icmd]
            if not safe_run(icmd, dirs["07_logs"] / "iqtree.log"):
                tf = Path(str(pfx) + ".treefile")
                if tf.exists():
                    metrics["tree"] = parse_iqtree(tf)

        # (4) taxmyPHAGE ICTV cins/tür
        tout = dirs["03_native_outputs"] / "taxmyphage"
        tcmd = tools.taxmyphage_cmd(genome, tout, get(cfg, "general.threads", 8))
        if cenv:
            tcmd = [cbin, "run", "-n", cenv, *tcmd]
        if not safe_run(tcmd, dirs["07_logs"] / "taxmyphage.log") and tout.exists():
            metrics["ictv"] = parse_taxmyphage(tout)

        (dirs["04_standardized"] / "comparative.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False))
        ctx.results[self.code] = metrics
        status = Status.PASS if (metrics.get("tree") or metrics.get("ictv")) else Status.WARNING
        return ModuleResult(status, self.write_summary(ctx.run_dir, status, metrics), metrics)


def _read_seq(fasta) -> str:
    return "".join(l.strip() for l in Path(fasta).read_text().splitlines() if not l.startswith(">"))
```
Not: `util.run_cmd` no-op satırını YAZMA — yukarıdaki placeholder açıklama; gerçek kodda o satır yok.

- [ ] **Step 4: pipeline.py + config bağla**

`pipeline.py`:
```python
from .modules.v09_comparative import V09Comparative
# DEFAULT_MODULES: ...V07PhageChar, V08Amr, V09Comparative, V10Report,
```
`config/default.yaml` `tools:` altına:
```yaml
  comparative:
    blast_db: ref_viruses_rep_genomes
    n_closest: 5
    min_hits: 3
    ref_cache: databases/ref_cache
    conda_env: ""          # gerekirse vf_phylo
    conda_bin: /home/ali/miniconda3/bin/conda
```

- [ ] **Step 5: Testi koştur (pass) + tüm suite**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS (araçsız ortamda V09 WARNING döner, çökmez)

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat(v09): Comparative modülü (online BLAST→efetch→MAFFT/IQ-TREE2+taxmyPHAGE) + pipeline bağlama"
```

---

### Task 7: registry + references + rapor bölümü (render V09)

**Files:**
- Modify: `virusforge/data/registry.yaml`
- Modify: `virusforge/report/references.py` (TOOL_REFERENCES + PIPELINE_STEPS'e V09)
- Modify: `virusforge/modules/v10_report.py` (`_ORDER`'a "V09")
- Modify: `virusforge/report/render.py` (V09 bölümü)

**Interfaces:**
- Consumes: `M["V09"]` metrics (blast_top_hit, closest_species, ictv, tree, similarity_matrix), `_svg_tree`, `_svg_matrix`.

- [ ] **Step 1: registry.yaml'a araçlar** (gerçek repo/version_cmd)

```yaml
blast:
  repo: https://blast.ncbi.nlm.nih.gov
  version_cmd: ["blastn", "-version"]
  doi: "10.1186/1471-2105-10-421"
mafft:
  repo: https://mafft.cbrc.jp/alignment/software/
  version_cmd: ["mafft", "--version"]
  doi: "10.1093/molbev/mst010"
iqtree2:
  repo: https://github.com/iqtree/iqtree2
  version_cmd: ["iqtree2", "--version"]
  doi: "10.1093/molbev/msaa015"
taxmyphage:
  repo: https://github.com/millardlab/taxmyphage
  version_cmd: ["taxmyphage", "--version"]
  doi: "10.1099/mgen.0.001344"
efetch:
  repo: https://www.ncbi.nlm.nih.gov/books/NBK179288/
  version_cmd: ["efetch", "-version"]
```

- [ ] **Step 2: references.py — TOOL_REFERENCES + PIPELINE_STEPS**

TOOL_REFERENCES sonuna:
```python
    ("blast", "BLAST+", "En yakın referans (online virus DB tanımlama)", "https://blast.ncbi.nlm.nih.gov", "10.1186/1471-2105-10-421"),
    ("mafft", "MAFFT", "Çoklu dizi hizalama", "https://mafft.cbrc.jp/alignment/software/", "10.1093/molbev/mst010"),
    ("iqtree2", "IQ-TREE2", "Maksimum-olabilirlik filogeni", "https://github.com/iqtree/iqtree2", "10.1093/molbev/msaa015"),
    ("taxmyphage", "taxmyPHAGE", "ICTV cins/tür (VIRIDIC + VMR)", "https://github.com/millardlab/taxmyphage", "10.1099/mgen.0.001344"),
```
PIPELINE_STEPS'e V08'den sonra (V10'dan önce):
```python
    ("V09", "Comparative Identification & Phylogeny", "BLAST + IQ-TREE2 + taxmyPHAGE"),
```

- [ ] **Step 3: v10_report.py `_ORDER`'a "V09"**

```python
_ORDER = ["V00", "V01", "V02", "V03", "V04", "V05", "V06", "V07", "V08", "V09"]
```

- [ ] **Step 4: render.py V09 bölümü** (V08 bölümünden sonra, Araçlar bölümünden önce)

```python
    # V09 — Karşılaştırmalı tanımlama & filogeni
    cmp = M["V09"]
    bh = cmp.get("blast_top_hit", {})
    ictv = cmp.get("ictv", {})
    v09body = table("Tanımlama — en yakın kayıt (BLAST, online virus DB)", ["Alan", "Değer"], [
        ["En yakın kayıt", f"<span class='mono'>{_esc(bh.get('accession','—'))}</span>"],
        ["Tür", f"<span class='kv'>{_esc(bh.get('species','—'))}</span>"],
        ["% Kimlik", f"{_esc(bh.get('identity','—'))} %"],
        ["% Kapsam", f"{_esc(bh.get('coverage','—'))} %"],
    ]) if bh else "<p class='na'>BLAST tanımlaması yapılmadı (ağ/DB?).</p>"
    v09body += table("ICTV sınıflandırma", ["Düzey", "Değer"], [
        ["Familya (geNomad)", _esc((M["V04"].get("taxonomy","") or "").split(";")[-1] or "—")],
        ["Alt-familya (PhaBOX)", _esc(subfam) or "—"],
        ["Cins (taxmyPHAGE)", f"<span class='kv'>{_esc(ictv.get('genus','—'))}</span>"],
        ["Tür (taxmyPHAGE)", f"<span class='kv'>{_esc(ictv.get('species','—'))}</span>"],
    ])
    rows = [[str(i+1), f"<span class='mono'>{_esc(h.get('accession'))}</span>", _esc(h.get('species')),
             f"{_esc(h.get('identity'))} %"] for i, h in enumerate(cmp.get("closest_species", []))]
    v09body += table("En yakın 5 tür (ağaç/ICTV referans seti)", ["#", "Accession", "Tür", "% Kimlik"], rows)
    if cmp.get("tree", {}).get("newick"):
        v09body += figure("Filogenetik ağaç — örnek ve en yakın akrabaları (MAFFT + IQ-TREE2).",
                          _svg_tree(cmp["tree"]["newick"]))
    if cmp.get("similarity_matrix") and cmp.get("matrix_labels"):
        v09body += figure("Genomlar arası benzerlik matrisi (VIRIDIC %; ≥95 tür, ≥70 cins).",
                          _svg_matrix(cmp["matrix_labels"], cmp["similarity_matrix"]))
    p.append(section("V09", "Karşılaştırmalı Tanımlama & Filogeni", v09body))
```

- [ ] **Step 5: Testi koştur + render smoke**

Run: `.venv/bin/python -m pytest -q` (66+ yeşil)
Run: `.venv/bin/python -c "from virusforge.report.render import render_html; print(len(render_html({'sample':'T7','mode':'SHORT_READ','run_id':'r','modules':[{'code':'V09','status':'PASS','metrics':{'blast_top_hit':{'accession':'V01146','species':'Escherichia virus T7','identity':'99.9','coverage':'98'},'closest_species':[],'ictv':{'genus':'Teseptimavirus','species':'Escherichia virus T7'},'tree':{'newick':'(sample:0.1,V01146:0.1);'}}}]})))"`
Expected: sayı basar, çökmez

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat(report): V09 karşılaştırmalı bölümü (BLAST tanımlama + ICTV + ağaç + matris) + registry/references"
```

---

### Task 8: Araç kurulumu + gerçek T7 doğrulaması

**Files:** (kod değişikliği yok; kurulum + doğrulama; bulgu çıkarsa TDD ile düzelt)

- [ ] **Step 1: Araçları kur**

```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda install -y -n virusforge -c conda-forge -c bioconda blast iqtree taxmyphage
# mafft + efetch zaten virusforge'da
```
(taxmyphage yoksa izole `vf_phylo` env + config `tools.comparative.conda_env=vf_phylo`.)

- [ ] **Step 2: Hibrit T7 run'ında resume ile V09 koş**

```bash
HYB=$(ls -dt runs/*_hybrid* | head -1)
rm -f "$HYB/V10_REPORT_EXPORT/V10_summary.json"   # rapor yeniden üretilsin
conda run -n virusforge python -m virusforge.cli run --sample samples/T7_hybrid --resume "$HYB"
```

- [ ] **Step 3: Biyolojiyi doğrula**

Beklenen: BLAST en yakın = Escherichia virus T7 / T7-benzeri; ICTV cins **Teseptimavirus**, tür
**Escherichia virus T7**; ağaç örneği V01146 ile aynı dalda; matris örnek-vs-T7ref ≈ %95+.
Gerçek çıktı parser'la uyuşmazsa (AMRFinder v4 dersi gibi) → TDD ile parser'ı düzelt.

- [ ] **Step 4: Commit + DURUM/bellek güncelle**

```bash
git add -A && git commit -m "feat(m3): V09 comparative T7'de gerçek-veri doğrulandı (BLAST/ICTV/ağaç)"
git push
```

---

## Self-Review

- **Spec coverage:** §3 akış → Task 6; §4 çıktı → Task 3/4/6; §5 rapor → Task 7; §6 araç/registry → Task 2/7; §7 dürüstlük → Task 6 (min_hits/WARNING); §8 test → Task 3-6; §9 doğrulama → Task 8. Rapor V09→V10 → Task 1. Tümü kapsanıyor.
- **Placeholder:** yok (her step gerçek kod/komut). Task 6'daki `util.run_cmd` satırı açıkça "YAZMA" notlu.
- **Tip tutarlılığı:** `parse_blast_hits`→`closest_species`/`blast_top_hit`; `parse_iqtree`→`tree.newick`; `parse_taxmyphage`→`ictv.genus/species`; render bunları birebir okur.
- **Not (benzerlik matrisi):** taxmyPHAGE/VIRIDIC matris çıktısının parse'ı Task 8 gerçek çıktıda netleşecek; render matris opsiyonel (yoksa atlanır) — WARNING değil.
