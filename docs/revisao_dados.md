# Revisão independente dos dados (07/11)

Conferência do `indicadores.csv` e do `representacao.csv` (PR #9) com código escrito à parte, sem reaproveitar `src/`, contra os recortes do Anuário em PDF e contra as próprias somas. O QASE bruto (`qase_longo.csv` e os 3.875 PDFs) só existe na máquina do Marcos, então o QASE foi conferido pelas somas, pela ponte de 2022 e pelo recálculo das medidas.

## O que foi conferido e bateu

| conferência | resultado |
|---|---|
| Anuário 2023–2026: extração independente dos PDFs (escola pública, PPI, renda até 3 SM, cursinho, mulheres, técnico; USP e áreas; Fuvest, ENEM-USP e Provão) | 268 células comparadas, diferença máxima 0,00 p.p. |
| QASE: soma dos respondentes das carreiras = área, e soma das áreas = USP | exata nos 132 recortes (ano × etapa × área × modalidade) |
| QASE: média das carreiras ponderada pelos respondentes vs. valor da área | até 0,33 p.p. (esperado: cada pergunta tem o próprio nº de respostas) |
| Ponte 2022, inscritos: QASE (soma das carreiras) vs. Anuário (tabela pronta) | até 0,01 p.p. e 1 pessoa de diferença nas 4 linhas (USP e 3 áreas). Confirma o parser do QASE e o mapa carreira → área por uma fonte independente |
| `representacao.csv` recalculado do zero a partir do `indicadores.csv` | idêntico (diferença ≤ 0,00005, só arredondamento); `amostra_pequena` idêntica |
| Números citados em `docs/representacao.md` (razão mediana 0,81 → 1,08; carreiras abaixo de 0,8: 73% em 2013 → 2% em 2022; exemplo 2017 e 2021) | conferem |
| Cobertura das perguntas reprovadas no QASE | nenhuma das 892 perguntas reprovadas é das que viram indicador: 100% dos respondentes entram em todos os indicadores |
| Faixas, chaves e áreas | nenhum % fora de 0–100, nenhuma chave duplicada, toda carreira tem área |
| Anuário 2023, tabela por área | confirmado que repete os números de 2022 (ex.: Exatas, inscritos, escola pública = 33,41% nos dois anos). Está certo deixá-la de fora |

## Problemas encontrados

### 1. Renda da Fuvest 2026 estava vazia (corrigido neste PR)

O Anuário 2026 (Tabelas 3.04 e 3.05) não imprime a faixa "Acima de 50 SM": as outras faixas somam 97,5 a 98,5%, a pergunta era reprovada (A1) e `pct_renda_ate_3SM` e `pct_renda_mais_10SM` ficavam vazios em 2026, o último ano da série.

As % impressas são calculadas sobre o total de questionários da coluna (ex.: 5.542 / 98.380 = 5,63%, como impresso), então o que falta para 100% é exatamente a faixa ausente. `completar_faixa_de_renda` (em `src/anuario_parser.py`) repõe a linha com quantidade = total da coluna − soma das faixas, marcada com `reconstruida = True`. O valor reposto (1,9% a 2,5% na USP) é coerente com a mesma faixa em 2025 (1,8% a 2,1%).

Resultado, USP: até 3 SM = 30,2% dos inscritos e 24,8% dos matriculados; mais de 10 SM = 25,4% e 31,3%.

### 2. Amostras pequenas: o corte de 30 matriculados não basta (corrigido neste PR)

Com 30 matriculados e 30% de um grupo, o erro-padrão da diferença é de ~8 p.p. O `representacao.csv` ganhou `ic95_inf_pp`, `ic95_sup_pp` e `diferenca_clara` (o intervalo não contém o zero). Entre as carreiras com 30 ou mais matriculados (modalidade Todas, % escola pública), só 39% têm diferença clara; por modalidade, 26%. Sugestão para o heatmap (B): esmaecer as células com `diferenca_clara = False` e mostrar o intervalo no tooltip.

### 3. Em 2022 os matriculados diferem entre as fontes (não é erro; afeta a leitura da série)

Os inscritos batem, mas os matriculados não: o QASE tem 7.648 respondentes e o Anuário 8.041 (+5%). Na USP: escola pública 43,1% vs. 41,5%, cursinho 53,0% vs. 50,5%, renda até 3 SM 22,1% vs. 20,5%. As duas fontes provavelmente contam a matrícula em momentos diferentes (ver `ponte_2022.csv`).

Consequência: comparar QASE 2022 com Anuário 2023 mistura método e mudança real (~1,5 a 2,5 p.p. nos matriculados). Para falar de 2022 → 2023 em diante, usar o Anuário 2022 como base. Ex.: escola pública entre os matriculados foi de 41,5% (Anuário 2022) para 45,3% (2023), +3,8 p.p.; pelo QASE 2022 pareceria +2,2. O app já mostra os dois pontos em 2022; o relatório deve dizer isso com essas palavras.

### 4. Definição de "escola pública" (nota para o relatório)

`pct_escola_publica` soma "todo" e "maior parte" do ensino médio em escola pública. Foi uma escolha de definição feita na estrutura inicial (19/10), não um erro de extração, e ela já aparece na seção de pré-processamento da entrega 1. O que falta dizer é que ela é mais larga que o critério da cota EP, que exige o ensino médio inteiro em escola pública. "Maior parte" acrescenta de 0,5 a 1,5 p.p. (Anuário 2022–2026), mais entre os inscritos do que entre os matriculados. Na Fuvest 2026 (USP), a diferença matriculados − inscritos seria +10,2 p.p. só com "todo" e é +9,5 p.p. com a definição atual; a razão seria 1,30 em vez de 1,27. Não muda as conclusões.

### 5. Lacunas que as visões não devem preencher

- Escolaridade do pai e da mãe: não existe de 2022 em diante (a pergunta passou a ser sobre "primeiro/segundo responsável").
- PPI e sexo no Anuário: só desde 2024.
- Áreas em 2023: só o total da USP (a tabela por área repete 2022).
- ENEM-USP 2025: sem escola pública, renda nem técnico. Provão Paulista: sem escola pública (todos vêm dela) nem PPI.

As linhas não devem ligar pontos através desses buracos.

### 6. Conferido nos PDFs do QASE (notebook do Marcos, 07/11)

- **Aviso M2 de 2021 (pai com ensino superior): não é erro.** Carreira 235, inscritos: a pergunta e as 11 opções são iguais em AC, EP e PPI, e o "N respostas" é igual ao nº de questionários (57, 23 e 17). O aviso vem do próprio M2: ele pondera as modalidades pelos questionários, mas "Não sei" e "Não possuo pai" saem do denominador e são muito mais comuns em EP e PPI (denominadores 56, 18 e 11). A conta exata dá os 45,88% de "Todas". Os outros avisos de pai e mãe devem ter a mesma causa.
- **Queda da escola pública 2014 → 2015: em parte era erro de harmonização (corrigido neste PR).** Em 2015 a opção residual passou a se chamar "Em outra situação (Escola particular com bolsa, Fundações, SESI, SENAI)" e saltou de 438 para 4.192 inscritos. Como o texto contém "particular", `categoria_escola` passou a contá-la como particular, e até 2014 ela ficava fora do denominador. Agora "outra situação" fica fora em todos os anos. Com isso, inscritos de escola pública: 2015 = 35,0% (era 33,8%), 2016 = 35,8% (era 34,5%); 2013 e 2014 não mudam. O resto da queda (~4 p.p.) é real: os inscritos de escola pública caem de 57,4 mil para 42,9 mil. Mesmo assim, a série tem uma quebra de questionário em 2015, porque alguns bolsistas de escola particular podem ter passado para a opção nova; isso deve constar no relatório.

Junto com essa correção, `respondentes` passou a ser o total de **todas** as respostas da pergunta sobre a escola (inclusive "No exterior" e "Em outra situação"), e não só das classificadas. Antes, mudar a classificação de uma opção mudava também o nº de respondentes, e com ele os pesos do M2, `amostra_pequena` e o intervalo de confiança. Agora `respondentes` é o nº de questionários, como diz a documentação. As porcentagens não mudam por isso; o nº de respondentes sobe ~0,4% (ex.: Fuvest 2022, inscritos, Anuário: 101.371, o total impresso).

Para o M2 e o intervalo de confiança ficarem exatos, o `indicadores.csv` ganhou nove colunas no fim, `n_escola_publica` … `n_tecnico`: o denominador de cada `pct_*`. As colunas antigas não mudam de nome nem de posição. O M2 agora pondera as modalidades por esse denominador, e o aviso da carreira 235 some (ver teste `test_m2_pondera_pelo_denominador_do_indicador`).

O `indicadores.csv` deste PR ainda **não** tem essa correção: ela precisa do `qase_longo.csv`, que só existe no notebook do Marcos. Ver "Como regenerar".

## Como regenerar

Os CSVs deste PR foram gerados aqui só para a parte do Anuário (o QASE não mudou; as linhas do QASE no `indicadores.csv` são as mesmas). Na máquina do Marcos, para regenerar tudo do zero:

```
python -m src.anuario_parser data/raw/anuario
python -m src.validacao --pdfs data/raw/por_carreira
python -m src.harmonizacao
python -m src.representacao
python -m src.ponte
```
