"""V10 varyant çağırma: RNA+BAM → varyantlar; DNA veya BAM-yok → NOT_APPLICABLE."""
from pathlib import Path

from virusforge.module import Context, Status
from virusforge.modules.v10_variants import V10VariantCall
from virusforge import util


def _ctx(tmp_path, molecule="rna", with_bam=True):
    run = tmp_path / "run"
    run.mkdir(exist_ok=True)
    ref = tmp_path / "ref.fa"
    ref.write_text(">NC\nACGT\n")
    ctx = Context(sample_dir=tmp_path, run_dir=run,
                  cfg={"general": {"molecule": molecule},
                       "tools": {"rna": {"conda_env": "vf_rna"}, "lofreq": {"conda_env": "vf_lofreq"}}},
                  mode="SHORT_READ")
    if with_bam:
        bam = tmp_path / "aln.bam"
        bam.write_text("bam")
        ctx.artifacts["V02"] = {"bam": str(bam), "reference": str(ref)}
    return ctx


def test_v10_na_on_dna(tmp_path):
    res = V10VariantCall().run(_ctx(tmp_path, molecule="dna"))
    assert res.status == Status.NOT_APPLICABLE


def test_v10_na_when_no_bam(tmp_path):
    res = V10VariantCall().run(_ctx(tmp_path, with_bam=False))
    assert res.status == Status.NOT_APPLICABLE


def test_v10_calls_variants_on_rna(tmp_path, monkeypatch):
    ctx = _ctx(tmp_path)

    def fake_pipe(c1, c2, out_path, log_path=None):
        pfx = c2[c2.index("-p") + 1]                    # ivar variants -p <prefix> → <prefix>.tsv
        Path(str(pfx) + ".tsv").write_text(
            "REGION\tPOS\tREF\tALT\tALT_FREQ\tTOTAL_DP\tREF_AA\tALT_AA\n"
            "NC\t241\tC\tT\t0.99\t1000\t\t\n"
            "NC\t23403\tA\tG\t0.15\t900\tD\tG\n")
        open(out_path, "w").write("")

    def fake_safe_run(cmd, log):                         # lofreq → vcf üret
        vcf = cmd[cmd.index("-o") + 1]
        Path(vcf).write_text("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
                             "NC\t241\t.\tC\tT\t5000\tPASS\tDP=1000;AF=0.99\n")
        return None
    monkeypatch.setattr(util, "run_pipe", fake_pipe)
    monkeypatch.setattr("virusforge.modules.v10_variants.safe_run", fake_safe_run)

    res = V10VariantCall().run(ctx)
    m = ctx.results["V10"]
    assert res.status == Status.PASS
    assert m["n_total"] == 2 and m["n_consensus"] == 1 and m["n_minor"] == 1 and m["quasispecies"] is True
    assert len(m["lofreq_variants"]) == 1


def test_fasta_first_id_reads_accession(tmp_path):
    from virusforge.modules.v10_variants import fasta_first_id
    f = tmp_path / "ref.fa"
    f.write_text(">NC_045512.2 Severe acute respiratory syndrome\nACGT\n")
    assert fasta_first_id(f) == "NC_045512.2"


def test_fasta_first_id_missing_file_falls_back(tmp_path):
    from virusforge.modules.v10_variants import fasta_first_id
    assert fasta_first_id(tmp_path / "yok.fa") == "yok"


def test_render_v10_shows_reference():
    """Varyant bölümü koordinat sistemini (referans accession) göstermeli."""
    from virusforge.report.render import render_html
    rep = {"sample": "CoV2", "mode": "SHORT_READ", "run_id": "r", "modules": [
        {"code": "V10", "status": "PASS", "metrics": {
            "reference": "NC_045512", "n_total": 3, "n_consensus": 2, "n_minor": 1,
            "quasispecies": True,
            "ivar_variants": [{"pos": 241, "ref": "C", "alt": "T", "freq": 0.99, "depth": 900, "aa": ""}],
            "lofreq_variants": [{"pos": 241, "ref": "C", "alt": "T", "af": 0.98, "dp": 900}]}}]}
    tr = render_html(rep, lang="tr")
    assert "NC_045512" in tr                       # referans görünür
    assert "LoFreq varyantları (düşük-frekans/quasispecies)" not in tr  # LoFreq tam tablosu kaldırıldı
    assert "LoFreq" in tr                           # ama LoFreq sayacı korunur


