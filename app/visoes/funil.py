"""Visão 2: funil do vestibular (slope chart) inscritos -> convocados -> matriculados, comparando dois anos."""
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dados import CORES_AREA, ETAPAS, SIMBOLOS_AREA, espalhar, fuvest_total


def _dados_do_ano(df, ano, indicador):
    # até 2022 usamos o QASE (mesma fonte da série de carreiras); de 2023 em diante só existe o Anuário,
    # que tem também a etapa de convocados
    fonte = "qase" if ano <= 2022 else "anuario"
    d = fuvest_total(df)
    d = d[(d["ano"] == ano) & (d["fonte"] == fonte) & d["nivel"].isin(["usp", "area"])].copy()
    d["grupo"] = d["area"].where(d["nivel"] == "area", "USP")
    return d.dropna(subset=[indicador]), fonte


def criar_grafico_funil(df, indicador, anos, rotulo=None):
    """Um painel por ano. Cada linha liga o valor do indicador nas etapas, para a USP e cada área.

    A inclinação mostra o filtro do vestibular: linha descendo = o grupo perde espaço até a matrícula.
    """
    rotulo = rotulo or indicador
    fig = make_subplots(rows=1, cols=len(anos), shared_yaxes=True, horizontal_spacing=0.16,
                        subplot_titles=[str(a) for a in anos])
    for col, ano in enumerate(anos, start=1):
        d, fonte = _dados_do_ano(df, ano, indicador)
        # os títulos dos painéis são as primeiras anotações da figura
        fig.layout.annotations[col - 1].text = f"{ano} ({'QASE' if fonte == 'qase' else 'Anuário'})"
        if d.empty:
            fig.add_annotation(text="Sem dados deste indicador<br>neste ano", showarrow=False,
                               x=0.5, y=0.5, xref=f"x{col if col > 1 else ''} domain",
                               yref=f"y{col if col > 1 else ''} domain", font=dict(color="gray", size=13))
            continue
        etapas = [e for e in ETAPAS if e in set(d["etapa"])]
        rotulos = []
        for grupo, g in d.groupby("grupo"):
            g = g.set_index("etapa").reindex(etapas)
            # a USP fica por cima e mais grossa; as áreas, mais finas
            largura = 4 if grupo == "USP" else 2.5
            fig.add_trace(go.Scatter(
                x=[ETAPAS[e] for e in etapas], y=g[indicador], name=grupo, legendgroup=grupo,
                showlegend=False, mode="lines+markers",
                line=dict(color=CORES_AREA[grupo], width=largura),
                marker=dict(size=9, symbol=SIMBOLOS_AREA[grupo]),
                customdata=g["respondentes"],
                hovertemplate=f"{grupo}, %{{x}}: %{{y:.1f}}%<br>%{{customdata}} respondentes<extra></extra>",
            ), row=1, col=col)
            # rótulo direto na ponta da linha: o nome do grupo e a variação do inscrito ao matriculado
            # (é a resposta da Q2); substitui a legenda
            ultimo = g[indicador].dropna()
            if ultimo.empty:
                continue
            texto = f"<b>{grupo}</b>"
            if {"inscritos", "matriculados"} <= set(etapas):
                delta = g.loc["matriculados", indicador] - g.loc["inscritos", indicador]
                texto += f" {delta:+.1f} pp".replace(".", ",").replace("-", "−")
            rotulos.append((grupo, ETAPAS[ultimo.index[-1]], ultimo.iloc[-1], texto))
        folga = 0.09 * (d[indicador].max() - d[indicador].min() or 1)
        for (grupo, x, _, texto), y in zip(rotulos, espalhar([v for _, _, v, _ in rotulos], folga)):
            fig.add_annotation(x=x, y=y, text=texto, showarrow=False, xanchor="left", xshift=12,
                               font=dict(color=CORES_AREA[grupo], size=12), row=1, col=col)
    fig.update_layout(title=f"Do inscrito ao matriculado: {rotulo}", plot_bgcolor="white", showlegend=False,
                      margin=dict(l=70, r=150, t=90, b=50), height=470, separators=",.")
    fig.update_yaxes(title_text=rotulo, row=1, col=1)
    fig.update_yaxes(showgrid=True, gridcolor="LightGray", ticksuffix="%")
    return fig
