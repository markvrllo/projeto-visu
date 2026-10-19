"""App Dash: perfil socioeconômico dos ingressantes da USP/ICMC a partir do QASE da Fuvest.

Três visões (1ª entrega):
  1. Série temporal do indicador escolhido, com a faixa de implantação das cotas.
  2. Funil inscritos -> convocados -> chamados -> matriculados para um ano.
  3. Coordenadas paralelas comparando todos os cursos num ano/etapa.

Rodar:  python app/app.py   e abrir http://127.0.0.1:8050
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

RAIZ = Path(__file__).resolve().parents[1]
REAL = RAIZ / "data" / "processed" / "indicadores.csv"
DEMO = RAIZ / "data" / "processed" / "indicadores_DEMO.csv"
USANDO_DEMO = not REAL.exists()
df = pd.read_csv(DEMO if USANDO_DEMO else REAL)

INDICADORES = {
    "pct_escola_publica": "% escola pública (ensino médio)",
    "pct_PPI": "% pretos, pardos e indígenas",
    "pct_renda_ate_3SM": "% renda familiar até 3 SM",
    "pct_renda_mais_10SM": "% renda familiar acima de 10 SM",
    "pct_pai_superior": "% pai com ensino superior",
    "pct_mae_superior": "% mãe com ensino superior",
    "pct_cursinho": "% fez cursinho",
}
# rótulos curtos para os eixos das coordenadas paralelas
CURTOS = {"pct_escola_publica": "Esc. pública", "pct_PPI": "PPI", "pct_renda_ate_3SM": "Renda ≤3 SM",
          "pct_renda_mais_10SM": "Renda >10 SM", "pct_pai_superior": "Pai superior",
          "pct_mae_superior": "Mãe superior", "pct_cursinho": "Cursinho"}
ETAPAS = {"inscritos": "Inscritos", "convocados": "Convocados 2ª fase",
          "chamados_1a": "Chamados 1ª matrícula", "matriculados": "Matriculados"}

# Paleta Okabe-Ito: segura para daltonismo
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000"]
COR_ICMC, COR_OUTROS = "#0072B2", "#BBBBBB"

cursos = sorted(df["nome"].dropna().unique())
cursos_icmc = sorted(df.loc[df["icmc"], "nome"].unique())
anos = sorted(df["ano"].unique())

app = Dash(__name__, title="Quem entra no ICMC?")

app.layout = html.Div(style={"fontFamily": "sans-serif", "maxWidth": "1200px", "margin": "auto"}, children=[
    html.H2("Do inscrito ao matriculado: o perfil de quem entra no ICMC"),
    html.Div("DADOS FICTÍCIOS DE DEMONSTRAÇÃO: rode o pipeline para usar os dados da Fuvest.",
             style={"background": "#D55E00", "color": "white", "padding": "8px", "fontWeight": "bold"})
    if USANDO_DEMO else None,
    html.Div(style={"display": "flex", "gap": "16px", "flexWrap": "wrap"}, children=[
        html.Div([html.Label("Indicador"),
                  dcc.Dropdown(id="indicador", options=[{"label": v, "value": k} for k, v in INDICADORES.items()],
                               value="pct_escola_publica", clearable=False)], style={"flex": "1 1 280px"}),
        html.Div([html.Label("Cursos"),
                  dcc.Dropdown(id="cursos", options=cursos, value=cursos_icmc[:4], multi=True)],
                 style={"flex": "2 1 400px"}),
        html.Div([html.Label("Etapa (visões 1 e 3)"),
                  dcc.RadioItems(id="etapa", options=[{"label": v, "value": k} for k, v in ETAPAS.items()],
                                 value="matriculados", inline=True)], style={"flex": "1 1 100%"}),
    ]),
    html.H3("1. Evolução ao longo dos anos"),
    dcc.Graph(id="serie"),
    html.H3("2. Funil do vestibular"),
    html.Label("Ano"),
    dcc.Slider(id="ano", min=min(anos), max=max(anos), step=1, value=max(anos),
               marks={int(a): str(a) for a in anos}),
    dcc.Graph(id="funil"),
    html.H3("3. Comparação entre cursos (ICMC em azul)"),
    dcc.Graph(id="paralelas"),
])


def cor_por_curso(nomes):
    return {n: OKABE_ITO[i % len(OKABE_ITO)] for i, n in enumerate(nomes)}


@app.callback(Output("serie", "figure"), Input("indicador", "value"), Input("cursos", "value"), Input("etapa", "value"))
def atualizar_serie(indicador, sel, etapa):
    d = df[(df["nome"].isin(sel or [])) & (df["etapa"] == etapa)].sort_values("ano")
    fig = px.line(d, x="ano", y=indicador, color="nome", markers=True, symbol="nome",
                  color_discrete_map=cor_por_curso(sel or []),
                  labels={indicador: INDICADORES[indicador], "ano": "Ano", "nome": "Curso"},
                  hover_data={"respondentes": True})
    # faixa de implantação escalonada das cotas na USP (confirmar os anos nos documentos oficiais)
    fig.add_vrect(x0=2017.5, x1=2021.5, fillcolor="#999999", opacity=0.15, line_width=0,
                  annotation_text="implantação das cotas", annotation_position="top left")
    fig.update_layout(yaxis_range=[0, 100], legend_title_text="")
    return fig


@app.callback(Output("funil", "figure"), Input("indicador", "value"), Input("cursos", "value"), Input("ano", "value"))
def atualizar_funil(indicador, sel, ano):
    d = df[(df["nome"].isin(sel or [])) & (df["ano"] == ano)].copy()
    d["etapa_ord"] = pd.Categorical(d["etapa"], categories=list(ETAPAS), ordered=True)
    d = d.sort_values("etapa_ord")
    d["Etapa"] = d["etapa"].map(ETAPAS)
    fig = px.line(d, x="Etapa", y=indicador, color="nome", markers=True, symbol="nome",
                  color_discrete_map=cor_por_curso(sel or []),
                  labels={indicador: INDICADORES[indicador], "nome": "Curso"})
    fig.update_layout(yaxis_range=[0, 100], legend_title_text="",
                      xaxis={"categoryorder": "array", "categoryarray": list(ETAPAS.values())})
    return fig


@app.callback(Output("paralelas", "figure"), Input("etapa", "value"), Input("ano", "value"))
def atualizar_paralelas(etapa, ano):
    d = df[(df["etapa"] == etapa) & (df["ano"] == ano)].dropna(subset=list(INDICADORES))
    fig = go.Figure(go.Parcoords(
        line={"color": d["icmc"].astype(int), "colorscale": [[0, COR_OUTROS], [1, COR_ICMC]]},
        dimensions=[{"label": CURTOS[col] + " (%)", "values": d[col], "range": [0, 100]}
                    for col in INDICADORES],
    ))
    fig.update_layout(margin={"l": 60, "r": 60, "t": 80})
    return fig


if __name__ == "__main__":
    app.run(debug=True)