def test_parse_gene_intervals_and_gene_at(tmp_path):
    from virusforge.modules.v10_variants import parse_gene_intervals, gene_at
    gff = tmp_path / "genes.gff3"
    gff.write_text(
        "##gff-version 3\n"
        ".\t.\tgene\t266\t13468\t.\t+\t.\tgene_name=ORF1a\n"
        ".\t.\tgene\t21563\t25384\t.\t+\t.\tgene_name=S\n"
        ".\t.\tgene\t28274\t29533\t.\t+\t.\tgene_name=N\n")
    iv = parse_gene_intervals(gff)
    assert ("S", 21563, 25384) in iv
    assert gene_at(23403, iv) == "S"       # S geni içinde
    assert gene_at(300, iv) == "ORF1a"
    assert gene_at(50, iv) == ""           # hiçbir gende değil (intergenik)


def test_gene_at_bad_pos_is_safe():
    from virusforge.modules.v10_variants import gene_at
    assert gene_at(None, [("S", 1, 10)]) == ""


def test_report_no_warning_badge():
    """WARNING statülü modül raporda 'WARNING' badge'i göstermez (PASS gösterilir)."""
    from virusforge.report.render import render_html
    rep = {"sample": "x", "mode": "SHORT_READ", "run_id": "r", "modules": [
        {"code": "V06", "status": "WARNING", "metrics": {"note": "iyi-huylu alert"}}]}
    html = render_html(rep, lang="tr")
    assert "WARNING" not in html            # ne badge ne legend ne caption


def test_report_variant_gene_column():
    from virusforge.report.render import render_html
    rep = {"sample": "x", "mode": "SHORT_READ", "run_id": "r", "modules": [
        {"code": "V10", "status": "PASS", "metrics": {
            "reference": "NC_045512", "n_total": 1, "n_consensus": 1, "n_minor": 0,
            "ivar_variants": [{"pos": 23403, "gene": "S", "ref": "A", "alt": "G",
                               "freq": 0.99, "depth": 900, "aa": ""}]}}]}
    tr = render_html(rep, lang="tr")
    assert "Gen/CDS" in tr and ">S<" in tr    # gen kolonu + değeri


def test_classify_variant():
    from virusforge.modules.v10_variants import classify_variant
    assert classify_variant("T") == "substitüsyon"
    assert classify_variant("+AC") == "insersiyon"
    assert classify_variant("-TCTGGTTTT") == "delesyon"


def test_variant_effect():
    from virusforge.modules.v10_variants import variant_effect
    assert variant_effect("substitüsyon", "L", "L", "T") == "sinonim"
    assert variant_effect("substitüsyon", "D", "G", "G") == "missense"
    assert variant_effect("substitüsyon", "Q", "*", "T") == "nonsense (stop)"
    assert variant_effect("delesyon", "", "", "-TCT") == "çerçeve-içi indel"  # 3 baz → çerçeve-içi
    assert variant_effect("delesyon", "", "", "-T") == "frameshift"          # 1 baz → frameshift
    assert variant_effect("delesyon", "", "", "-TCTGGT") == "çerçeve-içi indel"  # 6 baz → çerçeve-içi


def test_parse_ivar_variants_has_type_effect(tmp_path):
    from virusforge.modules.v10_variants import parse_ivar_variants
    tsv = tmp_path / "iv.tsv"
    tsv.write_text(
        "REGION\tPOS\tREF\tALT\tREF_DP\tREF_RV\tREF_QUAL\tALT_DP\tALT_RV\tALT_QUAL\tALT_FREQ\tTOTAL_DP\tPVAL\tPASS\tREF_AA\tALT_AA\n"
        "NC\t23403\tA\tG\t5\t0\t30\t900\t0\t35\t0.99\t905\t0\tTRUE\tD\tG\n"
        "NC\t11074\tC\t-T\t3\t0\t30\t100\t0\t35\t0.4\t103\t0\tTRUE\t\t\n")
    iv = parse_ivar_variants(tsv)
    assert iv[0]["type"] == "substitüsyon" and iv[0]["effect"] == "missense"
    assert iv[1]["type"] == "delesyon" and iv[1]["effect"] == "frameshift"
