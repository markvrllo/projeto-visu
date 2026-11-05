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
    fig = make_subplots(rows=1, cols=len(anos), shared_yaxes=True, horizontal_spacing=0.08,
                        subplot_titles=[str(a) for a in anos])
    for col, ano in enumerate(anos, start=1):
        d, fonte = _dados_do_ano(df, ano, indicador)
        etapas = [e for e in ETAPAS if e in set(d["etapa"])]
        deltas = []
        for grupo, g in d.groupby("grupo"):
            g = g.set_index("etapa").reindex(etapas)
            fig.add_trace(go.Scatter(
                x=[ETAPAS[e] for e in etapas], y=g[indicador], name=grupo, legendgroup=grupo,
                showlegend=(col == 1), mode="lines+markers",
                line=dict(color=CORES_AREA[grupo], width=3),
                marker=dict(size=10, symbol=SIMBOLOS_AREA[grupo]),
                customdata=g["respondentes"],
                hovertemplate=f"{grupo}, %{{x}}: %{{y:.1f}}%<br>%{{customdata}} respondentes<extra></extra>",
            ), row=1, col=col)
            # variação do inscrito ao matriculado, escrita na ponta da linha (é a resposta da Q2)
            if {"inscritos", "matriculados"} <= set(etapas):
                delta = g.loc["matriculados", indicador] - g.loc["inscritos", indicador]
                deltas.append((grupo, g.loc["matriculados", indicador], delta))
        folga = 0.08 * (d[indicador].max() - d[indicador].min() or 1)
        for (grupo, _, delta), y in zip(deltas, espalhar([v for _, v, _ in deltas], folga)):
            fig.add_annotation(x=ETAPAS["matriculados"], y=y, text=f"{delta:+.1f} pp", showarrow=False,
                               xanchor="left", xshift=10, font=dict(color=CORES_AREA[grupo], size=11),
                               row=1, col=col)
        fig.layout.annotations[col - 1].text = f"{ano} ({'QASE' if fonte == 'qase' else 'Anuário'})"
    fig.update_layout(title=f"Do inscrito ao matriculado: {rotulo}", plot_bgcolor="white",
                      legend_title_text="", margin=dict(r=60), height=450)
    fig.update_yaxes(title_text=f"{rotulo} (%)", row=1, col=1)
    fig.update_yaxes(showgrid=True, gridcolor="LightGray")
    return fig
