"""VirusForge profesyonel HTML rapor motoru (BacForge deseni uygulanmış).

Numaralı Table N. / Figure N. başlıkları, amaca-özel tablolar (jenerik döküm değil),
kart-CSS, pipeline akış şeması, veriden üretilen inline SVG grafikler, araç+DOI referansları.
Bağımsız (üçüncü-taraf native formata bağımlı değil). Gerçek veri; uydurma yok.
"""
from __future__ import annotations

import base64
import html
import re
from datetime import datetime
from pathlib import Path

from .. import registry
from .references import PIPELINE_STEPS, TOOL_REFERENCES

_STATUS_COLOR = {
    "PASS": "#2e9e6b", "WARNING": "#d99a2b", "FAIL": "#c62828",
    "NOT_APPLICABLE": "#8a949e", "SKIPPED": "#b7c0c8",
}

_CSS = """
:root{--bg:#f6f7f9;--card:#fff;--bd:#e2e6ea;--pri:#0d6b8f;--pri2:#0d8f86;--tx:#14181d;--mut:#6b7682}
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--tx);margin:0;padding:32px;line-height:1.55}
.wrap{max-width:1040px;margin:0 auto}
header{border-bottom:3px solid var(--pri);padding-bottom:16px;margin-bottom:22px}
h1{color:var(--pri);margin:0 0 6px;font-size:26px;letter-spacing:-.3px}
.sub{color:var(--mut);font-size:13px;margin:0}
.sub b{color:var(--tx)}
section{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:18px 22px;margin-bottom:16px}
h2{font-size:16px;margin:0 0 12px;display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--bd);padding-bottom:8px}
.mc{font-family:ui-monospace,monospace;font-weight:700;color:var(--pri);background:#eef4f6;padding:2px 7px;border-radius:6px;font-size:13px}
.badge{margin-left:auto;color:#fff;font-size:11px;font-weight:700;padding:3px 10px;border-radius:999px;font-family:ui-monospace,monospace;letter-spacing:.3px}
.cap{font-weight:600;font-size:12.5px;margin:14px 0 5px;color:var(--tx)}
.cap:first-child{margin-top:0}
table{width:100%;border-collapse:collapse;margin-bottom:4px}
th,td{text-align:left;padding:7px 11px;border-bottom:1px solid var(--bd);font-size:12.5px;font-variant-numeric:tabular-nums}
th{background:#eef4f6;color:var(--pri);font-weight:600}
tbody tr:hover{background:#fafcfd}
a{color:var(--pri);text-decoration:none}a:hover{text-decoration:underline}
.na{color:var(--mut);font-style:italic;font-size:12.5px}
.note{color:var(--mut);font-size:11.5px;margin-top:8px}
.mono{font-family:ui-monospace,monospace}
.kv{font-weight:700}
figure{margin:12px 0;text-align:center}
figcaption{font-size:12.5px;color:var(--tx);font-weight:600;margin-top:6px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-top:4px}
.stat{border:1px solid var(--bd);border-radius:9px;padding:11px 13px;background:#fbfcfd}
.stat .l{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.4px}
.stat .v{font-size:19px;font-weight:700;margin-top:3px;color:var(--tx)}
.stat .u{font-size:12px;color:var(--mut);font-weight:500}
.flow{display:flex;flex-wrap:wrap;gap:6px;align-items:stretch;justify-content:center;margin:8px 0}
.fnode{border:2px solid var(--bd);border-radius:9px;padding:8px 10px;min-width:96px;text-align:center;background:#fbfcfd}
.fnode .c{font-family:ui-monospace,monospace;font-weight:700;font-size:12px}
.fnode .n{font-size:10.5px;color:var(--mut);margin-top:2px;line-height:1.25}
.farrow{align-self:center;color:#b7c0c8;font-size:15px}
"""


def _esc(v) -> str:
    return html.escape(str(v)) if v is not None else "&mdash;"


