"""Executa os testes de auditoria sobre a base SINTETICA e compara excecoes encontradas x erros inseridos.
Saidas em resultados/. Uso: python src/02_executar_testes.py (apos 01_gerar_base.py)."""
import os, sys, json, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from config import *
D = os.path.join(ROOT, "data"); R = os.path.join(ROOT, "resultados"); os.makedirs(R, exist_ok=True)
b = pd.read_csv(os.path.join(D, "base_imoveis_a_comercializar_sintetica.csv.gz"), keep_default_na=False, na_values=[""],
                parse_dates=["data_lancamento", "data_documento", "data_competencia", "data_realizacao_prevista", "data_venda_unidade"])
forn = set(pd.read_csv(os.path.join(D, "cadastro_fornecedores_sintetico.csv")).fornecedor_cod)
reg = pd.read_csv(os.path.join(D, "registro_erros_inseridos.csv"))
DB = pd.Timestamp(DATA_BASE); out = {}

# ---------- materialidade (PT 320) ----------
lair = DF["lair"][0]; mat_global = round(0.05 * lair); mat_exec = round(0.65 * mat_global); trivial = round(0.05 * mat_global)
out["materialidade"] = dict(lair=lair, global_=mat_global, execucao=mat_exec, trivial=trivial,
    alt_receita_1pct=round(.01 * DF["receita_liquida"][0]), alt_ativo_05pct=round(.005 * DF["ativo_total"][0]), alt_pl_1pct=round(.01 * DF["patrimonio_liquido"][0]))

# ---------- T1 integridade e conciliacao ----------
out["linhas"] = int(len(b)); out["ids_unicos"] = bool(b.id_lancamento.is_unique)
out["nulos_campos_obrigatorios"] = int(b[["id_lancamento", "data_lancamento", "valor_rs", "categoria_nota7", "classificacao_balanco"]].isna().sum().sum())
concil = b.groupby("categoria_nota7").valor_rs.sum().rename("base_rs").to_frame()
concil["saldo_contabil_rs"] = [NOTA7[c] * 1000 for c in concil.index]
concil["diferenca_rs"] = concil.base_rs - concil.saldo_contabil_rs
concil["explicada_pelo_registro_rs"] = reg.groupby("categoria_nota7").efeito_total_rs.sum().reindex(concil.index).fillna(0)
concil["diferenca_nao_explicada_rs"] = (concil.diferenca_rs - concil.explicada_pelo_registro_rs).round(2)
concil.loc["TOTAL"] = concil.sum()
concil.round(2).to_csv(os.path.join(R, "conciliacao_por_categoria.csv"))
cl = b.groupby("classificacao_balanco").valor_rs.sum().to_frame("base_rs")
cl["saldo_contabil_rs"] = [SALDO_CIRC * 1000, SALDO_NC * 1000]
cl["diferenca_rs"] = cl.base_rs - cl.saldo_contabil_rs
cl["explicada_pelo_registro_rs"] = [reg.efeito_circulante_rs.sum(), reg.efeito_nao_circulante_rs.sum()]
cl["diferenca_nao_explicada_rs"] = (cl.diferenca_rs - cl.explicada_pelo_registro_rs).round(2)
cl.round(2).to_csv(os.path.join(R, "conciliacao_circulante_nc.csv"))
out["conciliacao_total"] = concil.loc["TOTAL"].round(2).to_dict()

# ---------- testes analiticos 100% (CAAT) ----------
ex = []
def add(teste, mask): 
    t = b.loc[mask, ["id_lancamento", "valor_rs"]].copy(); t["teste"] = teste; ex.append(t)
