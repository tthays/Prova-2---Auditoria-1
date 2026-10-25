# -*- coding: utf-8 -*-
"""Gera o dossie em PDF (reportlab). Uso: python src/04_gerar_dossie.py"""
import os, sys, json, hashlib, pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
sys.path.insert(0, os.path.dirname(__file__))
from config import *
from pt_conteudo import pts
FD = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", FD + "DejaVuSans.ttf")); pdfmetrics.registerFont(TTFont("DVB", FD + "DejaVuSans-Bold.ttf")); pdfmetrics.registerFont(TTFont("DVI", FD + "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB", italic="DVI", boldItalic="DVB")
R = json.load(open(os.path.join(ROOT, "resultados", "resultados_resumo.json"), encoding="utf8"))
C = R["comparacao"]; M = R["materialidade"]
comp = pd.read_csv(os.path.join(ROOT, "resultados", "mapa_distorcoes_pt450.csv")).to_dict("records")
sha = lambda p: hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()[:16]
SHA = "base_imoveis_a_comercializar_sintetica.csv.gz=" + sha("data/base_imoveis_a_comercializar_sintetica.csv.gz") + "...; registro_erros_inseridos.csv=" + sha("data/registro_erros_inseridos.csv") + "... (16 primeiros caracteres)"
PT = pts(R, M, C, SHA, comp)
f = lambda x: f"{x:,.0f}".replace(",", ".")
S = lambda n, **k: ParagraphStyle(n, fontName=k.pop("fontName", "DV"), fontSize=k.pop("fontSize", 7.6), leading=k.pop("leading", 10), **k)
b = S("b"); bs = S("bs", fontSize=6.8, leading=8.8); h1 = S("h1", fontName="DVB", fontSize=13, leading=17, spaceAfter=6, textColor=colors.HexColor("#1F3864"))
h2 = S("h2", fontName="DVB", fontSize=9.5, leading=12, spaceBefore=6, spaceAfter=3, textColor=colors.HexColor("#1F3864")); lab = S("lab", fontName="DVB", fontSize=7, leading=9, textColor=colors.white)
tc = S("tc", fontSize=6.6, leading=8.4); th = S("th", fontName="DVB", fontSize=6.6, leading=8.4, textColor=colors.white)
def esc(t): return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
P_ = lambda t, st=b: Paragraph(esc(t), st)
NAV = colors.HexColor("#1F3864"); CL = {"RP": ("#E2EFDA", "Realizado com evidência pública"), "PL": ("#FFF2CC", "Planejado por falta de acesso"), "SD": ("#DDEBF7", "Simulado para fins didáticos")}
def tabela(cab, rows, widths=None):
    cabs = cab.split("|"); data = [[Paragraph(esc(c), th) for c in cabs]] + [[Paragraph(esc(c), tc) for c in r] for r in rows]
    w = widths or [(A4[0] - 3.4 * cm) / len(cabs)] * len(cabs)
    t = Table(data, colWidths=w, repeatRows=1); t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAV), ("GRID", (0, 0), (-1, -1), .3, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FA")]), ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)])); return t
W = A4[0] - 3.4 * cm
def bloco(p):
    out = [Paragraph(esc(f"{p['cod']} - {p['titulo']}"), h1)]
    cab = Table([[Paragraph(f"<b>Código:</b> {esc(p['cod'])}", tc), Paragraph(f"<b>Norma e itens:</b> {esc(p['norma'])}", tc)]], colWidths=[3 * cm, W - 3 * cm])
    cab.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), .5, NAV), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF2F8")), ("VALIGN", (0, 0), (-1, -1), "TOP")])); out += [cab, Spacer(1, 4)]
    rows = [("Objetivo e conta/processo examinado", p["obj"]), ("Afirmações relevantes e riscos", p["ass"]), ("População, fontes e critérios de seleção", p["pop"])]
    for k, v in rows: out.append(KeepTogether([Paragraph(esc(k), h2), Paragraph(esc(v), b)]))
    out.append(Paragraph("Procedimentos planejados ou executados", h2))
    pr = [[Paragraph(f"<b>{c}</b>", tc), Paragraph(esc(t), tc)] for c, t in p["proc"]]
    tb = Table(pr, colWidths=[.9 * cm, W - .9 * cm]); st = [("GRID", (0, 0), (-1, -1), .3, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP")]
    for i, (c, _) in enumerate(p["proc"]): st.append(("BACKGROUND", (0, i), (0, i), colors.HexColor(CL[c][0])))
    tb.setStyle(TableStyle(st)); out.append(tb)
    if "tab" in p: out += [Spacer(1, 4), tabela(p["tab"][0], p["tab"][1])]
    for k, v in [("Evidências e referências cruzadas", f"{p['evi']}  Ver também: {p['xr']}."), ("Resultados, exceções e conclusão", p["res"]), ("Limitações", p["lim"])]:
        out.append(KeepTogether([Paragraph(esc(k), h2), Paragraph(esc(v), b)]))
    pie = Table([[Paragraph(f"<b>Preparador:</b> matrícula {MATRICULA} | <b>Data:</b> {DATA_PREPARO}", tc), Paragraph("<b>Revisão:</b> ____________________  Data: ___/___/_____ (campo em branco; sem simulação de revisão de terceiros)", tc)]], colWidths=[W * .42, W * .58])
    pie.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), .5, NAV), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")])); out += [Spacer(1, 5), pie, PageBreak()]
    return out
