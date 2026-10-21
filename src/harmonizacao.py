"""Harmoniza as perguntas do QASE e do Anuário e calcula os indicadores do contrato (indicadores.csv).

As perguntas mudam de número e de redação ao longo dos anos, então identificamos cada uma por
palavras-chave. As opções de resposta são reagrupadas em categorias comparáveis (ex.: as faixas
de renda viram "até 3 SM", "3 a 10 SM" e "mais de 10 SM").

Todas as agregações somam CONTAGENS, nunca porcentagens:
  - QASE (2013–2022): carreira → área (data/carreira_area.csv) → USP. De 2019 a 2022 cada carreira vem
    separada por modalidade (AC/EP/PPI); a modalidade "Todas" é a soma das três.
  - Anuário (2022+): já vem no nível USP e por área.

Perguntas ou tabelas reprovadas na validação (src/validacao.py) ficam de fora: o indicador fica vazio.

Uso:
    python -m src.harmonizacao                      # lê data/processed/{qase,anuario}_longo.csv
"""
import argparse
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "data" / "processed"

COLUNAS = ["ano", "fonte", "ingresso", "etapa", "nivel", "area", "cod_carreira", "carreira", "unidade",
           "modalidade", "respondentes", "pct_escola_publica", "pct_PPI", "pct_renda_ate_3SM",
           "pct_renda_mais_10SM", "pct_pai_superior", "pct_mae_superior", "pct_cursinho", "pct_mulheres",
           "pct_tecnico"]


def normalizar(txt):
    """minúsculas e sem acentos, para comparar textos."""
    txt = str(txt).replace("−", "-")  # a Fuvest usa o sinal de menos (U+2212) como hífen
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", txt.lower()).strip()


# --- 1. Qual é a pergunta? ---------------------------------------------------

def tipo_pergunta(pergunta):
    p = normalizar(pergunta)
    # perguntas restritas a um subgrupo (ex.: "cor ou raça, apenas para quem cursou escola pública")
    if any(k in p for k in ("apenas", "somente", "candidatos que", "para os candidatos")):
        return None
    if "cor" in p and ("raca" in p or "etnia" in p) and "escola publica" not in p:
        return "cor_raca"
    if "ensino medio" in p and "tipo" in p:
        return "tipo_medio"
    if p.startswith("onde") and "ensino medio" in p:
        return "escola_medio"
    # "Somando a renda ... das pessoas que moram com você, quanto é a renda familiar mensal?" é renda;
    # "Quantas pessoas ... vivem da renda" / "contribuem para essa renda" não é
    if "renda" in p and not p.startswith("quantas"):
        return "renda"
    if "modalidade" in p:
        return "modalidade"
    if "escolaridade" in p or "instrucao" in p:
        # o Anuário pergunta pelo "primeiro/segundo responsável (mãe, pai ou outra pessoa)":
        # não dá para separar pai e mãe, então não entra nesses indicadores
        if "responsavel por voce (mae, pai" in p:
            return None
        if "pai" in p:
            return "escolaridade_pai"
        if "mae" in p:
            return "escolaridade_mae"
    if "cursinho" in p or "pre-vestibular" in p:
        return "cursinho"
    if "sexo" in p or "genero" in p:
        return "sexo"
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
    """Usa o limite inferior da faixa, em salários mínimos (só o trecho antes de "SM";
    em 2021 a opção ainda traz os valores em reais depois do SM).

    'Até 1 SM' -> até 3; 'Acima de 2 até 3 SM' -> até 3; 'Acima de 3 até 5 SM' -> 3 a 10;
    'Acima de 10 até 15 SM' -> mais de 10.
    """
    o = normalizar(op).split(" sm")[0]
    nums = [float(x.replace(",", ".")) for x in re.findall(r"\d+(?:,\d+)?", o)]
    if not nums:
        return None
    inferior = 0.0 if o.startswith(("ate", "inferior", "menos")) else nums[0]
    if inferior < 3:
        return "ate_3SM"
    if inferior < 10:
        return "3a10SM"
    return "mais_10SM"


