# Do inscrito ao matriculado: o perfil de quem entra no ICMC

Projeto de SCC0252 Visualização Computacional (ICMC-USP, 2026/2).

Analisamos o Questionário de Avaliação Socioeconômica (QASE) da Fuvest de 2010 a 2022. O objetivo é ver como o perfil dos candidatos (escola pública, PPI, renda, escolaridade dos pais) muda entre as etapas do vestibular e ao longo dos anos, antes e depois das cotas, com foco nos cursos do ICMC.

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1. coletar os PDFs nas páginas de acervo da Fuvest (lista em data/fontes_coletadas.csv)
python scripts/coletar_fuvest.py --anos 2010-2022

# 2. (opcional) separar cada PDF em um arquivo por carreira/curso
python scripts/picotar_pdfs.py data/raw/*qase*.pdf

# 3. extrair as tabelas dos PDFs -> data/processed/qase_longo.csv
python -m src.qase_parser data/raw/*qase*.pdf      # ou data/raw/por_curso/*.pdf (não use os dois juntos)

# 4. harmonizar categorias e calcular indicadores -> data/processed/indicadores.csv
python -m src.harmonizacao

# 5. abrir o app em http://127.0.0.1:8050
python app/app.py
```

Para testar o app antes de ter os dados reais, rode `python scripts/gerar_dados_demo.py`. Ele gera números **fictícios**, e o app mostra um aviso enquanto estiver usando esses dados.

Testes: `python -m pytest`.

### Coleta (`scripts/coletar_fuvest.py`)

Abre a página de acervo de cada ano (`fuvest.br/acervo-vestibular-AAAA`) com requests + BeautifulSoup, classifica os links de PDF pelo nome do arquivo e pelo texto do link, e baixa os selecionados para `data/raw/`. O script respeita o `robots.txt` e espera 1 s entre pedidos.

```bash
python scripts/coletar_fuvest.py --anos 2013-2022 --etapas inscritos matriculados --nivel carreira   # prioridade da 1ª entrega
python scripts/coletar_fuvest.py --tipos nota_de_corte notas_minimas candidato_vaga --anos 2010-2026
python scripts/coletar_fuvest.py --so-listar     # só mostra o que encontrou
```

Se o site mudar e a coleta falhar, `scripts/baixar_pdfs.py` baixa a partir da lista fixa em `data/fontes_qase.csv`.

### Separação por curso (`scripts/picotar_pdfs.py`)

Os PDFs de "por curso" têm mais de 1000 páginas. O script lê o cabeçalho de cada página com pypdf e grava um PDF por carreira/curso em `data/raw/por_curso/`. As páginas de índice são descartadas. Os filtros servem para ficar só com o que interessa ou para mandar um trecho pequeno para alguém:

```bash
python scripts/picotar_pdfs.py data/raw/FUVEST_2021_qase_chamados_matricula_1_curso.pdf --unidade ICMC
python scripts/picotar_pdfs.py data/raw/*carreira*.pdf --carreira 710 875     # PDFs por carreira não têm a unidade no nome
```

### Anuário Estatístico da USP, 2023 em diante (`scripts/recortar_anuario.py`)

A Fuvest não publica o QASE em PDF desde 2023. O Anuário Estatístico da USP traz o mesmo questionário resumido (colunas Insc./Conv./Matr.), mas só para o total da USP e por área (Biológicas, Exatas, Humanas), sem carreira, curso ou modalidade. O script acha as tabelas de perfil pelo título (o número da tabela muda entre anuários) e grava um PDF por tabela em `data/raw/anuario/`: Fuvest em todos os anos, ENEM-USP a partir de 2025 e Provão Paulista em 2026.

```bash
python scripts/recortar_anuario.py AnuarioUSP_2023.pdf AnuarioUSP_2024.pdf AnuarioUSP_2025.pdf AnuarioUSP_2026.pdf
python scripts/recortar_anuario.py AnuarioUSP_2026.pdf --com-candidato-vaga     # inclui candidato/vaga por curso
```

## Estrutura

| Caminho | O que é |
|---|---|
| `data/fontes_qase.csv`, `data/fontes_notas.csv` | URLs de todos os PDFs da Fuvest usados |
| `docs/divisao_tarefas.md` | Divisão do trabalho entre os 4 perfis, questões e cronograma |
| `docs/lista_pdfs.md` | A mesma lista, legível, com a prioridade de download |
| `scripts/coletar_fuvest.py` | Coleta dos PDFs nas páginas de acervo (BeautifulSoup) |
| `scripts/picotar_pdfs.py` | Separa cada PDF do QASE em um arquivo por carreira/curso (pypdf) |
| `scripts/recortar_anuario.py` | Recorta do Anuário Estatístico da USP as tabelas de perfil dos candidatos (2023+) |
| `scripts/baixar_pdfs.py` | Plano B: download a partir da lista fixa |
| `src/qase_parser.py` | Extração das tabelas do QASE (pdfplumber + regex) |
| `src/harmonizacao.py` | Identificação das perguntas, reagrupamento das categorias e cálculo dos indicadores |
| `app/app.py` | App Dash com as visualizações |

## Calibração do parser

O parser foi calibrado com páginas reais de `FUVEST_2021_qase_chamados_matricula_1_curso.pdf` (ver o trecho em `tests/test_pipeline.py`). Os indicadores conferem com a contagem feita à mão. Outros anos podem ter pequenas diferenças de layout. Se um PDF der "0 linhas" ou números estranhos, veja o texto extraído com:

```bash
python -m src.qase_parser --dump data/raw/ARQUIVO.pdf --paginas 3-6
```

e ajuste as regex do topo de `src/qase_parser.py`.

## Pontos de atenção no pré-processamento

- **Carreira × curso:** até ~2018 os dados vêm por carreira (ex.: "710 Computação" junta vários cursos). "Chamados 1ª matrícula por curso" existe em todos os anos e é o recorte por curso mais consistente.
- **Renda:** as faixas são em salários mínimos e o SM muda a cada ano. Confira se algum ano usa reais.
- **Cobertura:** o QASE descreve só quem entrou pela Fuvest. As vagas do Sisu, do Enem-USP e do Provão Paulista ficam de fora, e isso deve ser discutido como limitação.
- **2023 em diante:** a Fuvest não publicou o QASE em PDF.
- **Modalidade (AC/EP/PPI):** em 2021 há a pergunta "Em qual modalidade de acesso você se inscreveu?". Os indicadores `pct_mod_*` ficam vazios nos anos sem essa pergunta.
- **Denominador:** respostas como "Não sei", "Não possuo pai" e "No exterior" ficam fora do cálculo do percentual.