def rodape(c, d):
    c.saveState(); c.setFont("DV", 6.5); c.setFillColor(colors.grey)
    c.drawString(1.7 * cm, 1 * cm, f"Dossiê P2 - Auditoria 1 - EZTEC - matrícula {MATRICULA} - trabalho acadêmico, sem opinião independente - dados da base: SINTÉTICOS"); c.drawRightString(A4[0] - 1.7 * cm, 1 * cm, f"pág. {d.page}"); c.restoreState()
out = os.path.join(ROOT, "dossie", f"Dossie_Auditoria_EZTEC_P2_{MATRICULA}.pdf")
doc = BaseDocTemplate(out, pagesize=A4, leftMargin=1.7 * cm, rightMargin=1.7 * cm, topMargin=1.5 * cm, bottomMargin=1.6 * cm, title=f"Dossiê de auditoria - EZTEC - P2 - {MATRICULA}", author=f"Matrícula {MATRICULA}")
doc.addPageTemplates([PageTemplate(id="x", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=rodape)])
E = []
E += [Spacer(1, 3 * cm), Paragraph("UNIVERSIDADE DE BRASÍLIA - UnB", S("c0", fontName="DVB", fontSize=11, alignment=1)), Paragraph("Auditoria 1 - CCA0024 - Turma 02 - 2026.2 - P2", S("c1", fontSize=9, alignment=1, spaceAfter=30)),
      Paragraph("DOSSIÊ DE AUDITORIA", S("c2", fontName="DVB", fontSize=22, leading=28, alignment=1, textColor=NAV)), Paragraph("EZ TEC Empreendimentos e Participações S.A. (EZTC3)", S("c3", fontName="DVB", fontSize=14, alignment=1, spaceAfter=6)),
      Paragraph("Demonstrações contábeis anuais de 31/12/2025 - NBC TA Estrutura Conceitual e NBC TA 200 a 600", S("c4", fontSize=10, alignment=1, spaceAfter=24))]
