"""M2-A faj zenginleştirme testleri: AMR modülü (AMRFinderPlus).

Parser gerçek tool-çıktısı fixture'larıyla; modül araçsız ortamda dürüst
WARNING/NOT_APPLICABLE döner (sentetik veri, gerçek indirme yok).
"""
from virusforge.module import Context, Status, is_phage
from virusforge.modules.v06_annotate import V06Annotate
from virusforge.modules.v08_amr import V08Amr, parse_amrfinder

from tests.conftest import write_fasta


# --------------------------------------------------------------------------- #
# Parser birim testleri (AMRFinderPlus)
# --------------------------------------------------------------------------- #
def test_parse_amrfinder_v4_column_names(tmp_path):
    # AMRFinderPlus v4.x gerçek başlık: Type / Element symbol / % Coverage of reference
    p = tmp_path / "amrfinder.tsv"
    p.write_text(
        "Protein id\tElement symbol\tElement name\tScope\tType\tSubtype\tClass\tSubclass"
        "\tMethod\tTarget length\tReference sequence length\t% Coverage of reference"
        "\t% Identity to reference\n"
        "p1\tblaTEM\tbeta-lactamase\tcore\tAMR\tAMR\tBETA-LACTAM\tBETA-LACTAM"
        "\tBLASTP\t100\t100\t100\t99.5\n"
        "p2\tvgrG\tType VI secretion\tcore\tVIRULENCE\tVIRULENCE\tVIRULENCE\tVIRULENCE"
        "\tBLASTP\t50\t50\t98\t88.0\n")
    m = parse_amrfinder(p)
    assert m["counts"] == {"amr": 1, "virulence": 1, "stress": 0}
    assert m["amr_genes"][0]["gene"] == "blaTEM"
    assert m["amr_genes"][0]["identity"] == "99.5"
    assert m["amr_genes"][0]["coverage"] == "100"
    assert m["virulence_genes"][0]["gene"] == "vgrG"


def test_parse_amrfinder_v3_column_names_still_work(tmp_path):
    # eski v3 başlıkları da desteklenmeli (geri uyumluluk)
    p = tmp_path / "amrfinder.tsv"
    p.write_text(
        "Protein identifier\tGene symbol\tSequence name\tElement type\tClass"
        "\t% Coverage of reference sequence\t% Identity to reference sequence\n"
        "p1\tblaTEM\tbeta-lactamase\tAMR\tBETA-LACTAM\t100\t99.5\n")
    m = parse_amrfinder(p)
    assert m["counts"]["amr"] == 1 and m["amr_genes"][0]["gene"] == "blaTEM"


def test_parse_amrfinder_empty_is_valid(tmp_path):
    p = tmp_path / "amrfinder.tsv"
    p.write_text("Protein identifier\tGene symbol\tElement type\n")  # yalnız header
    m = parse_amrfinder(p)
    assert m["counts"] == {"amr": 0, "virulence": 0, "stress": 0}
    assert m["amr_genes"] == []


# --------------------------------------------------------------------------- #
# conda_env sarmalayıcı (izole env — çalışan virusforge env'i korur)
# --------------------------------------------------------------------------- #
def test_amrfinder_cmd_wraps_conda_env():
    from virusforge import tools
    cmd = tools.amrfinder_cmd("in.faa", "o.tsv", conda_env="vf_amr", conda_bin="conda")
    assert cmd[:3] == ["conda", "run", "-n"]


def test_amrfinder_cmd_bare_without_env():
    from virusforge import tools
    assert tools.amrfinder_cmd("in.faa", "o.tsv")[0] == "amrfinder"


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
    c = _ctx(tmp_path, results={"V04": {"is_viral": True, "taxonomy": "Viruses;Caudoviricetes"}})
    assert is_phage(c) is True


def test_is_phage_false_when_not_viral(tmp_path):
    c = _ctx(tmp_path, results={"V04": {"is_viral": False, "taxonomy": ""}})
    assert is_phage(c) is False


def test_is_phage_false_without_v05(tmp_path):
    c = _ctx(tmp_path)
    assert is_phage(c) is False


# --------------------------------------------------------------------------- #
# AMR modülü koşumu (araçsız → dürüst WARNING)
# --------------------------------------------------------------------------- #
def test_amr_warning_when_tool_missing(tmp_path):
    genome = write_fasta(tmp_path / "genome.fasta")
    c = _ctx(tmp_path,
             results={"V04": {"is_viral": True, "taxonomy": "Caudoviricetes"}},
             artifacts={"V03": {"genome": str(genome)},
                        "V06": {"faa": str(tmp_path / "pharokka.faa")}})  # dosya yok → genom fallback
    res = V08Amr().run(c)
    assert res.status == Status.WARNING
    assert (c.run_dir / "V08_AMR_VIRULENCE" / "04_standardized" / "amr_virulence.json").exists()


# --------------------------------------------------------------------------- #
# V06 artifact yayınlama (AMR ön koşulu) + resume geri-yükleme
# --------------------------------------------------------------------------- #
def test_v07_restore_artifacts_resolves_phanotate_faa(tmp_path):
    # gerçek pharokka çıktısı: protein FASTA = phanotate.faa (PHANOTATE), pharokka.faa DEĞİL
    run_dir = tmp_path / "run"
    native = run_dir / "V06_GENOME_ANNOTATION" / "03_native_outputs" / "pharokka"
    native.mkdir(parents=True)
    (native / "phanotate.faa").write_text(">p1\nMAA\n")
    (native / "terL.faa").write_text(">terL\nMAA\n")   # bu SEÇİLMEMELİ
    (native / "pharokka.gbk").write_text("LOCUS x\n")
    c = Context(sample_dir=tmp_path, run_dir=run_dir, cfg={}, mode="SHORT_READ")
    V06Annotate().restore_artifacts(c)
    assert c.artifacts["V06"]["faa"] == str(native / "phanotate.faa")
    assert c.artifacts["V06"]["gbk"] == str(native / "pharokka.gbk")
