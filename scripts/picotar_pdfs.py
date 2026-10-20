"""Separa os PDFs do QASE em um PDF por carreira/curso.

Cada página de seção do QASE repete o cabeçalho com a carreira e o curso:

    Dos 42 candidatos, 42 (100,0%)
    Carreira 100−Administração, Ciências Contábeis, ...
    Curso 01−Administração − Diurno − Ribeirão Preto [USP/FEARP]

Páginas consecutivas com o mesmo cabeçalho viram um arquivo. As páginas de índice
(sem "Dos N candidatos") são descartadas.

Os arquivos de saída mantêm o nome original no começo, para o parser continuar
sabendo ano, etapa e nível:
    data/raw/por_curso/FUVEST_2021_qase_chamados_matricula_1_curso__710-06_bacharelado-em-ciencias-de-computacao-sao-carlos.pdf

Uso:
    python scripts/picotar_pdfs.py data/raw/*qase*.pdf
    python scripts/picotar_pdfs.py data/raw/*qase*.pdf --unidade ICMC          # só cursos do ICMC
    python scripts/picotar_pdfs.py data/raw/*qase*.pdf --carreira 710 875      # só essas carreiras
    python scripts/picotar_pdfs.py data/raw/*qase*.pdf --campus "São Carlos"
"""
import argparse
import logging
import re
import sys
import unicodedata
from pathlib import Path

from pypdf import PdfReader, PdfWriter

logging.getLogger("pypdf").setLevel(logging.ERROR)  # avisos de fonte não afetam o texto que usamos

RAIZ = Path(__file__).resolve().parents[1]
TRACO = r"\s*[−–—-]\s*"
RE_SECAO = re.compile(r"Dos\s+\d+\s+candidatos")
RE_CARREIRA = re.compile(rf"^Carreira\s+(\d+){TRACO}(.+?)\s*$", re.M)
RE_CURSO = re.compile(rf"^Curso\s+(\d+){TRACO}(.+?)\s*$", re.M)


def slug(txt, limite=60):
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode().lower()
    txt = re.sub(r"\[.*?\]", "", txt)
    return re.sub(r"[^a-z0-9]+", "-", txt).strip("-")[:limite].strip("-")


def cabecalho(texto):
    """Devolve (cod_carreira, carreira, cod_curso, curso) de uma página de seção, ou None."""
    if not RE_SECAO.search(texto):
        return None
    car = RE_CARREIRA.search(texto)
    if not car:
        return None
    cur = RE_CURSO.search(texto)
    return (car.group(1), car.group(2), cur.group(1) if cur else "", cur.group(2) if cur else "")


def secoes(leitor):
    """Agrupa páginas consecutivas com o mesmo cabeçalho. Devolve lista de (cabecalho, [páginas])."""
    grupos, ignoradas = [], 0
    for i, pagina in enumerate(leitor.pages):
        cab = cabecalho(pagina.extract_text() or "")
        if cab is None:
            ignoradas += 1
            continue
        if grupos and grupos[-1][0] == cab and grupos[-1][1][-1] == i - 1:
            grupos[-1][1].append(i)
        else:
            grupos.append((cab, [i]))
    return grupos, ignoradas


def passa_filtro(cab, args):
    cod_car, carreira, _, curso = cab
    if args.carreira and cod_car not in args.carreira:
        return False
    if args.unidade and not any(u.upper() in (curso + carreira).upper() for u in args.unidade):
        return False
    if args.campus and not any(c.lower() in (curso + carreira).lower() for c in args.campus):
        return False
    return True


def picotar(arquivo, destino, args):
    leitor = PdfReader(arquivo)
    grupos, ignoradas = secoes(leitor)
    destino.mkdir(parents=True, exist_ok=True)
    salvos = 0
    for cab, paginas in grupos:
        if not passa_filtro(cab, args):
            continue
        cod_car, carreira, cod_cur, curso = cab
        rotulo = f"{cod_car}-{cod_cur}" if cod_cur else cod_car
        saida = destino / f"{Path(arquivo).stem}__{rotulo}_{slug(curso or carreira)}.pdf"
        escritor = PdfWriter()
        for i in paginas:
            escritor.add_page(leitor.pages[i])
        with open(saida, "wb") as f:
            escritor.write(f)
        salvos += 1
    print(f"{Path(arquivo).name}: {len(grupos)} seções, {salvos} salvas, {ignoradas} páginas ignoradas (índice/totais)",
          file=sys.stderr)
    return salvos


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfs", nargs="+")
    ap.add_argument("-o", "--destino", default=str(RAIZ / "data" / "raw" / "por_curso"))
    ap.add_argument("--unidade", nargs="+", help="ex.: ICMC (procura em '[USP/ICMCSC]')")
    ap.add_argument("--carreira", nargs="+", help="códigos de carreira, ex.: 710 875")
    ap.add_argument("--campus", nargs="+", help='ex.: "São Carlos"')
    args = ap.parse_args(argv)
    total = sum(picotar(p, Path(args.destino), args) for p in args.pdfs)
    print(f"{total} arquivos em {args.destino}", file=sys.stderr)


if __name__ == "__main__":
    main()