E.append(tabela("Item|Informação", [["Aluna (identificação)", f"Thays Santos - matrícula {MATRICULA}"], ["Companhia atribuída", "EZTEC (conforme tabela de distribuição do enunciado)"], ["Data de preparação", DATA_PREPARO],
    ["Fonte principal", "DFP 2025, CVM, protocolo 155329, versão 1 (arquivo 155329_020770_23102026001008.pdf), acesso informado pelo aluno em 23/10/2026 às 00:16; PDF obtido no site da B3"],
    ["Normas", "NBC TA do CFC; versão consultada registrada em cada PT e no Apêndice B (confirmar na fonte)"],
    ["Natureza", "Trabalho acadêmico. NÃO é auditoria contratada e NÃO contém opinião profissional independente."],
    ["Declaração de uso de IA", "Trabalho produzido com apoio exclusivo de IA, conforme informado pelo aluno; o aluno deve verificar a conformidade com a política da disciplina e é responsável pelo conteúdo entregue."],
    ["Dados sintéticos", "A base de 520.180 lançamentos de 'Imóveis a comercializar' é SINTÉTICA; não são registros reais da EZTEC. Somente os totais da nota 7 e a divisão circulante/não circulante são dados reais usados como alvo."]], [4.2 * cm, W - 4.2 * cm]))
E += [PageBreak(), Paragraph("Legenda, critérios e resumo executivo", h1)]
E.append(tabela("Classe|Definição (enunciado, item 2)", [[k, CL[k][1]] for k in CL], [2 * cm, W - 2 * cm]))
E += [Spacer(1, 6), Paragraph("Resumo executivo", h2), Paragraph(esc(
    f"Conta de maior materialidade do ativo: Imóveis a comercializar, consolidado, R$ 3.125.834 mil (43,4% do ativo de R$ 7.196.637 mil; nota 7, p.51; balanço, p.20). "
    f"Materialidade global R$ {f(M['global_'])} mil (5% do LAIR), execução R$ {f(M['execucao'])} mil, trivial R$ {f(M['trivial'])} mil. "
    f"Base sintética: {R['linhas']:,} linhas; conciliação com a nota 7: diferença R$ {R['conciliacao_total']['diferenca_rs']:,.2f} totalmente explicada pelos 905 erros inseridos. "
    f"Testes de 100% detectaram todos os erros dos tipos E01-E09; a amostra MUS ({R['mus']['n_amostra']} itens) detectou 6 dos 60 erros de valor (E10). "
    f"Distorção potencial agregada sintética R$ {R['distorcao_potencial_total_rs']:,.2f}, acima da materialidade global. Fatos reais relevantes: POC e custo orçado (PAA); mais-valia e fiança da CAL; ganhos de R$ 46,5 mi nas vendas de AK14 e Tupi; encargos capitalizados acima da expectativa em R$ 9,7 mi; auditoria inicial.").replace("R$ 3.125.834", "R$ 3.125.834"), b)]
E += [Spacer(1, 6), Paragraph("Sumário dos papéis de trabalho", h2), tabela("Código|Título", [[p["cod"], p["titulo"]] for p in PT] + [["Apêndice A", "Matriz de cobertura das normas"], ["Apêndice B", "Fontes e versões das normas"], ["Apêndice C", "Programas de auditoria"], ["Apêndice D", "Conclusão integrada"]], [3 * cm, W - 3 * cm]), PageBreak()]
for p in PT: E += bloco(p)
# Apendice A
cov = [["NBC TA Estrutura Conceitual", "PT EC"], ["NBC TA 200", "PT 200"], ["NBC TA 210", "PT 210"], ["NBC TA 220", "PT 220"], ["NBC TA 230", "PT 230"], ["NBC TA 240", "PT 240"], ["NBC TA 250", "PT 250"], ["NBC TA 260", "PT 260"], ["NBC TA 265", "PT 265"],
       ["NBC TA 300", "PT 300"], ["NBC TA 315", "PT 315"], ["NBC TA 320", "PT 320 (planilha aba PT320)"], ["NBC TA 330", "PT 330"], ["NBC TA 402", "PT 402"], ["NBC TA 450", "PT 450 (aba PT450)"], ["NBC TA 500", "PT 500 (aba PT500)"], ["NBC TA 501", "PT 501"],
       ["NBC TA 505", "PT 505 (aba PT505)"], ["NBC TA 510", "PT 510"], ["NBC TA 520", "PT 520 (aba PT520)"], ["NBC TA 530", "PT 530 (aba PT530; resultados/amostra_mus_pt530.csv)"], ["NBC TA 540", "PT 540 (aba PT540)"], ["NBC TA 550", "PT 550"], ["NBC TA 560", "PT 560"],
       ["NBC TA 570", "PT 570 (aba PT570)"], ["NBC TA 580", "PT 580"], ["NBC TA 600", "PT 600 (dados_reais/nota9_controladas_2025.csv)"]]
