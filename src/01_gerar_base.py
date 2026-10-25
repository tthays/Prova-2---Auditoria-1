"""Gera a base SINTETICA de lancamentos analiticos da conta 'Imoveis a comercializar' (consolidado).
TODOS os dados deste arquivo sao ficticios. Somente os totais por categoria (nota 7, p.51 da DFP 2025)
e a divisao circulante/nao circulante (p.20) sao dados reais usados como alvo de calibracao.
Uso: python src/01_gerar_base.py   (semente fixa -> resultado identico a cada execucao)
"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from config import *

rng = np.random.default_rng(SEED)
OUT = os.path.join(ROOT, "data")
D0 = np.datetime64("2018-01-01"); DBASE = np.datetime64(DATA_BASE)

def alocar_centavos(raw, alvo_cent):
    """distribui alvo_cent (int) proporcionalmente a raw, em centavos inteiros, soma exata."""
    esc = raw / raw.sum() * alvo_cent
    base = np.floor(esc).astype(np.int64)
    resto = int(alvo_cent - base.sum())
    if resto > 0:
        idx = np.argsort(-(esc - base))[:resto]; base[idx] += 1
    return base

# ---------------- empreendimentos sinteticos ----------------
emp = pd.DataFrame({"id_empreendimento": [f"EMP-{i:03d}" for i in range(1, 111)]})
emp["fase"] = ["CONCLUIDO"] * 25 + ["EM_CONSTRUCAO"] * 20 + ["BANCO_TERRENOS"] * 65
emp["n_unidades"] = np.where(emp.fase == "BANCO_TERRENOS", 1, rng.integers(60, 420, len(emp)))
ini = np.empty(len(emp), dtype="datetime64[D]")
for i, f in enumerate(emp.fase):
    if f == "CONCLUIDO": ini[i] = np.datetime64("2018-06-01") + int(rng.integers(0, 1100))
    elif f == "EM_CONSTRUCAO": ini[i] = np.datetime64("2022-01-01") + int(rng.integers(0, 1150))
    else: ini[i] = np.datetime64("2019-01-01") + int(rng.integers(0, 2500))
emp["data_inicio"] = ini

CAT_EMP = {  # categorias -> empreendimentos elegiveis (indices)
    "IMOVEIS_CONCLUIDOS": np.arange(0, 25), "IMOVEIS_EM_CONSTRUCAO": np.arange(25, 45),
    "TERRENOS_NOVAS_OBRAS": np.arange(45, 110), "ENCARGOS_FINANCEIROS": np.arange(25, 110),
    "ADIANTAMENTO_FORNECEDORES": np.arange(25, 110)}
TIPOS = {
    "IMOVEIS_CONCLUIDOS": (["CUSTO_UNIDADE_RATEADO", "ACABAMENTO_FINAL", "HABITE_SE_TAXAS", "MANUTENCAO_CAPITALIZAVEL"], [.70, .12, .05, .13]),
    "IMOVEIS_EM_CONSTRUCAO": (["MEDICAO_EMPREITEIRO", "MATERIAL_CONSTRUCAO", "MAO_DE_OBRA_PROPRIA", "PROJETOS_INCORPORACAO", "TAXAS_APROVACAO", "SEGUROS_OBRA", "RATEIO_CUSTO_COMUM"], [.38, .30, .12, .06, .04, .03, .07]),
    "TERRENOS_NOVAS_OBRAS": (["PARCELA_AQUISICAO_TERRENO", "ITBI_REGISTRO", "CORRETAGEM_TERRENO", "DEMOLICAO_TERRAPLENAGEM", "PROJETOS_PRELIMINARES", "IPTU_TERRENO"], [.50, .08, .05, .12, .15, .10]),
    "ENCARGOS_FINANCEIROS": (["ENCARGO_FINANCEIRO_CAPITALIZADO"], [1.0]),
    "ADIANTAMENTO_FORNECEDORES": (["ADIANTAMENTO_FORNECEDOR_OBRA", "ADIANTAMENTO_FORNECEDOR_MATERIAL"], [.70, .30])}
DOC = {"MEDICAO_EMPREITEIRO": "MEDICAO", "MATERIAL_CONSTRUCAO": "NF-E", "MAO_DE_OBRA_PROPRIA": "APROPRIACAO_INTERNA",
       "PROJETOS_INCORPORACAO": "NF-E", "TAXAS_APROVACAO": "GUIA_TRIBUTO", "SEGUROS_OBRA": "APOLICE", "RATEIO_CUSTO_COMUM": "APROPRIACAO_INTERNA",
       "CUSTO_UNIDADE_RATEADO": "APROPRIACAO_INTERNA", "ACABAMENTO_FINAL": "NF-E", "HABITE_SE_TAXAS": "GUIA_TRIBUTO", "MANUTENCAO_CAPITALIZAVEL": "NF-E",
       "PARCELA_AQUISICAO_TERRENO": "CONTRATO_PARCELA", "ITBI_REGISTRO": "GUIA_TRIBUTO", "CORRETAGEM_TERRENO": "NF-E", "DEMOLICAO_TERRAPLENAGEM": "NF-E",
       "PROJETOS_PRELIMINARES": "NF-E", "IPTU_TERRENO": "GUIA_TRIBUTO", "ENCARGO_FINANCEIRO_CAPITALIZADO": "APROPRIACAO_INTERNA",
       "ADIANTAMENTO_FORNECEDOR_OBRA": "NF-E", "ADIANTAMENTO_FORNECEDOR_MATERIAL": "NF-E"}
SEM_FORNECEDOR = {"APROPRIACAO_INTERNA", "GUIA_TRIBUTO"}

N_FORN = 4000
forn = pd.DataFrame({"fornecedor_cod": [f"F{i:06d}" for i in range(1, N_FORN + 1)],
                     "nome_sintetico": [f"FORNECEDOR SINTETICO {i:04d}" for i in range(1, N_FORN + 1)],
                     "situacao": "ATIVO",
                     "data_cadastro": (np.datetime64("2015-01-01") + rng.integers(0, 3000, N_FORN)).astype(str)})

partes = []
for cat, n in N_LINHAS.items():
    alvo = NOTA7[cat] * 1000 * 100          # centavos
    raw = rng.lognormal(0, 1.15, n); raw = raw + 0.02 * raw.mean()
    cent = alocar_centavos(raw, alvo)
    if cat == "TERRENOS_NOVAS_OBRAS":       # ~4% de parcelas "redondas" (milhar) - comportamento natural
        idx = rng.choice(n, int(n * .04), replace=False)
        novo = np.maximum(np.round(cent[idx] / 100000) * 100000, 100000).astype(np.int64)
        dif = int(cent[idx].sum() - novo.sum()); cent[idx] = novo
        livre = np.setdiff1d(np.arange(n), idx); j = livre[np.argmax(cent[livre])]; cent[j] += dif
    df = pd.DataFrame({"categoria_nota7": cat, "valor_cent": cent})
    pool = CAT_EMP[cat]; w = 1 / np.arange(1, len(pool) + 1) ** 0.6; w /= w.sum()
    ei = rng.choice(pool, n, p=w); df["emp_idx"] = ei
    tp, pr = TIPOS[cat]; df["tipo_custo"] = rng.choice(tp, n, p=pr)
    # datas de lancamento
    ini_e = emp.data_inicio.values[ei].astype("datetime64[D]")
    span = (DBASE - ini_e).astype(int)
    u = rng.beta(1.6, 1.15, n)
    df["data_lancamento"] = ini_e + (u * np.maximum(span, 1)).astype(int)
    # unidade / lote
    nun = emp.n_unidades.values[ei]
    if cat in ("IMOVEIS_CONCLUIDOS", "IMOVEIS_EM_CONSTRUCAO"):
        un = rng.integers(1, 100000, n) % nun + 1
        df["id_unidade_lote"] = [f"{emp.id_empreendimento[e]}-U{u_:04d}" for e, u_ in zip(ei, un)]
        df["status_unidade"] = "EM_ESTOQUE"
    elif cat == "TERRENOS_NOVAS_OBRAS":
        df["id_unidade_lote"] = [f"{emp.id_empreendimento[e]}-L{(k % 3) + 1:02d}" for e, k in zip(ei, rng.integers(0, 3, n))]
        df["status_unidade"] = "BANCO_TERRENO"
    else:
        df["id_unidade_lote"] = [f"{emp.id_empreendimento[e]}-GERAL" for e in ei]; df["status_unidade"] = "NAO_APLICAVEL"
    partes.append(df)
b = pd.concat(partes, ignore_index=True)
n = len(b)

# ------------- origem, usuario, hora, documento -------------
b["origem_lancamento"] = rng.choice(["AUTOMATICO_ERP", "INTERFACE_MEDICAO", "MANUAL"], n, p=[.70, .24, .06])
man = (b.origem_lancamento == "MANUAL").values
dl = b.data_lancamento.values.astype("datetime64[D]")
wd = (dl.astype("int64") + 3) % 7               # 0=seg ... 5=sab, 6=dom
ajusta = man & (wd >= 5) & (rng.random(n) < 0.96)  # lancamentos manuais caem em dia util (96%)
dl = np.where(ajusta, dl + np.where(wd == 5, 2, 1), dl).astype("datetime64[D]")
dl = np.minimum(dl, DBASE); b["data_lancamento"] = dl
b["data_documento"] = (dl - rng.integers(0, 16, n).astype("timedelta64[D]")).astype("datetime64[D]")
hora = np.where(man, np.where(rng.random(n) < .92, rng.integers(8, 19, n), rng.integers(19, 24, n)),
                np.where(rng.random(n) < .5, rng.integers(0, 6, n), rng.integers(8, 20, n)))
b["hora_lancamento"] = [f"{h:02d}:{m:02d}:{s:02d}" for h, m, s in zip(hora, rng.integers(0, 60, n), rng.integers(0, 60, n))]
b["usuario_lancamento"] = np.where(man, [f"U{k:03d}" for k in rng.integers(1, 31, n)], np.where(b.origem_lancamento == "INTERFACE_MEDICAO", "SYS_MEDICAO", "SYS_ERP"))
b["documento_tipo"] = b.tipo_custo.map(DOC)
tem_f = ~b.documento_tipo.isin(SEM_FORNECEDOR)
b["fornecedor_cod"] = np.where(tem_f, [f"F{k:06d}" for k in rng.integers(1, N_FORN + 1, n)], "")
b["documento_numero"] = [f"{t.replace('-','')[:3]}-{k:07d}" for t, k in zip(b.documento_tipo, rng.integers(1, 9_999_999, n))]

# ------------- encargos: base capitalizavel x taxa mensal -------------
enc = (b.categoria_nota7 == "ENCARGOS_FINANCEIROS").values
tx = np.round(np.where(enc, rng.uniform(0.0080, 0.0115, n), np.nan), 6)
b["taxa_mensal"] = tx
b["base_capitalizavel_rs"] = np.where(enc, np.round(b.valor_cent.values / 100 / np.where(enc, tx, 1), 2), np.nan)

# ------------- classificacao circulante / nao circulante calibrada -------------
fat = b.categoria_nota7.map({"IMOVEIS_CONCLUIDOS": .5, "IMOVEIS_EM_CONSTRUCAO": 1.0, "TERRENOS_NOVAS_OBRAS": 1.6,
                             "ENCARGOS_FINANCEIROS": 1.0, "ADIANTAMENTO_FORNECEDORES": .4}).values
chave = rng.random(n) * fat
ordem = np.argsort(chave); cs = np.cumsum(b.valor_cent.values[ordem])
alvo_circ = SALDO_CIRC * 1000 * 100
k = np.searchsorted(cs, alvo_circ, side="right")
circ = np.zeros(n, bool); circ[ordem[:k]] = True
res = int(alvo_circ - cs[k - 1])
# ajuste exato: transfere 'res' centavos entre duas linhas da mesma categoria (uma circ., outra n.circ.)
cat_arr = b.categoria_nota7.values
for cat in b.categoria_nota7.unique():
    ci = np.where(circ & (cat_arr == cat))[0]; ni = np.where(~circ & (cat_arr == cat) & (b.valor_cent.values > res + 100))[0]
    if len(ci) and len(ni):
        b.loc[ci[0], "valor_cent"] += res; b.loc[ni[0], "valor_cent"] -= res
        if cat == "ENCARGOS_FINANCEIROS":
            for j in (ci[0], ni[0]): b.loc[j, "base_capitalizavel_rs"] = round(b.valor_cent[j] / 100 / b.taxa_mensal[j], 2)
        break
b["classificacao_balanco"] = np.where(circ, "CIRCULANTE", "NAO_CIRCULANTE")
b["data_realizacao_prevista"] = np.where(circ, np.datetime64("2026-01-01") + rng.integers(0, 365, n),
                                         np.datetime64("2027-01-01") + rng.integers(0, 1800, n)).astype("datetime64[D]")
b["data_venda_unidade"] = pd.NaT
b["lancamento_estorno_ref"] = ""
b["data_competencia"] = (b.data_lancamento.values.astype("datetime64[M]") + 1).astype("datetime64[D]") - np.timedelta64(1, "D")
b.insert(0, "id_lancamento", np.arange(1, n + 1))
b["id_empreendimento"] = emp.id_empreendimento.values[b.emp_idx.values]
b["sintetico"] = "SIM"
PRE = b[["valor_cent", "classificacao_balanco"]].copy()   # estado pre-insercao (para conciliacao)
assert b.valor_cent.sum() == SALDO_ESTOQUES * 100000
assert b.loc[b.classificacao_balanco == "CIRCULANTE", "valor_cent"].sum() == SALDO_CIRC * 100000
print("pre-insercao: linhas", n, "| soma R$", b.valor_cent.sum() / 100)

# ================= INSERCAO DE ERROS (registro completo) =================
usado = np.zeros(n, bool); reg = []; novas = []; prox_id = n + 1
V = b.valor_cent.values
def elegiveis(mask): return np.where(mask & ~usado)[0]
def escolhe(idx, k, pesos=None):
    p = None
    if pesos is not None: p = pesos[idx].astype(float); p /= p.sum()
    sel = rng.choice(idx, k, replace=False, p=p); usado[sel] = True; return sel
def r(tipo, i, campo, antes, depois, desc, det, ass, novo=False, orig=None):
    reg.append(dict(tipo_erro=tipo, id_lancamento_afetado=int(i) if novo else int(b.id_lancamento.values[i]), id_lancamento_original=orig,
                    campo_alterado=campo, valor_antes=antes, valor_depois=depois, descricao=desc, detectavel_por=det, assercao=ass, linha_nova=novo))

# E1 duplicidade (linhas novas)
e = escolhe(elegiveis((b.documento_tipo == "NF-E").values & (V >= 500000)), 180, V)
for i in e:
    d = b.iloc[i].copy(); d["id_lancamento"] = prox_id; d["data_lancamento"] = min(d.data_lancamento + np.timedelta64(int(rng.integers(1, 8)), "D"), DBASE)
    d["hora_lancamento"] = "10:%02d:00" % rng.integers(0, 60); d["usuario_lancamento"] = "SYS_ERP"; novas.append(d)
    r("E01_DUPLICIDADE", prox_id, "linha inteira", None, d.valor_cent / 100, "Lancamento duplicado (mesmo fornecedor, documento, valor e data do documento)", "ANALITICO_100%", "Ocorrencia/Existencia", True, int(b.id_lancamento.values[i])); prox_id += 1
# E2 corte (documento emitido em 2026 e lancado em 2025)
e = escolhe(elegiveis((b.documento_tipo == "NF-E").values & (V >= 800000)), 150, V)
for i in e:
    antes = str(b.data_documento.values[i])[:10]; b.loc[i, "data_documento"] = np.datetime64("2026-01-02") + int(rng.integers(0, 55))
    r("E02_CORTE", i, "data_documento", antes, str(b.data_documento.values[i])[:10], "Documento emitido em 2026 contabilizado em 2025", "ANALITICO_100%", "Corte")
# E3 manual, fim de semana, valor redondo
e = escolhe(elegiveis((V < 5_000_000)), 60)
for i in e:
    novo = int(rng.integers(2, 7)) * 5_000_000; antes = b.valor_cent.values[i]
    d = np.datetime64("2025-12-06") + int(rng.choice([0, 1, 7, 8, 14, 15, 21, 22]))
    b.loc[i, ["valor_cent", "origem_lancamento", "usuario_lancamento"]] = [novo * 1, "MANUAL", "U%03d" % rng.integers(1, 31)]
    b.loc[i, "data_lancamento"] = d; b.loc[i, "data_documento"] = d - np.timedelta64(2, "D"); b.loc[i, "hora_lancamento"] = "%02d:%02d:00" % (rng.choice([21, 22, 23]), rng.integers(0, 60))
    r("E03_MANUAL_FDS_REDONDO", i, "valor/origem/data", antes / 100, novo / 100, "Lancamento manual em fim de semana, fora do horario, valor redondo elevado", "ANALITICO_100%", "Ocorrencia/Valoracao")
# E4 classificacao circ/NC inconsistente com a data de realizacao
e = escolhe(elegiveis(np.ones(n, bool)), 120, V)
for i in e:
    antes = b.classificacao_balanco.values[i]; b.loc[i, "classificacao_balanco"] = "NAO_CIRCULANTE" if antes == "CIRCULANTE" else "CIRCULANTE"
    r("E04_CLASSIFICACAO", i, "classificacao_balanco", antes, b.classificacao_balanco.values[i], "Classificacao circulante/nao circulante incompativel com a data de realizacao prevista", "ANALITICO_100%", "Apresentacao")
# E5 custo nao capitalizavel
e = escolhe(elegiveis((b.categoria_nota7 == "IMOVEIS_EM_CONSTRUCAO").values & (V >= 300000)), 70, V)
for i in e:
    antes = b.tipo_custo.values[i]; b.loc[i, "tipo_custo"] = rng.choice(["DESPESA_STAND_VENDAS", "PUBLICIDADE_LANCAMENTO", "COMISSAO_VENDAS", "DESPESA_ADMINISTRATIVA_SEDE"])
    r("E05_CUSTO_NAO_CAPITALIZAVEL", i, "tipo_custo", antes, b.tipo_custo.values[i], "Despesa comercial/administrativa capitalizada em estoque", "ANALITICO_100%", "Classificacao/Valoracao")
# E6 encargo capitalizado acima do teto de taxa
e = escolhe(elegiveis((b.categoria_nota7 == "ENCARGOS_FINANCEIROS").values & (V >= 300000)), 60, V)
for i in e:
    antes = b.valor_cent.values[i]; nt = rng.uniform(0.025, 0.04); base = b.base_capitalizavel_rs.values[i]
    b.loc[i, "taxa_mensal"] = round(nt, 6); b.loc[i, "valor_cent"] = int(round(base * nt * 100))
    r("E06_ENCARGO_TAXA", i, "taxa_mensal/valor", antes / 100, b.valor_cent.values[i] / 100, "Encargo capitalizado com taxa mensal acima do teto da politica (1,5% a.m.)", "ANALITICO_100%", "Valoracao")
# E7 unidade ja vendida mantida em estoque
e = escolhe(elegiveis(b.categoria_nota7.isin(["IMOVEIS_CONCLUIDOS", "IMOVEIS_EM_CONSTRUCAO"]).values & (V >= 400000)), 110, V)
for i in e:
    b.loc[i, "data_venda_unidade"] = np.datetime64("2025-03-01") + int(rng.integers(0, 290))
    r("E07_UNIDADE_VENDIDA", i, "data_venda_unidade", None, str(b.data_venda_unidade.values[i])[:10], "Unidade vendida ate 31/12/2025 cujo custo permanece em estoque (falta de baixa ao CPV)", "ANALITICO_100%", "Existencia/Valoracao")
# E8 fornecedor inexistente no cadastro
e = escolhe(elegiveis((b.documento_tipo == "NF-E").values & (V >= 600000)), 45, V)
for i in e:
    antes = b.fornecedor_cod.values[i]; b.loc[i, "fornecedor_cod"] = "F9%05d" % rng.integers(0, 99999)
    r("E08_FORNECEDOR_INEXISTENTE", i, "fornecedor_cod", antes, b.fornecedor_cod.values[i], "Fornecedor ausente do cadastro mestre", "ANALITICO_100%", "Ocorrencia/Existencia")
# E9 estorno sem referencia
e = escolhe(elegiveis((V < 800000) & (V > 100000)), 50)
for i in e:
    antes = b.valor_cent.values[i]; b.loc[i, "valor_cent"] = -antes
    r("E09_ESTORNO_SEM_REFERENCIA", i, "valor_cent", antes / 100, -antes / 100, "Valor negativo sem referencia ao lancamento original", "ANALITICO_100%", "Valoracao")
# E10 valor lancado diferente do documento (so detectavel por inspecao documental)
lim = np.quantile(V[~usado], 0.9997)
e = escolhe(elegiveis(V >= lim), 60, V)
for i in e:
    antes = b.valor_cent.values[i]; f = rng.uniform(1.08, 1.30); novo = int(round(antes * f))
    b.loc[i, "valor_cent"] = novo
    r("E10_VALOR_DIVERGENTE", i, "valor_cent", antes / 100, novo / 100, "Valor lancado superior ao do documento fiscal", "AMOSTRA_DOCUMENTAL", "Valoracao")
if novas: b = pd.concat([b, pd.DataFrame(novas)], ignore_index=True)

# ------- registro com efeitos calculados -------
R = pd.DataFrame(reg)
idx_map = pd.Series(np.arange(len(b)), index=b.id_lancamento.values)
pos = idx_map[R.id_lancamento_afetado].values
pre_v = np.zeros(len(b), np.int64); pre_v[:n] = PRE.valor_cent.values
pre_c = np.array(list(PRE.classificacao_balanco.values) + [""] * (len(b) - n))
post_v = b.valor_cent.values; post_c = b.classificacao_balanco.values
R["efeito_total_rs"] = (post_v[pos] - pre_v[pos]) / 100
R["efeito_circulante_rs"] = (np.where(post_c[pos] == "CIRCULANTE", post_v[pos], 0) - np.where(pre_c[pos] == "CIRCULANTE", pre_v[pos], 0)) / 100
R["efeito_nao_circulante_rs"] = R.efeito_total_rs - R.efeito_circulante_rs
R["categoria_nota7"] = b.categoria_nota7.values[pos]
exp = R.efeito_total_rs.copy()
exp[R.tipo_erro == "E04_CLASSIFICACAO"] = 0; exp[R.tipo_erro == "E03_MANUAL_FDS_REDONDO"] = R.efeito_total_rs
exp[R.tipo_erro.isin(["E02_CORTE", "E05_CUSTO_NAO_CAPITALIZAVEL", "E07_UNIDADE_VENDIDA", "E08_FORNECEDOR_INEXISTENTE"])] = post_v[pos][R.tipo_erro.isin(["E02_CORTE", "E05_CUSTO_NAO_CAPITALIZAVEL", "E07_UNIDADE_VENDIDA", "E08_FORNECEDOR_INEXISTENTE"]).values] / 100
exp[R.tipo_erro == "E09_ESTORNO_SEM_REFERENCIA"] = R.efeito_total_rs
R["distorcao_potencial_rs"] = exp   # (+) superavaliacao do ativo / (-) subavaliacao, em relacao ao valor correto
R["id_lancamento_original"] = R.id_lancamento_original.astype("Int64")
R.insert(0, "id_erro", [f"ERR-{k:04d}" for k in range(1, len(R) + 1)])
R.to_csv(os.path.join(OUT, "registro_erros_inseridos.csv"), index=False)

# ------- saida da base -------
b = b.sort_values("id_lancamento").reset_index(drop=True)
b["valor_rs"] = np.round(b.valor_cent.values / 100, 2)
cols = ["id_lancamento", "data_lancamento", "data_documento", "data_competencia", "id_empreendimento", "id_unidade_lote", "categoria_nota7", "tipo_custo",
        "documento_tipo", "documento_numero", "fornecedor_cod", "valor_rs", "classificacao_balanco", "data_realizacao_prevista", "status_unidade",
        "data_venda_unidade", "origem_lancamento", "usuario_lancamento", "hora_lancamento", "base_capitalizavel_rs", "taxa_mensal", "lancamento_estorno_ref", "sintetico"]
for c in ["data_lancamento", "data_documento", "data_competencia", "data_realizacao_prevista", "data_venda_unidade"]:
    b[c] = pd.to_datetime(b[c]).dt.strftime("%Y-%m-%d")
b[cols].to_csv(os.path.join(OUT, "base_imoveis_a_comercializar_sintetica.csv.gz"), index=False, compression="gzip")
forn.to_csv(os.path.join(OUT, "cadastro_fornecedores_sintetico.csv"), index=False)
print("pos-insercao: linhas", len(b), "| soma R$", round(b.valor_rs.sum(), 2), "| erros registrados", len(R))
print(R.groupby("tipo_erro").agg(n=("id_erro", "count"), efeito=("efeito_total_rs", "sum"), potencial=("distorcao_potencial_rs", "sum")).round(0))
print("efeito liquido total R$", R.efeito_total_rs.sum(), "| distorcao potencial R$", R.distorcao_potencial_rs.sum())
print("maior linha R$", b.valor_rs.max(), "| linhas >=1M", (b.valor_rs >= 1e6).sum())