# T2 duplicidade
k = b.fornecedor_cod.notna() & (b.documento_tipo == "NF-E")
dup = b[k].duplicated(subset=["fornecedor_cod", "documento_numero", "valor_rs", "data_documento"], keep="first")
m = pd.Series(False, index=b.index); m[dup[dup].index] = True; add("T02_DUPLICIDADE", m)
# T3 corte
add("T03_CORTE", (b.data_documento > DB) | (b.data_lancamento > DB))
# T4 lancamentos manuais de risco (NBC TA 240)
fds = b.data_lancamento.dt.dayofweek >= 5; h = b.hora_lancamento.str[:2].astype(int)
add("T04_MANUAL_RISCO", (b.origem_lancamento == "MANUAL") & (fds | (h >= 19) | (h < 7)) & (b.valor_rs >= 50000))
# T5 classificacao
esp = np.where(b.data_realizacao_prevista <= pd.Timestamp("2026-12-31"), "CIRCULANTE", "NAO_CIRCULANTE")
add("T05_CLASSIFICACAO", b.classificacao_balanco != esp)
# T6 dominio de tipo de custo
perm = set(sum([["CUSTO_UNIDADE_RATEADO", "ACABAMENTO_FINAL", "HABITE_SE_TAXAS", "MANUTENCAO_CAPITALIZAVEL", "MEDICAO_EMPREITEIRO", "MATERIAL_CONSTRUCAO",
        "MAO_DE_OBRA_PROPRIA", "PROJETOS_INCORPORACAO", "TAXAS_APROVACAO", "SEGUROS_OBRA", "RATEIO_CUSTO_COMUM", "PARCELA_AQUISICAO_TERRENO", "ITBI_REGISTRO",
        "CORRETAGEM_TERRENO", "DEMOLICAO_TERRAPLENAGEM", "PROJETOS_PRELIMINARES", "IPTU_TERRENO", "ENCARGO_FINANCEIRO_CAPITALIZADO",
        "ADIANTAMENTO_FORNECEDOR_OBRA", "ADIANTAMENTO_FORNECEDOR_MATERIAL"]], []))
add("T06_TIPO_CUSTO_NAO_CAPITALIZAVEL", ~b.tipo_custo.isin(perm))
# T7 encargos
e = b.categoria_nota7 == "ENCARGOS_FINANCEIROS"
add("T07_ENCARGO_TAXA", e & ((b.taxa_mensal > 0.015) | ((b.valor_rs - (b.base_capitalizavel_rs * b.taxa_mensal)).abs() > 0.02)))
# T8 unidade vendida
add("T08_UNIDADE_VENDIDA", b.data_venda_unidade.notna() & (b.data_venda_unidade <= DB))
# T9 fornecedor
add("T09_FORNECEDOR_FORA_CADASTRO", b.fornecedor_cod.notna() & ~b.fornecedor_cod.isin(forn))
# T10 negativos sem referencia
add("T10_NEGATIVO_SEM_REFERENCIA", (b.valor_rs < 0) & b.lancamento_estorno_ref.isna())
EX = pd.concat(ex, ignore_index=True); EX.to_csv(os.path.join(R, "excecoes_testes_analiticos.csv"), index=False)
# comparacao inserido x detectado
mapa = {"E01_DUPLICIDADE": "T02_DUPLICIDADE", "E02_CORTE": "T03_CORTE", "E03_MANUAL_FDS_REDONDO": "T04_MANUAL_RISCO", "E04_CLASSIFICACAO": "T05_CLASSIFICACAO",
        "E05_CUSTO_NAO_CAPITALIZAVEL": "T06_TIPO_CUSTO_NAO_CAPITALIZAVEL", "E06_ENCARGO_TAXA": "T07_ENCARGO_TAXA", "E07_UNIDADE_VENDIDA": "T08_UNIDADE_VENDIDA",
        "E08_FORNECEDOR_INEXISTENTE": "T09_FORNECEDOR_FORA_CADASTRO", "E09_ESTORNO_SEM_REFERENCIA": "T10_NEGATIVO_SEM_REFERENCIA"}
linhas = []
for te, tt in mapa.items():
    ins = set(reg.loc[reg.tipo_erro == te, "id_lancamento_afetado"]); det = set(EX.loc[EX.teste == tt, "id_lancamento"])
    fp = det - ins; expl = fp & set(reg.id_lancamento_afetado)
    linhas.append(dict(tipo_erro_inserido=te, teste=tt, inseridos=len(ins), detectados_total=len(det), verdadeiros_positivos=len(ins & det),
                       falsos_negativos=len(ins - det), falsos_positivos=len(fp), fp_explicados_por_outro_erro_inserido=len(expl),
                       fp_nao_explicados=len(fp - expl), sensibilidade=round(len(ins & det) / len(ins), 4),
                       precisao=round(len(ins & det) / max(len(det), 1), 4)))
