"""Validações automáticas da extração (QASE e Anuário) e relatório do que falhou.

Nenhum número é corrigido à mão: o que não passa é reprovado e sai do indicadores.csv
(o indicador fica vazio), e o motivo fica registrado com arquivo e página.

QASE (data/processed/qase_longo.csv), por pergunta de cada PDF:
  Q1  a soma das contagens das opções é igual ao "N respostas" impresso          -> reprova a pergunta
  Q2  a pergunta não tem a linha "N respostas" (opção perdida ou página cortada) -> reprova a pergunta
  Q3  a % impressa bate com contagem / N respostas (tolerância 0,06 pp)          -> reprova a pergunta
  Q4  N respostas <= nº de questionários entregues                               -> aviso
  Q5  todo PDF de entrada gerou linhas                                           -> aviso
  Q6  carreira + modalidade + etapa aparece em um único PDF                      -> aviso
  Q7  modalidade reconhecida (AC, EP, PPI ou Todas)                              -> aviso
  Q8  a modalidade do cabeçalho é a mesma que 100% da seção marcou na pergunta
      "Em qual modalidade de acesso você se inscreveu?" (senão vale a das respostas) -> aviso

Anuário (data/processed/anuario_longo.csv), por pergunta, área e etapa:
  A1  as % impressas somam 100 (99 a 101)                                        -> reprova
  A2  a % impressa bate com quantidade / soma da pergunta (tolerância 0,06 pp)   -> aviso se até 1 pp, reprova acima
  A3  a soma das 3 áreas é igual ao total da USP (mesmo ano, pergunta e opção)   -> reprova a tabela por área
      quando a maioria das linhas não bate (tabela trocada); aviso nos casos isolados
  A4  o total de respostas da pergunta difere mais de 2% da mediana da tabela   -> aviso

Uso:
    python -m src.validacao --pdfs data/raw/por_carreira
"""
import argparse
import re
import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "data" / "processed"
TOL_PCT = 0.06


