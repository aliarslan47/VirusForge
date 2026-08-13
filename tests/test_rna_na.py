"""RNA yolunda faj/DNA-özel modüller dürüstçe NOT_APPLICABLE döner."""
import pytest

from virusforge.module import Context, Status
from virusforge.modules.v05_taxonomy import V05Taxonomy
from virusforge.modules.v07_phage_char import V07PhageChar
from virusforge.modules.v08_amr import V08Amr
from virusforge.modules.v09_comparative import V09Comparative


@pytest.mark.parametrize("Mod", [V05Taxonomy, V07PhageChar, V08Amr, V09Comparative])
def test_module_not_applicable_on_rna(tmp_path, Mod):
    run = tmp_path / "run"
    run.mkdir()
    ctx = Context(sample_dir=tmp_path, run_dir=run, cfg={"general": {"molecule": "rna"}}, mode="SHORT_READ")
    # gerçekçi: örnek viral RNA (geNomad Riboviria) → V09'un is_viral guard'ı geçer, is_rna N/A yapmalı
    ctx.results["V04"] = {"is_viral": True, "taxonomy": "Viruses;Riboviria;Nidovirales;Coronaviridae"}
    res = Mod().run(ctx)
    assert res.status == Status.NOT_APPLICABLE