CMP = pd.DataFrame(linhas)

# ---------- Benford (primeiro digito) ----------
v = b.valor_rs[b.valor_rs > 0]; fd = v.astype(str).str.replace(".", "", regex=False).str.lstrip("0").str[0].astype(int)
obs = fd.value_counts(normalize=True).reindex(range(1, 10)).fillna(0); esp_b = pd.Series({d: np.log10(1 + 1 / d) for d in range(1, 10)})
ben = pd.DataFrame({"digito": range(1, 10), "observado": obs.values, "benford": esp_b.values}); ben["dif_abs"] = (ben.observado - ben.benford).abs()
ben.round(5).to_csv(os.path.join(R, "benford_primeiro_digito.csv"), index=False)
out["benford_MAD"] = round(float(ben.dif_abs.mean()), 5)

# ---------- PT 530: MUS ----------
TM = mat_exec * 1000.0; RF = 3.00; I = TM / RF
pos = b[b.valor_rs > 0].sort_values("id_lancamento").reset_index(drop=True)
cum = pos.valor_rs.cumsum().values; popv = float(cum[-1])
rs = np.random.default_rng(SEED + 1); inicio = float(rs.uniform(0, I))
pts = np.arange(inicio, popv, I); idx = np.searchsorted(cum, pts, side="left")
amostra = pos.iloc[np.unique(idx)].copy(); amostra["pontos_selecionados"] = pd.Series(idx).value_counts().reindex(np.unique(idx)).values
amostra["item_chave"] = amostra.valor_rs >= I
# evidencia documental SIMULADA (oraculo = registro de erros inseridos)
vdoc = pd.to_numeric(reg[reg.tipo_erro == "E10_VALOR_DIVERGENTE"].set_index("id_lancamento_afetado").valor_antes)
amostra["valor_documento_simulado"] = [float(vdoc.get(i, vr)) for i, vr in zip(amostra.id_lancamento, amostra.valor_rs)]
a1 = (amostra.valor_rs - amostra.valor_documento_simulado).round(2)
a2 = (amostra.data_documento > DB); a3 = ~amostra.tipo_custo.isin(perm); a4 = amostra.fornecedor_cod.notna() & ~amostra.fornecedor_cod.isin(forn); a5 = amostra.data_venda_unidade.notna()
amostra["distorcao_rs"] = np.where(a1 != 0, a1, np.where(a2 | a3 | a4 | a5, amostra.valor_rs, 0.0))
amostra["tipo_excecao"] = np.where(a1 != 0, "VALOR_DIVERGENTE", np.where(a2, "CORTE", np.where(a3, "CUSTO_NAO_CAPITALIZAVEL", np.where(a4, "FORNECEDOR", np.where(a5, "UNIDADE_VENDIDA", "")))))
amostra["taint"] = (amostra.distorcao_rs / amostra.valor_rs.clip(lower=0.01)).clip(0, 1)
amostra.drop(columns=["lancamento_estorno_ref"]).to_csv(os.path.join(R, "amostra_mus_pt530.csv"), index=False)
amostra["ja_identificada_teste_100pct"] = amostra.id_lancamento.isin(EX.id_lancamento) & (amostra.distorcao_rs > 0)
todas = amostra[amostra.distorcao_rs > 0]
errs = amostra[(amostra.distorcao_rs > 0) & ~amostra.ja_identificada_teste_100pct].sort_values("taint", ascending=False)
amostra.drop(columns=["lancamento_estorno_ref"]).to_csv(os.path.join(R, "amostra_mus_pt530.csv"), index=False)
inc = [1.75, 1.55, 1.46, 1.40, 1.36, 1.33, 1.31, 1.29, 1.28, 1.27]   # incrementos de Poisson (risco 5%)
uel = RF * I; prev = RF
for j, t in enumerate(errs.taint.values): uel += t * I * inc[min(j, len(inc) - 1)]
proj = float((errs.taint * I).sum())
out["mus"] = dict(populacao_rs=round(popv, 2), tolerable_rs=TM, fator=RF, intervalo_rs=round(I, 2), n_amostra=int(len(amostra)), n_chave=int(amostra.item_chave.sum()),
    inicio_aleatorio=round(inicio, 2), n_excecoes_amostra_total=int(len(todas)), n_excecoes_ja_identificadas_100pct=int(len(todas)-len(errs)), n_excecoes=int(len(errs)), distorcao_na_amostra_rs=round(float(errs.distorcao_rs.sum()), 2),
    projecao_rs=round(proj, 2), limite_superior_stringer_rs=round(uel, 2), precisao_basica_rs=round(RF * I, 2),
    distorcao_pontual_E10_total_inserida=round(float(reg[reg.tipo_erro == "E10_VALOR_DIVERGENTE"].efeito_total_rs.sum()), 2),
    excecoes_por_tipo=amostra[amostra.tipo_excecao != ""].tipo_excecao.value_counts().to_dict())
