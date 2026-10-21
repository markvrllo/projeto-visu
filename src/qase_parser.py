"""Extrai as tabelas do Questionário de Avaliação Socioeconômica (QASE) da Fuvest.

Layout de cada página (calibrado com o PDF FUVEST_2021_qase_chamados_matricula_1_curso):

    Candidatos que foram chamados para a 1ª matrícula no seguinte curso:
    Dos 42 candidatos, 42 (100,0%) Carreira 100−Administração, Ciências Contábeis, ...
    entregaram o questionário respondido.
    42 vagas. Curso 01−Administração − Diurno − Ribeirão Preto [USP/FEARP]
    11 Qual é a renda bruta mensal da sua família, incluindo seu próprio rendimento? O valor do salário mínimo
    (SM) é R$ 1.045,00.
    2,4% Até 1 SM − até R$ 1.045,00. (1)
    7,1% Acima de 1 até 2 SM − de R$ 1.045,01 até R$ 2.090,00. (3)
    ...
    42 respostas

O cabeçalho do curso se repete em toda página. As duas primeiras páginas são um
índice e são ignoradas, porque o parser só aceita "Carreira" depois de "Dos N candidatos".

O resultado é uma tabela "longa": uma linha por (arquivo, carreira/curso, pergunta, opção).

Uso:
    python -m src.qase_parser data/raw/*qase*.pdf -o data/processed/qase_longo.csv
    python -m src.qase_parser --dump ARQUIVO.pdf --paginas 3-6     # ver o texto extraído
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

TRACO = r"\s*[−–—-]\s*"  # a Fuvest usa "−" (U+2212); aceitamos hífen e travessão também
# contagens grandes vêm com ponto de milhar ("Dos 3.229 candidatos", "(2.659)", "3.229 respostas")
NUM = r"\d{1,3}(?:\.\d{3})*"
RE_CARREIRA = re.compile(rf"^Dos\s+({NUM})\s+candidatos,\s+({NUM})\s+\([\d,]+%\)\s+Carreira\s+(\d+){TRACO}(.+?)\s*$")
# a partir de 2019: "26 vagas. Modalidade de Acesso: Ampla Concorrência" ou "4 vagas. Todas as Modalidades de Acesso"
RE_CURSO = re.compile(rf"^({NUM})\s+vagas\.?\s*(?:Curso\s+(\d+){TRACO}(.+?))?"
                      r"\s*(?:Modalidade de Acesso:\s*(?P<mod>.+?)|(?P<todas>Todas as Modalidades de Acesso))?\s*$")
RE_PERGUNTA = re.compile(r"^(\d{1,2})(?:\s+(\S.*))?$")  # "01 Qual..." (2021+) ou "1 Qual..." (2013)
# "52,4% Todo em escola pública. (22)" — a contagem é o ÚLTIMO número entre parênteses
# (há opções como "Região Intermediária de São Paulo (3501) (9)" e lixo como "(2) 2 PPI" no fim)
RE_OPCAO = re.compile(rf"^(?P<pct>\d{{1,3}},\d)%\s+(?P<texto>.+)\s*\((?P<n>{NUM})\)[^()]*$")
RE_RESPOSTAS = re.compile(rf"^({NUM})\s+respostas$")
RE_UNIDADE = re.compile(r"\[(?:USP/)?([^\]]+)\]")
CAMPI = ["São Carlos", "Ribeirão Preto", "Piracicaba", "Bauru", "Pirassununga", "Lorena", "Santos", "USP Leste"]
LIXO = ("FUVEST ", "Questionário de Avaliação", "Candidatos que", "Candidatos chamados", "Candidatos convocados",
        "Candidatos inscritos", "Candidatos matriculados", "entregaram o questionário", "Copyright")


def texto_do_pdf(caminho, paginas=None):
    """Devolve o texto de cada página do PDF (lista de strings)."""
    import pdfplumber

    with pdfplumber.open(caminho) as pdf:
        idx = range(len(pdf.pages)) if paginas is None else paginas
        return [pdf.pages[i].extract_text() or "" for i in idx]


def inteiro(txt):
    """'3.229' -> 3229."""
    return int(txt.replace(".", ""))


def separar_unidade_campus(nome):
    """'Bacharelado em Ciências de Computação − São Carlos [USP/ICMCSC]' -> (nome limpo, 'ICMCSC', 'São Carlos')."""
    m = RE_UNIDADE.search(nome)
    unidade = m.group(1) if m else None
    limpo = RE_UNIDADE.sub("", nome).strip(" −–-")
    campus = next((c for c in CAMPI if c in nome), "São Paulo")
    if unidade and unidade.endswith("SC"):  # ICMCSC, IAUSC, IQSC...
        campus = "São Carlos"
    return limpo, unidade, campus


def parse_linhas(linhas, meta=None):
    """Percorre as linhas de texto e devolve uma lista de dicionários (formato longo).

    `meta` é copiado para cada linha (ex.: ano, etapa, nivel, arquivo).
    """
    meta = meta or {}
    registros = []
    secao = None          # dados da carreira/curso atual
    pergunta = None       # [número, texto]
    lendo_enunciado = False

    for bruta in linhas:
        linha = bruta.strip()
        if not linha:
            continue

        if m := RE_CARREIRA.match(linha):
            # cabeçalho repetido em toda página; o curso (se houver) vem na linha "NN vagas. Curso ..."
            nome, unidade, campus = separar_unidade_campus(m.group(4))
            secao = {"candidatos": inteiro(m.group(1)), "questionarios": inteiro(m.group(2)),
                     "cod_carreira": m.group(3), "carreira": nome, "cod_curso": None, "curso": None,
                     "unidade": unidade, "campus": campus, "vagas": None, "modalidade": None}
            continue
        if secao is not None and (m := RE_CURSO.match(linha)):
            secao["vagas"] = inteiro(m.group(1))
            if m.group(2):
                nome, unidade, campus = separar_unidade_campus(m.group(3))
                secao.update(cod_curso=m.group(2), curso=nome, unidade=unidade, campus=campus)
            if m.group("mod") or m.group("todas"):
                secao["modalidade"] = m.group("mod") or "Todas"
            continue
        if secao is None or linha.startswith(LIXO) or RE_RESPOSTAS.match(linha):
            lendo_enunciado = False
            continue

        if m := RE_OPCAO.match(linha):
            lendo_enunciado = False
            if pergunta is None:
                continue
            registros.append({
                **meta,
                **secao,
                "num_pergunta": pergunta[0],
                "pergunta": pergunta[1],
                "opcao": m.group("texto").strip(" ."),
                "pct": float(m.group("pct").replace(",", ".")),
                "n": inteiro(m.group("n")),
            })
            continue

        if m := RE_PERGUNTA.match(linha):
            pergunta = [int(m.group(1)), m.group(2) or ""]
            lendo_enunciado = True
        elif lendo_enunciado and pergunta is not None:
            # enunciado que continua na linha seguinte
            pergunta[1] = (pergunta[1] + " " + linha).strip()
    return registros


def meta_do_nome(arquivo):
    """Deduz ano, etapa e nível a partir do nome do arquivo da Fuvest."""
    # arquivos gerados por scripts/picotar_pdfs.py têm "__<curso>" no fim; só o nome original importa
    nome = Path(arquivo).name.lower().split("__")[0]
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
