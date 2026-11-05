"""Visão 3: coordenadas paralelas com todas as carreiras de um ano (QASE, 2013–2022)."""
import plotly.graph_objects as go

from dados import CARREIRAS_ICMC, CORES_AREA, CURTOS, INDICADORES, fuvest_total

AREAS = ["Biológicas", "Exatas", "Humanas"]
COR_DESTAQUE, COR_OUTROS = "#D55E00", "#BBBBBB"


def criar_grafico_paralelas(df, ano, etapa, min_respondentes=20, destaque="area"):
    """destaque: "area" (cor por área), "icmc" (carreiras do ICMC) ou o código de uma carreira."""
    d = fuvest_total(df)
    d = d[(d["nivel"] == "carreira") & (d["ano"] == ano) & (d["etapa"] == etapa)
          & (d["respondentes"] >= min_respondentes)].copy()
    # eixos: só os indicadores que existem neste ano (pai e mãe somem em 2022)
    eixos = [c for c in INDICADORES if d[c].notna().any()]
    d = d.dropna(subset=eixos)
    d["area_num"] = d["area"].map({a: i for i, a in enumerate(AREAS)})

    if destaque == "area":
        cor = dict(color=d["area_num"], cmin=0, cmax=2, colorscale=[
            [0, CORES_AREA["Biológicas"]], [1 / 3, CORES_AREA["Biológicas"]],
            [1 / 3, CORES_AREA["Exatas"]], [2 / 3, CORES_AREA["Exatas"]],
            [2 / 3, CORES_AREA["Humanas"]], [1, CORES_AREA["Humanas"]]])
        legenda = "cor = área"
    else:
        alvo = CARREIRAS_ICMC if destaque == "icmc" else {int(destaque)}
        cor = dict(color=d["cod_carreira"].isin(alvo).astype(int), cmin=0, cmax=1,
                   colorscale=[[0, COR_OUTROS], [1, COR_DESTAQUE]])
        nomes = d.loc[d["cod_carreira"].isin(alvo), "carreira"].tolist()
        legenda = "em laranja: " + (", ".join(nomes) if nomes else "nenhuma carreira com dados neste filtro")

    # o 1º eixo é a área: serve de legenda e permite filtrar uma área arrastando sobre ele
    dimensoes = [dict(label="Área", values=d["area_num"], tickvals=[0, 1, 2], ticktext=AREAS)]
    dimensoes += [dict(label=CURTOS[c] + " (%)", values=d[c], range=[0, 100]) for c in eixos]
    fig = go.Figure(go.Parcoords(line=cor, dimensions=dimensoes))
    fig.update_layout(title=f"{len(d)} carreiras em {ano} ({etapa}, mín. {min_respondentes} respondentes); {legenda}",
                      margin=dict(l=70, r=50, t=90), height=500, font=dict(size=12))
    return fig


def opcoes_carreiras(df, ano):
    d = df[(df["nivel"] == "carreira") & (df["ano"] == ano)].drop_duplicates("cod_carreira")
    return [{"label": f"{int(c)} {n}", "value": int(c)} for c, n in sorted(zip(d["cod_carreira"], d["carreira"]))]
