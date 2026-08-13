"""M2-A faj zenginleştirme testleri: V09 host, V11 AMR, V12 termini, V13 domain.

Parser'lar gerçek tool-çıktısı fixture'larıyla; modüller araçsız ortamda dürüst
WARNING/NOT_APPLICABLE döner (sentetik veri, gerçek indirme yok).
"""
from pathlib import Path

from virusforge.module import Context, Status, is_phage
from virusforge.modules.v07_annotate import V07Annotate
from virusforge.modules.v09_host import V09Host, parse_rafah, parse_iphop
from virusforge.modules.v11_amr import V11Amr, parse_amrfinder
from virusforge.modules.v12_termini import V12Termini, parse_phageterm
from virusforge.modules.v13_domain import V13Domain, parse_phold

from tests.conftest import write_fasta, write_fastq


# --------------------------------------------------------------------------- #
# Parser birim testleri
# --------------------------------------------------------------------------- #
def test_parse_rafah_extracts_host_and_score(tmp_path):
    p = tmp_path / "T7_Host_Predictions.tsv"
    p.write_text("Sequence\tPredicted_Host\tScore\nT7\tEscherichia\t0.95\n")
    m = parse_rafah(p)
    assert m["predicted_host"] == "Escherichia" and m["confidence"] == "0.95"


def test_parse_iphop_extracts_genus_and_confidence(tmp_path):
    p = tmp_path / "Host_prediction_to_genus_m90.csv"
    p.write_text("Virus,AAI to closest reference,Host genus,Confidence score,List of methods\n"
                 "T7,,Escherichia,95.5,blast;crispr\n")
    m = parse_iphop(p)
    assert m["predicted_host"] == "Escherichia" and m["confidence"] == "95.5"


def test_parse_amrfinder_groups_by_element_type(tmp_path):
    p = tmp_path / "amrfinder.tsv"
    p.write_text(
        "Protein identifier\tGene symbol\tSequence name\tElement type\tClass"
        "\t% Coverage of reference sequence\t% Identity to reference sequence\n"
        "p1\tblaTEM\tbeta-lactamase\tAMR\tBETA-LACTAM\t100\t99.5\n"
        "p2\tvgrG\tType VI secretion\tVIRULENCE\tVIRULENCE\t98\t88.0\n")
    m = parse_amrfinder(p)
    assert m["counts"] == {"amr": 1, "virulence": 1, "stress": 0}
    assert m["amr_genes"][0]["gene"] == "blaTEM"
    assert m["amr_genes"][0]["identity"] == "99.5"
    assert m["virulence_genes"][0]["gene"] == "vgrG"


def test_parse_amrfinder_empty_is_valid(tmp_path):
    p = tmp_path / "amrfinder.tsv"
    p.write_text("Protein identifier\tGene symbol\tElement type\n")  # yalnız header
    m = parse_amrfinder(p)
    assert m["counts"] == {"amr": 0, "virulence": 0, "stress": 0}
    assert m["amr_genes"] == []


def test_parse_phageterm_reads_class_and_positions(tmp_path):
    p = tmp_path / "T7_PhageTerm_report.csv"
    p.write_text("Sequence,Class,Left,Right\nT7,DTR (long),1,160\n")
    m = parse_phageterm(p)
    assert m["termini_type"] == "DTR (long)" and m["left"] == "1" and m["right"] == "160"


def test_parse_phold_sums_functions_and_unknown(tmp_path):
    # phold_all_cds_functions.tsv — pharokka ile aynı format (Description/Count/contig)
    p = tmp_path / "phold_all_cds_functions.tsv"
    p.write_text("Description\tCount\tcontig\n"
                 "CDS\t60\tc1\nunknown function\t20\tc1\ntail\t10\tc1\nCDS\t2\tc2\n")
    m = parse_phold(p)
    assert m["cds"] == 62                 # contig'ler toplandı
    assert m["unknown_function"] == 20
    assert m["functions"]["tail"] == 10


# --------------------------------------------------------------------------- #
# is_phage yardımcısı
# --------------------------------------------------------------------------- #
def _ctx(tmp_path, **kw):
    c = Context(sample_dir=tmp_path, run_dir=tmp_path / "run", cfg={}, mode=kw.get("mode", "SHORT_READ"))
    (tmp_path / "run").mkdir(exist_ok=True)
    c.results.update(kw.get("results", {}))
    c.artifacts.update(kw.get("artifacts", {}))
    return c


def test_is_phage_true_for_caudoviricetes(tmp_path):
    c = _ctx(tmp_path, results={"V05": {"is_viral": True, "taxonomy": "Viruses;Caudoviricetes"}})
    assert is_phage(c) is True


