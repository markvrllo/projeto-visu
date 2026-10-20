"""Coleta os PDFs do QASE e de notas nas páginas de acervo da Fuvest (BeautifulSoup).

Para cada ano, abre https://www.fuvest.br/acervo-vestibular-AAAA/, encontra os links
de PDF, classifica cada um (QASE por etapa, notas de corte, candidato/vaga, notas mínimas)
e baixa os que interessam para data/raw/. A lista do que foi encontrado fica em
data/fontes_coletadas.csv.

Uso:
    python scripts/coletar_fuvest.py                          # QASE de 2010 a 2022, todas as etapas
    python scripts/coletar_fuvest.py --anos 2013-2022 --etapas inscritos matriculados --nivel carreira
    python scripts/coletar_fuvest.py --tipos qase nota_de_corte notas_minimas --anos 2010-2026
    python scripts/coletar_fuvest.py --so-listar               # só gera o CSV, sem baixar
"""
import argparse
import csv
import re
import sys
import time
from pathlib import Path
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

RAIZ = Path(__file__).resolve().parents[1]
SITE = "https://www.fuvest.br"
PAGINA_ANO = SITE + "/acervo-vestibular-{ano}/"
CABECALHO = {"User-Agent": "Mozilla/5.0 (projeto academico SCC0252 ICMC-USP)"}
PAUSA = 1.0  # segundos entre requisições, para não sobrecarregar o site
TIPOS = ("qase", "nota_de_corte", "candidato_vaga", "notas_minimas")
ETAPAS = ("inscritos", "convocados", "chamados_1a", "matriculados")


def classificar(url, texto):
    """Diz o que é um link de PDF a partir do nome do arquivo e do texto do link.

    Devolve dict com tipo/etapa/nivel, ou None se o PDF não interessa.
    """
    arquivo = Path(urlparse(url).path).name.lower()
    texto = " ".join(texto.split()).lower()
    if not arquivo.endswith(".pdf"):
        return None

    if "qase" in arquivo:
        if "inscritos" in arquivo:
            etapa = "inscritos"
        elif "convocados" in arquivo:
            etapa = "convocados"
        elif "chamados" in arquivo:
            etapa = "chamados_1a"
        elif "matriculados" in arquivo or "umatr" in arquivo:
            etapa = "matriculados"
        else:
            return None
        nivel = "curso" if re.search(r"curso|_cur\.pdf$", arquivo) or "(curso" in texto else "carreira"
        return {"tipo": "qase", "etapa": etapa, "nivel": nivel}
    if "minimas" in arquivo or "notas mínimas" in texto:
        return {"tipo": "notas_minimas", "etapa": "", "nivel": ""}
    if "corte" in arquivo or "notas de corte" in texto:
        return {"tipo": "nota_de_corte", "etapa": "", "nivel": ""}
    if "candidato_vaga" in arquivo or "candidato vaga" in texto:
        return {"tipo": "candidato_vaga", "etapa": "", "nivel": ""}
    return None


def links_da_pagina(html, url_base):
    """Extrai (url absoluta, texto) de todos os links da página, sem repetir URL."""
    sopa = BeautifulSoup(html, "html.parser")
    vistos = set()
    for a in sopa.find_all("a", href=True):
        url = urljoin(url_base, a["href"].strip())
        if url not in vistos:
            vistos.add(url)
            yield url, a.get_text(" ", strip=True)


def intervalo_anos(txt):
    ini, _, fim = txt.partition("-")
    return list(range(int(ini), int(fim or ini) + 1))


def robots_permite(sessao, url):
    rp = robotparser.RobotFileParser()
    try:
        r = sessao.get(SITE + "/robots.txt", timeout=30)
        rp.parse(r.text.splitlines())
    except requests.RequestException:
        return True  # sem robots.txt acessível, seguimos com cuidado (pausa entre pedidos)
    return rp.can_fetch(CABECALHO["User-Agent"], url)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--anos", default="2010-2022", help="ex.: 2015 ou 2013-2022")
    ap.add_argument("--tipos", nargs="+", default=["qase"], choices=TIPOS)
    ap.add_argument("--etapas", nargs="+", default=list(ETAPAS), choices=ETAPAS, help="só para QASE")
    ap.add_argument("--nivel", choices=["carreira", "curso"], help="só para QASE; padrão: os dois")
    ap.add_argument("--destino", default=str(RAIZ / "data" / "raw"))
    ap.add_argument("--so-listar", action="store_true", help="não baixa, só gera data/fontes_coletadas.csv")
    args = ap.parse_args(argv)

    sessao = requests.Session()
    sessao.headers.update(CABECALHO)
    destino = Path(args.destino)
    destino.mkdir(parents=True, exist_ok=True)

    encontrados = []
    for ano in intervalo_anos(args.anos):
        pagina = PAGINA_ANO.format(ano=ano)
        if not robots_permite(sessao, pagina):
            print(f"{ano}: robots.txt não permite ler {pagina}; baixe à mão", file=sys.stderr)
            continue
        try:
            r = sessao.get(pagina, timeout=60)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"{ano}: não consegui abrir a página de acervo ({e})", file=sys.stderr)
            continue
        time.sleep(PAUSA)

        n_ano = 0
        # bytes: o BeautifulSoup detecta a codificação pelo <meta charset> da página
        for url, texto in links_da_pagina(r.content, pagina):
            info = classificar(url, texto)
            if info is None or info["tipo"] not in args.tipos:
                continue
            if info["tipo"] == "qase" and (info["etapa"] not in args.etapas or
                                           (args.nivel and info["nivel"] != args.nivel)):
                continue
            encontrados.append({"ano": ano, **info, "texto_link": texto, "url": url})
            n_ano += 1
        print(f"{ano}: {n_ano} PDFs selecionados", file=sys.stderr)

    with open(RAIZ / "data" / "fontes_coletadas.csv", "w", newline="") as f:
        campos = ["ano", "tipo", "etapa", "nivel", "texto_link", "url"]
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(encontrados)
    print(f"lista salva em data/fontes_coletadas.csv ({len(encontrados)} PDFs)", file=sys.stderr)
    if args.so_listar:
        return

    falhas = []
    for item in encontrados:
        arquivo = destino / Path(urlparse(item["url"]).path).name
        if arquivo.exists() and arquivo.stat().st_size > 0:
            print(f"já existe  {arquivo.name}")
            continue
        try:
            r = sessao.get(item["url"], timeout=300)
            r.raise_for_status()
            arquivo.write_bytes(r.content)
            print(f"baixado    {arquivo.name} ({len(r.content) // 1024} KB)")
        except requests.RequestException as e:
            print(f"FALHOU     {arquivo.name}: {e}")
            falhas.append(item["url"])
        time.sleep(PAUSA)

    if falhas:
        print("\nNão consegui baixar (tente de novo ou baixe à mão):\n" + "\n".join(falhas))


if __name__ == "__main__":
    main()
