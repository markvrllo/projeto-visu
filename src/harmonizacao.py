"""Harmoniza perguntas e respostas do QASE entre os anos e calcula os indicadores por curso.

As perguntas mudam de número e de redação ao longo dos anos, então identificamos
cada uma por palavras-chave. As opções de resposta são reagrupadas em categorias
comparáveis (ex.: as faixas de renda viram "até 3 SM", "3 a 10 SM" e "mais de 10 SM").

Uso:
    python -m src.harmonizacao data/processed/qase_longo.csv -o data/processed/indicadores.csv
"""
import argparse
import re
import unicodedata

import pandas as pd


def normalizar(txt):
    """minúsculas e sem acentos, para comparar textos."""
    txt = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", txt.lower()).strip()


# --- 1. Qual é a pergunta? ---------------------------------------------------

def tipo_pergunta(pergunta):
    p = normalizar(pergunta)
    # perguntas restritas a um subgrupo (ex.: "cor ou raça, apenas para quem cursou escola pública")
    if any(k in p for k in ("apenas", "somente", "so escola", "entre os que")):
        return None
    if "cor" in p and ("raca" in p or "etnia" in p) and "escola publica" not in p:
        return "cor_raca"
    if "ensino medio" in p and ("onde" in p or "escola" in p or "cursou" in p) and "tipo" not in p and "turno" not in p:
        return "escola_medio"
    if "renda" in p and "pessoas" not in p:
        return "renda"
    if "escolaridade" in p or "grau de instrucao" in p:
        if "pai" in p:
            return "escolaridade_pai"
        if "mae" in p:
            return "escolaridade_mae"
    if "cursinho" in p or "pre-vestibular" in p:
        return "cursinho"
    if "sexo" in p or "genero" in p:
        return "sexo"
    if "atividade remunerada" in p or "trabalha" in p:
        return "trabalho"
    return None


# --- 2. Em que categoria cai a resposta? ------------------------------------

def categoria_cor(op):
    o = normalizar(op)
    if any(k in o for k in ("preta", "parda", "indigena")):
        return "PPI"
    if "branca" in o:
        return "branca"
    if "amarela" in o:
        return "amarela"
    return None


def categoria_escola(op):
    o = normalizar(op)
    # "todo em escola pública" e "maior parte em escola pública" contam como pública
    if "public" in o:
        return "publica"
    if "particular" in o or "privad" in o:
        return "particular"
    return None


def categoria_renda(op):
    """Usa o limite inferior da faixa, em salários mínimos.

    'Inferior a 1 SM' -> até 3; 'De 3 a 5 SM' -> 3 a 10; 'Acima de 20 SM' -> mais de 10.
    Se algum ano usar faixas em reais em vez de SM, é preciso converter antes (ver README).
    """
    o = normalizar(op)
    nums = [float(x.replace(",", ".")) for x in re.findall(r"\d+(?:,\d+)?", o)]
    if not nums:
        return None
    inferior = 0.0 if any(k in o for k in ("inferior", "ate ", "menos")) else nums[0]
    if inferior < 3:
        return "ate_3SM"
    if inferior < 10:
        return "3a10SM"
    return "mais_10SM"


def categoria_escolaridade(op):
    o = normalizar(op)
    if "superior completo" in o or "pos-graduacao" in o or "pos graduacao" in o:
        return "superior"
    return "sem_superior"


def categoria_cursinho(op):
    return "nao" if normalizar(op).startswith("nao") else "sim"


CATEGORIZADORES = {
    "cor_raca": categoria_cor,
    "escola_medio": categoria_escola,
    "renda": categoria_renda,
    "escolaridade_pai": categoria_escolaridade,
    "escolaridade_mae": categoria_escolaridade,
    "cursinho": categoria_cursinho,
}

# indicador final = % de respostas na categoria indicada, dentro da pergunta
INDICADORES = {
    "pct_PPI": ("cor_raca", "PPI"),
    "pct_escola_publica": ("escola_medio", "publica"),
    "pct_renda_ate_3SM": ("renda", "ate_3SM"),
    "pct_renda_mais_10SM": ("renda", "mais_10SM"),
    "pct_pai_superior": ("escolaridade_pai", "superior"),
    "pct_mae_superior": ("escolaridade_mae", "superior"),
    "pct_cursinho": ("cursinho", "sim"),
}


def harmonizar(longo: pd.DataFrame) -> pd.DataFrame:
    df = longo.copy()
    df["tipo"] = df["pergunta"].map(tipo_pergunta)
    df = df[df["tipo"].isin(CATEGORIZADORES)]
    df["categoria"] = [CATEGORIZADORES[t](o) for t, o in zip(df["tipo"], df["opcao"])]
    return df


def calcular_indicadores(harm: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por (ano, etapa, nível, carreira/curso) com os % de cada indicador."""
    chave = ["ano", "etapa", "nivel", "cod_carreira", "carreira", "cod_curso", "curso", "unidade", "campus"]
    harm = harm.copy()
    harm[chave] = harm[chave].fillna("")
    total = harm.groupby(chave + ["tipo"])["n"].sum().rename("total")
    por_cat = harm.groupby(chave + ["tipo", "categoria"])["n"].sum().rename("n_cat").reset_index()
    por_cat = por_cat.join(total, on=chave + ["tipo"])

    saida = None
    for nome, (tipo, cat) in INDICADORES.items():
        sel = por_cat[(por_cat["tipo"] == tipo) & (por_cat["categoria"] == cat)]
        col = (100 * sel["n_cat"] / sel["total"]).rename(nome)
        parte = pd.concat([sel[chave], col], axis=1)
        saida = parte if saida is None else saida.merge(parte, on=chave, how="outer")

    # nº de respondentes: total de respostas da pergunta de cor/raça, presente em todos os anos
    resp = (harm[harm["tipo"] == "cor_raca"].groupby(chave)["n"].sum().rename("respondentes").reset_index())
    saida = saida.merge(resp, on=chave, how="left")
    saida["nome"] = saida["curso"].where(saida["curso"] != "", saida["carreira"])
    # antes de ~2019 não há unidade no nome da carreira, então também olhamos o nome + campus
    nome_icmc = saida["nome"].str.contains("Computação|Sistemas de Informação|Estatística|Matemática", na=False)
    saida["icmc"] = saida["unidade"].str.contains("ICMC", na=False) | (nome_icmc & (saida["campus"] == "São Carlos"))
    return saida


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada", nargs="?", default="data/processed/qase_longo.csv")
    ap.add_argument("-o", "--saida", default="data/processed/indicadores.csv")
    args = ap.parse_args(argv)
    longo = pd.read_csv(args.entrada)
    ind = calcular_indicadores(harmonizar(longo))
    ind.to_csv(args.saida, index=False)
    print(f"{len(ind)} linhas salvas em {args.saida}")


if __name__ == "__main__":
    main()
