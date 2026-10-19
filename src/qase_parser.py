"""Extrai as tabelas do Questionário de Avaliação Socioeconômica (QASE) da Fuvest.

Cada PDF tem uma seção por carreira (ou curso). Dentro dela vêm as perguntas
numeradas e, para cada opção de resposta, o percentual e a contagem, no formato
"Opção ........ 45,2% (47)".

O resultado é uma tabela "longa": uma linha por (arquivo, carreira/curso, pergunta, opção).

ATENÇÃO: as expressões regulares abaixo foram escritas a partir da descrição do
layout dos PDFs, sem acesso a um arquivo real. Antes de rodar em lote, use
`python -m src.qase_parser --dump ARQUIVO.pdf --paginas 3-6` para ver o texto
extraído e ajustar as regex se necessário. Os testes em tests/ mostram o formato esperado.

Uso:
    python -m src.qase_parser data/raw/*.pdf -o data/processed/qase_longo.csv
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

# "Carreira 710−Computação" / "Curso 06−Bacharelado em Ciências de Computação − São Carlos [USP/ICMCSC]"
# A Fuvest usa o sinal "−" (U+2212), mas aceitamos hífen e travessão também.
TRACO = r"\s*[−–—-]\s*"
RE_CARREIRA = re.compile(rf"^Carreira\s+(\d+){TRACO}(.+?)\s*$")
RE_CURSO = re.compile(rf"^Curso\s+(\d+){TRACO}(.+?)\s*$")
# Pergunta: "11. Qual a renda familiar..." ou "11 - Qual ..." ou "11) ..."
RE_PERGUNTA = re.compile(r"^(\d{1,2})\s*[.)\-–−]\s*(\D.+?)\s*$")
# Opção: "texto 45,2% (47)" — pode haver mais de uma opção na mesma linha
RE_OPCAO = re.compile(r"(?P<texto>[^%()]*?\S)\s*\.*\s*(?P<pct>\d{1,3}(?:[.,]\d+)?)\s*%\s*\(\s*(?P<n>[\d.]+)\s*\)")
RE_UNIDADE = re.compile(r"\[(?:USP/)?([^\]]+)\]")
CAMPI = ["São Carlos", "Ribeirão Preto", "Piracicaba", "Bauru", "Pirassununga", "Lorena", "Santos", "São Paulo"]


def texto_do_pdf(caminho, paginas=None):
    """Devolve o texto de cada página do PDF (lista de strings)."""
    import pdfplumber

    with pdfplumber.open(caminho) as pdf:
        idx = range(len(pdf.pages)) if paginas is None else paginas
        return [pdf.pages[i].extract_text() or "" for i in idx]


def separar_unidade_campus(nome):
    """'Bacharelado em Ciências de Computação − São Carlos [USP/ICMCSC]' -> (nome limpo, 'ICMCSC', 'São Carlos')."""
    m = RE_UNIDADE.search(nome)
    unidade = m.group(1) if m else None
    limpo = RE_UNIDADE.sub("", nome).strip(" −–-")
    campus = next((c for c in CAMPI if c in limpo), None)
    return limpo, unidade, campus


def parse_linhas(linhas, meta=None):
    """Percorre as linhas de texto e devolve uma lista de dicionários (formato longo).

    `meta` é copiado para cada linha (ex.: ano, etapa, nivel, arquivo).
    """
    meta = meta or {}
    registros = []
    carreira = curso = pergunta = None

    for bruta in linhas:
        linha = bruta.strip()
        if not linha:
            continue

        if m := RE_CARREIRA.match(linha):
            carreira = (m.group(1), m.group(2))
            curso, pergunta = None, None
            continue
        if m := RE_CURSO.match(linha):
            curso = (m.group(1), m.group(2))
            pergunta = None
            continue

        opcoes = list(RE_OPCAO.finditer(linha))
        if not opcoes:
            if m := RE_PERGUNTA.match(linha):
                pergunta = (int(m.group(1)), m.group(2))
            continue

        if carreira is None and curso is None or pergunta is None:
            continue  # opção fora de uma seção reconhecida (índice, capa...)

        nome_base = curso[1] if curso else carreira[1]
        nome, unidade, campus = separar_unidade_campus(nome_base)
        for op in opcoes:
            registros.append({
                **meta,
                "cod_carreira": carreira[0] if carreira else None,
                "carreira": carreira[1] if carreira else None,
                "cod_curso": curso[0] if curso else None,
                "curso": nome if curso else None,
                "unidade": unidade,
                "campus": campus,
                "num_pergunta": pergunta[0],
                "pergunta": pergunta[1],
                "opcao": op.group("texto").strip(" .:"),
                "pct": float(op.group("pct").replace(",", ".")),
                "n": int(op.group("n").replace(".", "")),
            })
    return registros


def meta_do_nome(arquivo):
    """Deduz ano, etapa e nível a partir do nome do arquivo da Fuvest."""
    nome = Path(arquivo).name.lower()
    ano = int(re.search(r"20\d\d", nome).group())
    if "inscritos" in nome:
        etapa = "inscritos"
    elif "convocados" in nome:
        etapa = "convocados"
    elif "chamados" in nome:
        etapa = "chamados_1a"
    else:
        etapa = "matriculados"
    nivel = "curso" if ("curso" in nome or "_cur." in nome) else "carreira"
    return {"ano": ano, "etapa": etapa, "nivel": nivel, "arquivo": Path(arquivo).name}


def parse_pdf(arquivo):
    linhas = []
    for pagina in texto_do_pdf(arquivo):
        linhas.extend(pagina.splitlines())
    return parse_linhas(linhas, meta_do_nome(arquivo))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfs", nargs="+")
    ap.add_argument("-o", "--saida", default="data/processed/qase_longo.csv")
    ap.add_argument("--dump", action="store_true", help="só imprime o texto extraído (para calibrar as regex)")
    ap.add_argument("--paginas", help="intervalo de páginas para --dump, ex.: 3-6 (começa em 1)")
    args = ap.parse_args(argv)

    if args.dump:
        paginas = None
        if args.paginas:
            ini, fim = (int(x) for x in args.paginas.split("-"))
            paginas = range(ini - 1, fim)
        for i, txt in enumerate(texto_do_pdf(args.pdfs[0], paginas)):
            print(f"===== página {i + 1 if paginas is None else paginas[i] + 1} =====")
            print(txt)
        return

    todos = []
    for arquivo in args.pdfs:
        regs = parse_pdf(arquivo)
        print(f"{Path(arquivo).name}: {len(regs)} linhas", file=sys.stderr)
        if not regs:
            print("  nenhuma linha reconhecida — rode com --dump e ajuste as regex", file=sys.stderr)
        todos.extend(regs)

    df = pd.DataFrame(todos)
    Path(args.saida).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.saida, index=False)
    print(f"salvo em {args.saida} ({len(df)} linhas)", file=sys.stderr)


if __name__ == "__main__":
    main()
