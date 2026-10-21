"""Recorta do Anuário Estatístico da USP só as tabelas de perfil dos candidatos.

A partir de 2023 a Fuvest não publica mais o QASE em PDF. O mesmo questionário aparece
resumido no Anuário Estatístico da USP (capítulo 3), em tabelas com colunas
Insc. / Conv. / Matr. (inscritos, convocados, matriculados):

    Tabela 3.04  Características pessoais dos candidatos ao vestibular da FUVEST, em AAAA
    Tabela 3.05  ... da FUVEST, por Área de Conhecimento, em AAAA
    Tabela 3.37  Características pessoais dos candidatos do ENEM-USP, em AAAA        (2025+)
    Tabela 3.38  ... do ENEM-USP, por Área de Conhecimento, em AAAA                  (2025+)
    Tabela 3.40  Características pessoais dos candidatos do Provão Paulista, em AAAA (2026+)
    Tabela 3.41  ... do Provão Paulista, por Área de Conhecimento, em AAAA           (2026+)

Os números das tabelas mudam de um anuário para outro, então a busca é pelo título.
Cada tabela vira um PDF. Diferente do QASE, o anuário só traz o total da USP e as três
áreas (Biológicas, Exatas, Humanas): não há quebra por carreira, curso ou modalidade.

Uso:
    python scripts/recortar_anuario.py AnuarioUSP_2023.pdf AnuarioUSP_2024.pdf
    python scripts/recortar_anuario.py AnuarioUSP_*.pdf -o data/raw/anuario
    python scripts/recortar_anuario.py AnuarioUSP_2026.pdf --com-candidato-vaga
"""
import argparse
import logging
import re
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

logging.getLogger("pypdf").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parents[1]
INGRESSO = {"vestibular da FUVEST": "fuvest", "ENEM-USP": "enem-usp", "Provão Paulista": "provao-paulista"}
RE_PERFIL = re.compile(r"Características\s+pessoais\s+dos\s+candidatos\s+(?:ao|do)\s+(?:vestibular\s+do\s+)?"
                       r"(vestibular\s+da\s+FUVEST|ENEM-USP|Provão\s+Paulista)(,\s+por\s+Área)?")
RE_CAND_VAGA = re.compile(r"Relação\s+número\s+de\s+candidatos\s+por\s+vaga\s+no\s+(?:vestibular\s+d[oa]\s+)?"
                          r"(FUVEST|ENEM-USP|Provão\s+Paulista)")
RE_ANO = re.compile(r"(?:em|Unidade/Curso)\s+(20\d\d)")


def classificar(texto, com_candidato_vaga=False):
    """Diz qual tabela está na página, como 'fuvest_geral' ou 'enem-usp_por_area', ou None.

    Exige 'Quant.' (perfil) ou 'Unidade/Curso' (candidato/vaga) para não pegar o sumário,
    que repete os mesmos títulos.
    """
    texto = " ".join(texto.split())
    if m := RE_PERFIL.search(texto):
        if "Quant." not in texto:
            return None
        ingresso = INGRESSO[" ".join(m.group(1).split())]
        return f"{ingresso}_{'por_area' if m.group(2) else 'geral'}"
    if com_candidato_vaga and (m := RE_CAND_VAGA.search(texto)) and "Unidade/Curso" in texto:
        nome = " ".join(m.group(1).split())
        ingresso = "fuvest" if nome == "FUVEST" else INGRESSO[nome]
        return f"{ingresso}_candidato_vaga"
    return None


def recortar(arquivo, destino, com_candidato_vaga=False):
    """Grava um PDF por tabela encontrada; devolve {tabela: [páginas (1-based)]}."""
    leitor = PdfReader(arquivo)
    tabelas, ano = {}, None
    for i, pagina in enumerate(leitor.pages):
        texto = pagina.extract_text() or ""
        tabela = classificar(texto, com_candidato_vaga)
        if tabela is None:
            continue
        tabelas.setdefault(tabela, []).append(i)
        if ano is None and (m := RE_ANO.search(" ".join(texto.split()))):
            ano = m.group(1)

    ano = ano or (re.search(r"20\d\d", Path(arquivo).stem) or [""])[0]
    destino.mkdir(parents=True, exist_ok=True)
    for tabela, paginas in tabelas.items():
        escritor = PdfWriter()
        for i in paginas:
            escritor.add_page(leitor.pages[i])
        with open(destino / f"anuario_{ano}__{tabela}.pdf", "wb") as f:
            escritor.write(f)
    return {t: [i + 1 for i in p] for t, p in tabelas.items()}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfs", nargs="+")
    ap.add_argument("-o", "--destino", default=str(RAIZ / "data" / "raw" / "anuario"))
    ap.add_argument("--com-candidato-vaga", action="store_true",
                    help="também recorta a relação candidato/vaga por curso (Tabela 3.03 e equivalentes)")
    args = ap.parse_args(argv)

    for arquivo in args.pdfs:
        print(f"{Path(arquivo).name}: lendo páginas...", file=sys.stderr)
        achadas = recortar(arquivo, Path(args.destino), args.com_candidato_vaga)
        if not achadas:
            print("  nenhuma tabela de perfil encontrada", file=sys.stderr)
        for tabela, paginas in achadas.items():
            print(f"  {tabela:28} p. {paginas[0]}-{paginas[-1]} ({len(paginas)} páginas)", file=sys.stderr)


if __name__ == "__main__":
    main()
