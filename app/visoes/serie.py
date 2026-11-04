import plotly.graph_objects as go
import pandas as pd

def criar_grafico_serie(df, indicador, etapa):
    """
    Cria a Visão 1: Série temporal (2013-2026) para a USP e as 3 áreas.
    """
    df_q1 = df[(df['etapa'] == etapa) & (df['nivel'].isin(['usp', 'area']))].copy()
    df_q1['area_plot'] = df_q1.apply(lambda x: 'USP' if x['nivel'] == 'usp' else x['area'], axis=1)
    df_agg = df_q1.groupby(['ano', 'fonte', 'area_plot'], as_index=False)[indicador].mean()
    
    fig = go.Figure()

    cores = {
        'USP': '#000000',
        'Biológicas': '#009E73',
        'Exatas': '#0072B2',
        'Humanas': '#E69F00'
    }

    areas = df_agg['area_plot'].unique()

    for area in areas:
        df_area = df_agg[df_agg['area_plot'] == area].sort_values('ano')
        cor = cores.get(area, '#333333')
        
        df_qase = df_area[df_area['fonte'] == 'qase']
        if not df_qase.empty:
            fig.add_trace(go.Scatter(
                x=df_qase['ano'], y=df_qase[indicador],
                mode='lines+markers', name=f'{area} (QASE)',
                line=dict(color=cor, width=3), marker=dict(size=8),
                showlegend=False
            ))

        df_anuario = df_area[df_area['fonte'] == 'anuario']
        if not df_anuario.empty:
            fig.add_trace(go.Scatter(
                x=df_anuario['ano'], y=df_anuario[indicador],
                mode='lines+markers', name=f'{area} (Anuário)',
                line=dict(color=cor, width=3, dash='dot'),
                marker=dict(size=8, symbol='square'),
                showlegend=False
            ))
            
        ultimo_ano = df_area['ano'].max()
        ultimo_valor = df_area[df_area['ano'] == ultimo_ano][indicador].values[0]
        
        fig.add_annotation(
            x=ultimo_ano + 0.3, y=ultimo_valor,
            text=f"<b>{area}</b>", showarrow=False,
            font=dict(color=cor, size=12), xanchor='left', yanchor='middle'
        )
    
    fig.add_vline(x=2022.5, line_width=1.5, line_dash="dash", line_color="gray")
    fig.add_annotation(
        x=2022.5, y=df_agg[indicador].max(),
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
        title=f"Evolução Temporal: {indicador} ({etapa.title()})",
        xaxis_title="Ano", yaxis_title=f"{indicador} (%)",
        margin=dict(r=100), plot_bgcolor='white', hovermode="x unified"
    )
    
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig.update_xaxes(showgrid=False)

    return fig