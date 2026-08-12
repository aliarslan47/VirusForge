"""Basit, bağımsız HTML rapor motoru (üçüncü-taraf native formata bağımlı değil)."""
from __future__ import annotations

import html
import json

_STATUS_COLOR = {
    "PASS": "#2C7BB6", "WARNING": "#E8A33D", "FAIL": "#D7191C",
    "NOT_APPLICABLE": "#888", "SKIPPED": "#aaa",
}


def render_html(report: dict) -> str:
    parts = [
        "<!doctype html><meta charset='utf-8'><title>VirusForge Report</title>",
        "<style>body{font-family:system-ui,sans-serif;margin:2rem;max-width:1000px}"
        "h1{border-bottom:2px solid #2C7BB6}section{margin:1.5rem 0;padding:1rem;"
        "border:1px solid #ddd;border-radius:8px}.badge{color:#fff;padding:.15rem .5rem;"
        "border-radius:4px;font-size:.8rem}pre{background:#f6f6f6;padding:.6rem;"
        "overflow:auto;border-radius:6px}</style>",
        f"<h1>VirusForge — {html.escape(str(report.get('sample','')))}</h1>",
        f"<p>Mode: <b>{html.escape(str(report.get('mode','')))}</b> · "
        f"Run: {html.escape(str(report.get('run_id','')))}</p>",
    ]
    for mod in report.get("modules", []):
        st = mod.get("status", "")
        color = _STATUS_COLOR.get(st, "#333")
        parts.append(
            f"<section><h2>{html.escape(mod.get('code',''))} — "
            f"{html.escape(mod.get('module',''))} "
            f"<span class='badge' style='background:{color}'>{html.escape(st)}</span></h2>"
            f"<pre>{html.escape(json.dumps(mod.get('metrics',{}), indent=2, ensure_ascii=False))}</pre>"
            "</section>"
        )
    return "\n".join(parts)
