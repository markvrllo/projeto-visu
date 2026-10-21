"""Gera um arquivo de indicadores FICTÍCIO só para testar o app antes de os PDFs serem processados.

Os números são inventados. Nunca use este arquivo no relatório.
O app mostra um aviso vermelho sempre que estiver usando estes dados.

Tem as mesmas colunas e a mesma cobertura do indicadores.csv real (ver docs/divisao_tarefas.md):
  - QASE 2013–2022: inscritos e matriculados; carreira, área e USP; modalidades AC/EP/PPI de 2019 a 2022;
  - Anuário 2022–2026: inscritos, convocados e matriculados; USP e área; Fuvest, ENEM-USP (2025+)
    e Provão Paulista (2026); PPI e mulheres só a partir de 2024; pai/mãe vazios.
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
rng = np.random.default_rng(0)

COLUNAS = ["ano", "fonte", "ingresso", "etapa", "nivel", "area", "cod_carreira", "carreira", "unidade",
           "modalidade", "respondentes", "pct_escola_publica", "pct_PPI", "pct_renda_ate_3SM",
           "pct_renda_mais_10SM", "pct_pai_superior", "pct_mae_superior", "pct_cursinho", "pct_mulheres",
           "pct_tecnico"]
CARREIRAS = [  # (código, nome, unidade, área) — nomes reais, números inventados
    (710, "Computação", "ICMC", "Exatas"), (720, "Engenharia (São Carlos)", "EESC", "Exatas"),
    (730, "Engenharia (Poli)", "EP", "Exatas"), (750, "Física", "IF", "Exatas"),
    (815, "Medicina", "FM", "Biológicas"), (830, "Odontologia", "FO", "Biológicas"),
    (860, "Ciências Biológicas", "IB", "Biológicas"), (870, "Enfermagem", "EE", "Biológicas"),
    (200, "Direito", "FD", "Humanas"), (230, "Letras", "FFLCH", "Humanas"),
    (245, "Pedagogia", "FE", "Humanas"), (100, "Administração", "FEA", "Humanas"),
]
MOD_DESLOC = {"AC": -12, "EP": 30, "PPI": 25}


def perfil(base, ano, etapa, mod="Todas"):
    cota = min(max(ano - 2017, 0), 5) * 4  # efeito "cotas" inventado
    filtro = (6 if etapa == "matriculados" else 3 if etapa == "convocados" else 0) * (1 if ano < 2018 else 0.4)
    ep = np.clip(base + cota - filtro + MOD_DESLOC.get(mod, 0) + rng.normal(0, 2), 5, 98)
    return {
        "pct_escola_publica": ep,
        "pct_PPI": np.clip(ep * 0.45 + rng.normal(0, 2), 2, 80),
        "pct_renda_ate_3SM": np.clip(ep * 0.6 + rng.normal(0, 3), 2, 90),
        "pct_renda_mais_10SM": np.clip(60 - ep * 0.7 + rng.normal(0, 3), 2, 90),
        "pct_pai_superior": np.clip(90 - ep + rng.normal(0, 3), 5, 95),
        "pct_mae_superior": np.clip(92 - ep + rng.normal(0, 3), 5, 95),
        "pct_cursinho": np.clip(rng.uniform(30, 70), 5, 95),
        "pct_mulheres": np.clip(rng.uniform(30, 65), 5, 95),
        "pct_tecnico": np.clip(ep * 0.3 + rng.normal(0, 2), 1, 60),
    }


linhas = []
for ano in range(2013, 2023):
    for etapa in ["inscritos", "matriculados"]:
        mods = ["Todas"] + (["AC", "EP", "PPI"] if ano >= 2019 else [])
        for mod in mods:
            for cod, nome, unidade, area in CARREIRAS:
                linhas.append({"ano": ano, "fonte": "qase", "ingresso": "fuvest", "etapa": etapa, "nivel": "carreira",
                               "area": area, "cod_carreira": cod, "carreira": nome, "unidade": unidade,
                               "modalidade": mod, "respondentes": int(rng.integers(30, 3000)),
                               **perfil(rng.uniform(15, 45), ano, etapa, mod)})
            for area in ["Biológicas", "Exatas", "Humanas"]:
                linhas.append({"ano": ano, "fonte": "qase", "ingresso": "fuvest", "etapa": etapa, "nivel": "area",
                               "area": area, "modalidade": mod, "respondentes": int(rng.integers(3000, 40000)),
                               **perfil(30, ano, etapa, mod)})
            linhas.append({"ano": ano, "fonte": "qase", "ingresso": "fuvest", "etapa": etapa, "nivel": "usp",
                           "modalidade": mod, "respondentes": int(rng.integers(8000, 120000)),
                           **perfil(30, ano, etapa, mod)})

for ano in range(2022, 2027):
    vias = ["fuvest"] + (["enem-usp"] if ano >= 2025 else []) + (["provao-paulista"] if ano >= 2026 else [])
    for via in vias:
        etapas = ["inscritos", "convocados", "matriculados"] if via == "fuvest" else ["inscritos", "matriculados"]
        for etapa in etapas:
            for nivel, area in [("usp", None), ("area", "Biológicas"), ("area", "Exatas"), ("area", "Humanas")]:
                p = perfil(30 + (15 if via != "fuvest" else 0), ano, etapa)
                p["pct_pai_superior"] = p["pct_mae_superior"] = np.nan  # o Anuário não separa pai e mãe
                if ano < 2024:
                    p["pct_PPI"] = p["pct_mulheres"] = np.nan
                linhas.append({"ano": ano, "fonte": "anuario", "ingresso": via, "etapa": etapa, "nivel": nivel,
                               "area": area, "modalidade": "Todas", "respondentes": int(rng.integers(500, 100000)), **p})

saida = RAIZ / "data" / "processed" / "indicadores_DEMO.csv"
pd.DataFrame(linhas).reindex(columns=COLUNAS).to_csv(saida, index=False, float_format="%.2f")
print(f"dados fictícios salvos em {saida}")
