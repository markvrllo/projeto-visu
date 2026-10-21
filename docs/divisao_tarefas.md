# Divisão do trabalho em 4 perfis (revisão de 21/10)

Projeto: **"Quem entra na USP: o perfil dos ingressantes antes e depois das cotas (2013–2026)"**.

## O que mudou nesta revisão

- **Escopo:** a análise passa a ser das cotas na **USP inteira**. O ICMC deixa de ser o foco e vira só um exemplo que pode ser destacado nas visões.
- **Fontes:** são duas, com granularidades diferentes.

| Período | Fonte | Etapas | Granularidade | Modalidade (AC/EP/PPI) |
|---|---|---|---|---|
| 2013–2022 | QASE da Fuvest, PDFs por carreira (já separados em `data/raw/por_carreira`) | inscritos e matriculados | carreira (≈ 100 por ano) | sim, de 2019 a 2022 |
| 2022–2026 | Anuário Estatístico da USP, tabelas recortadas por `scripts/recortar_anuario.py` | inscritos, convocados e matriculados | total da USP e 3 áreas (Biológicas, Exatas, Humanas) | não |

- **Ponte:** o Anuário 2022 e o QASE 2022 descrevem o mesmo ano. Comparar os dois mostra se a série pode ser emendada.
- **Vias de ingresso:** os anuários trazem também o ENEM-USP (perfil a partir de 2025) e o Provão Paulista (2026). Isso vira uma questão nova.
- **Limites dos anuários:** não têm carreira, curso nem modalidade, e cor/raça e sexo só aparecem a partir de 2024. Por isso a **única série contínua de 2013 a 2026 é a do total da USP e das 3 áreas**. Para comparar carreiras e modalidades, o período é 2013–2022.

## Os 4 perfis

| Perfil | Papel | Questões que responde | Dono no código |
|---|---|---|---|
| **A. Dados** | Montar e manter o dataset | base para todas | `scripts/`, `src/qase_parser.py`, `src/harmonizacao.py`, `data/` |
| **B. Evolução** | Visões temporais | Q1 (evolução na USP e nas áreas) e, na 2ª entrega, Q5 (seletividade e modalidades) | `app/visoes/serie.py`, `app/visoes/heatmap.py`, `app/visoes/modalidades.py` |
| **C. Funil e carreiras** | Funil e comparação entre carreiras | Q2 (funil) e Q3 (carreiras), e na 2ª entrega Q6 (vias de ingresso) | `app/visoes/funil.py`, `app/visoes/paralelas.py`, `app/visoes/vias.py` |
| **D. Integração e interação** | Leitura dos anuários, layout do app, interações, acessibilidade, relatório e vídeo | coordena as conclusões | `src/anuario_parser.py`, `app/app.py`, `app/estado.py`, relatório e vídeo |

Cada pessoa escreve o código **e** a parte do relatório da sua área, e precisa saber explicar o que fez (pode haver arguição sobre uso de IA). Todos precisam entender o projeto como um todo.

## O "contrato" entre os perfis

O arquivo `data/processed/indicadores.csv`. Enquanto A e D montam os dados reais, B e C trabalham com `indicadores_DEMO.csv` (`python scripts/gerar_dados_demo.py`), que precisa ser atualizado para as colunas novas abaixo.

Colunas (não mudar sem avisar o grupo):

`ano, fonte, ingresso, etapa, nivel, area, cod_carreira, carreira, unidade, modalidade, respondentes, pct_escola_publica, pct_PPI, pct_renda_ate_3SM, pct_renda_mais_10SM, pct_pai_superior, pct_mae_superior, pct_cursinho, pct_mulheres, pct_tecnico`

| Coluna | Valores |
|---|---|
| `fonte` | `qase` ou `anuario` |
| `ingresso` | `fuvest`, `enem-usp` ou `provao-paulista` |
| `etapa` | `inscritos`, `convocados` ou `matriculados` |
| `nivel` | `usp`, `area` ou `carreira` |
| `area` | `Biológicas`, `Exatas` ou `Humanas` (vazio no nível `usp`) |
| `modalidade` | `Todas`, `AC`, `EP` ou `PPI` (só `Todas` nos anuários e antes de 2019) |

Indicador que não existe numa fonte ou ano fica vazio (`NaN`), nunca zero. Ex.: `pct_PPI` nos anuários de 2022 e 2023.

