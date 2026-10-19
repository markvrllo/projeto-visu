"""Gera um arquivo de indicadores FICTÍCIO só para testar o app antes de os PDFs serem processados.

Os números são inventados. Nunca use este arquivo no relatório.
O app mostra um aviso vermelho sempre que estiver usando estes dados.
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
rng = np.random.default_rng(0)

CURSOS = [
    ("Ciências de Computação", "ICMCSC", "São Carlos", True),
    ("Sistemas de Informação", "ICMCSC", "São Carlos", True),
    ("Engenharia de Computação", "EESC/ICMC", "São Carlos", True),
    ("Estatística e Ciência de Dados", "ICMCSC", "São Carlos", True),
    ("Matemática", "ICMCSC", "São Carlos", True),
    ("Medicina", "FM", "São Paulo", False),
    ("Direito", "FD", "São Paulo", False),
    ("Engenharia Civil", "EP", "São Paulo", False),
    ("Pedagogia", "FE", "São Paulo", False),
    ("Física", "IFSC", "São Carlos", False),
    ("Arquitetura", "IAU", "São Carlos", False),
    ("Letras", "FFLCH", "São Paulo", False),
]
ETAPAS = ["inscritos", "convocados", "chamados_1a", "matriculados"]

linhas = []
for nome, unidade, campus, icmc in CURSOS:
    base = rng.uniform(20, 45)
    for ano in range(2013, 2023):
        cota = min(max(ano - 2017, 0), 4) * 4  # efeito "cotas" inventado a partir de 2018
        for i, etapa in enumerate(ETAPAS):
            filtro = (3 - i) * rng.uniform(1, 4) * (1 if ano < 2018 else 0.5)  # o funil "filtra" menos depois
            ep = np.clip(base + 15 + cota - filtro + rng.normal(0, 2), 5, 95)
            linhas.append({
                "ano": ano, "etapa": etapa, "nivel": "curso", "curso": nome, "nome": nome,
                "unidade": unidade, "campus": campus, "icmc": icmc,
                "pct_escola_publica": ep,
                "pct_PPI": np.clip(ep * 0.45 + rng.normal(0, 2), 2, 80),
                "pct_renda_ate_3SM": np.clip(ep * 0.6 + rng.normal(0, 3), 2, 90),
                "pct_renda_mais_10SM": np.clip(60 - ep * 0.7 + rng.normal(0, 3), 2, 90),
                "pct_pai_superior": np.clip(90 - ep + rng.normal(0, 3), 5, 95),
                "pct_mae_superior": np.clip(92 - ep + rng.normal(0, 3), 5, 95),
                "pct_cursinho": np.clip(rng.uniform(30, 70), 5, 95),
                # modalidade só existe depois das cotas
                "pct_mod_EP": rng.uniform(20, 35) if ano >= 2018 else np.nan,
                "pct_mod_PPI": rng.uniform(10, 25) if ano >= 2018 else np.nan,
                "respondentes": int(rng.integers(40, 3000) / (i + 1)),
            })

saida = RAIZ / "data" / "processed" / "indicadores_DEMO.csv"
pd.DataFrame(linhas).to_csv(saida, index=False)
print(f"dados fictícios salvos em {saida}")
