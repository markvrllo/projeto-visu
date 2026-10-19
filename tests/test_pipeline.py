import pandas as pd

from src.harmonizacao import calcular_indicadores, categoria_renda, harmonizar, tipo_pergunta
from src.qase_parser import meta_do_nome, parse_linhas

# Trecho no formato esperado do QASE (montado à mão a partir da descrição do layout).
# Quando tiverem um PDF real, troquem por um trecho copiado de `--dump`.
TRECHO = """
Candidatos chamados para a 1a matrícula na seguinte carreira
Carreira 710−Computação
Curso 06−Bacharelado em Ciências de Computação − São Carlos [USP/ICMCSC]
3. Cor ou raça
Branca 60,0% (60)
Preta 10,0% (10) Parda 25,0% (25)
Amarela 5,0% (5)
6. Onde cursou o ensino médio?
Todo em escola pública 40,0% (40)
Todo em escola particular 50,0% (50)
Maior parte em escola pública 10,0% (10)
11. Qual a renda familiar mensal?
Inferior a 1 SM 5,0% (5)
De 1 a 3 SM 20,0% (20)
De 3 a 5 SM 25,0% (25)
De 10 a 15 SM 30,0% (30)
Acima de 20 SM 20,0% (20)
"""


def test_parse_reconhece_secao_e_opcoes():
    regs = parse_linhas(TRECHO.splitlines(), {"ano": 2021, "etapa": "chamados_1a", "nivel": "curso"})
    df = pd.DataFrame(regs)
    assert set(df["num_pergunta"]) == {3, 6, 11}
    assert df["unidade"].iloc[0] == "ICMCSC"
    assert df["campus"].iloc[0] == "São Carlos"
    assert df["curso"].iloc[0] == "Bacharelado em Ciências de Computação − São Carlos"
    parda = df[df["opcao"] == "Parda"].iloc[0]
    assert (parda["pct"], parda["n"]) == (25.0, 25)


def test_indicadores():
    regs = parse_linhas(TRECHO.splitlines(), {"ano": 2021, "etapa": "chamados_1a", "nivel": "curso"})
    ind = calcular_indicadores(harmonizar(pd.DataFrame(regs))).iloc[0]
    assert ind["pct_PPI"] == 35.0
    assert ind["pct_escola_publica"] == 50.0
    assert ind["pct_renda_ate_3SM"] == 25.0
    assert ind["pct_renda_mais_10SM"] == 50.0
    assert bool(ind["icmc"])


def test_categorias_e_perguntas():
    assert categoria_renda("Inferior a 1 SM") == "ate_3SM"
    assert categoria_renda("De 5 a 7 SM") == "3a10SM"
    assert categoria_renda("Acima de 20 SM") == "mais_10SM"
    assert tipo_pergunta("Qual a escolaridade da sua mãe?") == "escolaridade_mae"
    assert tipo_pergunta("Cor ou raça, apenas para quem cursou todo o ensino médio em escola pública") is None
    assert tipo_pergunta("Onde cursou o ensino médio?") == "escola_medio"


def test_meta_do_nome():
    m = meta_do_nome("FUVEST_2021_qase_matriculados_no_final_curso.pdf")
    assert (m["ano"], m["etapa"], m["nivel"]) == (2021, "matriculados", "curso")
    m = meta_do_nome("fuvest_2017_qase_umatr_USP_cur.pdf")
    assert (m["ano"], m["etapa"], m["nivel"]) == (2017, "matriculados", "curso")
