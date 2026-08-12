"""VirusForge HTML rapor motoru (BacForge-tarzı: şema + numaralı tablolar + araç/DOI + referanslar).
Bağımsız (üçüncü-taraf native formata bağımlı değil). Gerçek veri; uydurma yok."""
from __future__ import annotations

import html
from datetime import datetime

from .. import registry
from .references import PIPELINE_STEPS, TOOL_REFERENCES

_STATUS_COLOR = {
    "PASS": "#2C7BB6", "WARNING": "#E8A33D", "FAIL": "#D7191C",
    "NOT_APPLICABLE": "#888", "SKIPPED": "#bbb",
}

_CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;color:#1a1a1a;background:#fff;line-height:1.5}
.wrap{max-width:1080px;margin:0 auto;padding:2rem}
h1{font-size:1.8rem;margin:0 0 .3rem;border-bottom:3px solid #2C7BB6;padding-bottom:.5rem}
h2{font-size:1.25rem;margin:2rem 0 .6rem;color:#0b3d61}
.sub{color:#555;margin:.2rem 0 1.2rem}
.badge{color:#fff;padding:.12rem .5rem;border-radius:4px;font-size:.78rem;font-weight:600;white-space:nowrap}
table{border-collapse:collapse;width:100%;margin:.5rem 0 1rem;font-size:.9rem}
th,td{border:1px solid #dde;padding:.4rem .6rem;text-align:left;vertical-align:top}
th{background:#f2f6fa}
.flow{display:flex;flex-wrap:wrap;gap:.4rem;align-items:center;margin:1rem 0}
.node{border:2px solid #ccc;border-radius:8px;padding:.4rem .6rem;font-size:.82rem;min-width:80px}
.arrow{color:#999}
.cap{font-size:.82rem;color:#666;margin:.2rem 0 1rem;font-style:italic}
.mono{font-family:ui-monospace,monospace;font-size:.85rem}
a{color:#2C7BB6}
.summary-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.5rem;margin:1rem 0}
.card{border:1px solid #e0e6ee;border-radius:8px;padding:.6rem}
.card .c{font-weight:600;font-size:.85rem}
"""


def _esc(x) -> str:
    return html.escape(str(x))


def _metrics_table(metrics: dict) -> str:
    if not metrics:
        return "<p class='cap'>Veri yok.</p>"
    rows = []
    for k, v in metrics.items():
        if isinstance(v, dict):
            inner = "".join(
                f"<tr><td class='mono'>{_esc(ik)}</td><td>{_esc(iv)}</td></tr>"
                for ik, iv in v.items())
            val = f"<table>{inner}</table>" if inner else "—"
        elif isinstance(v, list):
            if v and isinstance(v[0], dict):
                cols = list(v[0].keys())
                head = "".join(f"<th>{_esc(c)}</th>" for c in cols)
                body = "".join(
                    "<tr>" + "".join(f"<td>{_esc(r.get(c,''))}</td>" for c in cols) + "</tr>"
                    for r in v[:15])
                val = f"<table><tr>{head}</tr>{body}</table>"
            else:
                val = ", ".join(_esc(x) for x in v[:20])
        else:
            val = _esc(v)
        rows.append(f"<tr><td class='mono'>{_esc(k)}</td><td>{val}</td></tr>")
    return f"<table><tr><th>alan</th><th>değer</th></tr>{''.join(rows)}</table>"


def _badge(status: str) -> str:
    c = _STATUS_COLOR.get(status, "#333")
    return f"<span class='badge' style='background:{c}'>{_esc(status)}</span>"


def render_html(report: dict) -> str:
    mods = {m.get("code"): m for m in report.get("modules", [])}
    try:
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
    except Exception:
        date = ""

    p = [f"<style>{_CSS}</style>", "<div class='wrap'>"]
    p.append("<h1>VirusForge — Viral/Faj Genom Analiz Raporu</h1>")
    p.append(f"<p class='sub'>Örnek: <b>{_esc(report.get('sample',''))}</b> · "
             f"Mod: <b>{_esc(report.get('mode',''))}</b> · "
             f"Run: <span class='mono'>{_esc(report.get('run_id',''))}</span> · {date}</p>")

    # Özet kartlar
    p.append("<h2>Özet</h2><div class='summary-grid'>")
    for code, name, _tool in PIPELINE_STEPS:
        st = mods.get(code, {}).get("status", "SKIPPED")
        p.append(f"<div class='card'><div class='c'>{code}</div>"
                 f"<div style='font-size:.78rem;color:#555;margin:.2rem 0'>{_esc(name)}</div>"
                 f"{_badge(st)}</div>")
    p.append("</div>")

    # Figure 1: pipeline akış şeması
    p.append("<h2>Figure 1 — Pipeline Akış Şeması</h2><div class='flow'>")
    for i, (code, name, _tool) in enumerate(PIPELINE_STEPS):
        st = mods.get(code, {}).get("status", "SKIPPED")
        col = _STATUS_COLOR.get(st, "#ccc")
        p.append(f"<div class='node' style='border-color:{col}'>"
                 f"<b>{code}</b><br><span style='font-size:.72rem'>{_esc(name)}</span></div>")
        if i < len(PIPELINE_STEPS) - 1:
            p.append("<span class='arrow'>→</span>")
    p.append("</div><p class='cap'>Figure 1. Modül akışı; renk = durum (mavi PASS, turuncu WARNING, kırmızı FAIL, gri N/A).</p>")

    # Numaralı modül bölümleri
    tn = 0
    for code, name, tool in PIPELINE_STEPS:
        if code == "V19":
            continue
        m = mods.get(code)
        if not m:
            continue
        tn += 1
        p.append(f"<h2>{code} — {_esc(name)} {_badge(m.get('status',''))}</h2>")
        p.append(f"<p class='cap'>Araç: {_esc(tool)}</p>")
        p.append(f"<p class='cap'>Table {tn}. {code} standardize metrikler.</p>")
        p.append(_metrics_table(m.get("metrics", {})))

    # Araç & sürüm & referans tablosu (gerçek sürümler)
    p.append("<h2>Araçlar, Sürümler ve Bilimsel Referanslar</h2>")
    p.append("<table><tr><th>Araç</th><th>Sürüm (tespit edilen)</th><th>Amaç</th><th>Repo</th><th>DOI</th></tr>")
    for key, disp, purpose, repo, doi in TOOL_REFERENCES:
        try:
            ver = registry.detect_version(key)
        except Exception:
            ver = None
        ver_txt = _esc(ver) if ver else "<span style='color:#999'>kurulu değil</span>"
        doi_txt = (f"<a href='https://doi.org/{_esc(doi)}'>{_esc(doi)}</a>" if doi else "—")
        p.append(f"<tr><td><b>{_esc(disp)}</b></td><td class='mono'>{ver_txt}</td>"
                 f"<td>{_esc(purpose)}</td><td><a href='{_esc(repo)}'>{_esc(repo)}</a></td>"
                 f"<td>{doi_txt}</td></tr>")
    p.append("</table>")
    p.append("<p class='cap'>Sürümler runtime'da tespit edildi; DOI'ler yayın kaynağıdır (uydurma yok).</p>")

    p.append("</div>")
    return "\n".join(p)
