import pandas as pd

from src.anuario_parser import FAIXA_TOPO, completar_faixa_de_renda

RENDA = "Qual é a renda mensal bruta da sua família, incluindo seu próprio rendimento?"
ESCOLA = "Onde você cursa ou cursou o ensino médio?"


def _linhas(com_topo, area=None):
    base = {"ano": 2026, "fonte": "anuario", "ingresso": "fuvest", "arquivo": "anuario_2026__fuvest_geral.pdf",
            "tabela": "3.04", "pagina": 4, "nivel": "usp" if area is None else "area", "area": area,
            "etapa": "inscritos"}
    linhas = [{**base, "pergunta": ESCOLA, "opcao": "Todo em escola pública", "n": 40, "pct": 40.0},
              {**base, "pergunta": ESCOLA, "opcao": "Todo em escola particular", "n": 60, "pct": 60.0},
              {**base, "pergunta": RENDA, "opcao": "Até 1 SM: até R$ 1.518,00", "n": 50, "pct": 50.0},
              {**base, "pergunta": RENDA, "opcao": "Acima de 30 SM até 50 SM: de R$ 45.540,01 até R$ 75.900,00",
               "n": 47, "pct": 47.0}]
    if com_topo:
        linhas.append({**base, "pergunta": RENDA, "opcao": "Acima de 50 SM", "n": 3, "pct": 3.0})
    return pd.DataFrame(linhas)


def test_repoe_a_faixa_de_cima_pelo_total_da_coluna():
    for area in (None, "Exatas"):
        df = completar_faixa_de_renda(_linhas(com_topo=False, area=area))
        nova = df[df["reconstruida"]]
        assert len(nova) == 1
        assert nova["opcao"].iloc[0] == FAIXA_TOPO
        assert nova["n"].iloc[0] == 3 and nova["pct"].iloc[0] == 3.0


def test_nao_mexe_quando_a_faixa_existe():
    df = completar_faixa_de_renda(_linhas(com_topo=True))
    assert not df["reconstruida"].any() and len(df) == 5