def _pill(status: str) -> str:
    c = _STATUS_COLOR.get(status, "#333")
    return f"<span class='badge' style='background:{c}'>{_esc(status)}</span>"


def _svg_hbar(pairs, unit="", color="#0d8f86", max_rows=12):
    """Veriden yatay bar grafiği (bağımsız inline SVG)."""
    pairs = [(l, v) for l, v in pairs if isinstance(v, (int, float)) and v > 0][:max_rows]
    if not pairs:
        return "<p class='na'>Grafik için pozitif veri yok.</p>"
    vmax = max(v for _, v in pairs)
    row_h, w, lblw = 22, 620, 250
    barw = w - lblw - 60
    h = row_h * len(pairs) + 10
    out = [f"<svg viewBox='0 0 {w} {h}' width='100%' style='max-width:{w}px' font-family='system-ui' font-size='11.5'>"]
    for i, (lbl, v) in enumerate(pairs):
        y = i * row_h + 5
        bw = max(2, int(barw * v / vmax))
        out.append(f"<text x='{lblw-8}' y='{y+13}' text-anchor='end' fill='#14181d'>{_esc(lbl)[:38]}</text>")
        out.append(f"<rect x='{lblw}' y='{y+3}' width='{bw}' height='{row_h-9}' rx='3' fill='{color}'/>")
        out.append(f"<text x='{lblw+bw+6}' y='{y+13}' fill='#6b7682'>{_esc(round(v,4))}{_esc(unit)}</text>")
    out.append("</svg>")
    return "".join(out)


def _svg_tree(newick: str) -> str:
    """Newick'ten basit yatay dendrogram (bağımsız inline SVG). Yaprak etiketleri sırayla dizilir."""
    labels = re.findall(r"[(,]([A-Za-z0-9_.\-]+):", newick or "")
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
            try:
                fv = float(matrix[i][j])
            except (TypeError, ValueError):
                fv = 0.0
            shade = max(0, min(255, int(255 - fv * 2.2)))
            fill = f"rgb({shade},{min(255, shade+20)},255)"
            x, y = pad + j * cell, pad + i * cell
            out.append(f"<rect x='{x}' y='{y}' width='{cell-2}' height='{cell-2}' rx='3' fill='{fill}'/>")
            out.append(f"<text x='{x+cell//2}' y='{y+cell//2+4}' text-anchor='middle' fill='#14181d'>{_esc(round(fv,1))}</text>")
    out.append("</svg>")
    return "".join(out)


_FUNC_COLORS = {
    "head and packaging": "#c0392b", "connector": "#e67e22", "tail": "#2980b9",
    "DNA, RNA and nucleotide metabolism": "#27ae60", "lysis": "#8e44ad",
    "moron, auxiliary metabolic gene and host takeover": "#16a085",
    "transcription regulation": "#d4ac0d", "integration and excision": "#7f8c8d",
    "unknown function": "#bdc3c7", "other": "#95a5a6",
}