def categoria_escolaridade(op):
    o = normalizar(op)
    if o.startswith(("nao sei", "nao possuo")):
        return None  # fica fora do denominador
    if "superior completo" in o or "pos-graduacao" in o or "pos graduacao" in o:
        return "superior"
    return "sem_superior"


def categoria_cursinho(op):
    return "nao" if normalizar(op).startswith("nao") else "sim"


def categoria_sexo(op):
    o = normalizar(op)
    if o.startswith("fem"):
        return "F"
    if o.startswith("masc"):
        return "M"
    return None


def categoria_tipo_medio(op):
    return "tecnico" if "tecnico" in normalizar(op) else "outro"


def categoria_modalidade(op):
    o = normalizar(op)
    if "ampla" in o:
        return "AC"
    if "preto" in o or "pardo" in o or "indigena" in o or "ppi" in o:
        return "PPI"
    if "escola publica" in o:
        return "EP"
    return None


CATEGORIZADORES = {
    "cor_raca": categoria_cor,
    "escola_medio": categoria_escola,
    "renda": categoria_renda,
    "escolaridade_pai": categoria_escolaridade,
    "escolaridade_mae": categoria_escolaridade,
    "cursinho": categoria_cursinho,
    "sexo": categoria_sexo,
    "tipo_medio": categoria_tipo_medio,
}

# indicador final = % de respostas na categoria indicada, dentro da pergunta
INDICADORES = {
    "pct_escola_publica": ("escola_medio", "publica"),
    "pct_PPI": ("cor_raca", "PPI"),
    "pct_renda_ate_3SM": ("renda", "ate_3SM"),
    "pct_renda_mais_10SM": ("renda", "mais_10SM"),
    "pct_pai_superior": ("escolaridade_pai", "superior"),
    "pct_mae_superior": ("escolaridade_mae", "superior"),
    "pct_cursinho": ("cursinho", "sim"),
    "pct_mulheres": ("sexo", "F"),
    "pct_tecnico": ("tipo_medio", "tecnico"),
}
# nº de respondentes = total de respostas da pergunta sobre a escola do ensino médio; onde ela não existe
# (ENEM-USP 2025, Provão Paulista, que só aceita aluno de escola pública), a de cor/raça ou a de sexo
TIPOS_RESPONDENTES = ["escola_medio", "cor_raca", "sexo"]


def harmonizar(longo: pd.DataFrame) -> pd.DataFrame:
    df = longo.copy()
    df["tipo"] = df["pergunta"].map(tipo_pergunta)
    df = df[df["tipo"].isin(CATEGORIZADORES)].copy()
    df["categoria"] = [CATEGORIZADORES[t](o) for t, o in zip(df["tipo"], df["opcao"])]
    # respostas sem categoria ("Não sei", "No exterior"...) saem também do denominador
    return df[df["categoria"].notna()]


# --- 3. Preparar as duas fontes no mesmo formato -----------------------------

def modalidade_qase(txt):
    """Cabeçalho do PDF -> AC/EP/PPI; vazio (antes de 2019) -> Todas."""
    if txt is None or (isinstance(txt, float) and np.isnan(txt)) or txt == "Todas":
        return "Todas"
    return categoria_modalidade(txt) or f"?{txt}"


def modalidade_pelas_respostas(q: pd.DataFrame) -> dict:
    """{arquivo: modalidade} quando todos os respondentes da seção marcaram a mesma modalidade de acesso.

    Corrige rótulos trocados no PDF: em 2022 (matriculados) a seção do grupo PPI vem com o cabeçalho
    "Todas as Modalidades de Acesso", mas 100% das respostas à pergunta de modalidade são PPI.
    A troca é registrada pela validação (check Q8).
    """
    tipos = q["pergunta"].map(tipo_pergunta)
    m = q[(tipos == "modalidade") & (q["n"] > 0)]
    cats = m.assign(cat=m["opcao"].map(categoria_modalidade)).groupby("arquivo")["cat"].agg(
        lambda c: c.iloc[0] if c.nunique() == 1 and c.notna().all() else None)
    return cats.dropna().to_dict()