def _nz(t):
    t = unicodedata.normalize("NFKD", str(t).replace("−", "-")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def validar_qase(q: pd.DataFrame, pdfs=None):
    """Devolve (problemas, reprovados)."""
    probs = []
    chave = ["arquivo", "num_pergunta"]
    g = q.groupby(chave, sort=False)
    blocos = g.agg(ano=("ano", "first"), etapa=("etapa", "first"), cod_carreira=("cod_carreira", "first"),
                   modalidade=("modalidade", "first"), pergunta=("pergunta", "first"), pagina=("pagina", "first"),
                   soma=("n", "sum"), n_respostas=("n_respostas", "first"), sem_total=("n_respostas", lambda s: s.isna().any()),
                   questionarios=("questionarios", "first")).reset_index()

    def add(df, check, gravidade, detalhe):
        for _, r in df.iterrows():
            probs.append({"check": check, "gravidade": gravidade, "arquivo": r["arquivo"], "pagina": r.get("pagina"),
                          "ano": r.get("ano"), "etapa": r.get("etapa"), "cod_carreira": r.get("cod_carreira"),
                          "modalidade": r.get("modalidade"), "num_pergunta": r.get("num_pergunta"),
                          "pergunta": r.get("pergunta"), "detalhe": detalhe(r)})

    sem = blocos[blocos["sem_total"]]
    add(sem, "Q2 sem 'N respostas'", "reprova", lambda r: f"soma das opções = {r['soma']}")
    com = blocos[~blocos["sem_total"]]
    dif = com[com["soma"] != com["n_respostas"]]
    add(dif, "Q1 soma != N respostas", "reprova", lambda r: f"soma = {r['soma']}, impresso = {int(r['n_respostas'])}")

    qq = q[q["n_respostas"].notna() & (q["n_respostas"] > 0)].copy()
    qq["pct_calc"] = 100 * qq["n"] / qq["n_respostas"]
    ruim = qq[(qq["pct"] - qq["pct_calc"]).abs() > TOL_PCT]
    for _, r in ruim.iterrows():
        probs.append({"check": "Q3 % impressa != contagem", "gravidade": "reprova", "arquivo": r["arquivo"],
                      "pagina": r["pagina"], "ano": r["ano"], "etapa": r["etapa"], "cod_carreira": r["cod_carreira"],
                      "modalidade": r["modalidade"], "num_pergunta": r["num_pergunta"], "pergunta": r["pergunta"],
                      "detalhe": f"'{r['opcao']}': {r['pct']}% impresso, {r['pct_calc']:.2f}% calculado ({r['n']}/{int(r['n_respostas'])})"})

    acima = com[com["n_respostas"] > com["questionarios"]]
    add(acima, "Q4 N respostas > questionários", "aviso",
        lambda r: f"{int(r['n_respostas'])} respostas, {r['questionarios']} questionários")

    if pdfs is not None:
        lidos = set(q["arquivo"])
        for nome in sorted(set(pdfs) - lidos):
            probs.append({"check": "Q5 PDF sem linhas", "gravidade": "aviso", "arquivo": nome,
                          "detalhe": "nenhuma pergunta reconhecida"})

    por_sec = q.groupby(["ano", "etapa", "cod_carreira", q["modalidade"].fillna("Todas")])["arquivo"].nunique()
    for (ano, etapa, cod, mod), k in por_sec[por_sec > 1].items():
        arqs = sorted(q[(q["ano"] == ano) & (q["etapa"] == etapa) & (q["cod_carreira"] == cod)
                        & (q["modalidade"].fillna("Todas") == mod)]["arquivo"].unique())
        probs.append({"check": "Q6 seção repetida", "gravidade": "aviso", "arquivo": "; ".join(arqs), "ano": ano,
                      "etapa": etapa, "cod_carreira": cod, "modalidade": mod, "detalhe": f"em {k} PDFs"})

    from src.harmonizacao import modalidade_qase
    mods = q["modalidade"].drop_duplicates()
    for m in mods:
        if modalidade_qase(m).startswith("?"):
            arqs = q.loc[q["modalidade"] == m, "arquivo"].unique()
            probs.append({"check": "Q7 modalidade desconhecida", "gravidade": "aviso", "arquivo": "; ".join(arqs[:3]),
                          "modalidade": m, "detalhe": f"{len(arqs)} PDFs"})

    from src.harmonizacao import modalidade_pelas_respostas
    pelas_resp = modalidade_pelas_respostas(q)
    cab = q.drop_duplicates("arquivo").set_index("arquivo")["modalidade"].map(modalidade_qase)
    for arq, mod in pelas_resp.items():
        if cab.get(arq) != mod:
            r = q[q["arquivo"] == arq].iloc[0]
            probs.append({"check": "Q8 modalidade do cabeçalho != respostas", "gravidade": "aviso", "arquivo": arq,
                          "pagina": 1, "ano": r["ano"], "etapa": r["etapa"], "cod_carreira": r["cod_carreira"],
                          "modalidade": r["modalidade"],
                          "detalhe": f"cabeçalho '{r['modalidade']}', mas 100% marcaram {mod}; usado {mod}"})

    probs = pd.DataFrame(probs)
    reprov = (probs[probs["gravidade"] == "reprova"][["arquivo", "num_pergunta"]].drop_duplicates()
              if not probs.empty else pd.DataFrame(columns=["arquivo", "num_pergunta"]))
    if not reprov.empty:
        reprov["num_pergunta"] = reprov["num_pergunta"].astype(int)
    return probs, reprov


def validar_anuario(a: pd.DataFrame):
    probs, reprov = [], []
    chave = ["arquivo", "pergunta", "area", "etapa"]
    a = a.copy()
    a["area"] = a["area"].fillna("")
    soma_pct = a.groupby(chave, sort=False).agg(ano=("ano", "first"), ingresso=("ingresso", "first"),
                                                pagina=("pagina", "first"), soma_pct=("pct", "sum")).reset_index()
    fora = soma_pct[(soma_pct["soma_pct"] < 99) | (soma_pct["soma_pct"] > 101)]
    for _, r in fora.iterrows():
        probs.append({**{c: r[c] for c in ["arquivo", "pagina", "ano", "ingresso", "pergunta", "area", "etapa"]},
                      "check": "A1 % não somam 100", "gravidade": "reprova", "detalhe": f"soma = {r['soma_pct']:.2f}%"})
        reprov.append({c: r[c] for c in chave})

    a["pct_calc"] = 100 * a["n"] / a["n_respostas"]
    a["dif"] = (a["pct"] - a["pct_calc"]).abs()
    for _, r in a[a["dif"] > TOL_PCT].iterrows():
        grave = r["dif"] > 1
        probs.append({**{c: r[c] for c in ["arquivo", "pagina", "ano", "ingresso", "pergunta", "area", "etapa"]},
                      "check": "A2 % impressa != quantidade", "gravidade": "reprova" if grave else "aviso",
                      "detalhe": f"'{r['opcao']}': {r['pct']}% impresso, {r['pct_calc']:.2f}% calculado "
                                 f"({r['n']}/{r['n_respostas']})"})
        if grave:
            reprov.append({c: r[c] for c in chave})

    # A4: dentro de uma tabela e coluna, quase todas as perguntas têm o mesmo total de respostas
    tot = a.groupby(chave, sort=False).agg(ano=("ano", "first"), ingresso=("ingresso", "first"),
                                           pagina=("pagina", "first"), total=("n", "sum")).reset_index()
    tot["mediana"] = tot.groupby(["arquivo", "area", "etapa"])["total"].transform("median")
    for _, r in tot[(tot["total"] - tot["mediana"]).abs() > 0.02 * tot["mediana"]].iterrows():
        probs.append({**{c: r[c] for c in ["arquivo", "pagina", "ano", "ingresso", "pergunta", "area", "etapa"]},
                      "check": "A4 total da pergunta != total da tabela", "gravidade": "aviso",
                      "detalhe": f"{r['total']} respostas; a mediana das perguntas é {r['mediana']:.0f}"})

    a["pq"], a["op"] = a["pergunta"].map(_nz), a["opcao"].map(_nz)
    k = ["ano", "ingresso", "pq", "op", "etapa"]
    areas = a[a["nivel"] == "area"].groupby(k).agg(soma_areas=("n", "sum"), arquivo=("arquivo", "first"),
                                                   pagina=("pagina", "first"), pergunta=("pergunta", "first"))
    usp = a[a["nivel"] == "usp"].groupby(k)["n"].sum().rename("usp")
    j = areas.join(usp, how="inner").reset_index()
    j["bate"] = j["soma_areas"] == j["usp"]
    for arq, g in j.groupby("arquivo"):
        if (~g["bate"]).mean() > 0.5:
            outro = _tabela_de_outro_ano(a, arq)
            probs.append({"check": "A3 soma das áreas != USP", "gravidade": "reprova", "arquivo": arq,
                          "ano": g["ano"].iloc[0], "ingresso": g["ingresso"].iloc[0],
                          "detalhe": f"{(~g['bate']).sum()} de {len(g)} opções não batem com a tabela geral"
                                     + (f"; as quantidades são idênticas às de {outro}" if outro else "")})
            reprov.append({"arquivo": arq, "pergunta": "", "area": "", "etapa": ""})
        else:
            for _, r in g[~g["bate"]].iterrows():
                probs.append({"check": "A3 soma das áreas != USP", "gravidade": "aviso", "arquivo": arq,
                              "pagina": r["pagina"], "ano": r["ano"], "ingresso": r["ingresso"],
                              "pergunta": r["pergunta"], "etapa": r["etapa"],
                              "detalhe": f"opção '{r['op']}': áreas = {r['soma_areas']}, USP = {r['usp']}"})
    probs = pd.DataFrame(probs)
    reprov = pd.DataFrame(reprov, columns=chave).drop_duplicates()
    return probs, reprov


def _tabela_de_outro_ano(a, arquivo):
    """Se as quantidades de `arquivo` forem idênticas às de outro recorte, devolve o nome dele."""
    este = a[a["arquivo"] == arquivo]["n"].to_numpy()
    for outro, g in a.groupby("arquivo"):
        if outro != arquivo and len(g) == len(este) and (g["n"].to_numpy() == este).all():
            return outro
    return None


def tabela_md(df):
    """DataFrame -> tabela Markdown (sem depender do pacote tabulate)."""
    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    corpo = ["| " + " | ".join(str(v) for v in linha) + " |" for linha in df.itertuples(index=False)]
    return "\n".join([cab, sep] + corpo)


def resumo_md(qp, qr, q, ap, ar, a):
    linhas = ["# Relatório de validação da extração", "",
              "Gerado por `python -m src.validacao`. Tudo aqui é calculado a partir dos CSVs extraídos; "
              "nenhum número foi digitado à mão.", ""]
    nq = q.groupby(["arquivo", "num_pergunta"]).ngroups
    linhas += ["## QASE (2013–2022)", "",
               f"- {q['arquivo'].nunique()} PDFs, {nq} perguntas, {len(q)} linhas extraídas.",
               f"- Perguntas reprovadas: {len(qr)} ({100 * len(qr) / max(nq, 1):.2f}%).", ""]
    if not qp.empty:
        t = qp.groupby(["check", "gravidade"]).size().rename("ocorrências").reset_index()
        linhas += [t.pipe(tabela_md), ""]
        rep = qp[qp["gravidade"] == "reprova"]
        if not rep.empty:
            por_ano = rep.groupby(["ano", "etapa"])["arquivo"].nunique().rename("PDFs com reprovação").reset_index()
            linhas += ["Por ano e etapa:", "", por_ano.pipe(tabela_md), ""]
    linhas += ["## Anuário (2022–2026)", "",
               f"- {a['arquivo'].nunique()} recortes, {len(a)} linhas extraídas.", ""]
    if not ap.empty:
        t = ap.groupby(["check", "gravidade"]).size().rename("ocorrências").reset_index()
        linhas += [t.pipe(tabela_md), ""]
        grave = ap[(ap["gravidade"] == "reprova")]
        if not grave.empty:
            linhas += ["Reprovações:", ""]
            for _, r in grave.drop_duplicates(["arquivo", "check", "pergunta", "area"]).head(40).iterrows():
                onde = f"{r['arquivo']}" + (f" p. {int(r['pagina'])}" if pd.notna(r.get("pagina")) else "")
                perg = f" — {r['pergunta']}" if isinstance(r.get("pergunta"), str) and r["pergunta"] else ""
                area = f" [{r['area']}]" if isinstance(r.get("area"), str) and r["area"] else ""
                linhas.append(f"- {onde}{perg}{area}: {r['check']} ({r['detalhe']})")
            linhas.append("")
        avisos = ap[(ap["gravidade"] == "aviso") & (ap["check"].str.startswith("A2"))]
        if not avisos.empty:
            linhas += ["Avisos de porcentagem (as contagens são usadas; a % impressa pelo Anuário difere um pouco):", "",
                       avisos.groupby("arquivo").size().rename("opções").reset_index().pipe(tabela_md), ""]
    linhas += ["Os detalhes, com arquivo e página, estão em `data/processed/validacao_qase.csv` e "
               "`data/processed/validacao_anuario.csv`.", ""]
    return "\n".join(linhas)


def main(argv=None):
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--qase", default=str(PROC / "qase_longo.csv"))
    ap_.add_argument("--anuario", default=str(PROC / "anuario_longo.csv"))
    ap_.add_argument("--pdfs", help="pasta dos PDFs do QASE, para conferir se todos geraram linhas")
    ap_.add_argument("--relatorio", default=str(RAIZ / "docs" / "relatorio_validacao.md"))
    args = ap_.parse_args(argv)

    q = pd.read_csv(args.qase, dtype={"modalidade": str})
    pdfs = [p.name for p in Path(args.pdfs).glob("*.pdf")] if args.pdfs else None
    qp, qr = validar_qase(q, pdfs)
    a = pd.read_csv(args.anuario)
    ap, ar = validar_anuario(a)
    qp.to_csv(PROC / "validacao_qase.csv", index=False)
    qr.to_csv(PROC / "qase_reprovados.csv", index=False)
    ap.to_csv(PROC / "validacao_anuario.csv", index=False)
    ar.to_csv(PROC / "anuario_reprovados.csv", index=False)
    Path(args.relatorio).write_text(resumo_md(qp, qr, q, ap, ar, a), encoding="utf-8")
    print(f"QASE: {len(qp)} problemas, {len(qr)} perguntas reprovadas")
    print(f"Anuário: {len(ap)} problemas, {len(ar)} blocos reprovados")
    print(f"relatório em {args.relatorio}")


if __name__ == "__main__":
    main()
