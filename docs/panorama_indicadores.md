# Panorama do `indicadores.csv` (v1, 21/10)

Arquivo: `data/processed/indicadores.csv`, 4.870 linhas e 20 colunas. Uma linha é um recorte (ano × fonte × via de ingresso × etapa × nível × área/carreira × modalidade) e traz o perfil desse grupo em porcentagens. Todas as porcentagens vêm de **contagens somadas**, nunca de médias de porcentagens.

## Colunas

| Coluna | O que é | Valores |
|---|---|---|
| `ano` | ano do vestibular | 2013–2026 |
| `fonte` | de onde veio o número | `qase` (PDFs da Fuvest, 2013–2022) ou `anuario` (Anuário Estatístico da USP, 2022–2026) |
| `ingresso` | via de ingresso | `fuvest`, `enem-usp` (2025–2026), `provao-paulista` (2026) |
| `etapa` | momento do processo | `inscritos`, `convocados` (só Anuário/Fuvest), `matriculados` |
| `nivel` | agregação | `usp`, `area`, `carreira` (carreira só no QASE) |
| `area` | área de conhecimento | `Biológicas`, `Exatas`, `Humanas`; vazio no nível `usp` |
| `cod_carreira`, `carreira` | código e nome da carreira Fuvest | 117 carreiras; só no nível `carreira` |
| `unidade` | unidade USP | vazia por enquanto (os PDFs por carreira não trazem a unidade) |
| `modalidade` | modalidade de acesso | `Todas`, `AC`, `EP`, `PPI` (AC/EP/PPI só QASE 2019–2022) |
| `respondentes` | nº de pessoas que responderam (base das %) | total da pergunta de escola do ensino médio; sem ela, a de cor/raça ou a de sexo |
| `pct_escola_publica` | % que cursou o ensino médio todo ou a maior parte em escola pública | |
| `pct_PPI` | % pretos, pardos e indígenas | |
| `pct_renda_ate_3SM` | % com renda familiar até 3 salários mínimos | |
| `pct_renda_mais_10SM` | % com renda familiar acima de 10 SM | |
| `pct_pai_superior`, `pct_mae_superior` | % com pai / mãe com ensino superior completo | |
| `pct_cursinho` | % que fez cursinho | |
| `pct_mulheres` | % do sexo feminino | |
| `pct_tecnico` | % que fez ensino médio técnico | |

Respostas como "Não sei" e "No exterior" ficam fora do denominador. Indicador que a fonte não tem fica **vazio, nunca zero**.

## Cobertura

| Fonte | Via | Níveis | Anos | Etapas | Modalidades |
|---|---|---|---|---|---|
| QASE | Fuvest | USP, área, carreira | 2013–2022 | inscritos, matriculados | Todas; AC/EP/PPI de 2019 a 2022 |
| Anuário | Fuvest | USP, área | 2022–2026 (área sem 2023) | inscritos, convocados, matriculados | Todas |
| Anuário | ENEM-USP | USP, área | 2025–2026 | inscritos, matriculados | Todas |
| Anuário | Provão Paulista | USP, área | 2026 | inscritos, matriculados | Todas |

2022 aparece nas duas fontes (QASE e Anuário). É o ano da tabela ponte.

## Indicadores disponíveis por fonte e ano

| | esc. pública | PPI | renda | pai/mãe | cursinho | mulheres | técnico |
|---|---|---|---|---|---|---|---|
| QASE 2013–2021 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| QASE 2022 | ✓ | ✓ | ✓ | — (1) | ✓ | ✓ | ✓ |
| Anuário Fuvest 2022–2023 | ✓ | — | ✓ | — (1) | ✓ | — | ✓ |
| Anuário Fuvest 2024–2025 | ✓ | ✓ | ✓ | — (1) | ✓ | ✓ | ✓ |
| Anuário Fuvest 2026 | ✓ | ✓ | — (2) | — (1) | ✓ | ✓ | ✓ |
| ENEM-USP 2025 | — | ✓ | — | — | — | ✓ | — |
| ENEM-USP 2026 | ✓ | ✓ | ✓ | — | — | ✓ | ✓ |
| Provão Paulista 2026 | — (3) | — | — | ✓ | — | ✓ | — |

(1) A partir de 2022 a pergunta é sobre o "primeiro/segundo responsável (mãe, pai ou outra pessoa)", que não dá para separar em pai e mãe.
(2) A tabela de renda do Anuário 2026 omite a faixa "acima de 50 SM" (as % somam 98%). Foi reprovada na validação.
(3) O Provão Paulista é só para alunos de escola pública, então a pergunta não existe.

## Exemplos

Computação (carreira 710), 2022, QASE:

| etapa | modalidade | respondentes | esc. pública | PPI | renda ≤3 SM | mulheres |
|---|---|---|---|---|---|---|
| inscritos | Todas | 3.932 | 40,4 | 20,9 | 25,2 | 17,2 |
| inscritos | AC | 2.507 | 6,7 | 13,5 | 14,5 | 15,7 |
| matriculados | Todas | 221 | 41,6 | 21,2 | 15,8 | 13,5 |
| matriculados | PPI | 30 | 100,0 | 100,0 | 33,3 | 16,7 |

USP, Fuvest, matriculados, escola pública: 29,5% (2013), 31,4% (2018), 43,1% (2022, QASE), 45,2% (2024, Anuário).

## Lacunas e cuidados

- **Emenda das séries:** nos inscritos de 2022, QASE e Anuário coincidem (100.998 × 100.999 respondentes, indicadores iguais em todas as áreas). Nos matriculados, o Anuário tem cerca de 5% mais pessoas e as diferenças chegam a ~3 pp. Ao emendar a série dos matriculados em 2022, mostre os dois pontos.
- **Anuário 2023 por área:** reprovado. A tabela repete os números de 2022. Só existe o total da USP de 2023.
- **QASE 2022, matriculados:** a seção PPI vem rotulada como "Todas as Modalidades" no PDF. A modalidade foi tirada das respostas da própria seção (100% PPI).
- **Provão Paulista 2026:** as perguntas de sexo e idade têm cerca de 187 mil respostas, contra cerca de 131 mil nas demais. É uma inconsistência do próprio Anuário, registrada como aviso. `respondentes` usa o total de sexo.
- **Carreiras pequenas:** metade das linhas de carreira tem menos de 70 respondentes, e as modalidades EP e PPI têm bases bem menores. Convém filtrar por `respondentes` ao comparar carreiras.
- **Treineiros** (carreiras 399, 699 e 999) estão fora de tudo.

Rastreio: cada número volta ao PDF de origem por `data/processed/qase_longo.csv` (gerado localmente, ~300 MB, fora do git) e `anuario_longo.csv`, que guardam `arquivo` e `pagina`. O que a validação reprovou está em `docs/relatorio_validacao.md`.
