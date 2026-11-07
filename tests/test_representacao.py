import pandas as pd
import pytest

from src.representacao import INDICADORES, representacao, validar_modalidades


def linha(ano, etapa, modalidade, resp, ep, ppi, nivel="carreira", cod=710, area="Exatas", fonte="qase"):
    d = {"ano": ano, "fonte": fonte, "ingresso": "fuvest", "etapa": etapa, "nivel": nivel, "area": area,
         "cod_carreira": cod if nivel == "carreira" else None, "carreira": "Computação" if nivel == "carreira" else None,
         "unidade": None, "modalidade": modalidade, "respondentes": resp}
    d.update({c: None for c in INDICADORES})
    d.update(pct_escola_publica=ep, pct_PPI=ppi)
    return d


def test_diferenca_e_razao_do_plano():
    # exemplo do plano: USP 2017, 33,5% dos inscritos e 28,5% dos matriculados
    ind = pd.DataFrame([linha(2017, "inscritos", "Todas", 1000, 33.5, 20.0, nivel="usp", area=None),
                        linha(2017, "matriculados", "Todas", 100, 28.5, 0.0, nivel="usp", area=None)])
    rep = representacao(ind).set_index("indicador")
    ep = rep.loc["pct_escola_publica"]
    assert ep["diferenca_pp"] == pytest.approx(-5.0)
    assert ep["razao"] == pytest.approx(28.5 / 33.5)
    assert pd.isna(ep["cod_carreira"]) and ep["nivel"] == "usp"
    assert rep.loc["pct_PPI", "razao"] == 0          # nenhum PPI matriculado
    assert set(rep.index) == {"pct_escola_publica", "pct_PPI"}   # indicadores vazios não entram


def test_razao_vazia_quando_ninguem_do_grupo_se_inscreveu():
    ind = pd.DataFrame([linha(2019, "inscritos", "AC", 50, 0.0, 10.0), linha(2019, "matriculados", "AC", 10, 0.0, 10.0)])
    rep = representacao(ind).set_index("indicador")
    assert pd.isna(rep.loc["pct_escola_publica", "razao"])
    assert rep.loc["pct_escola_publica", "diferenca_pp"] == 0
    assert bool(rep.loc["pct_PPI", "amostra_pequena"])


def test_recorte_sem_as_duas_etapas_fica_de_fora():
    ind = pd.DataFrame([linha(2019, "inscritos", "AC", 50, 10.0, 10.0), linha(2019, "matriculados", "EP", 10, 100.0, 10.0)])
    assert representacao(ind).empty


def test_criterio_da_modalidade():
    ind = pd.DataFrame([linha(2019, e, "PPI", 40, 100.0, 100.0) for e in ["inscritos", "matriculados"]])
    rep = representacao(ind)
    assert rep["criterio_da_modalidade"].all()


def test_validar_modalidades():
    ind = pd.DataFrame([
        linha(2019, "inscritos", "AC", 60, 10.0, 20.0),
        linha(2019, "inscritos", "EP", 30, 100.0, 10.0),
        linha(2019, "inscritos", "PPI", 10, 70.0, 100.0),      # M4: PPI com 70% de escola pública
        linha(2019, "inscritos", "Todas", 101, 43.0, 25.0),    # M1: soma = 100; M2: média = 43,0 / 25,0
        linha(2019, "matriculados", "AC", 6, 10.0, 20.0),
        linha(2019, "matriculados", "EP", 4, 100.0, 50.0),     # M3: falta PPI
        linha(2019, "matriculados", "Todas", 10, 46.0, 32.0),  # M2 em pct_escola_publica (46 vs 46) ok; PPI 32 ok
        linha(2018, "inscritos", "Todas", 10, 46.0, 32.0),     # sem modalidades: fora da validação
    ])
    val = validar_modalidades(ind)
    checks = val.groupby("check").size().to_dict()
    assert checks == {"M1 AC+EP+PPI != Todas (respondentes)": 1, "M3 modalidade faltando": 1,
                      "M4 modalidade fora do próprio critério": 1}
    m3 = val[val["check"].str.startswith("M3")].iloc[0]
    assert (m3["etapa"], m3["modalidade"], m3["cod_carreira"]) == ("matriculados", "PPI", 710)


def test_validar_modalidades_media_ponderada():
    ind = pd.DataFrame([linha(2020, "inscritos", m, n, ep, 0.0) for m, n, ep in
                        [("AC", 50, 0.0), ("EP", 50, 100.0), ("PPI", 0, 100.0), ("Todas", 100, 60.0)]])
    val = validar_modalidades(ind)
    m2 = val[val["check"].str.startswith("M2")]
    assert list(m2["indicador"]) == ["pct_escola_publica"]


def test_intervalo_da_diferenca():
    # 1000 inscritos com 30%, 100 matriculados com 45%: diferença 15 p.p., erro-padrão ~5,2 p.p.
    ind = pd.DataFrame([linha(2017, "inscritos", "Todas", 1000, 30.0, None, nivel="usp", area=None),
                        linha(2017, "matriculados", "Todas", 100, 45.0, None, nivel="usp", area=None)])
    ep = representacao(ind).set_index("indicador").loc["pct_escola_publica"]
    meia = 1.96 * 100 * ((0.3 * 0.7 / 1000) + (0.45 * 0.55 / 100)) ** 0.5
    assert ep["ic95_inf_pp"] == pytest.approx(15 - meia)
    assert ep["ic95_sup_pp"] == pytest.approx(15 + meia)
    assert bool(ep["diferenca_clara"])          # ~4,9 a ~25 p.p.: não inclui o zero
    pequena = pd.DataFrame([linha(2017, "inscritos", "Todas", 1000, 30.0, None, nivel="usp", area=None),
                            linha(2017, "matriculados", "Todas", 10, 40.0, None, nivel="usp", area=None)])
    assert not bool(representacao(pequena).set_index("indicador").loc["pct_escola_publica", "diferenca_clara"])


def test_m2_pondera_pelo_denominador_do_indicador():
    # carreira 235, inscritos 2021 (PDFs conferidos): pai com superior = 32/56, 7/18 e 0/11; Todas = 39/85.
    # "Não sei" e "Não possuo pai" saem do denominador, então pesar pelos respondentes (57, 23, 17) erra 3 p.p.
    def l(mod, resp, n, pct):
        d = linha(2021, "inscritos", mod, resp, None, None, cod=235, area="Humanas")
        d.update(pct_pai_superior=pct, n_pai_superior=n)
        return d
    linhas = [l("AC", 57, 56, 100 * 32 / 56), l("EP", 23, 18, 100 * 7 / 18), l("PPI", 17, 11, 0.0),
              l("Todas", 97, 85, 100 * 39 / 85)]
    val = validar_modalidades(pd.DataFrame(linhas))
    assert not val["check"].str.startswith("M2").any()
    sem_n = pd.DataFrame(linhas).drop(columns="n_pai_superior")
    assert validar_modalidades(sem_n)["check"].str.startswith("M2").any()