def _svg_synteny(top_genes, bottom_genes, links, top_label, bottom_label) -> str:
    """İki genomun gen-düzeni synteny'si: gen okları (fonksiyona göre renkli) + homolog bağlantılar.
    top/bottom_genes: [{gene,start,end,strand,function}]; links: [(top_gene, bottom_gene)]."""
    if not top_genes or not bottom_genes:
        return "<p class='na'>Synteny için gen verisi yok.</p>"
    W, margin, gh = 680, 20, 16
    y_top, y_bot = 40, 150
    trackw = W - 2 * margin

    def _draw(genes, y):
        glen = max((g["end"] for g in genes), default=1) or 1
        cx = {}
        parts = [f"<line x1='{margin}' y1='{y+gh//2}' x2='{margin+trackw}' y2='{y+gh//2}' stroke='#d0d5da' stroke-width='1'/>"]
        for g in genes:
            x1 = margin + int(g["start"] / glen * trackw)
            x2 = margin + int(g["end"] / glen * trackw)
            w = max(3, x2 - x1)
            col = _FUNC_COLORS.get(g.get("function", ""), "#95a5a6")
            parts.append(f"<rect x='{x1}' y='{y}' width='{w}' height='{gh}' fill='{col}' rx='2'/>")
            cx[g["gene"]] = x1 + w // 2
        return "".join(parts), cx

    top_svg, top_cx = _draw(top_genes, y_top)
    bot_svg, bot_cx = _draw(bottom_genes, y_bot)
    link_svg = []
    for a, b in links:
        if a in top_cx and b in bot_cx:
            link_svg.append(f"<line x1='{top_cx[a]}' y1='{y_top+gh}' x2='{bot_cx[b]}' y2='{y_bot}' "
                            "stroke='#8a949e' stroke-width='0.7' opacity='0.5'/>")
    out = [f"<svg viewBox='0 0 {W} 185' width='100%' style='max-width:{W}px' font-family='system-ui' font-size='11'>"]
    out.append(f"<text x='{margin}' y='{y_top-8}' fill='#14181d' font-weight='700'>{_esc(top_label)}</text>")
    out.append(f"<text x='{margin}' y='{y_bot-8}' fill='#14181d' font-weight='700'>{_esc(bottom_label)}</text>")
    out.append("".join(link_svg))          # bağlantılar altta (oklar üstte görünsün)
    out.append(top_svg)
    out.append(bot_svg)
    out.append("</svg>")
    return "".join(out)


def _img_b64(path: Path):
    try:
        if path.exists() and path.stat().st_size > 0:
            return base64.b64encode(path.read_bytes()).decode("ascii")
    except Exception:
        pass
    return None