def preparar_qase(qase: pd.DataFrame, carreira_area: pd.DataFrame) -> pd.DataFrame:
    """Linhas de carreira do QASE com ano, fonte, ingresso, etapa, area, modalidade e as contagens."""
    q = qase.copy()
    q["cod_carreira"] = q["cod_carreira"].astype(int)
    q["fonte"], q["ingresso"], q["nivel"] = "qase", "fuvest", "carreira"
    q["modalidade"] = q["modalidade"].map(modalidade_qase)
    q["modalidade"] = q["arquivo"].map(modalidade_pelas_respostas(q)).fillna(q["modalidade"])
    # treineiros (códigos 399, 699, 999) não entram em nenhum nível, como no Anuário
    if "treinamento" in carreira_area:
        treino = carreira_area.loc[carreira_area["treinamento"].astype(bool), ["ano", "cod_carreira"]]
        chave_treino = set(map(tuple, treino.to_numpy()))
        q = q[[(a, c) not in chave_treino for a, c in zip(q["ano"], q["cod_carreira"])]]
    mapa = carreira_area[["ano", "cod_carreira", "area"]].drop_duplicates()
    q = q.merge(mapa, on=["ano", "cod_carreira"], how="left")
    return q


def contagens(harm: pd.DataFrame, chave) -> pd.DataFrame:
    """n por categoria e total por pergunta, somando todas as linhas da chave."""
    harm = harm.copy()
    harm[chave] = harm[chave].fillna("")
    por_cat = harm.groupby(chave + ["tipo", "categoria"])["n"].sum().rename("n_cat").reset_index()
    total = harm.groupby(chave + ["tipo"])["n"].sum().rename("total")
    return por_cat.join(total, on=chave + ["tipo"])


def indicadores_de(cont: pd.DataFrame, chave) -> pd.DataFrame:
    linhas = cont[chave].drop_duplicates().reset_index(drop=True)
    for nome, (tipo, cat) in INDICADORES.items():
        tot = cont[cont["tipo"] == tipo][chave + ["total"]].drop_duplicates()
        sel = cont[(cont["tipo"] == tipo) & (cont["categoria"] == cat)][chave + ["n_cat"]]
        parte = tot.merge(sel, on=chave, how="left")
        # a pergunta existe mas ninguém marcou a categoria -> 0 %; pergunta ausente -> NaN
        parte[nome] = 100 * parte["n_cat"].fillna(0) / parte["total"]
        linhas = linhas.merge(parte[chave + [nome]], on=chave, how="left")
    linhas["respondentes"] = np.nan
    for tipo in TIPOS_RESPONDENTES:
        resp = cont[cont["tipo"] == tipo][chave + ["total"]].drop_duplicates().rename(columns={"total": "_r"})
        linhas = linhas.merge(resp, on=chave, how="left")
        linhas["respondentes"] = linhas["respondentes"].fillna(linhas.pop("_r"))
    return linhas


def indicadores_qase(q: pd.DataFrame) -> pd.DataFrame:
    """Níveis carreira, área e USP, por modalidade e com a modalidade 'Todas' (soma das três)."""
    harm = harmonizar(q)
    base = ["ano", "fonte", "ingresso", "etapa"]
    # "Todas" = a seção "Todas as Modalidades" do PDF, quando existe (antes de 2019 e em carreiras
    # pequenas); senão, a soma das modalidades AC + EP + PPI. Nunca as duas, para não contar em dobro.
    sec = list(zip(harm["ano"], harm["etapa"], harm["cod_carreira"]))
    tem_todas = {s for s, m in zip(sec, harm["modalidade"]) if m == "Todas"}
    por_mod = harm[harm["modalidade"] != "Todas"]
    soma = por_mod[[s not in tem_todas for s in zip(por_mod["ano"], por_mod["etapa"], por_mod["cod_carreira"])]]
    harm = pd.concat([por_mod, harm[harm["modalidade"] == "Todas"], soma.assign(modalidade="Todas")],
                     ignore_index=True)
    # nome e unidade da carreira: os do PDF da modalidade "Todas" ou da primeira modalidade
    nomes = (q.sort_values("modalidade").groupby(["ano", "cod_carreira"])[["carreira", "unidade", "area"]]
             .first().reset_index())

    partes = []
    chave = base + ["cod_carreira", "modalidade"]
    car = indicadores_de(contagens(harm, chave), chave)
    car["cod_carreira"] = car["cod_carreira"].astype(int)
    car = car.merge(nomes, on=["ano", "cod_carreira"], how="left")
    car["nivel"] = "carreira"
    partes.append(car)

    chave = base + ["area", "modalidade"]
    area = indicadores_de(contagens(harm[harm["area"].notna()], chave), chave)
    area["nivel"] = "area"
    partes.append(area)

    chave = base + ["modalidade"]
    usp = indicadores_de(contagens(harm, chave), chave)
    usp["nivel"] = "usp"
    partes.append(usp)
    return pd.concat(partes, ignore_index=True)


