"""VirusForge CLI. `python3 -m virusforge.cli run --sample DIR --out DIR`."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, config, pipeline, registry


def cmd_run(args) -> int:
    cfg = config.load_config(args.config)
    if args.threads:
        cfg.setdefault("general", {})["threads"] = args.threads
    if args.mode:
        cfg.setdefault("general", {})["mode"] = args.mode
    run_dir = pipeline.run(args.sample, args.out, cfg)
    print(f"Bitti. Run dizini: {run_dir}")
    print(f"Rapor: {run_dir / 'report.html'}")
    return 0


def cmd_info(args) -> int:
    print(f"VirusForge {__version__}")
    print("Kurulu araç sürümleri (uydurma yok — yoksa 'kurulu değil'):")
    for name in ("fastp", "spades", "flye", "unicycler", "checkv",
                 "genomad", "mash", "pharokka", "phabox"):
        try:
            ver = registry.detect_version(name)
        except KeyError:
            ver = None
        print(f"  {name:12s} {ver or 'kurulu değil'}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="virusforge", description="VirusForge viral/faj genom pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("run", help="pipeline çalıştır")
    pr.add_argument("--sample", required=True, help="örnek dizini (FASTQ/FASTA)")
    pr.add_argument("--out", default="runs", help="çıktı kök dizini (default: runs)")
    pr.add_argument("--config", default=None, help="kullanıcı config YAML")
    pr.add_argument("--threads", type=int, default=None)
    pr.add_argument("--mode", default=None, choices=["auto", "short", "long", "hybrid", "assembly"])
    pr.set_defaults(func=cmd_run)

    pi = sub.add_parser("info", help="sürüm + kurulu araçlar")
    pi.set_defaults(func=cmd_info)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