E += [Paragraph("Apêndice A - Matriz de cobertura das normas", h1), tabela("Norma|Papel de trabalho e arquivos", cov, [5 * cm, W - 5 * cm]), PageBreak()]
# Apendice B
src = [["F1", "DFP 2025 EZ TEC (PDF completo: DFs, notas, relatório do auditor, parecer do Comitê)", "https://www.rad.cvm.gov.br/ENETWEB/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento=155329&CodigoTipoInstituicao=1", "23/10/2026 00:16 (informado pelo aluno)", "pp.3-77; usadas: 20-23, 26-27, 33, 40-68, 70-75", "2025 (comparativos 2024 e 2023)", "Fonte principal. Link CVM/RAD informado e validado pelo aluno (protocolo 155329). O PDF foi obtido pelo aluno no site da B3, página de empresas listadas: https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/empresas.htm (endereço informado pelo aluno; é a página de navegação, não o link direto do arquivo)."],
       ["F2", "Factsheet 2026 (RI EZTEC)", "https://api.mziq.com/mzfilemanager/v2/d/653fada3-cbcd-4015-9a94-2149f610a321/e524e863-f58b-e898-d005-fb0f2260d700?origin=2", "25/10/2026", "p.1", "2022-2025", "Confronto: ativo total e lucro coincidem com a DFP; rótulo 'dividends per share' parece ser o LPA (não usado)."],
       ["F3", "Índice do Formulário de Referência (RI EZTEC)", "https://api.mziq.com/mzfilemanager/v2/d/653fada3-cbcd-4015-9a94-2149f610a321/2e3efe24-5cd8-bbd0-94e2-77fcbcf1d958?origin=2", "25/10/2026", "índice", "rótulo '31/12/2026'", "Só o índice foi visível; conteúdo NÃO utilizado."],
       ["F4", "Notícia: guidance de lançamentos 2026", "https://financenews.com.br/2026/01/eztec-btg-considera-positivo-guidance-de-lancamentos/", "25/10/2026", "-", "2026", "Secundária; PT 560."],
       ["F5", "Notícia: resultados do 2T26", "https://visnoinvest.com.br/news/14606/eztec-eztc3-registra-lucro-de-r-1104-mi-no-2t26", "25/10/2026", "-", "2026", "Secundária; PT 560; números divergem de F6."],
       ["F6", "Análise Safra: 2T26", "https://oespecialista.safra.com.br/analise/eztec-eztc3-resultados-segundo-trimestre-2026/", "25/10/2026", "-", "2026", "Secundária; lucro divergente de F5."],
       ["F7", "Listagem de comunicados (agregador)", "https://investidor10.com.br/acoes/fatos-relevantes-comunicados?page=537", "25/10/2026", "-", "-", "DESCARTADA: itens não atribuíveis à EZTEC."],
       ["N1", "CFC - publicação NBC TA de auditoria (resoluções originais 2009)", "https://cfc.org.br/wp-content/uploads/2018/04/Publicacao_NBC_TA_AUDITORIA.pdf", "25/10/2026", "-", "-", "Numeração das normas."],
       ["N2", "CFC - tabela NBC TA (2016) com revisões", "https://cfc.org.br/wp-content/uploads/2016/02/NBC_TA_03112016.pdf", "25/10/2026", "-", "-", "Versões: 200 (R1), 220 (R2 em 2016), 230 (R1), 240 (R1), 260 (R2), 315 (R1), 500 (R1), 560 (R1), 580 (R1), 600 (R1)."],
       ["N3", "NBC TA 220 (R3) - texto CFC de 18/11/2021", "https://www.ibet.com.br/wp-content/uploads/2022/03/NBCTA220-R3.pdf", "25/10/2026", "-", "-", "Data do texto: 18/11/2021 (diferente da informação do aluno de 'final de 2023'; o CFC alterou itens pontuais depois, N4)."],
       ["N4", "CFC/CRC-MS: aprovação da NBC TA 600 (R2) em 25/10/2023 e ajustes da NBC TA 220 (R3)", "https://crcms.org.br/cfc-publica-as-revisoes-da-nbc-20-e-nbc-21-e-a-aprovacao-da-nbc-ta-600-r2-publicacoes-elevam-padroes-da-auditoria-contabil-no-brasil/", "25/10/2026", "-", "-", "Versão do PT 600."],
       ["N5", "CFC: audiência pública da NBC TA 600 (R2)", "https://cfc.org.br/noticias/audiencia-publica-envie-contribuicoes-para-a-minuta-da-nbc-ta-600-r2-e-alteracoes-decorrentes/", "25/10/2026", "-", "-", "Minuta cita vigência para períodos iniciados em ou após 01/01/2024; confirmar na norma final."]]
