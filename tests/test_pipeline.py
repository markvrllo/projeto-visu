import pandas as pd

from src.harmonizacao import calcular_indicadores, categoria_renda, harmonizar, tipo_pergunta
from src.qase_parser import meta_do_nome, parse_linhas

# Trecho real (resumido) de FUVEST_2021_qase_chamados_matricula_1_curso.pdf, páginas 3 a 9,
# com o índice da p. 1 no começo para garantir que ele é ignorado.
TRECHO = """
3 Carreira 100−Administração, Ciências Contábeis, Economia, Economia e 483 Carreira 265−Publicidade e Propaganda
Curso 01−Administração − Diurno − Ribeirão Preto [USP/FEARP] Curso 61−Publicidade e Propaganda − Matutino [USP/ECA]
FUVEST 2021
Questionário de Avaliação Socioeconômica 3
Candidatos que foram chamados para a 1ª matrícula no seguinte curso:
Dos 42 candidatos, 42 (100,0%) Carreira 100−Administração, Ciências Contábeis, Economia, Economia e
entregaram o questionário respondido.
42 vagas. Curso 01−Administração − Diurno − Ribeirão Preto [USP/FEARP]
02 Onde você cursou/cursa o ensino médio?
52,4% Todo em escola pública. (22)
47,6% Todo em escola particular. (20)
0,0% Maior parte em escola pública. (0)
0,0% No exterior. (0)
42 respostas
05 Você frequenta ou frequentou cursinho pré−vestibular?
42,9% Não. (18)
16,7% Sim, durante um ano. (7)
40,5% Sim, já é o segundo ano em que frequento cursinho. (17)
42 respostas
11 Qual é a renda bruta mensal da sua família, incluindo seu próprio rendimento? O valor do salário mínimo
(SM) é R$ 1.045,00.
2,4% Até 1 SM − até R$ 1.045,00. (1)
14,3% Acima de 2 até 3 SM − de R$ 2.090,01 até R$ 3.135,00. (6)
54,8% Acima de 3 até 5 SM − de R$ 3.135,01 até R$ 5.225,00. (23)
28,6% Acima de 20 até 30 SM − de R$ 20.900,01 até R$ 31.350,00. (12)
42 respostas
Copyright(c) 2021−FUVEST (Fundação Universitária para o Vestibular)−Universidade de São Paulo. 07/07/2021|14:19:17|QASE−01
FUVEST 2021
Questionário de Avaliação Socioeconômica 5
Candidatos que foram chamados para a 1ª matrícula no seguinte curso:
Dos 42 candidatos, 42 (100,0%) Carreira 100−Administração, Ciências Contábeis, Economia, Economia e
entregaram o questionário respondido.
42 vagas. Curso 01−Administração − Diurno − Ribeirão Preto [USP/FEARP]
15 Qual é o nível de instrução de seu pai ou do homem responsável por você?
21,4% Ensino médio completo. (9)
21,4% Ensino superior completo. (9)
21,4% Pós−graduação completa. (9)
4,8% Não sei. (2)
31,0% Ensino fundamental incompleto. (13)
42 respostas
18
A partir da apresentação de algumas ocupações divididas e ordenadas abaixo, indique o grupo que contempla a ocupação
mais próxima do(a) principal responsável pelo domicílio (no caso de desempregado, indique a última ocupação).
50,0% Grupo 4: Professor (de ensino fundamental, médio, educação infantil, de idiomas, música, artes, etc), técnico... (21)
50,0% Grupo 5: Médico, engenheiro, dentista, psicólogo, economista, advogado, juiz, defensor, delegado, promotor, tenente, ... (21)
42 respostas
23 Em qual modalidade de acesso você se inscreveu?
47,6% Ampla Concorrência (20)
31,0% Escola Pública (13)
21,4% Preto, Pardo ou Indígena (9)
42 respostas
24 Qual é a sua cor ou etnia?
73,8% Branca (31)
19,0% Preta (8)
7,1% Parda (3)
0,0% Indigena (0)
42 respostas
31 Para os candidatos que cursaram todo o Ensino Médio em Escolas Públicas: Qual seu sexo?
81,8% Masculino (9)
18,2% Feminino (2) 2 PPI
11 respostas
33 Região Intermediária de Origem.
21,4% Região Intermediária de São Paulo (3501) (9)
78,6% Outra (33)
42 respostas
"""