def render_html(report: dict, run_dir=None) -> str:
    mods = {m.get("code"): m for m in report.get("modules", [])}
    M = {c: (mods.get(c, {}) or {}).get("metrics", {}) or {} for c, _n, _t in PIPELINE_STEPS}
    try:
        date = datetime.now().strftime("%d %B %Y, %H:%M")
    except Exception:
        date = ""

    counters = {"t": 0, "f": 0}

    def table(caption, headers, rows):
        counters["t"] += 1
        n = counters["t"]
        if not rows:
            return (f"<div class='cap'>Tablo {n}. {_esc(caption)}</div>"
                    f"<p class='na'>Veri yok / analiz uygulanmadı.</p>")
        head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
        body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
        return (f"<div class='cap'>Tablo {n}. {_esc(caption)}</div>"
                f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")

    def figure(caption, inner):
        counters["f"] += 1
        n = counters["f"]
        return f"<figure>{inner}<figcaption>Şekil {n}. {_esc(caption)}</figcaption></figure>"

    def figs_for(code, caption):
        """Modülün 06_visualization/ altındaki PNG'leri gömer."""
        if not run_dir:
            return ""
        out = ""
        for png in sorted(Path(run_dir).glob(f"{code}_*/06_visualization/*.png")):
            b64 = _img_b64(png)
            if b64:
                out += figure(caption, f"<img src='data:image/png;base64,{b64}' "
                                       "style='max-width:100%;border:1px solid var(--bd);border-radius:8px'/>")
        return out

    # Düzgün HTML iskeleti — charset ŞART: yoksa tarayıcı UTF-8'i Latin-1 okur, Türkçe harfler bozulur
    p = [
        "<!DOCTYPE html>",
        "<html lang='tr'><head>",
        "<meta charset=\"utf-8\">",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>VirusForge — Viral / Faj Genom Analiz Raporu</title>",
        f"<style>{_CSS}</style>",
        "</head><body>",
        "<div class='wrap'>",
    ]

    # ---------- Header ----------
    p.append("<header><h1>VirusForge — Viral / Faj Genom Analiz Raporu</h1>"
             f"<p class='sub'>Örnek: <b>{_esc(report.get('sample',''))}</b> &nbsp;·&nbsp; "
             f"Sekans tipi: <b>{_esc(report.get('mode',''))}</b> &nbsp;·&nbsp; "
             f"Run: <span class='mono'>{_esc(report.get('run_id',''))}</span> &nbsp;·&nbsp; {date}</p></header>")

    # ---------- Genel Bakış (executive summary) ----------
    q, cv = M["V03"].get("quast", {}), M["V03"].get("checkv", {})
    v6 = (M["V05"].get("closest_10") or [{}])[0]
    v8l, v8t = M["V07"].get("lifestyle", {}), M["V07"].get("taxonomy", {})
    lineage = v8t.get("Lineage", "") or M["V04"].get("taxonomy", "")
    subfam = lineage.split("subfamily:")[-1].split(";")[0] if "subfamily:" in lineage else ""

    def stat(label, val, unit=""):
        return (f"<div class='stat'><div class='l'>{_esc(label)}</div>"
                f"<div class='v'>{_esc(val)}<span class='u'> {_esc(unit)}</span></div></div>")

    cards = [
        stat("Genom uzunluğu", q.get("total_length", "—"), "bp"),
        stat("Contig", q.get("contigs", "—")),
        stat("Tamlık (CheckV)", cv.get("completeness", "—"), "%"),
        stat("Kontaminasyon", cv.get("contamination", "—"), "%"),
        stat("Gen (CDS)", M["V06"].get("cds", "—")),
        stat("Yaşam tarzı", v8l.get("TYPE", "—")),
    ]
    overview_rows = [
        ["Örnek", _esc(report.get("sample", ""))],
        ["Sekans tipi", _esc(report.get("mode", ""))],
        ["Viral doğrulama (geNomad)", f"{_esc(M['V04'].get('is_viral'))} · skor {_esc(M['V04'].get('top_score'))}"],
        ["Taksonomi", f"<span class='mono'>{_esc(M['V04'].get('taxonomy',''))}</span>"],
        ["Alt-familya (PhaGCN)", _esc(subfam) or "—"],
        ["En yakın referans (Mash)", f"{_esc(v6.get('accession','—'))} · mesafe {_esc(v6.get('mash_dist','—'))}"],
        ["Yaşam tarzı (PhaTYP)", f"{_esc(v8l.get('TYPE','—'))} · skor {_esc(v8l.get('PhaTYPScore','—'))}"],
        ["Genom kalitesi (CheckV)", f"{_esc(cv.get('checkv_quality','—'))} · {_esc(cv.get('completeness','—'))}% tam"],
    ]
    p.append("<section><h2>Genel Bakış</h2>"
             f"<div class='grid'>{''.join(cards)}</div>"
             + table("Analiz özeti — temel bulgular", ["Alan", "Değer"], overview_rows)
             + "</section>")

    # ---------- Figure 1: pipeline akış şeması ----------
    flow = []
    steps = PIPELINE_STEPS
    for i, (code, name, _tool) in enumerate(steps):
        stt = mods.get(code, {}).get("status", "SKIPPED")
        col = _STATUS_COLOR.get(stt, "#b7c0c8")
        flow.append(f"<div class='fnode' style='border-color:{col}'>"
                    f"<div class='c'>{code}</div><div class='n'>{_esc(name)}</div></div>")
        if i < len(steps) - 1:
            flow.append("<span class='farrow'>→</span>")
    p.append("<section><h2>Pipeline</h2>"
             + figure("VirusForge modül akışı ve modül durumları (yeşil=PASS, turuncu=WARNING, kırmızı=FAIL, gri=N/A).",
                      f"<div class='flow'>{''.join(flow)}</div>") + "</section>")

    # ---------- Modül bölümleri (amaca-özel tablolar) ----------
    def section(code, name, body):
        stt = mods.get(code, {}).get("status", "SKIPPED")
        return (f"<section><h2><span class='mc'>{code}</span> {_esc(name)} {_pill(stt)}</h2>{body}</section>")

    # V00
    ev = M["V00"].get("evidence", {})
    p.append(section("V00", "Input & Otomatik Tespit",
        table("Girdi tespiti", ["Alan", "Değer"], [
            ["Belirlenen sekans tipi", _esc(M["V00"].get("mode", ""))],
            ["Ortalama okuma uzunluğu", f"{_esc(ev.get('short_mean_len', ev.get('long_mean_len','—')))} bp"],
            ["Karar kaynağı", _esc(ev.get("source", "—"))],
        ])))

    # V01
    sh = M["V01"].get("short", {})
    v01rows = []
    if sh:
        ret = ""
        if sh.get("raw_reads") and sh.get("clean_reads"):
            ret = f"{100*sh['clean_reads']/sh['raw_reads']:.1f}"
        v01rows = [
            ["Ham okuma", _esc(sh.get("raw_reads"))],
            ["Temiz okuma", _esc(sh.get("clean_reads"))],
            ["Tutulma oranı", f"{ret} %" if ret else "—"],
            ["Q30 oranı", f"{100*sh['q30_rate']:.1f} %" if sh.get("q30_rate") else "—"],
            ["GC içeriği", f"{100*sh['gc_content']:.1f} %" if sh.get("gc_content") else "—"],
        ]
    lo = M["V01"].get("long", {})
    if lo:
        v01rows += [["Uzun-okuma ort. uzunluk", f"{_esc(lo.get('mean_len'))} bp"],
                    ["Uzun-okuma N50", _esc(lo.get("read_n50"))]]
    p.append(section("V01", "Okuma Kalitesi & Ön-İşleme (fastp)",
        table("Okuma kalite metrikleri", ["Metrik", "Değer"], v01rows)))

    # V02
    p.append(section("V02", "Viral Genom Assembly",
        table("Assembly", ["Alan", "Değer"], [
            ["Assembler", _esc(M["V02"].get("assembler", "—"))],
            ["Taslak genom", f"<span class='mono'>draft_viral_genome.fasta</span>"],
        ])))

    # V03
    v04body = table("Assembly kalite metrikleri (QUAST)", ["Metrik", "Değer"], [
        ["Toplam uzunluk", f"{_esc(q.get('total_length'))} bp"],
        ["Contig sayısı", _esc(q.get("contigs"))],
        ["En büyük contig", f"{_esc(q.get('largest_contig'))} bp"],
        ["N50", f"{_esc(q.get('n50'))} bp"],
        ["GC", f"{_esc(q.get('gc'))} %"],
    ] if q else [])
    v04body += table("Viral genom tamlık & kontaminasyon (CheckV)", ["Metrik", "Değer"], [
        ["Tamlık", f"{_esc(cv.get('completeness'))} %"],
        ["Kontaminasyon", f"{_esc(cv.get('contamination'))} %"],
        ["CheckV kalitesi", f"<span class='kv'>{_esc(cv.get('checkv_quality'))}</span>"],
        ["Değerlendirilen contig", f"{_esc(cv.get('contig_length'))} bp"],
    ] if cv else [])
    p.append(section("V03", "Cilalama & Genom Kalitesi (QUAST + CheckV)", v04body))

    # V04
    p.append(section("V04", "Viral Dizi Tanıma (geNomad)",
        table("Viral dizi tanıma özeti", ["Alan", "Değer"], [
            ["Viral mi?", _esc(M["V04"].get("is_viral"))],
            ["Viral dizi sayısı", _esc(M["V04"].get("n_viral"))],
            ["En yüksek virus skoru", _esc(M["V04"].get("top_score"))],
            ["Taksonomi", f"<span class='mono'>{_esc(M['V04'].get('taxonomy',''))}</span>"],
        ])))

    # V05
    closest = M["V05"].get("closest_10") or []
    v06rows = [[str(i+1), f"<span class='mono'>{_esc(c.get('accession'))}</span>", _esc(round(c.get('mash_dist',0),5)),
                f"{100*(1-c.get('mash_dist',0)):.2f} %"]
               for i, c in enumerate(closest[:10])]
    v06body = table("En yakın referans genomlar (Mash + INPHARED/ICTV)",
                    ["#", "Accession", "Mash mesafesi", "~Benzerlik"], v06rows)
    if closest:
        v06body += figure("En yakın referanslara Mash mesafesi (küçük = daha yakın).",
                          _svg_hbar([(c.get("accession"), c.get("mash_dist")) for c in closest[:10]],
                                    color="#0d6b8f"))
    p.append(section("V05", "Taksonomi & En Yakın Referanslar", v06body))

    # V06
    fns = M["V06"].get("functions", {}) or {}
    func_rows = [[_esc(k), _esc(v)] for k, v in fns.items()
                 if isinstance(v, int) and v > 0 and k not in ("CDS",)]
    v07body = table("Annotation özeti (Pharokka)", ["Alan", "Değer"], [
        ["Toplam CDS", _esc(M["V06"].get("cds"))],
        ["tRNA", _esc(M["V06"].get("trna"))],
    ])
    v07body += table("Fonksiyonel kategori dağılımı (PHROGs)", ["Kategori", "Gen sayısı"], func_rows)
    # circular genom haritası (öne çıkan görsel)
    gmap = figs_for("V06", "Pharokka circular genom haritası — CDS (renk = PHROG fonksiyonel kategorisi), "
                           "tRNA, GC içeriği ve GC-skew.")
    if func_rows:
        v07body += figure("Fonksiyonel kategorilere göre gen dağılımı.",
                          _svg_hbar([(k, v) for k, v in fns.items() if isinstance(v, int) and v > 0 and k != "CDS"],
                                    color="#0d8f86"))
    p.append(section("V06", "Genom Annotation (Pharokka)", gmap + v07body))

    # V07
    v08body = table("Faj yaşam tarzı & taksonomi (PhaBOX)", ["Alan", "Değer"], [
        ["Yaşam tarzı (PhaTYP)", f"<span class='kv'>{_esc(v8l.get('TYPE','—'))}</span>"],
        ["PhaTYP skoru", _esc(v8l.get("PhaTYPScore", "—"))],
        ["Alt-familya (PhaGCN)", _esc(subfam) or "—"],
        ["Soy hattı", f"<span class='mono'>{_esc(v8t.get('Lineage','—'))}</span>"],
    ]) if (v8l or v8t) else "<p class='na'>Bakteriyofaj karakterizasyonu uygulanmadı.</p>"
    p.append(section("V07", "Faj-Özel Karakterizasyon (PhaBOX)", v08body))

    # V08 — AMR & virülans
    a11 = M["V08"]
    cnt = a11.get("counts", {}) or {}
    amr_rows = [[_esc(g.get("gene")), _esc(g.get("class")), f"{_esc(g.get('identity'))} %",
                 f"{_esc(g.get('coverage'))} %"]
                for g in (a11.get("amr_genes", []) + a11.get("virulence_genes", [])
                          + a11.get("stress_genes", []))]
    if a11.get("counts") is not None:
        v11body = table("AMR / virülans / stres gen sayıları", ["Kategori", "Gen sayısı"], [
            ["AMR", _esc(cnt.get("amr", 0))],
            ["Virülans", _esc(cnt.get("virulence", 0))],
            ["Stres", _esc(cnt.get("stress", 0))],
        ])
        v11body += (table("Saptanan genler (AMRFinderPlus)", ["Gen", "Sınıf", "Kimlik", "Kapsam"], amr_rows)
                    if amr_rows else
                    "<p class='na'>AMR / virülans geni saptanmadı — fajlarda beklenen sonuç.</p>")
    else:
        v11body = "<p class='na'>AMR taraması uygulanmadı.</p>"
    p.append(section("V08", "AMR & Virülans (AMRFinderPlus)", v11body))

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
        ["Familya (geNomad)", _esc((M["V04"].get("taxonomy", "") or "").split(";")[-1] or "—")],
        ["Alt-familya (PhaBOX)", _esc(subfam) or "—"],
        ["Cins (taxmyPHAGE)", f"<span class='kv'>{_esc(ictv.get('genus', '—'))}</span>"],
        ["Tür (taxmyPHAGE)", f"<span class='kv'>{_esc(ictv.get('species', '—'))}</span>"],
    ])
    close_rows = [[str(i + 1), f"<span class='mono'>{_esc(h.get('accession'))}</span>",
                   _esc(h.get('species')), f"{_esc(h.get('identity'))} %"]
                  for i, h in enumerate(cmp.get("closest_species", []))]
    v09body += table("En yakın 5 tür (ağaç/ICTV referans seti)", ["#", "Accession", "Tür", "% Kimlik"], close_rows)
    if (cmp.get("tree") or {}).get("newick"):
        v09body += figure("Filogenetik ağaç — örnek ve en yakın akrabaları (MAFFT + IQ-TREE2).",
                          _svg_tree(cmp["tree"]["newick"]))
    if cmp.get("similarity_matrix") and cmp.get("matrix_labels"):
        v09body += figure("Genomlar arası benzerlik matrisi (VIRIDIC %; ≥95 tür, ≥70 cins).",
                          _svg_matrix(cmp["matrix_labels"], cmp["similarity_matrix"]))
    # taxmyPHAGE VIRIDIC ısı-haritası (varsa) — gerçek intergenomic benzerlik
    v09body += figs_for("V09", "VIRIDIC genomlar-arası benzerlik ısı-haritası "
                               "(taxmyPHAGE; ICTV eşiği ≥95% tür, ≥70% cins).")
    # synteny: örnek vs en yakın referans gen-düzeni (homolog bağlantılar)
    syn = cmp.get("synteny") or {}
    if syn.get("sample_genes") and syn.get("ref_genes"):
        v09body += figure(f"Gen-düzeni synteny — örnek vs en yakın referans ({_esc(syn.get('ref','—'))}); "
                          f"{_esc(syn.get('n_links', 0))} homolog gen bağlantısı, renk = PHROG fonksiyonel kategorisi.",
                          _svg_synteny(syn["sample_genes"], syn["ref_genes"], syn.get("links", []),
                                       "örnek", syn.get("ref", "referans")))
    p.append(section("V09", "Karşılaştırmalı Tanımlama & Filogeni", v09body))

    # ---------- Araçlar & referanslar ----------
    tool_rows = []
    for key, disp, purpose, repo, doi in TOOL_REFERENCES:
        try:
            ver = registry.detect_version(key)
        except Exception:
            ver = None
        ver_txt = f"<span class='mono'>{_esc(ver)}</span>" if ver else "<span class='na'>—</span>"
        doi_txt = f"<a href='https://doi.org/{_esc(doi)}'>{_esc(doi)}</a>" if doi else "—"
        tool_rows.append([f"<b>{_esc(disp)}</b>", ver_txt, _esc(purpose),
                          f"<a href='{_esc(repo)}'>{_esc(repo)}</a>", doi_txt])
    p.append("<section><h2>Araçlar, Sürümler & Bilimsel Referanslar</h2>"
             + table("Kullanılan araçlar (sürümler runtime'da tespit edildi; DOI'ler yayın kaynağıdır — uydurma yok)",
                     ["Araç", "Sürüm", "Amaç", "Depo", "DOI"], tool_rows)
             + "<p class='note'>Her sonuç tool + veritabanı sürümü ve parametreleriyle yeniden üretilebilir "
               "(provenance.json). Durum kodları: PASS / WARNING / FAIL / NOT_APPLICABLE / SKIPPED.</p></section>")

    p.append("<p class='note' style='text-align:center'>VirusForge · RNA+DNA viral/faj genom analiz platformu · "
             "github.com/aliarslan47/VirusForge</p>")
    p.append("</div>")
    p.append("</body></html>")
    return "\n".join(p)