Regras de git:
- cada pessoa trabalha num branch próprio e abre um PR para a `main`;
- revisões em duplas cruzadas: **A ↔ D** e **B ↔ C**;
- commits pequenos e com mensagem clara (o histórico mostra quem fez o quê).

---

## 1ª entrega (até 03/11)

### Questões da 1ª entrega

1. **Q1 Evolução:** como evoluiu a proporção de matriculados de escola pública, PPI e baixa renda na USP e em cada área de 2013 a 2026, antes e depois da implantação das cotas?
2. **Q2 Funil:** como o perfil muda de inscritos para convocados e matriculados? O filtro do vestibular sobre escola pública, PPI e renda diminuiu depois das cotas?
3. **Q3 Carreiras:** quais carreiras são mais elitizadas, e quais mais mudaram com as cotas (2013–2022)?

### A. Dados
**Código**
- Rodar `src/qase_parser.py` nos 3.875 PDFs de `data/raw/por_carreira` (2013–2022, inscritos e matriculados) e corrigir os anos com layout diferente.
- Validar: em cada pergunta, a soma das contagens deve bater com "N respostas". Anotar os anos ou carreiras que falharem.
- Criar a tabela **carreira → área** (`data/carreira_area.csv`) com as mesmas 3 áreas do anuário. Ela permite somar as carreiras do QASE e comparar com os números do anuário.
- Somar as contagens (não as porcentagens) para gerar os níveis `area` e `usp` do QASE.
- Gerar `indicadores.csv` real a partir do QASE e juntar com a parte do anuário que D entrega.

**Relatório:** seções *Conjunto de dados* (fontes, tamanho, tipos de variáveis, cobertura por ano e por fonte) e *Pré-processamento* (extração, harmonização das categorias, agregação de carreira para área, emenda das duas fontes).
**Vídeo (~1 min):** de onde vêm os dados e como viraram tabela.

### B. Evolução
**Código**
- Visão 1: série temporal de cada indicador (escola pública, PPI, renda até 3 SM, pais com ensino superior) para a USP e as 3 áreas, de 2013 a 2026. Marcar com uma linha vertical ou mudança de traço a troca de fonte entre 2022 e 2023 e mostrar o ponto de 2022 nas duas fontes.
- Faixa anotada com a implantação das cotas. Confirmar nos documentos oficiais da USP os anos e percentuais exatos (implantação escalonada a partir de 2018) e a entrada do ENEM-USP e do Provão Paulista.
- Justificar a escolha (linha para tendência temporal; cor + rótulo direto para as áreas).

**Relatório:** análise visual e insights da **Q1**.
**Vídeo (~1 min 15):** a evolução do perfil na USP antes e depois das cotas.

### C. Funil e carreiras
**Código**
- Visão 2: funil inscritos → convocados → matriculados (slope chart) para um ano e um indicador. De 2023 a 2026 há as 3 etapas; de 2013 a 2022, só inscritos e matriculados.
- Visão 3: coordenadas paralelas com todas as carreiras de um ano (2013–2022), eixos = indicadores, cor = área. Permitir destacar uma unidade (ex.: ICMC) ou uma carreira.
- Justificar as escolhas (etapas ordenadas; dados multidimensionais).

**Relatório:** análise visual e insights da **Q2** e da **Q3**.
**Vídeo (~1 min 30):** em que etapa o perfil muda e quais carreiras mudaram mais.

### D. Integração e interação
**Código**
- `src/anuario_parser.py`: ler as tabelas de `data/raw/anuario/` (geral e por área; colunas Insc./Conv./Matr., Quant. e %) para o formato longo do QASE (`ano, fonte, ingresso, etapa, nivel, area, pergunta, opcao, n, pct`), de forma que `src/harmonizacao.py` sirva para as duas fontes. Ignorar as colunas de **treineiros**. A revisa.
- Comparar Anuário 2022 com a soma do QASE 2022 (tabela "ponte" para o relatório).
- Separar `app/app.py` em um arquivo por visão (`app/visoes/*.py`), para B e C não editarem o mesmo arquivo.
- Filtros globais (indicador, nível/área, etapa, ano) e tooltips.
- Acessibilidade: paleta Okabe-Ito, rótulos diretos e teste com simulador de daltonismo (print para o relatório).
- Garantir que o app roda com um comando a partir do README limpo.

**Relatório:** *Apresentação e motivação*, as **3+ questões** (escritas em conjunto), *Limitações* (duas fontes, anuário sem carreira e modalidade, QASE só cobre quem entrou pela Fuvest), *Lições aprendidas* e *Próximos passos*. Montar o PDF final.
**Vídeo (~1 min 15 + edição):** abertura, conclusões e próximos passos. Editar o vídeo final (máx. 6 min).

