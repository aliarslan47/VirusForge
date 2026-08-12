#!/usr/bin/env bash
# VirusForge veritabanı indirici. `conda activate virusforge` sonrası çalıştır.
# Yollar config/default.yaml ile aynı: databases/<tool>
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p databases

echo "== CheckV DB =="
checkv download_database databases/checkv_tmp && \
  mv databases/checkv_tmp/checkv-db-* databases/checkv && rmdir databases/checkv_tmp || true

echo "== geNomad DB =="
genomad download-database databases/ && mv databases/genomad_db databases/genomad || true

echo "== Pharokka DB =="
install_databases.py -o databases/pharokka || pharokka_install_databases.py -o databases/pharokka

echo "== INPHARED Mash sketch =="
mkdir -p databases/inphared
# Güncel sketch millardlab'dan (tarih değişebilir; en güncel için https://github.com/RyanCook94/inphared)
wget -q -O databases/inphared/inphared.msh \
  "https://millardlab-inphared.s3.climb.ac.uk/latest_genomes.msh" || \
  echo "INPHARED sketch elle indirilmeli: https://github.com/RyanCook94/inphared"

echo "== PhaBOX DB =="
mkdir -p databases/phabox
echo "PhaBOX DB'sini elle indir: https://github.com/KennthShang/PhaBOX (phabox_db_v2 zip) → databases/phabox/"

echo "Bitti. DB yolları config/default.yaml ile uyumlu."