def indicadores_anuario(a: pd.DataFrame) -> pd.DataFrame:
    harm = harmonizar(a)
    chave = ["ano", "fonte", "ingresso", "etapa", "nivel", "area"]
    ind = indicadores_de(contagens(harm, chave), chave)
    ind["modalidade"] = "Todas"
    return ind


def excluir_reprovados(df: pd.DataFrame, reprovados: pd.DataFrame | None) -> pd.DataFrame:
    """Tira as linhas reprovadas na validação (src/validacao.py).

    `reprovados` tem a coluna `arquivo` e, opcionalmente, outras colunas-chave (ex.: `num_pergunta`
    no QASE; `pergunta`, `area`, `etapa` no Anuário). Coluna vazia num reprovado vale para qualquer valor.
    """
    if reprovados is None or reprovados.empty:
        return df
    fora = pd.Series(False, index=df.index)
    chaves = [c for c in reprovados.columns if c in df.columns]
    for _, r in reprovados.iterrows():
        marca = pd.Series(True, index=df.index)
        for c in chaves:
            if pd.notna(r[c]) and r[c] != "":
                marca &= df[c].astype(str) == str(r[c])
        fora |= marca
    return df[~fora]


def montar(qase, anuario, carreira_area, reprov_qase=None, reprov_anuario=None):
    partes = []
    if qase is not None:
        q = preparar_qase(excluir_reprovados(qase, reprov_qase), carreira_area)
        partes.append(indicadores_qase(q))
    if anuario is not None:
        partes.append(indicadores_anuario(excluir_reprovados(anuario, reprov_anuario)))
    ind = pd.concat(partes, ignore_index=True)
    for c in COLUNAS:
        if c not in ind:
            ind[c] = np.nan
    ind = ind[COLUNAS].replace({"": np.nan})
    ind["cod_carreira"] = ind["cod_carreira"].astype("Int64")
    ind["respondentes"] = ind["respondentes"].astype("Int64")
    ordem_nivel = {"usp": 0, "area": 1, "carreira": 2}
    ind = ind.sort_values(["ano", "fonte", "ingresso", "etapa", "nivel", "area", "cod_carreira", "modalidade"],
                          key=lambda s: s.map(ordem_nivel) if s.name == "nivel" else s)
    return ind.reset_index(drop=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--qase", default=str(PROC / "qase_longo.csv"))
    ap.add_argument("--anuario", default=str(PROC / "anuario_longo.csv"))
    ap.add_argument("--carreira-area", default=str(RAIZ / "data" / "carreira_area.csv"))
    ap.add_argument("-o", "--saida", default=str(PROC / "indicadores.csv"))
    args = ap.parse_args(argv)

    def ler(caminho):
        return pd.read_csv(caminho) if Path(caminho).exists() else None

    ind = montar(pd.read_csv(args.qase, dtype={"modalidade": str}), pd.read_csv(args.anuario),
                 pd.read_csv(args.carreira_area),
                 ler(PROC / "qase_reprovados.csv"), ler(PROC / "anuario_reprovados.csv"))
    ind.to_csv(args.saida, index=False)
    print(f"{len(ind)} linhas salvas em {args.saida}")


if __name__ == "__main__":
    main()
