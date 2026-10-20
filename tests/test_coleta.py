import sys
from pathlib import Path
from types import SimpleNamespace

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from coletar_fuvest import classificar, links_da_pagina  # noqa: E402
from picotar_pdfs import picotar, secoes  # noqa: E402

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