def test_is_phage_false_when_not_viral(tmp_path):
    c = _ctx(tmp_path, results={"V05": {"is_viral": False, "taxonomy": ""}})
    assert is_phage(c) is False


def test_is_phage_false_without_v05(tmp_path):
    c = _ctx(tmp_path)
    assert is_phage(c) is False


# --------------------------------------------------------------------------- #
# Modül koşumları (araçsız → dürüst WARNING / N/A)
# --------------------------------------------------------------------------- #
def _phage_ctx_with_genome(tmp_path, **kw):
    genome = write_fasta(tmp_path / "genome.fasta")
    c = _ctx(tmp_path,
             results={"V05": {"is_viral": True, "taxonomy": "Caudoviricetes"}},
             artifacts={"V04": {"genome": str(genome)}},
             **kw)
    return c, genome


def test_v09_not_applicable_when_not_phage(tmp_path):
    c = _ctx(tmp_path, results={"V05": {"is_viral": False}},
             artifacts={"V04": {"genome": str(write_fasta(tmp_path / "g.fasta"))}})
    res = V09Host().run(c)
    assert res.status == Status.NOT_APPLICABLE


def test_v09_warning_when_tool_missing(tmp_path):
    c, _ = _phage_ctx_with_genome(tmp_path)
    res = V09Host().run(c)
    assert res.status == Status.WARNING
    d = c.run_dir / "V09_HOST_PREDICTION"
    assert (d / "V09_summary.json").exists()
    assert (d / "04_standardized" / "host_prediction.json").exists()
    assert (d / "01_input").is_dir() and (d / "08_metadata").is_dir()  # 8 std klasör


def test_v11_warning_when_tool_missing(tmp_path):
    c, _ = _phage_ctx_with_genome(tmp_path)
    c.artifacts["V07"] = {"faa": str(tmp_path / "pharokka.faa")}  # dosya yok → genom fallback
    res = V11Amr().run(c)
    assert res.status == Status.WARNING
    assert (c.run_dir / "V11_AMR_VIRULENCE" / "04_standardized" / "amr_virulence.json").exists()


def test_v12_not_applicable_for_long_only(tmp_path):
    c, _ = _phage_ctx_with_genome(tmp_path, mode="LONG_READ")
    res = V12Termini().run(c)
    assert res.status == Status.NOT_APPLICABLE


def test_v12_warning_when_tool_missing(tmp_path):
    c, _ = _phage_ctx_with_genome(tmp_path, mode="SHORT_READ")
    r1 = write_fastq(tmp_path / "reads_R1.fastq")
    r2 = write_fastq(tmp_path / "reads_R2.fastq")
    c.artifacts["V01"] = {"clean_r1": str(r1), "clean_r2": str(r2)}
    res = V12Termini().run(c)
    assert res.status == Status.WARNING


def test_v13_not_applicable_when_not_phage(tmp_path):
    c = _ctx(tmp_path, results={"V05": {"is_viral": False}})
    res = V13Domain().run(c)
    assert res.status == Status.NOT_APPLICABLE


def test_v13_warning_when_tool_missing(tmp_path):
    c, _ = _phage_ctx_with_genome(tmp_path)
    c.artifacts["V07"] = {"gbk": str(tmp_path / "pharokka.gbk")}
    res = V13Domain().run(c)
    assert res.status == Status.WARNING


# --------------------------------------------------------------------------- #
# V07 artifact yayınlama (V11/V13 ön koşulu) + resume geri-yükleme
# --------------------------------------------------------------------------- #
def test_v07_restore_artifacts_resolves_phanotate_faa(tmp_path):
    # gerçek pharokka çıktısı: protein FASTA = phanotate.faa (PHANOTATE), pharokka.faa DEĞİL
    run_dir = tmp_path / "run"
    native = run_dir / "V07_GENOME_ANNOTATION" / "03_native_outputs" / "pharokka"
    native.mkdir(parents=True)
    (native / "phanotate.faa").write_text(">p1\nMAA\n")
    (native / "terL.faa").write_text(">terL\nMAA\n")   # bu SEÇİLMEMELİ
    (native / "pharokka.gbk").write_text("LOCUS x\n")
    c = Context(sample_dir=tmp_path, run_dir=run_dir, cfg={}, mode="SHORT_READ")
    V07Annotate().restore_artifacts(c)
    assert c.artifacts["V07"]["faa"] == str(native / "phanotate.faa")
    assert c.artifacts["V07"]["gbk"] == str(native / "pharokka.gbk")
