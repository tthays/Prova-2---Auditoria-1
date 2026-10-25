"""Parametros e dados reais usados no trabalho (matricula 180109791 - EZTEC).
Valores reais extraidos da DFP 2025 (CVM, protocolo 155329, versao 1). R$ mil, salvo indicacao.
Cada valor traz a pagina do PDF da DFP em que aparece.
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATRICULA = "180109791"
SEED = 180109791           # semente fixa: reproducao deterministica
DATA_BASE = "2025-12-31"
DATA_PREPARO = "25/10/2026"

# ---- Nota 7 (consolidado, pag. 51) - R$ mil ----
NOTA7 = {
    "IMOVEIS_CONCLUIDOS": 485897,
    "IMOVEIS_EM_CONSTRUCAO": 1421820,
    "TERRENOS_NOVAS_OBRAS": 1001151,
    "ENCARGOS_FINANCEIROS": 197453,
    "ADIANTAMENTO_FORNECEDORES": 19513,
}
SALDO_ESTOQUES = 3125834      # soma da nota 7 (pag. 51); = 1.282.510 (circ.) + 1.843.324 (nao circ.), pag. 20
SALDO_CIRC = 1282510
SALDO_NC = 1843324

# ---- Demonstracoes consolidadas (R$ mil): (2025, 2024, 2023, pagina) ----
DF = {
    "ativo_total": (7196637, 6466534, 5879316, "p.20"),
    "ativo_circulante": (3303420, 2616102, 2510852, "p.20"),
    "caixa_equiv": (66575, 71381, 84186, "p.20"),
    "aplicacoes_fin": (1491967, 699051, 678090, "p.20"),
    "contas_receber_circ": (439254, 434949, 296195, "p.20"),
    "estoques_circ": (1282510, 1378328, 1422577, "p.20"),
    "contas_receber_nc": (1288193, 1318621, 903841, "p.20"),
    "estoques_nc": (1843324, 1750556, 1668196, "p.20"),
    "imobilizado": (45743, 36152, 34188, "p.20"),
    "investimentos": (511945, 514136, 501241, "p.20"),
    "passivo_circulante": (396609, 382378, 402620, "p.21"),
    "fornecedores": (50909, 55179, 52607, "p.21"),
    "emprest_circ": (148795, 85958, 136471, "p.21"),
    "passivo_nc": (1680131, 1201030, 771632, "p.21-22"),
    "emprest_nc": (1557190, 1050424, 719700, "p.21"),
    "patrimonio_liquido": (5119897, 4883126, 4705064, "p.22"),
    "receita_liquida": (1498822, 1560541, 1083172, "p.23"),
    "custo": (873665, 1027729, 739473, "p.23"),
    "lucro_bruto": (625157, 532812, 343699, "p.23"),
    "lair": (601586, 466419, 273948, "p.23"),
    "lucro_liquido": (547595, 428718, 246096, "p.23"),
    "desp_vendas": (127383, 120117, 113873, "p.23"),
    "desp_ga": (152525, 144542, 138562, "p.23"),
    "equivalencia": (65619, 79410, 102637, "p.23"),
    "rec_financeiras": (245765, 176919, 135503, "p.23"),
    "desp_financeiras": (86036, 44891, 50635, "p.23"),
    "fco": (503785, -28991, -228599, "p.26"),
}
N_LINHAS = {"IMOVEIS_CONCLUIDOS": 150000, "IMOVEIS_EM_CONSTRUCAO": 250000, "TERRENOS_NOVAS_OBRAS": 70000,
            "ENCARGOS_FINANCEIROS": 40000, "ADIANTAMENTO_FORNECEDORES": 10000}