E += [Paragraph("Apêndice B - Fontes (endereço, data de acesso, documento, página, exercício) e versões das normas", h1),
      tabela("ID|Documento|Endereço|Acesso|Página|Exercício|Uso/observação", src, [.8 * cm, 3 * cm, 4.4 * cm, 1.7 * cm, 1.6 * cm, 1.4 * cm, W - 12.9 * cm]),
      Spacer(1, 6), Paragraph("Versões das NBC TA: apenas as indicadas em N2-N4 foram verificadas nesta sessão; as demais constam como 'a confirmar' e devem ser conferidas no portal do CFC (norma vigente em 31/12/2025). Nenhuma outra versão foi presumida.", b),
      Paragraph("Nome empresarial e código: a DFP e o RI 2026 mostram 'EZ TEC Empreendimentos e Participações S.A.' e EZTC3; não foi identificada alteração. Cadastro CVM/B3 e Formulário de Referência não foram consultados diretamente.", b), PageBreak()]
# Apendice C
prog = [("Receitas (POC)", "Ocorrência, precisão, corte", ["Obter mapa de vendas, contratos, distratos e orçamentos por empreendimento [PL]", "Recalcular POC por unidade e a receita apropriada [PL]; sensibilidade agregada [RP/PT 540]", "Testar cancelamentos de vendas (+55%, nota 19) e provisão de distratos de R$ 10.550 mil [PL]", "Testes de corte nas medições do fim do ano [PL; análogo SD: T03]", "Reconciliar receita da nota 19 com a DRE [RP: conferido]"]),
        ("Disponibilidades", "Existência, direitos, classificação", ["Confirmação bancária de saldos e aplicações [PL; PT 505]", "Conciliações bancárias de 31/12/2025 [PL]", "Verificar prazo e liquidez das LFs de R$ 466.557 mil, descritas como de curto prazo [PL]", "Recálculo de rendimentos (97%-103% do CDI) [PL]", "Composição da nota 5 = balanço [RP: confere]"]),
        ("Estoques", "Existência, valoração, corte, classificação", ["Testes de 100% sobre base sintética (T02-T10) [SD]", "MUS documental de 483 itens [SD]", "Roll-forward de encargos e expectativas [RP/PT 520]", "Inspeção física de obras e terrenos; matrículas; VRL [PL]", "Conciliação razão x DFP [SD: diferença explicada; RP: nota 7 = balanço]"]),
        ("Imobilizado (R$ 45.743 mil, 0,64% do ativo, acima da PM de R$ 19.551 mil por 2,3x)", "Existência, valoração", ["Roll-forward (36.152+2.959+21.775-12.042 = 45.743+3.101) [RP: fechou sem diferença]", "Teste de adições relevantes e de baixas [PL]", "Recálculo de depreciação (vidas úteis de 5 e 10 anos, nota 2.10) [PL]", "Conclusão: risco baixo; programa reduzido, pois a conta não é significativa em risco, apesar de superar a PM"]),
        ("Passivos", "Completude, classificação, apresentação", ["Roll-forward de empréstimos e debêntures/CRI [RP: sem diferença]", "Confirmação com credores e agente fiduciário; escrituras [PL]", "Covenants: recomputação parcial [RP], completa [PL]", "Provisões (R$ 6.469 mil) e perdas possíveis: cartas de advogados [PL]", "Fornecedores (R$ 50.909 mil), terrenos a pagar, tributos diferidos [PL; RP: alíquota efetiva 8,97% analisada]"]),
        ("Estimativas", "Valoração", ["POC/custo orçado: sensibilidade [RP]; revisão retrospectiva e especialista [PL]", "Provisão de distratos, AVP (NTN-B), VRL, mais-valia da CAL (R$ 51.394 mil) [PL]", "Evidências de viés da administração [PL]"])]
