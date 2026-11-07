"""Medidas de representação (inscritos -> matriculados) e validação das modalidades AC/EP/PPI.

Para cada grupo (um indicador do indicadores.csv, ex.: % escola pública) e cada recorte
(ano, fonte, via de ingresso, nível, área, carreira, modalidade):

    diferenca_pp = % do grupo entre os matriculados - % do grupo entre os inscritos   (0 = proporcional)
    razao        = % do grupo entre os matriculados / % do grupo entre os inscritos   (1 = proporcional)

A razão é a mesma forma do "disparate impact" (Feldman et al., 2015); o limiar 0,8 da regra dos 4/5
serve só de régua de leitura. As medidas mostram disparidade no resultado, não a causa: não separam
preparo anterior, escolha de carreira, desistência da matrícula e a própria reserva de vagas.

Uso:
    python -m src.representacao     # lê data/processed/indicadores.csv e grava
                                    # data/processed/representacao.csv e data/processed/validacao_modalidades.csv
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "data" / "processed"

INDICADORES = ["pct_escola_publica", "pct_PPI", "pct_renda_ate_3SM", "pct_renda_mais_10SM", "pct_pai_superior",
               "pct_mae_superior", "pct_cursinho", "pct_mulheres", "pct_tecnico"]
RECORTE = ["ano", "fonte", "ingresso", "nivel", "area", "cod_carreira", "modalidade"]
MODALIDADES = ["AC", "EP", "PPI"]

# Abaixo disso de respondentes matriculados a razão oscila muito (1 aluno a mais muda vários p.p.).
AMOSTRA_MINIMA = 30
# Indicadores que são o próprio critério da modalidade: dentro dela valem ~100% nas duas etapas.
CRITERIO_DA_MODALIDADE = {("EP", "pct_escola_publica"), ("PPI", "pct_escola_publica"), ("PPI", "pct_PPI")}

COLUNAS = ["ano", "fonte", "ingresso", "nivel", "area", "cod_carreira", "carreira", "modalidade", "indicador",
           "respondentes_inscritos", "respondentes_matriculados", "pct_inscritos", "pct_matriculados",
           "diferenca_pp", "razao", "amostra_pequena", "criterio_da_modalidade"]


def _chave(df: pd.DataFrame) -> pd.DataFrame:
    """Troca os vazios das colunas do recorte por marcadores, para o merge não perder linhas."""
    return df.fillna({"area": "", "cod_carreira": -1})


def representacao(ind: pd.DataFrame) -> pd.DataFrame:
    """indicadores.csv -> uma linha por recorte e indicador com diferença e razão de representação.

    Só entram recortes que têm as duas etapas (inscritos e matriculados) na mesma fonte.
    """
    ind = _chave(ind)
    longos = {}
    for etapa in ["inscritos", "matriculados"]:
        e = ind[ind["etapa"] == etapa]
        longo = e.melt(id_vars=RECORTE + ["carreira", "respondentes"], value_vars=INDICADORES,
                       var_name="indicador", value_name="pct")
        longos[etapa] = longo.rename(columns={"pct": f"pct_{etapa}", "respondentes": f"respondentes_{etapa}"})
    rep = longos["inscritos"].drop(columns="carreira").merge(longos["matriculados"], on=RECORTE + ["indicador"],
                                                             how="inner", validate="one_to_one")
    rep = rep.dropna(subset=["pct_inscritos", "pct_matriculados"])

    rep["diferenca_pp"] = rep["pct_matriculados"] - rep["pct_inscritos"]
    rep["razao"] = rep["pct_matriculados"] / rep["pct_inscritos"].where(rep["pct_inscritos"] > 0)
    rep["amostra_pequena"] = rep["respondentes_matriculados"] < AMOSTRA_MINIMA
    rep["criterio_da_modalidade"] = [(m, i) in CRITERIO_DA_MODALIDADE
                                     for m, i in zip(rep["modalidade"], rep["indicador"])]

    rep["area"] = rep["area"].replace("", np.nan)
    rep["cod_carreira"] = rep["cod_carreira"].astype(int).astype(object).where(rep["cod_carreira"] >= 0)
    ordem_ind = {c: i for i, c in enumerate(INDICADORES)}
    rep = rep.sort_values(["ano", "fonte", "ingresso", "nivel", "area", "cod_carreira", "modalidade", "indicador"],
                          key=lambda s: s.map(ordem_ind) if s.name == "indicador" else s, na_position="first")
    return rep[COLUNAS].reset_index(drop=True)


def validar_modalidades(ind: pd.DataFrame, tolerancia_pp=1.0, minimo_criterio=90.0) -> pd.DataFrame:
    """Confere AC + EP + PPI contra a linha 'Todas' do QASE (2019–2022). Devolve uma linha por problema.

    M1 (reprova) soma dos respondentes das modalidades != respondentes de 'Todas'.
    M2 (aviso)   média dos indicadores das modalidades, ponderada pelos respondentes, longe de 'Todas'
                 por mais de `tolerancia_pp`. É aproximada: cada pergunta tem o próprio nº de respostas.
    M3 (aviso)   recorte sem alguma das três modalidades (o PDF daquela modalidade não existe ou foi reprovado).
    M4 (aviso)   modalidade que não bate com o próprio critério: EP ou PPI com menos de `minimo_criterio`%
                 de escola pública, ou PPI com menos disso de pretos, pardos e indígenas.
    """
    q = _chave(ind[(ind["fonte"] == "qase") & ind["modalidade"].isin(MODALIDADES + ["Todas"])])
    grupos = ["ano", "etapa", "nivel", "area", "cod_carreira"]
    q = q[q.groupby(grupos)["modalidade"].transform(lambda s: s.isin(MODALIDADES).any())]
    todas = q[q["modalidade"] == "Todas"].set_index(grupos)
    mods = q[q["modalidade"] != "Todas"]
    problemas = []

    def add(idx, check, gravidade, detalhe, modalidade="", indicador=""):
        ano, etapa, nivel, area, cod = idx
        problemas.append({"check": check, "gravidade": gravidade, "ano": ano, "etapa": etapa, "nivel": nivel,
                          "area": area, "cod_carreira": cod, "modalidade": modalidade, "indicador": indicador,
                          "detalhe": detalhe})

    soma = mods.groupby(grupos)["respondentes"].sum()
    presentes = mods.groupby(grupos)["modalidade"].agg(set)
    for idx, linha in todas.iterrows():
        if idx not in soma.index:
            add(idx, "M3 modalidade faltando", "aviso", "nenhuma modalidade, só 'Todas'")
            continue
        if soma[idx] != linha["respondentes"]:
            add(idx, "M1 AC+EP+PPI != Todas (respondentes)", "reprova",
                f"soma = {soma[idx]}, Todas = {linha['respondentes']}")
        faltam = [m for m in MODALIDADES if m not in presentes[idx]]
        if faltam:
            add(idx, "M3 modalidade faltando", "aviso", "falta " + ", ".join(faltam), modalidade=",".join(faltam))

    for col in INDICADORES:
        ok = mods[mods[col].notna()]
        n = ok.groupby(grupos)["respondentes"].sum()
        media = (ok[col] * ok["respondentes"]).groupby([ok[g] for g in grupos]).sum() / n
        dif = (media - todas[col]).dropna()
        for idx, v in dif[dif.abs() > tolerancia_pp].items():
            add(idx, "M2 média ponderada != Todas", "aviso",
                f"modalidades = {media[idx]:.2f}%, Todas = {todas.loc[idx, col]:.2f}% ({v:+.2f} p.p.)",
                indicador=col)

    for (mod, col) in sorted(CRITERIO_DA_MODALIDADE):
        fora = mods[(mods["modalidade"] == mod) & (mods[col] < minimo_criterio)]
        for _, r in fora.iterrows():
            add(tuple(r[g] for g in grupos), "M4 modalidade fora do próprio critério", "aviso",
                f"{col} = {r[col]:.1f}% com {r['respondentes']} respondentes", modalidade=mod, indicador=col)

    cols = ["check", "gravidade", "ano", "etapa", "nivel", "area", "cod_carreira", "modalidade", "indicador", "detalhe"]
    out = pd.DataFrame(problemas, columns=cols)
    out["area"] = out["area"].replace("", np.nan)
    out["cod_carreira"] = out["cod_carreira"].where(out["cod_carreira"] != -1).astype("Int64")
    return out.sort_values(["check", "ano", "etapa", "nivel", "cod_carreira"]).reset_index(drop=True)


def resumo(rep: pd.DataFrame, val: pd.DataFrame) -> str:
    linhas = [f"representacao.csv: {len(rep)} linhas, "
              f"{rep.loc[rep['nivel'] == 'carreira', 'cod_carreira'].nunique()} carreiras, anos {rep['ano'].min()}–{rep['ano'].max()}",
              f"  com amostra pequena (< {AMOSTRA_MINIMA} matriculados): {int(rep['amostra_pequena'].sum())}",
              "validacao_modalidades.csv:"]
    if val.empty:
        linhas.append("  nenhum problema")
    else:
        for (check, grav), n in val.groupby(["check", "gravidade"]).size().items():
            linhas.append(f"  {check} [{grav}]: {n}")
    return "\n".join(linhas)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--indicadores", default=str(PROC / "indicadores.csv"))
    ap.add_argument("-o", "--saida", default=str(PROC / "representacao.csv"))
    ap.add_argument("--validacao", default=str(PROC / "validacao_modalidades.csv"))
    args = ap.parse_args(argv)
    ind = pd.read_csv(args.indicadores)
    rep = representacao(ind)
    val = validar_modalidades(ind)
    rep.to_csv(args.saida, index=False, float_format="%.4f")
    val.to_csv(args.validacao, index=False)
    print(resumo(rep, val))


if __name__ == "__main__":
    main()
