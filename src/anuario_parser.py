"""Extrai as tabelas de perfil dos candidatos do Anuário Estatístico da USP (2022 em diante).

Lê os recortes feitos por scripts/recortar_anuario.py (data/raw/anuario/anuario_AAAA__<ingresso>_<tabela>.pdf).
Layout de cada página (texto extraído com pdfplumber):

    Tabela 3.05 Características pessoais dos candidatos ao vestibular da FUVEST, por Área de Conhecimento, em 2024
    Biológicas Exatas Humanas
    Insc. Conv. Matr. Insc. Conv. Matr. Insc. Conv. Matr.
    Quant. % Quant. % ...
    Onde você cursou o Ensino Fundamental?
    Todo em escola pública. 11.148 24,55 1.960 26,89 429 22,63 4.534 22,49 ...

Cada linha de opção termina com pares "quantidade porcentagem", um por coluna. As colunas vêm do
cabeçalho: na tabela geral são Candidatos (Insc./Conv./Matr.) e, no vestibular da Fuvest, Treineiros
(Insc./Conv./Matr.), que são descartados; na tabela por área são as 3 áreas × 3 etapas.

O resultado tem o mesmo formato longo do QASE:
    ano, fonte, ingresso, etapa, nivel, area, pergunta, opcao, n, pct
mais as colunas de rastreio (arquivo, pagina, tabela) e `n_respostas` (soma das quantidades da
pergunta naquela coluna; o anuário não imprime o total).

Etapas em que a coluna inteira de uma pergunta vem zerada (ex.: "Conv." do ENEM-USP e do Provão
Paulista, que não têm convocação) são descartadas: não existe dado, e zero seria mentira.

Uso:
    python -m src.anuario_parser data/raw/anuario -o data/processed/anuario_longo.csv
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

NUM = r"\d{1,3}(?:\.\d{3})*"
PAR = rf"({NUM})\s+(\d{{1,3}},\d{{1,2}})"
RE_PARES = re.compile(rf"^(?P<texto>.*?)\s*(?P<pares>(?:{NUM}\s+\d{{1,3}},\d{{1,2}}\s*)+)$")
RE_TABELA = re.compile(r"^Tabela\s+(\d+\.\d+)")
RE_NOME = re.compile(r"anuario_(\d{4})__(.+?)_(geral|por_area)\.pdf$")
AREAS = ["Biológicas", "Exatas", "Humanas"]
ETAPAS = {"Insc.": "inscritos", "Conv.": "convocados", "Matr.": "matriculados"}
CABECALHO = ("Candidatos", "Insc.", "Quant.", "Biológicas Exatas Humanas")
RODAPE = ("Processado em", "Fonte:", "Nota:", "Notas:", "(*)")


def linhas_do_pdf(caminho):
    """Devolve, para cada página, a lista de linhas como (texto, topo em pt, negrito?)."""
    import pdfplumber

    paginas = []
    with pdfplumber.open(caminho) as pdf:
        for pagina in pdf.pages:
            linhas = []
            for ln in pagina.extract_text_lines(return_chars=True):
                negrito = sum("Bold" in c["fontname"] for c in ln["chars"]) > len(ln["chars"]) / 2
                linhas.append((ln["text"].strip(), ln["top"], negrito))
            paginas.append(linhas)
    return paginas


def numero(txt):
    return int(txt.replace(".", ""))


def colunas(tipo):
    """Lista de (area, etapa) na ordem das colunas; area None = total da USP; etapa None = treineiros."""
    if tipo == "por_area":
        return [(a, e) for a in AREAS for e in ETAPAS.values()]
    return [(None, e) for e in ETAPAS.values()] + [(None, None)] * 3


# linhas de texto quebrado ficam a ~9 pt da vizinha; entre opções a distância é de ~17 pt
QUEBRA = 13


def _cola_na_proxima_opcao(uteis, i):
    """A linha i (sem números) é o começo do texto de uma opção cujos números vêm logo abaixo?"""
    j = i
    while j + 1 < len(uteis) and uteis[j + 1]["topo"] - uteis[j]["topo"] < QUEBRA and not uteis[j + 1]["negrito"]:
        j += 1
        if uteis[j]["m"] is not None:
            return True
    return False


def parse_paginas(paginas, meta, tipo):
    """Devolve (registros, problemas). Cada registro é uma (pergunta, opção, coluna).

    `paginas` é a saída de linhas_do_pdf. Uma linha sem números é o enunciado de uma pergunta,
    a continuação dele ou um pedaço do texto de uma opção que não coube numa linha. A decisão
    é pela posição: texto quebrado fica colado (< QUEBRA pt) na linha vizinha; o enunciado vem
    em negrito na maioria dos anos e, sempre, separado das opções por um espaço maior.
    """
    cols = colunas(tipo)
    registros, problemas = [], []
    pergunta = None
    tabela = None

    for num_pag, linhas in enumerate(paginas, start=1):
        uteis = []
        for texto, topo, negrito in linhas:
            if m := RE_TABELA.match(texto):
                tabela = m.group(1)
                continue
            if not texto or texto.startswith(CABECALHO) or texto.startswith(RODAPE):
                continue
            m = RE_PARES.match(texto)
            uteis.append({"texto": texto, "topo": topo, "negrito": negrito,
                          "m": m if (m and m.group("texto")) else None, "regs": []})

        anterior_pergunta = None  # topo da última linha de enunciado, se a linha anterior foi enunciado
        opcao_aberta = None       # (registros, topo da última linha) da opção que pode continuar abaixo
        prefixo = []
        for i, ln in enumerate(uteis):
            if ln["m"] is None:
                if anterior_pergunta is not None and ln["topo"] - anterior_pergunta < QUEBRA:
                    pergunta = f"{pergunta} {ln['texto']}"
                    anterior_pergunta = ln["topo"]
                elif not ln["negrito"] and opcao_aberta and ln["topo"] - opcao_aberta[1] < QUEBRA:
                    for reg in opcao_aberta[0]:
                        reg["opcao"] = f"{reg['opcao']} {ln['texto']}".strip(" .")
                    opcao_aberta = (opcao_aberta[0], ln["topo"])
                elif not ln["negrito"] and _cola_na_proxima_opcao(uteis, i):
                    prefixo.append(ln["texto"])
                else:
                    pergunta, anterior_pergunta, prefixo, opcao_aberta = ln["texto"], ln["topo"], [], None
                continue

            anterior_pergunta = None
            m = ln["m"]
            pares = re.findall(PAR, m.group("pares"))
            if pergunta is None:
                problemas.append({**meta, "pagina": num_pag, "problema": "opção antes de qualquer pergunta",
                                  "detalhe": ln["texto"]})
                continue
            if len(pares) == len(cols):
                usar = cols
            elif tipo == "geral" and len(pares) == 3:
                usar = cols[:3]  # ENEM-USP e Provão Paulista não têm treineiros
            else:
                problemas.append({**meta, "pagina": num_pag, "problema": f"{len(pares)} pares, esperado {len(cols)}",
                                  "detalhe": ln["texto"]})
                continue
            opcao = " ".join(prefixo + [m.group("texto")]).strip(" .")
            prefixo = []
            for (area, etapa), (n, pct) in zip(usar, pares):
                if etapa is None:
                    continue  # treineiros
                reg = {**meta, "tabela": tabela, "pagina": num_pag, "nivel": "area" if area else "usp",
                       "area": area, "etapa": etapa, "pergunta": pergunta, "opcao": opcao,
                       "n": numero(n), "pct": float(pct.replace(",", "."))}
                registros.append(reg)
                ln["regs"].append(reg)
            opcao_aberta = (ln["regs"], ln["topo"])
    return registros, problemas


def descartar_colunas_vazias(df):
    """Tira (pergunta, área, etapa) em que todas as quantidades são zero: a coluna não existe."""
    chave = ["arquivo", "pergunta", "area", "etapa"]
    total = df.groupby(chave, dropna=False)["n"].transform("sum")
    return df[total > 0].copy()


def parse_pdf(arquivo):
    m = RE_NOME.search(Path(arquivo).name)
    if not m:
        raise ValueError(f"nome inesperado: {arquivo}")
    ano, ingresso, tipo = int(m.group(1)), m.group(2), m.group(3)
    meta = {"ano": ano, "fonte": "anuario", "ingresso": ingresso, "arquivo": Path(arquivo).name}
    return parse_paginas(linhas_do_pdf(arquivo), meta, tipo)


def ler_pasta(pdfs):
    registros, problemas = [], []
    for arquivo in pdfs:
        regs, probs = parse_pdf(arquivo)
        print(f"{Path(arquivo).name}: {len(regs)} linhas, {len(probs)} problemas", file=sys.stderr)
        registros.extend(regs)
        problemas.extend(probs)
    df = pd.DataFrame(registros)
    if not df.empty:
        df = descartar_colunas_vazias(df)
        df["n_respostas"] = df.groupby(["arquivo", "pergunta", "area", "etapa"], dropna=False)["n"].transform("sum")
    return df, pd.DataFrame(problemas)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfs", nargs="+", help="recortes do anuário ou a pasta com eles")
    ap.add_argument("-o", "--saida", default="data/processed/anuario_longo.csv")
    ap.add_argument("--problemas", default="data/processed/anuario_problemas.csv")
    args = ap.parse_args(argv)

    pdfs = []
    for item in args.pdfs:
        p = Path(item)
        pdfs.extend(sorted(p.glob("anuario_*_geral.pdf")) + sorted(p.glob("anuario_*_por_area.pdf")) if p.is_dir() else [p])
    df, problemas = ler_pasta(pdfs)
    Path(args.saida).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.saida, index=False)
    problemas.to_csv(args.problemas, index=False)
    print(f"salvo em {args.saida} ({len(df)} linhas); {len(problemas)} problemas em {args.problemas}", file=sys.stderr)


if __name__ == "__main__":
    main()