E += [Paragraph("Apêndice C - Programas de auditoria", h1), tabela("Área|Afirmações|Passos e status", [[a, b_, "\n".join("• " + x for x in ps)] for a, b_, ps in prog], [3.2 * cm, 3 * cm, W - 6.2 * cm]), PageBreak()]
# Apendice D
cnc = [f"Este dossiê não emite opinião profissional independente. Os procedimentos que dependem de acesso a registros, pessoas, confirmações e inspeções físicas permanecem PLANEJADOS; os executados usaram a DFP 2025 (evidência pública) ou dados sintéticos, sempre identificados.",
       "Riscos significativos (PT 315): receita/POC com custo orçado (+1,43% no orçado consome a PM de R$ 19.551 mil; sensibilidade +5% = -R$ 65,9 mi); estoques (43,4% do ativo; expectativa de encargos capitalizados acima em R$ 9,7 mi, a investigar); transações com a CAL (mais-valia, fiança de R$ 200 mi) e vendas de participações (ganhos de R$ 46,5 mi líquidos); partes relacionadas; lançamentos manuais.",
       "Evidências públicas: a DFP é internamente consistente nas verificações feitas (balanços, notas e movimentações recalculadas, com diferenças de R$ 1 mil e R$ 11 mil, abaixo do trivial). Os covenants (-0,08) são reproduzidos em aproximação; o índice 13,83 não foi reproduzido. Liquidez ampla e FCO positivo não sugerem dúvida sobre continuidade, mas a decisão depende de informações internas.",
       f"Teste na base sintética: 100% dos erros E01-E09 foram detectados por testes analíticos (com falsos positivos explicados); a amostra MUS detectou 10% dos erros de valor (E10); limite superior Stringer R$ {R['mus']['limite_superior_stringer_rs']:,.0f} acima da PM, o que, se fossem dados reais, exigiria ampliação ou ajuste. O agregado das distorções sintéticas (R$ {R['distorcao_potencial_total_rs']:,.0f}) excede a materialidade global (R$ {M['global_']:,.0f} mil).",
       "Limitações principais: ausência de razão, orçamentos e documentos reais; fontes secundárias frágeis (divergência no 2T26; listagem descartada); versões de algumas NBC TA a confirmar; relatório do auditor anterior e DFP 2024 originais não acessados; Formulário de Referência não acessado; trabalho individual sem revisão independente.",
       "Verificações do aluno antes da entrega: confirmar a independência (PT 200); confirmar versões das normas; consultar IPE/CVM para eventos subsequentes (PT 560); criar o repositório e verificar o acesso do professor; decidir se a política da disciplina admite o uso de IA e como declará-lo."]
E += [Paragraph("Apêndice D - Conclusão integrada", h1)] + [Paragraph("• " + esc(c), S("cb", fontSize=8, leading=11, spaceAfter=5)) for c in cnc]
doc.build(E); print("PDF", out)
