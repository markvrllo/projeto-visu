"""Tabela "ponte" de 2022: QASE (soma das carreiras) × Anuário Estatístico da USP, no mesmo ano.

Se os indicadores das duas fontes forem parecidos em 2022, a série 2013–2022 (QASE) pode ser
emendada com a série 2023–2026 (Anuário). Compara o total da USP e as 3 áreas, nas etapas que
existem nas duas fontes (inscritos e matriculados), modalidade "Todas".

Uso:
    python -m src.ponte          # lê data/processed/indicadores.csv, grava data/processed/ponte_2022.csv
"""
import argparse
from pathlib import Path

import pandas as pd

from src.harmonizacao import INDICADORES

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "data" / "processed"


def ponte(ind: pd.DataFrame, ano=2022) -> pd.DataFrame:
    sel = ind[(ind["ano"] == ano) & (ind["ingresso"] == "fuvest") & (ind["modalidade"] == "Todas")
              & (ind["nivel"].isin(["usp", "area"]))].copy()
    sel["area"] = sel["area"].fillna("USP")
    colunas = ["respondentes"] + list(INDICADORES)
    longo = sel.melt(id_vars=["fonte", "etapa", "area"], value_vars=colunas, var_name="indicador", value_name="valor")
    tab = longo.pivot_table(index=["area", "etapa", "indicador"], columns="fonte", values="valor", aggfunc="first")
    tab = tab.reindex(columns=["qase", "anuario"]).dropna(how="any").reset_index()
    tab["diferenca"] = tab["anuario"] - tab["qase"]
    tab["unidade"] = tab["indicador"].map(lambda c: "pessoas" if c == "respondentes" else "pp")
    tab.loc[tab["indicador"] == "respondentes", "diferenca_rel_pct"] = 100 * tab["diferenca"] / tab["qase"]
    return tab


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--indicadores", default=str(PROC / "indicadores.csv"))
    ap.add_argument("-o", "--saida", default=str(PROC / "ponte_2022.csv"))
    args = ap.parse_args(argv)
    tab = ponte(pd.read_csv(args.indicadores))
    tab.to_csv(args.saida, index=False, float_format="%.2f")
    print(tab.to_string(index=False, float_format=lambda x: f"{x:.2f}"))


if __name__ == "__main__":
    main()