### Cronograma da 1ª entrega
| Data | Marco |
|---|---|
| 21–23/10 | A: parser rodando nos PDFs por carreira de 2013–2022 e tabela carreira → área. D: `anuario_parser.py` e demo com as colunas novas. B e C: visões com os dados de demonstração. |
| 24/10 | `indicadores.csv` real v1 (QASE + anuário). Reunião rápida para fechar as 3 questões. |
| 25–28/10 | B e C: visões com dados reais e insights anotados. D: app separado por visão, filtros globais e tabela ponte 2022. |
| 31/10 | Rascunho do relatório completo (cada um a sua parte). |
| 01/11 | Gravação dos trechos do vídeo. D edita. |
| 02/11 | Revisão cruzada do relatório e do vídeo. Teste do app numa máquina "limpa". |
| 03/11 | Entrega. |

---

## 2ª entrega (até 03/12)

Exigência: **pelo menos 2 interações novas e pelo menos 2 visualizações novas**, coordenadas (linked views), respondendo a **novas questões**. Clique, hover e zoom só contam se afetarem mais de uma visão.

| Perfil | Visualização nova | Interação nova | Nova questão |
|---|---|---|---|
| **A. Dados** | — | — | fornece os dados novos (abaixo) |
| **B. Evolução** | **Heatmap** carreira × ano do "índice de seletividade" (% no matriculado − % no inscrito) e **barras divergentes** do perfil por modalidade (AC × EP × PPI, 2019–2022) | clicar numa célula do heatmap seleciona carreira + ano em todas as visões | Q5: em quais carreiras e anos o vestibular mais filtrou? Quanto o perfil de quem entra por EP e PPI difere de quem entra por AC? |
| **C. Funil e carreiras** | **Small multiples** comparando Fuvest, ENEM-USP e Provão Paulista (2025–2026, total e por área) | clicar numa via de ingresso filtra as outras visões | Q6: as novas vias de ingresso trazem um perfil diferente do da Fuvest? |
| **D. Integração e interação** | — | **Brushing + linking** (selecionar carreiras nas coordenadas paralelas destaca nas outras visões) e **dynamic query** (slider de anos e seletores de área, etapa e modalidade filtrando tudo) | coordena como as interações respondem às novas questões |

### A. Dados (2ª entrega)
- Coluna de **índice de seletividade** por carreira, ano e indicador.
- Indicadores por **modalidade** (2019–2022) já validados contra o total da carreira.
- Dados de ENEM-USP e Provão Paulista no `indicadores.csv` (com D).
- Opcional, se houver tempo: indicadores por **região de origem** (pergunta do QASE) e geometria das regiões do IBGE para um mapa coroplético.
- **Relatório e vídeo:** novos dados e como foram tratados.

### B, C e D (2ª entrega)
- Cada um implementa o que está na tabela e escreve no relatório a nova análise da sua questão, com prints mostrando a interação revelando o insight.
- D cria o estado compartilhado do app (`dcc.Store` com a seleção atual), que todas as visões leem. Assim o linking funciona sem cada visão conhecer as outras.
- D prepara o **roteiro da apresentação ao vivo de 10 min** (08/12, se o grupo for sorteado). A apresentação deve ser feita com o app rodando, não com o vídeo, e todos ensaiam juntos.

### Cronograma da 2ª entrega
| Data | Marco |
|---|---|
| 04–10/11 | A: seletividade, modalidades e vias de ingresso. D: estado compartilhado (`dcc.Store`) e dynamic query. |
| 11–20/11 | B e C: novas visões ligadas ao estado. D: brushing + linking. |
| 21–26/11 | Novas análises e insights com as interações. |
| 27–30/11 | Relatório e vídeo atualizados. |
| 01–02/12 | Revisão cruzada e ensaio da apresentação ao vivo. |
| 03/12 | Entrega. |

## Equilíbrio de carga

- **A** continua com mais trabalho na 1ª entrega (10 anos de PDF por carreira), mas a leitura dos anuários passou para **D**, que tinha menos código no começo.
- **D** tem as duas interações obrigatórias na 2ª entrega.
- **B** e **C** têm carga parecida nas duas.

Se A atrasar, D ajuda na validação dos anos com problema, já que os dois estão em dupla de revisão.
