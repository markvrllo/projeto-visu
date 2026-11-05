"""Carrega o indicadores.csv uma vez e guarda o que as visões compartilham (rótulos, cores, carreiras do ICMC)."""
from pathlib import Path

import pandas as pd

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
    "pct_mulheres": "% mulheres",
    "pct_tecnico": "% ensino médio técnico",
}
CURTOS = {"pct_escola_publica": "Esc. pública", "pct_PPI": "PPI", "pct_renda_ate_3SM": "Renda ≤3 SM",
          "pct_renda_mais_10SM": "Renda >10 SM", "pct_pai_superior": "Pai superior",
          "pct_mae_superior": "Mãe superior", "pct_cursinho": "Cursinho", "pct_mulheres": "Mulheres",
          "pct_tecnico": "Técnico"}
ETAPAS = {"inscritos": "Inscritos", "convocados": "Convocados", "matriculados": "Matriculados"}

# Okabe-Ito (segura para daltonismo); as mesmas cores por área em todas as visões
CORES_AREA = {"USP": "#000000", "Biológicas": "#009E73", "Exatas": "#0072B2", "Humanas": "#E69F00"}
SIMBOLOS_AREA = {"USP": "circle", "Biológicas": "diamond", "Exatas": "triangle-up", "Humanas": "square"}

# a coluna `unidade` vem vazia (os PDFs por carreira não trazem a unidade), então o ICMC sai pelo código
CARREIRAS_ICMC = {710, 765, 791, 810, 815, 835, 875}

ANOS = sorted(df["ano"].unique())
ANOS_CARREIRA = sorted(df.loc[df["nivel"] == "carreira", "ano"].unique())


def fuvest_total(d):
    """Só a Fuvest e o total das modalidades: a base comum às 3 visões da 1ª entrega."""
    return d[(d["ingresso"] == "fuvest") & (d["modalidade"] == "Todas")]


def espalhar(valores, folga):
    """Posições y para rótulos que ficariam um em cima do outro: afasta cada um do anterior em pelo menos `folga`."""
    ordem = sorted(range(len(valores)), key=lambda i: valores[i])
    pos = list(valores)
    for anterior, atual in zip(ordem, ordem[1:]):
        pos[atual] = max(pos[atual], pos[anterior] + folga)
    return pos
