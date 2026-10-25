#!/bin/sh
set -e
python3 src/01_gerar_base.py
python3 src/02_executar_testes.py
python3 src/03_gerar_planilhas.py
python3 src/04_gerar_dossie.py
