"""Gera data/carreira_area.csv: a área (Biológicas, Exatas, Humanas) de cada carreira do QASE, por ano.

A Fuvest numera as carreiras por área: 100–398 Humanas, 400–698 Biológicas e 700–998 Exatas.
Os códigos 399, 699 e 999 são as "carreiras" de treinamento (treineiros), que o Anuário também deixa
de fora. Eles ficam na tabela com treinamento = True e são excluídos dos indicadores.

A regra é conferida pela tabela ponte de 2022 (src/ponte.py): a soma das carreiras de cada área no
QASE é comparada com a mesma área no Anuário.

Uso:
    python scripts/gerar_carreira_area.py        # lê data/processed/qase_longo.csv
"""
import argparse
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
TREINAMENTO = {399, 699, 999}


def area_do_codigo(cod):
    cod = int(cod)
    if cod in TREINAMENTO:
        return None
    if 100 <= cod < 400:
        return "Humanas"
    if 400 <= cod < 700:
        return "Biológicas"
    if 700 <= cod < 1000:
        return "Exatas"
    raise ValueError(f"código de carreira fora das faixas conhecidas: {cod}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--qase", default=str(RAIZ / "data" / "processed" / "qase_longo.csv"))
    ap.add_argument("-o", "--saida", default=str(RAIZ / "data" / "carreira_area.csv"))
    args = ap.parse_args(argv)
    q = pd.read_csv(args.qase, usecols=["ano", "cod_carreira", "carreira"], dtype={"cod_carreira": int})
    tab = (q.drop_duplicates(["ano", "cod_carreira"]).sort_values(["cod_carreira", "ano"])
           [["ano", "cod_carreira", "carreira"]].reset_index(drop=True))
    tab["area"] = tab["cod_carreira"].map(area_do_codigo)
    tab["treinamento"] = tab["cod_carreira"].isin(TREINAMENTO)
    tab.to_csv(args.saida, index=False)
    print(f"{len(tab)} linhas ({tab['cod_carreira'].nunique()} códigos) em {args.saida}")
    print(tab.groupby(["ano", "area"], dropna=False).size().unstack(fill_value=0))


if __name__ == "__main__":
    main()
