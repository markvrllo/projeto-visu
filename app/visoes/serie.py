import plotly.graph_objects as go
import pandas as pd

from dados import espalhar

def criar_grafico_serie(df, indicador, etapa, rotulo=None):
    """
    Cria a Visão 1: Série temporal (2013-2026) para a USP e as 3 áreas.
    """
    # só Fuvest e o total das modalidades: AC/EP/PPI (2019-2022) e ENEM-USP/Provão (2025-2026)
    # são outros grupos de pessoas e não podem entrar na mesma linha
    df_q1 = df[(df['etapa'] == etapa) & (df['nivel'].isin(['usp', 'area']))
               & (df['ingresso'] == 'fuvest') & (df['modalidade'] == 'Todas')].copy()
    df_q1['area_plot'] = df_q1.apply(lambda x: 'USP' if x['nivel'] == 'usp' else x['area'], axis=1)
    # já sobra uma linha por ano, fonte e área; as % vêm das contagens, então não se tira média
    df_agg = df_q1[['ano', 'fonte', 'area_plot', 'respondentes', indicador]].dropna(subset=[indicador])
    rotulo = rotulo or indicador

    fig = go.Figure()
    if df_agg.empty:
        fig.add_annotation(text="Sem dados para este indicador nesta etapa", showarrow=False,
                           x=0.5, y=0.5, xref="paper", yref="paper")
        return fig

    cores = {
        'USP': '#000000',
        'Biológicas': '#009E73',
        'Exatas': '#0072B2',
        'Humanas': '#E69F00'
    }
    # forma do marcador por área, para não depender só da cor
    simbolos = {'USP': 'circle', 'Biológicas': 'diamond', 'Exatas': 'triangle-up', 'Humanas': 'square'}
    hover = '%{x}: %{y:.1f}%<br>%{customdata} respondentes<extra>%{fullData.name}</extra>'

    areas = df_agg['area_plot'].unique()
    rotulos = []

    for area in areas:
        df_area = df_agg[df_agg['area_plot'] == area].sort_values('ano')
        cor = cores.get(area, '#333333')
        
        df_qase = df_area[df_area['fonte'] == 'qase']
        if not df_qase.empty:
            fig.add_trace(go.Scatter(
                x=df_qase['ano'], y=df_qase[indicador],
                mode='lines+markers', name=f'{area} (QASE)',
                line=dict(color=cor, width=3), marker=dict(size=8, symbol=simbolos.get(area)),
                customdata=df_qase['respondentes'], hovertemplate=hover,
                showlegend=False
            ))

        df_anuario = df_area[df_area['fonte'] == 'anuario']
        if not df_anuario.empty:
            # ano sem dado (ex.: áreas em 2023) vira NaN para a linha não ligar por cima da lacuna
            anos = range(df_anuario['ano'].min(), df_anuario['ano'].max() + 1)
            df_anuario = df_anuario.set_index('ano').reindex(anos).rename_axis('ano').reset_index()
            fig.add_trace(go.Scatter(
                x=df_anuario['ano'], y=df_anuario[indicador],
                mode='lines+markers', name=f'{area} (Anuário)',
                line=dict(color=cor, width=3, dash='dot'),
                marker=dict(size=8, symbol=simbolos.get(area, 'circle') + '-open', line=dict(width=2)),
                customdata=df_anuario['respondentes'], hovertemplate=hover,
                showlegend=False
            ))
            
        ultimo_ano = df_area['ano'].max()
        ultimo_valor = df_area[df_area['ano'] == ultimo_ano][indicador].values[-1]
        rotulos.append((area, ultimo_ano, ultimo_valor, cor))

    # rótulo direto no fim de cada linha, afastando os que ficariam sobrepostos
    folga = 0.06 * (df_agg[indicador].max() - df_agg[indicador].min() or 1)
    ys = espalhar([r[2] for r in rotulos], folga)
    for (area, ultimo_ano, _, cor), y in zip(rotulos, ys):
        fig.add_annotation(
            x=ultimo_ano + 0.3, y=y,
            text=f"<b>{area}</b>", showarrow=False,
            font=dict(color=cor, size=12), xanchor='left', yanchor='middle'
        )
    
    # 2022 está nas duas fontes: os dois pontos aparecem, e a diferença entre eles é de método
    fig.add_vline(x=2022, line_width=1.5, line_dash="dash", line_color="gray")
    fig.add_annotation(
        x=2022, y=df_agg[indicador].max(),
        text="Mudança de Fonte<br>(QASE → Anuário)",
        showarrow=False, xanchor='center', yanchor='bottom',
        font=dict(size=10, color="gray")
    )

    if indicador in ['pct_escola_publica', 'pct_PPI']:
        cotas_info = {2018: '37%', 2019: '40%', 2020: '45%', 2021: '50%'}
        fig.add_vrect(
            x0=2017.5, x1=2021.5,
            fillcolor="#F0E442", opacity=0.15, layer="below", line_width=0,
            annotation_text="Implementação de Cotas (2018-2021)",
            annotation_position="top left", annotation_font_size=10
        )
        for ano, pct in cotas_info.items():
            fig.add_annotation(
                x=ano, y=df_agg[indicador].min() * 0.9,
                text=f"Meta:<br>{pct}", showarrow=False,
                font=dict(size=9, color="darkgray"), yanchor='top'
            )

    fig.update_layout(
        title=f"Evolução Temporal: {rotulo} ({etapa.title()})",
        xaxis_title="Ano", yaxis_title=f"{rotulo} (%)",
        margin=dict(r=100), plot_bgcolor='white', hovermode="x unified"
    )
    
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig.update_xaxes(showgrid=False)

    return fig