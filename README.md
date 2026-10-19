# Do inscrito ao matriculado: o perfil de quem entra no ICMC

Projeto de SCC0252 Visualização Computacional (ICMC-USP, 2026/2).

Analisamos o Questionário de Avaliação Socioeconômica (QASE) da Fuvest de 2010 a 2022. O objetivo é ver como o perfil dos candidatos (escola pública, PPI, renda, escolaridade dos pais) muda entre as etapas do vestibular e ao longo dos anos, antes e depois das cotas, com foco nos cursos do ICMC.

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1. baixar os PDFs (lista completa em docs/lista_pdfs.md)
python scripts/baixar_pdfs.py --so-prioridade       # ou sem a flag para baixar tudo

# 2. extrair as tabelas dos PDFs -> data/processed/qase_longo.csv
python -m src.qase_parser data/raw/*qase*.pdf

# 3. harmonizar categorias e calcular indicadores -> data/processed/indicadores.csv
python -m src.harmonizacao

# 4. abrir o app em http://127.0.0.1:8050
python app/app.py
```

Para testar o app antes de ter os dados reais, rode `python scripts/gerar_dados_demo.py`. Ele gera números **fictícios**, e o app mostra um aviso enquanto estiver usando esses dados.

Testes: `python -m pytest`.

## Estrutura

| Caminho | O que é |
|---|---|
| `data/fontes_qase.csv`, `data/fontes_notas.csv` | URLs de todos os PDFs da Fuvest usados |
| `docs/lista_pdfs.md` | A mesma lista, legível, com a prioridade de download |
| `scripts/baixar_pdfs.py` | Download dos PDFs para `data/raw/` |
| `src/qase_parser.py` | Extração das tabelas do QASE (pdfplumber + regex) |
| `src/harmonizacao.py` | Identificação das perguntas, reagrupamento das categorias e cálculo dos indicadores |
| `app/app.py` | App Dash com as visualizações |

## Primeiro passo com um PDF real: calibrar o parser

O parser foi escrito antes de termos os PDFs em mãos. Com o primeiro PDF baixado:

```bash
python -m src.qase_parser --dump data/raw/FUVEST_2021_qase_chamados_matricula_1_curso.pdf --paginas 3-6
```

Compare o texto impresso com as regex do topo de `src/qase_parser.py` (`RE_CARREIRA`, `RE_CURSO`, `RE_PERGUNTA`, `RE_OPCAO`). Ajuste o que for preciso e cole um trecho real em `tests/test_pipeline.py`.

## Pontos de atenção no pré-processamento

- **Carreira × curso:** até ~2018 os dados vêm por carreira (ex.: "710 Computação" junta vários cursos). "Chamados 1ª matrícula por curso" existe em todos os anos e é o recorte por curso mais consistente.
- **Renda:** as faixas são em salários mínimos e o SM muda a cada ano. Confira se algum ano usa reais.
- **Cobertura:** o QASE descreve só quem entrou pela Fuvest. As vagas do Sisu, do Enem-USP e do Provão Paulista ficam de fora, e isso deve ser discutido como limitação.
- **2023 em diante:** a Fuvest não publicou o QASE em PDF.
