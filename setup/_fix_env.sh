set -x
CONDA=/home/ali/miniconda3/bin/conda
echo "### 1) ana env: diamond 2.x"
$CONDA install -n virusforge -c conda-forge -c bioconda -y "diamond>=2.1"
echo "### 2) ayrı phabox env (pandas uyumlu)"
$CONDA create -n vf_phabox -c conda-forge -c bioconda -y phabox
echo "### doğrulama"
$CONDA run -n virusforge diamond --version
$CONDA run -n vf_phabox phabox2 --help 2>&1 | head -3
echo "### DONE"