e10 = set(reg.loc[reg.tipo_erro == "E10_VALOR_DIVERGENTE", "id_lancamento_afetado"]); s10 = set(amostra.id_lancamento)
CMP = pd.concat([CMP, pd.DataFrame([dict(tipo_erro_inserido="E10_VALOR_DIVERGENTE", teste="AMOSTRA_MUS_DOCUMENTAL", inseridos=len(e10), detectados_total=len(e10 & s10),
    verdadeiros_positivos=len(e10 & s10), falsos_negativos=len(e10 - s10), falsos_positivos=0, fp_explicados_por_outro_erro_inserido=0, fp_nao_explicados=0, sensibilidade=round(len(e10 & s10) / len(e10), 4), precisao=1.0)])], ignore_index=True)
CMP.to_csv(os.path.join(R, "comparacao_erros_inseridos_x_detectados.csv"), index=False)
out["comparacao"] = CMP.to_dict("records")

# ---------- mapa de distorcoes (PT 450) ----------
mp = reg.groupby("tipo_erro").agg(n=("id_erro", "count"), efeito_na_base_rs=("efeito_total_rs", "sum"), distorcao_potencial_rs=("distorcao_potencial_rs", "sum")).reset_index()
mp.round(2).to_csv(os.path.join(R, "mapa_distorcoes_pt450.csv"), index=False)
out["distorcao_potencial_total_rs"] = round(float(reg.distorcao_potencial_rs.sum()), 2)
out["efeito_liquido_base_rs"] = round(float(reg.efeito_total_rs.sum()), 2)
sup = reg.distorcao_potencial_rs.clip(lower=0).sum(); sub = reg.distorcao_potencial_rs.clip(upper=0).sum()
out["superavaliacao_rs"] = round(float(sup), 2); out["subavaliacao_rs"] = round(float(sub), 2)

# ---------- descritivas ----------
out["descritivas"] = dict(soma_rs=round(float(b.valor_rs.sum()), 2), media=round(float(b.valor_rs.mean()), 2), mediana=round(float(b.valor_rs.median()), 2),
    maximo=round(float(b.valor_rs.max()), 2), p99=round(float(b.valor_rs.quantile(.99)), 2), linhas_manuais=int((b.origem_lancamento == "MANUAL").sum()),
    top10_emp_pct=round(float(b.groupby("id_empreendimento").valor_rs.sum().nlargest(10).sum() / b.valor_rs.sum()), 4),
    por_ano=b.groupby(b.data_lancamento.dt.year).valor_rs.sum().round(0).to_dict())
out["excecoes_por_teste"] = EX.teste.value_counts().to_dict()
json.dump(out, open(os.path.join(R, "resultados_resumo.json"), "w"), indent=1, default=str, ensure_ascii=False)
print(json.dumps({k: out[k] for k in ["materialidade", "conciliacao_total", "mus", "excecoes_por_teste", "benford_MAD", "superavaliacao_rs", "subavaliacao_rs"]}, indent=1, default=str))
print(CMP.to_string()); print(concil.round(2).to_string()); print(cl.round(2).to_string())
