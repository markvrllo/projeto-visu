"""Baixa os PDFs listados em data/fontes_qase.csv e data/fontes_notas.csv para data/raw/.

Uso:
    python scripts/baixar_pdfs.py            # baixa tudo
    python scripts/baixar_pdfs.py --so-prioridade   # só inscritos + matriculados por carreira, 2013-2022
"""
import argparse
import csv
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "data" / "raw"
CABECALHO = {"User-Agent": "Mozilla/5.0 (projeto academico SCC0252 ICMC-USP)"}


def ler_fontes(prioridade: bool):
    for nome in ("fontes_qase.csv", "fontes_notas.csv"):
        with open(RAIZ / "data" / nome, newline="") as f:
            for linha in csv.DictReader(f):
                if prioridade:
                    if nome != "fontes_qase.csv" or int(linha["ano"]) < 2013:
                        continue
                    if not (linha["nivel"] == "carreira" and linha["etapa"] in ("inscritos", "matriculados")):
                        continue
                yield linha["url"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-prioridade", action="store_true")
    args = ap.parse_args()
    DESTINO.mkdir(parents=True, exist_ok=True)

    falhas = []
    for url in ler_fontes(args.so_prioridade):
        arquivo = DESTINO / url.rsplit("/", 1)[1]
        if arquivo.exists() and arquivo.stat().st_size > 0:
            print(f"já existe  {arquivo.name}")
            continue
        try:
            r = requests.get(url, headers=CABECALHO, timeout=120)
            r.raise_for_status()
            arquivo.write_bytes(r.content)
            print(f"baixado    {arquivo.name} ({len(r.content) // 1024} KB)")
        except requests.RequestException as e:
            print(f"FALHOU     {arquivo.name}: {e}")
            falhas.append(url)
        time.sleep(1)  # não sobrecarregar o servidor da Fuvest

    if falhas:
        print("\nBaixe manualmente (abra o acervo do ano no site da Fuvest):")
        print("\n".join(falhas))


if __name__ == "__main__":
    main()