def registros():
    return pd.DataFrame(parse_linhas(TRECHO.splitlines(), {"ano": 2021, "etapa": "chamados_1a", "nivel": "curso"}))


def test_parse_reconhece_secao_e_opcoes():
    df = registros()
    assert set(df["num_pergunta"]) == {2, 5, 11, 15, 18, 23, 24, 31, 33}
    linha = df.iloc[0]
    assert (linha["cod_curso"], linha["unidade"], linha["campus"], linha["vagas"]) == ("01", "FEARP", "Ribeirão Preto", 42)
    assert linha["curso"] == "Administração − Diurno − Ribeirão Preto"
    # enunciado em duas linhas e número sozinho na linha
    assert df[df["num_pergunta"] == 11]["pergunta"].iloc[0].endswith("(SM) é R$ 1.045,00.")
    assert df[df["num_pergunta"] == 18]["pergunta"].iloc[0].startswith("A partir da apresentação")
    # contagem é o último parêntese, mesmo com código da região ou lixo no fim
    sp = df[df["opcao"].str.startswith("Região Intermediária de São Paulo")].iloc[0]
    assert (sp["opcao"], sp["n"]) == ("Região Intermediária de São Paulo (3501)", 9)
    assert df[(df["num_pergunta"] == 31) & (df["opcao"] == "Feminino")]["n"].iloc[0] == 2
    # cada pergunta soma o total de "42 respostas"
    assert (df[df["num_pergunta"] != 31].groupby("num_pergunta")["n"].sum() == 42).all()


def test_indicadores():
    ind = calcular_indicadores(harmonizar(registros())).iloc[0]
    assert round(ind["pct_PPI"], 1) == 26.2
    assert round(ind["pct_escola_publica"], 1) == 52.4
    assert round(ind["pct_renda_ate_3SM"], 1) == 16.7        # até 1 SM + 2 a 3 SM
    assert round(ind["pct_renda_mais_10SM"], 1) == 28.6
    assert round(ind["pct_pai_superior"], 1) == 45.0          # "Não sei" fora do denominador: 18/40
    assert round(ind["pct_cursinho"], 1) == 57.1
    assert (round(ind["pct_mod_AC"], 1), round(ind["pct_mod_EP"], 1), round(ind["pct_mod_PPI"], 1)) == (47.6, 31.0, 21.4)
    assert not bool(ind["icmc"])


def test_categorias_e_perguntas():
    assert categoria_renda("Até 1 SM − até R$ 1.045,00.") == "ate_3SM"
    assert categoria_renda("Acima de 2 até 3 SM − de R$ 2.090,01 até R$ 3.135,00.") == "ate_3SM"
    assert categoria_renda("Acima de 3 até 5 SM − de R$ 3.135,01 até R$ 5.225,00.") == "3a10SM"
    assert categoria_renda("Acima de 10 até 15 SM − de R$ 10.45,01 até R$ 15.675,00.") == "mais_10SM"
    assert tipo_pergunta("Qual é o nível de instrução de sua mãe ou da mulher responsável por você?") == "escolaridade_mae"
    assert tipo_pergunta("Para os candidatos que cursaram todo o Ensino Médio em Escolas Públicas: "
                         "Onde você cursou o ensino fundamental?") is None
    assert tipo_pergunta("Candidatos que se autodeclararam do grupo PPI: Qual seu sexo?") is None
    assert tipo_pergunta("Onde você cursou/cursa o ensino médio?") == "escola_medio"
    assert tipo_pergunta("Qual é a sua cor ou etnia?") == "cor_raca"


def test_meta_do_nome():
    m = meta_do_nome("FUVEST_2021_qase_matriculados_no_final_curso.pdf")
    assert (m["ano"], m["etapa"], m["nivel"]) == (2021, "matriculados", "curso")
    m = meta_do_nome("fuvest_2017_qase_umatr_USP_cur.pdf")
    assert (m["ano"], m["etapa"], m["nivel"]) == (2017, "matriculados", "curso")
