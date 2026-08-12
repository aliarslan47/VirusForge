set -x
source /home/ali/miniconda3/etc/profile.d/conda.sh && conda activate virusforge
cd /home/ali/VirusForge/databases
echo "### CheckV DB"; checkv download_database . 2>&1 | tail -3
echo "### geNomad DB"; genomad download-database . 2>&1 | tail -3
echo "### Pharokka DB"
( install_databases.py -o pharokka 2>&1 || pharokka_install_databases.py -o pharokka 2>&1 || pharokka-db -o pharokka 2>&1 ) | tail -3
echo "### path bağlama"
[ -d checkv-db-v1.5 ] && ln -sfn checkv-db-v1.5 checkv
[ -d genomad_db ] && ln -sfn genomad_db genomad
echo "### DB LISTE"; ls -la
