import sys
from pathlib import Path
from types import SimpleNamespace

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from coletar_fuvest import classificar, links_da_pagina  # noqa: E402
from picotar_pdfs import cabecalho, picotar, secoes  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
AMOSTRA = FIXTURES / "FUVEST_2021_qase_chamados_matricula_1_curso_amostra.pdf"

# Trecho no formato da página https://www.fuvest.br/acervo-vestibular-2022/ (links reais, HTML simplificado)
HTML_2022 = """
<div class="estatisticas">
  <h3>Questionário de Avaliação Socioeconômica</h3>
  <a href="/wp-content/uploads/FUVEST_2022_qase_inscritos_carreira.pdf">Inscritos</a>
  <a href="/wp-content/uploads/FUVEST_2022_qase_convocados_carreira.pdf">Convocados para a 2ª Fase</a>
  <a href="/wp-content/uploads/FUVEST_2022_qase_chamados_matricula_1_carreira.pdf">Chamados para a 1ª Matrícula (carreira)</a>
  <a href="/wp-content/uploads/FUVEST_2022_qase_chamados_matricula_1_curso.pdf">Chamados para a 1ª Matrícula (curso)</a>
  <a href="/wp-content/uploads/FUVEST_2022_qase_matriculados_no_final_carreira.pdf">Matriculados Finais (carreira)</a>
  <a href="/wp-content/uploads/FUVEST_2022_qase_matriculados_no_final_curso.pdf">Matriculados Finais (curso)</a>
  <a href="/wp-content/uploads/FUVEST_2022_inscritos_por_opcao_de_curso.pdf">Inscritos por Opção de Curso</a>
  <a href="/wp-content/uploads/fuvest_2022_candidato_vaga.pdf">Relação Candidato Vaga</a>
</div>
<a href="https://www.fuvest.br/wp-content/uploads/fuvest_2022_notas_de_corte.pdf">Notas de Corte</a>
<a href="https://app.fuvest.br/login">Área do Candidato</a>
<a href="/wp-content/uploads/fuvest2026-chamada-1-notas-minimas.pdf">Relação de notas mínimas dos candidatos aprovados em 1ª chamada</a>
<a href="/wp-content/uploads/fuvest_2017_qase_umatr_USP_cur.pdf">Matriculados Finais (cursos USP)</a>
"""


def test_coleta_classifica_links():
    links = list(links_da_pagina(HTML_2022, "https://www.fuvest.br/acervo-vestibular-2022/"))
    assert links[0][0] == "https://www.fuvest.br/wp-content/uploads/FUVEST_2022_qase_inscritos_carreira.pdf"
    tipos = [(Path(u).name, classificar(u, t)) for u, t in links]
    info = {nome: c for nome, c in tipos if c}
    assert info["FUVEST_2022_qase_inscritos_carreira.pdf"] == {"tipo": "qase", "etapa": "inscritos", "nivel": "carreira"}
    assert info["FUVEST_2022_qase_chamados_matricula_1_curso.pdf"]["nivel"] == "curso"
    assert info["FUVEST_2022_qase_matriculados_no_final_curso.pdf"]["etapa"] == "matriculados"
    assert info["fuvest_2017_qase_umatr_USP_cur.pdf"] == {"tipo": "qase", "etapa": "matriculados", "nivel": "curso"}
    assert info["fuvest_2022_notas_de_corte.pdf"]["tipo"] == "nota_de_corte"
    assert info["fuvest_2022_candidato_vaga.pdf"]["tipo"] == "candidato_vaga"
    assert info["fuvest2026-chamada-1-notas-minimas.pdf"]["tipo"] == "notas_minimas"
    # links que não interessam ficam de fora
    assert "FUVEST_2022_inscritos_por_opcao_de_curso.pdf" not in info
    assert "login" not in info
    assert sum(c["tipo"] == "qase" for c in info.values()) == 7


def test_picotar_amostra_real(tmp_path):
    grupos, ignoradas = secoes(PdfReader(AMOSTRA))
    assert ignoradas == 2  # as duas páginas de índice
    assert [cab[:3] for cab, _ in grupos] == [("100", grupos[0][0][1], "01"), ("100", grupos[1][0][1], "02")]
    assert [len(p) for _, p in grupos] == [8, 8]

    filtro = SimpleNamespace(unidade=None, carreira=None, campus=None)
    assert picotar(AMOSTRA, tmp_path, filtro) == 2
    nomes = sorted(p.name for p in tmp_path.iterdir())
    assert nomes[0] == "FUVEST_2021_qase_chamados_matricula_1_curso_amostra__100-01_administracao-diurno-ribeirao-preto.pdf"

    so_icmc = SimpleNamespace(unidade=["ICMC"], carreira=None, campus=None)
    assert picotar(AMOSTRA, tmp_path / "icmc", so_icmc) == 0


def test_cabecalho_milhar_e_modalidade():
    # texto do pypdf em fuvest_2013_qase_inscritos_car.pdf p. 635 e FUVEST_2022_..._carreira.pdf p. 1941
    p2013 = "Carreira 710−Computação\nCopyright(c) 2013\nDos 3.229 candidatos, 3.229 (100,0%)\n330 vagas.\n"
    assert cabecalho(p2013) == ("710", "Computação", "", "", "")
    p2022 = ("Carreira 735−Engenharia Civil (São Carlos)\nDos 26 candidatos, 26 (100,0%)\n"
             "26 vagas.\nModalidade de Acesso: Ampla Concorrência\n")
    assert cabecalho(p2022)[4] == "Ampla Concorrência"
    assert cabecalho(p2022.replace("Modalidade de Acesso: Ampla Concorrência", "Todas as Modalidades de Acesso"))[4] == "Todas"


def test_classificar_anuario():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from recortar_anuario import classificar as classificar_anuario

    # sumário repete o título, mas sem "Quant.": não pode entrar
    sumario = "Tabela 3.04 Características pessoais dos candidatos ao vestibular da FUVEST,\nem 2023"
    assert classificar_anuario(sumario) is None
    # textos reais (resumidos) do AnuarioUSP_2025.pdf, p. 237 e p. 332
    fuvest = ("Tabela 3.04 Características pessoais dos candidatos ao vestibular da FUVEST, em 2025\n"
              "Candidatos Treineiros\nInsc. Conv. Matr. Insc. Conv. Matr.\nQuant. %")
    assert classificar_anuario(fuvest) == "fuvest_geral"
    assert classificar_anuario(fuvest.replace("FUVEST, em", "FUVEST, por Área de Conhecimento, em")) == "fuvest_por_area"
    enem = "Tabela 3.37 - Características pessoais dos candidatos do ENEM-USP, em 2025\nInsc. Conv. Matr.\nQuant. %"
    assert classificar_anuario(enem) == "enem-usp_geral"
    provao = "Tabela 3.40 Características pessoais dos candidatos do Provão Paulista, em 2026\nQuant. %"
    assert classificar_anuario(provao) == "provao-paulista_geral"
    cand = "Tabela 3.03 - Relação número de candidatos por vaga no vestibular da FUVEST\nUnidade/Curso 2024"
    assert classificar_anuario(cand) is None
    assert classificar_anuario(cand, com_candidato_vaga=True) == "fuvest_candidato_vaga"
