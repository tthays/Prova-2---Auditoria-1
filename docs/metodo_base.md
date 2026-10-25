# Método de geração da base SINTÉTICA (matrícula 180109791 - EZTEC)

**Aviso:** todos os registros são fictícios. Não são lançamentos reais da EZTEC.

## Escolha da conta e materialidade
Maior conta do ativo consolidado em 31/12/2025: **Imóveis a comercializar**, R$ 3.125.834 mil = 43,4% do ativo total de R$ 7.196.637 mil (balanço p.20; nota 7 p.51). Contas seguintes: contas a receber (24,0%) e aplicações financeiras (20,7%).

## Premissas
1. Cada linha = lançamento analítico de custo capitalizado (medição, nota fiscal, parcela de terreno, encargo, adiantamento) alocado a uma unidade/lote de estoque.
2. Totais por categoria = nota 7 em reais (R$ mil x 1.000): concluídos 485.897.000; em construção 1.421.820.000; terrenos 1.001.151.000; encargos 197.453.000; adiantamentos 19.513.000.
3. Linhas por categoria: 150.000 / 250.000 / 70.000 / 40.000 / 10.000 = 520.000 antes da inserção de erros; valores lognormais (sigma 1,15) alocados em centavos inteiros com soma exata (método do maior resto).
4. Circulante = R$ 1.282.510.000,00 (balanço): linhas ordenadas por chave aleatória ponderada por categoria; ajuste final de centavos entre duas linhas da mesma categoria. A data de realização prevista é coerente com a classificação.
5. 110 empreendimentos sintéticos (25 concluídos, 20 em construção, 65 bancos de terrenos); 4.000 fornecedores sintéticos; semente 180109791.
6. Ruído natural: ~4% das parcelas de terreno com valor redondo; 6% de lançamentos manuais; 8% dos manuais fora do horário.

## Erros inseridos (905 registros em registro_erros_inseridos.csv)
E01 duplicidade (180 linhas novas); E02 corte (150); E03 manual/fim de semana/valor redondo (60); E04 classificação (120); E05 custo não capitalizável (70); E06 encargo com taxa acima do teto (60); E07 unidade vendida em estoque (110); E08 fornecedor fora do cadastro (45); E09 estorno sem referência (50); E10 valor divergente do documento (60; detectável só por amostra documental).

## Conciliação
Antes da inserção: base = nota 7 e circulante = balanço, sem diferença. Após: diferença de R$ 25.349.559,03, igual à soma dos efeitos do registro (diferença não explicada R$ 0,00). Distorções que não alteram o total (E02, E04, E05, E07, E08) constam da coluna 'distorção potencial'.

## Evidência simulada
Para os itens da amostra MUS, o valor do 'documento' é obtido do registro de erros (oráculo). Não é documento real.
