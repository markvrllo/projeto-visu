# Relatório de validação da extração

Gerado por `python -m src.validacao`. Tudo aqui é calculado a partir dos CSVs extraídos; nenhum número foi digitado à mão.

## QASE (2013–2022)

- 3875 PDFs, 136982 perguntas, 1024931 linhas extraídas.
- Perguntas reprovadas: 892 (0.65%).

| check | gravidade | ocorrências |
|---|---|---|
| Q1 soma != N respostas | reprova | 892 |
| Q4 N respostas > questionários | aviso | 609 |
| Q8 modalidade do cabeçalho != respostas | aviso | 100 |

Por ano e etapa:

| ano | etapa | PDFs com reprovação |
|---|---|---|
| 2014 | inscritos | 111 |
| 2014 | matriculados | 101 |
| 2015 | inscritos | 111 |
| 2015 | matriculados | 90 |
| 2016 | inscritos | 56 |
| 2016 | matriculados | 9 |
| 2017 | inscritos | 41 |
| 2017 | matriculados | 5 |
| 2018 | inscritos | 108 |
| 2018 | matriculados | 88 |
| 2019 | inscritos | 4 |

## Anuário (2022–2026)

- 16 recortes, 10890 linhas extraídas.

| check | gravidade | ocorrências |
|---|---|---|
| A1 % não somam 100 | reprova | 42 |
| A2 % impressa != quantidade | aviso | 484 |
| A2 % impressa != quantidade | reprova | 58 |
| A3 soma das áreas != USP | aviso | 1 |
| A3 soma das áreas != USP | reprova | 1 |

Reprovações:

- anuario_2026__fuvest_geral.pdf p. 4 — Qual é a renda mensal bruta da sua família, incluindo seu próprio rendimento? O valor do salário mínimo (SM) é R$ 1.518,00: A1 % não somam 100 (soma = 98.07%)
- anuario_2026__fuvest_geral.pdf p. 5 — Qual é o nível de instrução do primeiro responsável por você (mãe, pai ou outra pessoa)?: A1 % não somam 100 (soma = 98.10%)
- anuario_2026__fuvest_geral.pdf p. 6 — Qual é o nível de instrução do segundo responsável por você (mãe, pai ou outra pessoa)?: A1 % não somam 100 (soma = 94.69%)
- anuario_2022__fuvest_por_area.pdf p. 4 — Quantas pessoas da família, incluindo você, vivem da renda indicada na pergunta anterior? [Biológicas]: A1 % não somam 100 (soma = 87.80%)
- anuario_2022__fuvest_por_area.pdf p. 4 — Quantas pessoas da família, incluindo você, vivem da renda indicada na pergunta anterior? [Exatas]: A1 % não somam 100 (soma = 87.80%)
- anuario_2022__fuvest_por_area.pdf p. 4 — Quantas pessoas da família, incluindo você, vivem da renda indicada na pergunta anterior? [Humanas]: A1 % não somam 100 (soma = 89.10%)
- anuario_2023__fuvest_por_area.pdf p. 4 — Quantas pessoas da família, incluindo você, vivem da renda indicada na pergunta anterior? [Biológicas]: A1 % não somam 100 (soma = 87.80%)
- anuario_2023__fuvest_por_area.pdf p. 4 — Quantas pessoas da família, incluindo você, vivem da renda indicada na pergunta anterior? [Exatas]: A1 % não somam 100 (soma = 87.80%)
- anuario_2023__fuvest_por_area.pdf p. 4 — Quantas pessoas da família, incluindo você, vivem da renda indicada na pergunta anterior? [Humanas]: A1 % não somam 100 (soma = 89.10%)
- anuario_2026__fuvest_por_area.pdf p. 4 — Qual é a renda mensal bruta da sua família, incluindo seu próprio rendimento? O valor do salário mínimo (SM) é R$ 1.518,00 [Biológicas]: A1 % não somam 100 (soma = 98.54%)
- anuario_2026__fuvest_por_area.pdf p. 4 — Qual é a renda mensal bruta da sua família, incluindo seu próprio rendimento? O valor do salário mínimo (SM) é R$ 1.518,00 [Exatas]: A1 % não somam 100 (soma = 97.60%)
- anuario_2026__fuvest_por_area.pdf p. 4 — Qual é a renda mensal bruta da sua família, incluindo seu próprio rendimento? O valor do salário mínimo (SM) é R$ 1.518,00 [Humanas]: A1 % não somam 100 (soma = 97.76%)
- anuario_2026__fuvest_por_area.pdf p. 5 — Qual é o nível de instrução do primeiro responsável por você (mãe, pai ou outra pessoa)? [Biológicas]: A1 % não somam 100 (soma = 98.49%)
- anuario_2026__fuvest_por_area.pdf p. 5 — Qual é o nível de instrução do primeiro responsável por você (mãe, pai ou outra pessoa)? [Exatas]: A1 % não somam 100 (soma = 98.52%)
- anuario_2026__fuvest_por_area.pdf p. 5 — Qual é o nível de instrução do primeiro responsável por você (mãe, pai ou outra pessoa)? [Humanas]: A1 % não somam 100 (soma = 97.32%)
- anuario_2026__fuvest_por_area.pdf p. 6 — Qual é o nível de instrução do segundo responsável por você (mãe, pai ou outra pessoa)? [Biológicas]: A1 % não somam 100 (soma = 95.33%)
- anuario_2026__fuvest_por_area.pdf p. 6 — Qual é o nível de instrução do segundo responsável por você (mãe, pai ou outra pessoa)? [Exatas]: A1 % não somam 100 (soma = 95.34%)
- anuario_2026__fuvest_por_area.pdf p. 6 — Qual é o nível de instrução do segundo responsável por você (mãe, pai ou outra pessoa)? [Humanas]: A1 % não somam 100 (soma = 93.48%)
- anuario_2026__fuvest_geral.pdf p. 5 — Qual é o nível de instrução do primeiro responsável por você (mãe, pai ou outra pessoa)?: A2 % impressa != quantidade ('Pós-graduação completa': 35.44% impresso, 36.56% calculado (2878/7872))
- anuario_2026__fuvest_geral.pdf p. 6 — Qual é o nível de instrução do segundo responsável por você (mãe, pai ou outra pessoa)?: A2 % impressa != quantidade ('Ensino Médio completo': 22.63% impresso, 23.90% calculado (22294/93291))
- anuario_2022__fuvest_por_area.pdf p. 4 — Quantas pessoas da família, incluindo você, vivem da renda indicada na pergunta anterior? [Biológicas]: A2 % impressa != quantidade ('Duas': 11.6% impresso, 13.25% calculado (5503/41530))
- anuario_2022__fuvest_por_area.pdf p. 4 — Quantas pessoas da família, incluindo você, vivem da renda indicada na pergunta anterior? [Exatas]: A2 % impressa != quantidade ('Duas': 10.9% impresso, 12.42% calculado (2128/17127))
- anuario_2022__fuvest_por_area.pdf p. 4 — Quantas pessoas da família, incluindo você, vivem da renda indicada na pergunta anterior? [Humanas]: A2 % impressa != quantidade ('Duas': 13.3% impresso, 14.94% calculado (4608/30840))
- anuario_2023__fuvest_por_area.pdf p. 4 — Quantas pessoas da família, incluindo você, vivem da renda indicada na pergunta anterior? [Biológicas]: A2 % impressa != quantidade ('Duas': 11.6% impresso, 13.25% calculado (5503/41530))
- anuario_2023__fuvest_por_area.pdf p. 4 — Quantas pessoas da família, incluindo você, vivem da renda indicada na pergunta anterior? [Exatas]: A2 % impressa != quantidade ('Duas': 10.9% impresso, 12.42% calculado (2128/17127))
- anuario_2023__fuvest_por_area.pdf p. 4 — Quantas pessoas da família, incluindo você, vivem da renda indicada na pergunta anterior? [Humanas]: A2 % impressa != quantidade ('Duas': 13.3% impresso, 14.94% calculado (4608/30840))
- anuario_2026__fuvest_por_area.pdf p. 5 — Qual é o nível de instrução do primeiro responsável por você (mãe, pai ou outra pessoa)? [Humanas]: A2 % impressa != quantidade ('Ensino Superior completo': 28.28% impresso, 29.37% calculado (3442/11718))
- anuario_2026__fuvest_por_area.pdf p. 6 — Qual é o nível de instrução do segundo responsável por você (mãe, pai ou outra pessoa)? [Biológicas]: A2 % impressa != quantidade ('Ensino Médio completo': 23.93% impresso, 25.10% calculado (10053/40049))
- anuario_2026__fuvest_por_area.pdf p. 6 — Qual é o nível de instrução do segundo responsável por você (mãe, pai ou outra pessoa)? [Exatas]: A2 % impressa != quantidade ('Ensino Médio completo': 21.56% impresso, 22.61% calculado (4818/21307))
- anuario_2026__fuvest_por_area.pdf p. 6 — Qual é o nível de instrução do segundo responsável por você (mãe, pai ou outra pessoa)? [Humanas]: A2 % impressa != quantidade ('Ensino Médio completo': 21.73% impresso, 23.24% calculado (7423/31935))
- anuario_2023__fuvest_por_area.pdf: A3 soma das áreas != USP (330 de 334 opções não batem com a tabela geral; as quantidades são idênticas às de anuario_2022__fuvest_por_area.pdf)

Avisos de porcentagem (as contagens são usadas; a % impressa pelo Anuário difere um pouco):

| arquivo | opções |
|---|---|
| anuario_2022__fuvest_por_area.pdf | 6 |
| anuario_2023__fuvest_por_area.pdf | 6 |
| anuario_2026__fuvest_geral.pdf | 122 |
| anuario_2026__fuvest_por_area.pdf | 350 |

Os detalhes, com arquivo e página, estão em `data/processed/validacao_qase.csv` e `data/processed/validacao_anuario.csv`.
