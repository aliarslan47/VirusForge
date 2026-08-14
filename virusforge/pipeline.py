"""Pipeline orkestrasyonu: V00 → ... → V09, moda göre yönlendirme + resume."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from . import config, detect
from .module import Context, Status
from .modules.v00_input import V00Input
from .modules.v01_qc import V01ReadQC
from .modules.v02_assembly import V02Assembly
from .modules.v03_polish_qc import V03PolishQC
from .modules.v04_identify import V04Identify
from .modules.v05_taxonomy import V05Taxonomy
from .modules.v06_annotate import V06Annotate
from .modules.v07_phage_char import V07PhageChar
from .modules.v08_amr import V08Amr
from .modules.v09_comparative import V09Comparative
from .modules.v10_variants import V10VariantCall
from .modules.v11_lineage import V11Lineage
from .modules.v12_report import V12Report

# M1 çekirdek + M2-A faj zenginleştirme + M3 karşılaştırma (mode/faj/viral'e göre kendi içinde dallanır)
DEFAULT_MODULES = [
    V00Input, V01ReadQC, V02Assembly, V03PolishQC,
    V04Identify, V05Taxonomy, V06Annotate, V07PhageChar,
    V08Amr, V09Comparative, V10VariantCall, V11Lineage, V12Report,
]


def organism_label(sample_dir, cfg=None) -> str:
    """Run'ları organizmaya göre klasörlemek için etiket. Öncelik: config `general.organism`;
    yoksa örnek dizini adının ilk '_' öncesi (T7_short→T7, CoV2_ERR11728561→CoV2). Dosya-sistemi
    güvenli hale getirilir (boşluk/slash → alt çizgi)."""
    label = ""
    if cfg:
        label = str((cfg.get("general") or {}).get("organism") or "").strip()
    if not label:
        name = Path(str(sample_dir)).name
        label = name.split("_")[0] if name else "unknown"
    safe = "".join(c if (c.isalnum() or c in "-.") else "_" for c in label)
    return safe or "unknown"


def _log(run_dir: Path, msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    with open(run_dir / "pipeline.log", "a") as fh:
        fh.write(f"[{ts}] {msg}\n")


def run(sample_dir, out_root, cfg=None, modules=None, clock=None, resume=True,
        run_dir=None) -> Path:
    """Örneği çalıştır; run dizinini döndür. run_dir verilirse ona resume edilir."""
    cfg = cfg or config.load_config()
    modules = modules or DEFAULT_MODULES
    det = detect.detect_mode(sample_dir, cfg)
    mode = det["mode"]
    if run_dir is not None:
        run_dir = Path(run_dir)                       # mevcut koşuya devam (resume)
    else:
        ts = clock() if clock else datetime.now().strftime("%Y%m%d_%H%M%S")
        # organizmaya göre iç klasör: runs/<organizma>/<ts>_<mode> — mod aynı olsa da karışmaz
        run_dir = Path(out_root) / organism_label(sample_dir, cfg) / f"{ts}_{mode.lower()}"
    run_dir.mkdir(parents=True, exist_ok=True)

    ctx = Context(sample_dir=Path(sample_dir), run_dir=run_dir, cfg=cfg, mode=mode)
    ctx.results["V00_detect"] = det

    for cls in modules:
        mod = cls()
        if resume and mod.is_done(run_dir):
            # resume: sonuç + artifact'leri diskten geri yükle (aşağı akış modülleri için)
            try:
                data = json.loads((mod.module_dir(run_dir) / f"{mod.code}_summary.json").read_text())
                ctx.results[mod.code] = data.get("metrics", {})
            except Exception:
                pass
            mod.restore_artifacts(ctx)
            _log(run_dir, f"{mod.code} atlandı (resume — zaten bitmiş)")
            continue
        _log(run_dir, f"{mod.code} başladı")
        try:
            res = mod.run(ctx)
            _log(run_dir, f"{mod.code} bitti: {res.status.value}")
        except Exception as exc:  # yüksek sesle: FAIL summary + devam
            mod.write_summary(run_dir, Status.FAIL, {"exception": str(exc)})
            _log(run_dir, f"{mod.code} HATA: {exc}")
    return run_dir
