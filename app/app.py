"""App Dash: perfil socioeconômico de quem entra na USP, antes e depois das cotas.

Três visões (1ª entrega), uma por arquivo em app/visoes/:
  1. serie.py      Série temporal 2013–2026 da USP e das 3 áreas (Q1).
  2. funil.py      Funil inscritos -> convocados -> matriculados, comparando dois anos (Q2).
  3. paralelas.py  Coordenadas paralelas com todas as carreiras de um ano (Q3).

Rodar:  python app/app.py   e abrir http://127.0.0.1:8050
"""
from dash import Dash, Input, Output, dcc, html

from dados import ANOS, ANOS_CARREIRA, ETAPAS, INDICADORES, USANDO_DEMO, df
from visoes.funil import criar_grafico_funil
from visoes.paralelas import criar_grafico_paralelas, opcoes_carreiras
from visoes.serie import criar_grafico_serie

app = Dash(__name__, title="Quem entra na USP?")


def opcoes_destaque(ano):
    return [{"label": "Cor por área", "value": "area"}, {"label": "Carreiras do ICMC", "value": "icmc"}] \
        + opcoes_carreiras(df, ano)


def controle(rotulo, componente, largura="1 1 260px"):
    return html.Div([html.Label(rotulo, style={"fontWeight": "bold"}), componente], style={"flex": largura})


app.layout = html.Div(style={"fontFamily": "sans-serif", "maxWidth": "1200px", "margin": "auto", "padding": "0 16px"}, children=[
    html.H2("Quem entra na USP: o perfil dos ingressantes antes e depois das cotas (2013–2026)"),
    html.Div("DADOS FICTÍCIOS DE DEMONSTRAÇÃO: rode o pipeline para usar os dados da Fuvest.",
             style={"background": "#D55E00", "color": "white", "padding": "8px", "fontWeight": "bold"})
    if USANDO_DEMO else None,
    html.P("Fontes: QASE da Fuvest (2013–2022, por carreira) e Anuário Estatístico da USP (2022–2026, total e "
           "por área). Só candidatos da Fuvest; as porcentagens vêm de contagens somadas."),

    # filtros globais
    html.Div(style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "position": "sticky", "top": 0,
                    "background": "white", "padding": "8px 0", "zIndex": 10, "borderBottom": "1px solid #ddd"}, children=[
        controle("Indicador (visões 1 e 2)", dcc.Dropdown(
            id="indicador", options=[{"label": v, "value": k} for k, v in INDICADORES.items()],
            value="pct_escola_publica", clearable=False), "2 1 320px"),
        controle("Etapa (visões 1 e 3)", dcc.RadioItems(
            id="etapa", options=[{"label": v, "value": k} for k, v in ETAPAS.items()],
            value="matriculados", inline=True)),
    ]),

    html.H3("1. Evolução ao longo dos anos (Q1)"),
    html.P("Linha cheia: QASE. Linha pontilhada e marcador vazado: Anuário. Em 2022 aparecem as duas fontes."),
    dcc.Graph(id="serie"),

    html.H3("2. Funil do vestibular (Q2)"),
    html.P("Quanto mais a linha desce do inscrito ao matriculado, mais o vestibular filtrou aquele grupo."),
    html.Div(style={"display": "flex", "gap": "16px", "flexWrap": "wrap"}, children=[
        controle("Ano antes", dcc.Dropdown(id="ano_antes", options=ANOS, value=2017, clearable=False), "0 1 160px"),
        controle("Ano depois", dcc.Dropdown(id="ano_depois", options=ANOS, value=max(ANOS), clearable=False), "0 1 160px"),
    ]),
    dcc.Graph(id="funil"),

    html.H3("3. Comparação entre carreiras (Q3)"),
    html.P("Cada linha é uma carreira. Arraste sobre um eixo para filtrar as carreiras por faixa de valor."),
    html.Div(style={"display": "flex", "gap": "16px", "flexWrap": "wrap"}, children=[
        controle("Ano", dcc.Slider(id="ano_carreiras", min=min(ANOS_CARREIRA), max=max(ANOS_CARREIRA), step=1,
                                   value=max(ANOS_CARREIRA), marks={int(a): str(a) for a in ANOS_CARREIRA}), "3 1 420px"),
        controle("Destacar", dcc.Dropdown(id="destaque", options=opcoes_destaque(max(ANOS_CARREIRA)), value="area",
                                          clearable=False), "2 1 300px"),
        controle("Mínimo de respondentes", dcc.Slider(id="min_resp", min=0, max=300, step=10, value=20,
                                                     marks={0: "0", 20: "20", 100: "100", 200: "200", 300: "300"}), "2 1 260px"),
    ]),
    dcc.Graph(id="paralelas"),
])


@app.callback(Output("serie", "figure"), Input("indicador", "value"), Input("etapa", "value"))
def atualizar_serie(indicador, etapa):
    return criar_grafico_serie(df, indicador, etapa, INDICADORES[indicador])


@app.callback(Output("funil", "figure"), Input("indicador", "value"),
              Input("ano_antes", "value"), Input("ano_depois", "value"))
def atualizar_funil(indicador, ano_antes, ano_depois):
    return criar_grafico_funil(df, indicador, sorted({ano_antes, ano_depois}), INDICADORES[indicador])


@app.callback(Output("destaque", "options"), Input("ano_carreiras", "value"))
def atualizar_opcoes_destaque(ano):
    return opcoes_destaque(ano)


@app.callback(Output("paralelas", "figure"), Input("ano_carreiras", "value"), Input("etapa", "value"),
              Input("min_resp", "value"), Input("destaque", "value"))
def atualizar_paralelas(ano, etapa, min_resp, destaque):
    # convocados só existe no Anuário (sem carreiras): nesse caso a visão usa matriculados
    etapa = etapa if etapa in ("inscritos", "matriculados") else "matriculados"
    return criar_grafico_paralelas(df, ano, etapa, min_resp, destaque or "area")


if __name__ == "__main__":
    app.run(debug=True)
