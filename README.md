# Dossiê de auditoria - EZTEC (EZ TEC Empreendimentos e Participações S.A., EZTC3)
UnB - Auditoria 1 (CCA0024) - Turma 02 - 2026.2 - P2 | **Thays Santos - matrícula 180109791** | Preparação: 25/10/2026

**Aviso:** trabalho acadêmico, sem opinião profissional independente. A base de dados é **SINTÉTICA** (não são registros reais da EZTEC). Declaração de uso de IA: trabalho produzido com apoio exclusivo de IA, conforme informado pelo aluno; verificar a política da disciplina.

## Conteúdo
| Pasta/arquivo | Descrição |
|---|---|
| `dossie/Dossie_Auditoria_EZTEC_P2_180109791.pdf` | Dossiê: PT EC e PT 200-600, programas de auditoria, matriz de cobertura, fontes, conclusão |
| `data/base_imoveis_a_comercializar_sintetica.csv.gz` | Base sintética: 520.180 linhas (CSV compactado; abrir com `zcat` ou pandas) |
| `docs/dicionario_variaveis.csv` | Dicionário de variáveis |
| `docs/metodo_base.md` | Justificativa da conta, premissas e método |
| `data/registro_erros_inseridos.csv` | Registro dos 905 erros inseridos (compara inseridos x detectados) |
| `data/cadastro_fornecedores_sintetico.csv` | Cadastro sintético usado em T09 |
| `resultados/` | Saídas dos testes, amostra MUS, conciliações, Benford |
| `planilhas/Planilhas_P2_180109791.xlsx` | Cálculos com fórmulas: PT320, PT520, PT530, PT500, PT450, PT540, PT570, PT505 |
| `docs/matriz_cobertura.md`, `docs/fontes.md` | Cobertura por norma; fontes (também no Apêndice B do PDF) |
| `dados_reais/nota9_controladas_2025.csv` | Dados reais extraídos da nota 9 da DFP (PT 600) |
| `src/` | Código: `01_gerar_base.py`, `02_executar_testes.py`, `03_gerar_planilhas.py`, `04_gerar_dossie.py` |

## Reprodução
```
pip install -r requirements.txt
sh run_all.sh        # semente fixa 180109791: resultados idênticos
```
Passo 03 requer LibreOffice só para recalcular as fórmulas (opcional); passo 04 usa a fonte DejaVu Sans. Se o arquivo `.csv.gz` ultrapassar o limite do GitHub (100 MB), use o código para regerá-lo (arquivo atual: ~19 MB).

## Fonte principal
DFP 2025 da EZTEC (CVM, protocolo 155329): https://www.rad.cvm.gov.br/ENETWEB/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento=155329&CodigoTipoInstituicao=1 (acesso em 23/10/2026 às 00:16, informado pelo aluno). O PDF foi obtido no site da B3 (https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/empresas.htm) e não está no repositório; use-o para conferir as páginas citadas.

## Pendências do aluno
Conferir independência (PT 200), versões das NBC TA (Apêndice B), eventos subsequentes no IPE/CVM (PT 560),  criação do repositório e acesso do professor.
