# Medidas de representação (`data/processed/representacao.csv`)

Gerado por `python -m src.representacao` a partir do `indicadores.csv`. Nenhum número é digitado à mão.

## Definições

Para cada grupo (um indicador do contrato, ex.: % escola pública) e cada recorte:

- **Diferença de representação** = % do grupo entre os matriculados − % do grupo entre os inscritos, em pontos percentuais. 0 = proporcional.
- **Razão de representação** = % do grupo entre os matriculados ÷ % do grupo entre os inscritos. 1 = proporcional; abaixo de 1 o grupo encolheu no funil, acima de 1 cresceu.

A razão tem a mesma forma do *disparate impact* (Feldman et al., 2015). O limiar 0,8 (regra dos 4/5 das diretrizes da EEOC, 1978) é uma convenção de seleção de emprego nos EUA e entra aqui só como régua de leitura.

As medidas mostram **disparidade no resultado, não a causa**. Não separam preparo anterior, escolha de carreira, desistência da matrícula e a própria reserva de vagas. O valor acima de 1 depois de 2019 é o efeito esperado das cotas. De 2013 a 2022 só há inscritos e matriculados por carreira, então a medida também não separa a aprovação da decisão de se matricular.

Conferência com o exemplo do plano (Fuvest, USP inteira, % escola pública, modalidade Todas):

| ano | % inscritos | % matriculados | diferença (p.p.) | razão |
|---|---|---|---|---|
| 2017 | 34,95 | 29,97 | −4,98 | 0,86 |
| 2021 | 38,17 | 43,07 | +4,90 | 1,13 |

## Colunas

Uma linha por recorte × indicador. Só entram recortes com as duas etapas (inscritos e matriculados) na mesma fonte e com o indicador preenchido nas duas.

| coluna | conteúdo |
|---|---|
| `ano`, `fonte`, `ingresso`, `nivel`, `area`, `cod_carreira`, `carreira`, `modalidade` | Iguais ao `indicadores.csv`. `area` e `cod_carreira` ficam vazios nos níveis acima. |
| `indicador` | Nome da coluna do `indicadores.csv` que define o grupo (`pct_escola_publica`, `pct_PPI`, ...). Os rótulos estão em `app/dados.py` (`INDICADORES`). |
| `respondentes_inscritos`, `respondentes_matriculados` | Questionários respondidos em cada etapa. |
| `n_inscritos`, `n_matriculados` | Denominador do indicador em cada etapa (respostas classificadas da pergunta). É o que entra no intervalo de confiança. |
| `pct_inscritos`, `pct_matriculados` | % do grupo em cada etapa. |
| `diferenca_pp`, `razao` | As duas medidas. `razao` fica vazia quando o grupo tem 0% entre os inscritos. |
| `ic95_inf_pp`, `ic95_sup_pp` | Intervalo de 95% da diferença (aproximação normal). Os dados são o universo de quem respondeu; o intervalo mede quanto a diferença oscilaria com outra turma do mesmo tamanho. É conservador (trata as etapas como independentes, mas os matriculados estão dentro dos inscritos) e aproximado (usa o nº de questionários, não o de respostas de cada pergunta). |
| `diferenca_clara` | `True` quando o intervalo não contém o zero. Mais informativo que `amostra_pequena`: entre as carreiras com 30 ou mais matriculados (modalidade Todas, % escola pública), só 39% têm diferença clara. O heatmap deve esmaecer as células com `False`. |
| `amostra_pequena` | `True` quando há menos de 30 respondentes matriculados: a razão oscila muito (um aluno muda vários p.p.). O heatmap deve marcar essas células ou deixá-las mais claras. |
| `criterio_da_modalidade` | `True` quando o indicador é o próprio critério da modalidade (escola pública em EP e PPI; PPI em PPI). Dentro da modalidade ele vale ~100% nas duas etapas, então a medida não informa nada. A V5 deve filtrar essas linhas. |

Cobertura: QASE 2013–2022 (USP, áreas e 117 carreiras; por modalidade AC/EP/PPI de 2019 a 2022) e Anuário 2022–2026 (USP e áreas; Fuvest, ENEM-USP 2025–26 e Provão Paulista 2026). A renda da Fuvest 2026 usa a faixa "Acima de 50 SM" reconstruída (o Anuário 2026 não a imprime; ver `docs/revisao_dados.md`). 54% das linhas de carreira têm amostra pequena; nas modalidades AC, EP e PPI, 81%.

Leitura rápida (carreiras, modalidade Todas, % escola pública, sem amostra pequena): a razão mediana foi 0,82 em 2013–2018 e 1,08 em 2019–2022. A fração de carreiras com razão abaixo de 0,8 caiu de 72% em 2013 para 2% em 2022.

## Validação das modalidades AC/EP/PPI (`data/processed/validacao_modalidades.csv`)

Para cada recorte do QASE de 2019 a 2022 (carreira, área e USP, inscritos e matriculados):

| check | gravidade | o que confere | ocorrências |
|---|---|---|---|
| M1 | reprova | soma dos respondentes de AC + EP + PPI = respondentes de "Todas" | 0 |
| M2 | aviso | média dos indicadores das modalidades, ponderada pelo denominador de cada indicador (`n_*`), a até 1 p.p. de "Todas" | 0 |
| M3 | aviso | as três modalidades existem no recorte | 77 |
| M4 | aviso | EP e PPI com ≥ 90% de escola pública; PPI com ≥ 90% de PPI | 17 |

- **M1** passa em todos os 884 recortes. Atenção: quando o PDF não tem a seção "Todas as Modalidades", o `src/harmonizacao.py` monta o "Todas" somando as modalidades, então nesses casos o teste confirma só que a soma não perdeu linhas. Ele é uma conferência independente apenas onde o PDF traz a seção "Todas" impressa.
- **M2** pondera cada modalidade pelo denominador do próprio indicador (`n_*` do `indicadores.csv`), então é exato. Na versão anterior o peso era o nº de questionários, e isso gerava avisos falsos: na carreira 235 (2021, inscritos), "Não sei" e "Não possuo pai" tiram 1 de 57 respostas na AC, mas 5 de 23 na EP e 6 de 17 na PPI, e a média ponderada errava 3,2 p.p. (conferido nos PDFs em 07/11).
- **M3**: 73 recortes sem PPI e 4 sem EP, quase todos carreiras pequenas. Sem o PDF daquela modalidade não dá para saber se não houve candidato ou se o arquivo não existe; o "Todas" continua certo porque soma o que existe.
- **M4**: todos os 17 casos têm entre 1 e 19 respondentes. É coerente com autodeclaração no questionário diferente da usada na inscrição, ou com um único aluno fora do padrão; não indica erro de extração.

Nenhuma linha foi removida por essas checagens: elas registram onde ler com cuidado.
