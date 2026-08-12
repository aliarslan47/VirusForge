"""V00 — Input & Automatic Data Detection."""
from __future__ import annotations

import json
from pathlib import Path

from .. import detect, util
from ..module import Context, Module, ModuleResult, Status


def _count_reads(fastq: Path) -> int:
    with detect._open(fastq) as fh:
        return sum(1 for _ in fh) // 4


class V00Input(Module):
    name = "Input & Auto-Detection"
    code = "V00"
    dirname = "V00_INPUT_AUTO_DETECTION"

    def run(self, ctx: Context) -> ModuleResult:
        dirs = self.make_dirs(ctx.run_dir)
        det = ctx.results.get("V00_detect") or detect.detect_mode(ctx.sample_dir, ctx.cfg)
        mode = det["mode"]

        # data_type.json
        (dirs["04_standardized"] / "data_type.json").write_text(
            json.dumps(det, indent=2, ensure_ascii=False)
        )

        # read_statistics.tsv + checksums.sha256
        rows = ["file\treads\tmean_len\tsha256"]
        checks = []
        for p in sorted(Path(ctx.sample_dir).iterdir()):
            name = p.name.lower()
            if not name.endswith((".fastq", ".fq", ".fastq.gz", ".fq.gz",
                                  ".fasta", ".fa", ".fna")):
                continue
            digest = util.sha256(p)
            checks.append(f"{digest}  {p.name}")
            if name.endswith((".fastq", ".fq", ".fastq.gz", ".fq.gz")):
                rows.append(f"{p.name}\t{_count_reads(p)}\t{detect.mean_read_length(p):.1f}\t{digest}")
            else:
                rows.append(f"{p.name}\tNA\tNA\t{digest}")
        (dirs["05_statistics"] / "read_statistics.tsv").write_text("\n".join(rows) + "\n")
        (dirs["08_metadata"] / "checksums.sha256").write_text("\n".join(checks) + "\n")

        metrics = {"mode": mode, "evidence": det.get("evidence", {})}
        ctx.mode = mode
        ctx.results[self.code] = metrics
        summary = self.write_summary(ctx.run_dir, Status.PASS, metrics)
        return ModuleResult(Status.PASS, summary, metrics)
