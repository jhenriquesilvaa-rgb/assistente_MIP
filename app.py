from datetime import date, datetime
import re
from typing import List
from urllib.parse import quote

import pandas as pd
import requests
import streamlit as st

from rules_operacoes_v10 import (
    RULES_VERSION,
    get_operacoes_rules,
    get_sadipem_field_matrix,
)

from decision_engine_v10 import (
    evaluate_operation,
    build_review_dataframe,
    compare_mip_text_to_rules,
    extract_section_titles,
    extract_change_signals,
    detect_text_from_uploaded_file,
    build_sadipem_action_plan,
    build_conditional_checklist_dataframe,
)

st.set_page_config(page_title="MIP PVL Assistant v12.6.2", layout="wide")

st.title("MIP PVL Assistant v12.6.2")
st.caption("Versão endurecida com pesquisa PVL/API corrigida: filtros explícitos, seleção persistente e avaliação confiável do PVL localizado.")

operacoes_rules = get_operacoes_rules()
sadipem_df = get_sadipem_field_matrix()

with st.sidebar:
    st.subheader("Base normativa")
    st.write(f"Versão da base: **{RULES_VERSION}**")
    st.write("Foco da versão: preservar o que já foi construído e corrigir de forma robusta a pesquisa e avaliação do PVL.")

SADIPEM_PVL_BASE_URL = "https://apidatalake.tesouro.gov.br/ords/sadipem/tt/pvl"


def build_checklist_catalog_local():
    catalog = {}
    for op_code in operacoes_rules.keys():
        data_jan = date(date.today().year, 3, 1)
        data_pos = date(date.today().year, 4, 1)
        jan_df = build_conditional_checklist_dataframe(op_code, data_jan, operacoes_rules)
        pos_df = build_conditional_checklist_dataframe(op_code, data_pos, operacoes_rules)
        for janela, df in [('janeiro', jan_df), ('apos_3003', pos_df)]:
            if df is None or df.empty:
                continue
            for _, row in df.iterrows():
                aba = row.get('aba', 'Geral')
                item = row.get('item_checklist', '')
                catalog.setdefault(op_code, {}).setdefault(aba, {}).setdefault(janela, [])
                if item and item not in catalog[op_code][aba][janela]:
                    catalog[op_code][aba][janela].append(item)
    return catalog


checklist_catalog = build_checklist_catalog_local()

if 'pvl_search_results' not in st.session_state:
    st.session_state.pvl_search_results = []
if 'pvl_selected_key' not in st.session_state:
    st.session_state.pvl_selected_key = None


def normalizar_numero_pvl(raw: str) -> str:
    if not raw:
        return ""
    return re.sub(r"[^0-9A-Za-z/_.-]", "", raw.strip())


def parse_data(valor):
    if not valor:
        return None
    txt = str(valor).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%d/%m/%Y"):
        try:
            return datetime.strptime(txt[:26], fmt)
        except Exception:
            pass
    return None


def periodo_referencia(data_obj):
    if not data_obj:
        return "janeiro"
    return "janeiro" if data_obj.month <= 3 else "apos_3003"


def inferir_familia_por_tipo(tipo_operacao: str) -> str:
    t = (tipo_operacao or "").lower()
    if "reestrutura" in t or "recomposi" in t:
        return "reestruturacao"
    if "antecipação de receita orçamentária" in t or "antecipacao de receita orcamentaria" in t or "aro" in t:
        return "aro"
    if "regulariza" in t:
        return "regularizacao"
    if "consórcio" in t or "consorcio" in t:
        return "consorcio"
    if "garantia" in t and ("estado" in t or "município" in t or "municipio" in t):
        return "garantia_ente"
    if "lc 156" in t:
        return "lc_156"
    if "lc 159" in t:
        return "lc_159"
    if "lc 178" in t:
        return "lc_178"
    if "lc 212" in t:
        return "lc_212"
    if "extern" in t:
        return "externa"
    return "interna"


def grupo_status(status: str) -> str:
    s = (status or "").lower()
    if any(x in s for x in ["preenchimento", "assinado pelo interessado"]):
        return "inicial"
    if "retificação" in s or "retificacao" in s:
        return "retificacao"
    if "análise" in s or "analise" in s:
        return "analise"
    if any(x in s for x in ["deferido", "encaminhado pgfn"]):
        return "final_favoravel"
    if any(x in s for x in ["indeferido", "pendente de regularização", "pendente de regularizacao"]):
        return "final_desfavoravel"
    if any(x in s for x in ["arquivado", "cancelado"]):
        return "arquivamento"
    if any(x in s for x in ["suspenso", "sobrestado"]):
        return "suspensao"
    return "nao_classificado"


def _first_nonempty(item: dict, keys: List[str]):
    for key in keys:
        if key in item and item.get(key) not in (None, "", [], {}):
            return item.get(key)
    return None


def _request_items(url: str):
    resp = requests.get(url, headers={"accept": "application/json"}, timeout=25)
    if not resp.ok:
        return []
    data = resp.json()
    return data.get("items", data if isinstance(data, list) else [])


def consultar_pvl_api_com_filtros(numero_pvl: str = "", ente: str = "", uf: str = "", status: str = "", tipo_operacao: str = "", data_inicial=None, data_final=None):
    filtros = []
    numero_norm = normalizar_numero_pvl(numero_pvl)
    if numero_norm:
        numero_q = quote(numero_norm)
        urls_numero = [
            f"{SADIPEM_PVL_BASE_URL}?num_pvl=eq.{numero_q}",
            f"{SADIPEM_PVL_BASE_URL}?num_processo=eq.{numero_q}",
            f"{SADIPEM_PVL_BASE_URL}?num_pvl=like.*{numero_q}*",
            f"{SADIPEM_PVL_BASE_URL}?num_processo=like.*{numero_q}*",
        ]
        for url in urls_numero:
            items = _request_items(url)
            if items:
                return {"ok": True, "items": items, "url": url, "modo": "numero"}
        return {"ok": False, "erro": "Nenhum PVL encontrado para o número/processo informado."}

    if ente:
        filtros.append(f"interessado=like.*{quote(ente)}*")
    if uf:
        filtros.append(f"uf=eq.{quote(uf)}")
    if status:
        filtros.append(f"status=like.*{quote(status)}*")
    if tipo_operacao:
        filtros.append(f"tipo_operacao=like.*{quote(tipo_operacao)}*")
    if data_inicial:
        filtros.append(f"data_status=gte.{data_inicial.strftime('%Y-%m-%d')}")
    if data_final:
        filtros.append(f"data_status=lte.{data_final.strftime('%Y-%m-%d')}")

    if not filtros:
        return {"ok": False, "erro": "Informe ao menos um filtro de pesquisa. A consulta sem filtro foi bloqueada para evitar retorno massivo da base pública."}

    url = f"{SADIPEM_PVL_BASE_URL}?{'&'.join(filtros)}"
    items = _request_items(url)
    if not items:
        return {"ok": False, "erro": "Nenhum PVL encontrado com os filtros informados."}
    return {"ok": True, "items": items[:200], "url": url, "modo": "filtros"}


def extrair_dados_pvl(item: dict):
    return {
        "id_pleito": _first_nonempty(item, ["id_pleito", "idPleito"]),
        "num_pvl": _first_nonempty(item, ["num_pvl", "numero_pvl", "nu_pvl"]),
        "num_processo": _first_nonempty(item, ["num_processo", "numero_processo", "processo"]),
        "interessado": _first_nonempty(item, ["interessado", "nome_interessado", "ente"]),
        "uf": _first_nonempty(item, ["uf", "sigla_uf"]),
        "tipo_interessado": _first_nonempty(item, ["tipo_interessado", "tipo_ente"]),
        "tipo_operacao": _first_nonempty(item, ["tipo_operacao", "operacao", "descricao_tipo_operacao"]),
        "status": _first_nonempty(item, ["status", "status_pvl", "descricao_status"]),
        "credor": _first_nonempty(item, ["instituicao_credora", "credor", "nome_credor"]),
        "data_status": _first_nonempty(item, ["data_status", "dt_status"]),
        "data_protocolo": _first_nonempty(item, ["data_protocolo", "dt_protocolo"]),
        "finalidade": _first_nonempty(item, ["finalidade", "descricao_finalidade"]),
        "valor": _first_nonempty(item, ["valor", "valor_operacao"]),
        "moeda": _first_nonempty(item, ["moeda", "descricao_moeda"]),
        "tipo_credor": _first_nonempty(item, ["tipo_credor", "categoria_credor"]),
        "pvl_assoc_divida": _first_nonempty(item, ["pvl_assoc_divida", "associado_divida"]),
        "pvl_contratado_credor": _first_nonempty(item, ["pvl_contratado_credor", "contratado_credor"]),
        "raw": item,
    }


def campos_presentes_ausentes(dados: dict):
    presentes, ausentes = [], []
    for k, v in dados.items():
        if k == "raw":
            continue
        if v in (None, "", [], {}):
            ausentes.append(k)
        else:
            presentes.append(k)
    return presentes, ausentes


def coletar_checklist_esperado_calibrado(familia: str, data_status_str: str):
    fam = checklist_catalog.get(familia, {})
    data_obj = parse_data(data_status_str)
    janela = periodo_referencia(data_obj)
    itens = []
    for aba, fases in fam.items():
        lista = fases.get(janela) or fases.get("janeiro") or []
        for item in lista:
            itens.append(f"[{aba}] {item}")
    if data_obj and data_obj.month <= 3:
        itens.append("[Documentos] Entre 01/01 e 30/03, revisar exigências do exercício anterior fechado e documentos sazonais da modalidade.")
    return itens or ["Não foi possível montar checklist esperado para a família identificada."]


def avaliar_campos_pvl(dados: dict) -> pd.DataFrame:
    familia = inferir_familia_por_tipo(dados.get("tipo_operacao"))
    data_obj = parse_data(dados.get("data_status"))
    janela = periodo_referencia(data_obj)
    linhas = []
    catalogo = checklist_catalog.get(familia, {})
    for aba, regras in catalogo.items():
        for item in regras.get(janela, regras.get("janeiro", [])):
            status_campo = "Não verificável pela API"
            evidencia = ""
            item_low = item.lower()
            if "rreo" in item_low:
                status_campo = "Depende de documento/anexo"
                evidencia = "A API pública do PVL não comprova sozinha o conteúdo do RREO."
            elif "rgf" in item_low:
                status_campo = "Depende de documento/anexo"
                evidencia = "A API pública do PVL não comprova sozinha o conteúdo do RGF."
            elif "declara" in item_low and dados.get("status"):
                status_campo = "Provavelmente exigível"
                evidencia = f"Status atual: {dados.get('status')}"
            elif "document" in aba.lower() or "document" in item_low:
                status_campo = "Depende de documento/anexo"
                evidencia = "Necessita conferência documental no SADIPEM/SEI."
            linhas.append({
                "aba_sadipem": aba,
                "item_mip": item,
                "avaliacao": status_campo,
                "evidencia_publica": evidencia,
            })
    if not linhas:
        linhas.append({
            "aba_sadipem": "Geral",
            "item_mip": "Sem checklist calibrado para a família identificada.",
            "avaliacao": "Não verificável pela API",
            "evidencia_publica": "",
        })
    return pd.DataFrame(linhas)


def diagnosticar_item_pvl(item: dict, fonte_api: str):
    dados = extrair_dados_pvl(item)
    familia = inferir_familia_por_tipo(dados.get("tipo_operacao"))
    data_obj = parse_data(dados.get("data_status"))
    presentes, ausentes = campos_presentes_ausentes(dados)
    checklist = coletar_checklist_esperado_calibrado(familia, dados.get("data_status"))
    grupo = grupo_status(dados.get("status"))

    pendencias = []
    inconsistencias = []
    if grupo == "retificacao":
        pendencias.append("O PVL está em retificação; há indício de exigência não integralmente atendida.")
    if grupo == "analise":
        pendencias.append("O PVL está em análise; ainda pode receber exigências complementares.")
    if grupo == "final_desfavoravel":
        inconsistencias.append("O status atual é materialmente desfavorável ao pleito e exige revisão do enquadramento ou saneamento.")
    if data_obj and data_obj.month <= 3:
        pendencias.append("Como a data do status está no início do exercício, revisar documentos sensíveis ao exercício anterior fechado.")
    if not dados.get("tipo_operacao"):
        inconsistencias.append("Campo tipo_operacao não retornado; a inferência normativa ficou prejudicada.")
    if not dados.get("status"):
        inconsistencias.append("Campo status não retornado; o diagnóstico fica prejudicado.")

    dados_pleito = [
        f"Número do PVL: {dados.get('num_pvl') or 'Não informado'}",
        f"Processo: {dados.get('num_processo') or 'Não informado'}",
        f"Interessado: {dados.get('interessado') or 'Não informado'} / UF: {dados.get('uf') or 'N/I'}",
        f"Tipo do interessado: {dados.get('tipo_interessado') or 'Não informado'}",
        f"Tipo de operação: {dados.get('tipo_operacao') or 'Não informado'}",
        f"Família inferida: {familia}",
        f"Status atual: {dados.get('status') or 'Não informado'} / Grupo de status: {grupo}",
        f"Data do status: {dados.get('data_status') or 'Não informada'} / Data de protocolo: {dados.get('data_protocolo') or 'Não informada'}",
        f"Credor: {dados.get('credor') or 'Não informado'}",
        f"Valor/moeda: {dados.get('valor') or 'Não informado'} / {dados.get('moeda') or 'N/I'}",
        f"Campos públicos presentes: {len(presentes)} / Campos públicos ausentes: {len(ausentes)}",
    ]

    if not pendencias:
        pendencias.append("Nenhuma pendência provável inferida apenas pelos dados públicos; ainda é necessária conferência documental.")
    if not inconsistencias:
        inconsistencias.append("Nenhuma inconsistência evidente inferida apenas com base nos dados públicos disponíveis.")

    return {
        "ok": True,
        "dados_pleito": dados_pleito,
        "checklist_esperado": checklist,
        "pendencias_provaveis": pendencias,
        "inconsistencias_detectadas": inconsistencias,
        "dados_brutos": dados.get("raw", {}),
        "campos_presentes": presentes,
        "campos_ausentes": ausentes,
        "familia_identificada": familia,
        "fonte_api": fonte_api,
        "avaliacao_campos_df": avaliar_campos_pvl(dados),
    }


def render_operacoes_tab():
    st.subheader("Operações")
    st.caption("Escolha o tipo de operação e a data para obter documentos, canal de envio, fluxo e observações do MIP.")
    c1, c2 = st.columns([2, 1])
    with c1:
        op_label = st.selectbox("Tipo de operação", options=list(operacoes_rules.keys()), format_func=lambda x: operacoes_rules[x]["label"])
    with c2:
        data_ref = st.date_input("Data de referência", value=date.today(), format="DD/MM/YYYY")
    result = evaluate_operation(op_label, data_ref, operacoes_rules)
    regra = result["regra"]
    g1, g2 = st.columns(2)
    with g1:
        with st.container(border=True):
            st.markdown("### Enquadramento")
            st.write(f"**Canal principal:** {regra.get('canal_principal')}")
            st.write(f"**Origem do envio:** {regra.get('origem_envio')}")
            st.write(f"**Família lógica:** {regra.get('family')}")
            st.write(f"**Exige garantia da União:** {regra.get('garantia_uniao')}")
    with g2:
        with st.container(border=True):
            st.markdown("### Observações do período")
            for item in result.get("observacoes", []):
                st.markdown(f"- {item}")
    st.markdown("### Documentos e providências")
    for item in regra.get("documentos_base", []):
        st.markdown(f"- {item}")
    checklist_df = build_conditional_checklist_dataframe(op_label, data_ref, operacoes_rules)
    if not checklist_df.empty:
        st.markdown("### Checklist condicional")
        st.dataframe(checklist_df, use_container_width=True, hide_index=True)


def render_upload_tab():
    st.subheader("Upload do MIP")
    st.caption("Envie o MIP mais recente para verificar se a base normativa do sistema continua aderente e mapear ajustes necessários.")
    uploaded = st.file_uploader("Upload do MIP", type=["pdf", "txt", "md"], accept_multiple_files=False)
    if st.button("Comparar com a base atual") and uploaded is not None:
        txt, src = detect_text_from_uploaded_file(uploaded)
        comparison = compare_mip_text_to_rules(txt, operacoes_rules)
        review_df = build_review_dataframe(comparison, extract_section_titles(txt), extract_change_signals(txt))
        st.write(f"Fonte: {src}")
        st.dataframe(review_df, use_container_width=True, hide_index=True)
    elif uploaded is None:
        st.info("Envie um PDF/TXT/MD do MIP para comparar a base atual com a nova edição.")


def render_sadipem_tab():
    st.subheader("SADIPEM")
    st.caption("Escolha a operação e a data para ver o que deve ser usado nas abas do SADIPEM, inclusive documentos e referências contábeis como RREO e RGF.")
    s1, s2 = st.columns([2, 1])
    with s1:
        op_sadipem = st.selectbox("Tipo de operação", options=list(operacoes_rules.keys()), key="sadipem_select", format_func=lambda x: operacoes_rules[x]["label"])
    with s2:
        data_ref_sadipem = st.date_input("Data de referência", value=date.today(), key="sadipem_date", format="DD/MM/YYYY")
    plano = pd.DataFrame(build_sadipem_action_plan(op_sadipem, data_ref_sadipem, sadipem_df, operacoes_rules))
    checklist_df = build_conditional_checklist_dataframe(op_sadipem, data_ref_sadipem, operacoes_rules)
    filtro = sadipem_df[sadipem_df["operacao_codigo"] == op_sadipem].copy() if "operacao_codigo" in sadipem_df.columns else pd.DataFrame()
    if not checklist_df.empty:
        st.markdown("### Checklist condicional por modalidade")
        st.dataframe(checklist_df, use_container_width=True, hide_index=True)
    if not plano.empty:
        st.markdown("### Plano de ação por aba/campo")
        st.dataframe(plano, use_container_width=True, hide_index=True)
    if not filtro.empty:
        st.markdown("### Matriz estrutural no SADIPEM")
        st.dataframe(filtro, use_container_width=True, hide_index=True)


def render_pesquisa_pvl_tab():
    st.subheader("Pesquisa PVL/API")
    st.caption("Pesquise por número, processo e filtros adicionais. A consulta sem filtro foi bloqueada para evitar retorno massivo da base pública.")

    col1, col2, col3 = st.columns(3)
    with col1:
        numero_pvl = st.text_input("Número do PVL ou processo", placeholder="Ex.: 17944.001693/2026-48")
    with col2:
        ente = st.text_input("Interessado/ente", placeholder="Ex.: Recife")
    with col3:
        uf = st.text_input("UF", placeholder="Ex.: PE")

    col4, col5, col6 = st.columns(3)
    with col4:
        status = st.text_input("Status", placeholder="Ex.: Deferido")
    with col5:
        tipo_operacao = st.text_input("Tipo de operação", placeholder="Ex.: interna")
    with col6:
        aplicar_periodo = st.checkbox("Filtrar por período de data_status")

    data_inicial = data_final = None
    if aplicar_periodo:
        c7, c8 = st.columns(2)
        with c7:
            data_inicial = st.date_input("Data inicial", value=date(date.today().year, 1, 1), key="pvl_dt_ini")
        with c8:
            data_final = st.date_input("Data final", value=date.today(), key="pvl_dt_fim")

    if st.button("Pesquisar PVL", type="primary"):
        with st.spinner("Consultando API pública do SADIPEM..."):
            consulta = consultar_pvl_api_com_filtros(numero_pvl, ente, uf.upper().strip(), status, tipo_operacao, data_inicial, data_final)
        if not consulta.get("ok"):
            st.session_state.pvl_search_results = []
            st.session_state.pvl_selected_key = None
            st.error(consulta.get("erro", "Não foi possível localizar PVL com os filtros informados."))
        else:
            resultados = consulta.get("items", [])
            st.session_state.pvl_search_results = resultados
            st.session_state.pvl_selected_key = None
            st.success(f"{len(resultados)} PVL(s) localizado(s) na API pública.")
            st.caption(f"Consulta usada: {consulta.get('url')}")

    resultados = st.session_state.pvl_search_results
    if resultados:
        rows = []
        opcoes = []
        mapa = {}
        for i, item in enumerate(resultados):
            d = extrair_dados_pvl(item)
            chave = d.get("num_pvl") or d.get("num_processo") or f"linha_{i}"
            label = f"{chave} | {d.get('interessado') or 'Sem interessado'} | {d.get('uf') or 'UF?'} | {d.get('status') or 'Sem status'}"
            opcoes.append(label)
            mapa[label] = item
            rows.append({
                "num_pvl": d.get("num_pvl"),
                "num_processo": d.get("num_processo"),
                "interessado": d.get("interessado"),
                "uf": d.get("uf"),
                "tipo_operacao": d.get("tipo_operacao"),
                "status": d.get("status"),
                "data_status": d.get("data_status"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        selecionado = st.selectbox("Selecione o PVL para avaliar", opcoes, key="pvl_select_box")
        st.session_state.pvl_selected_key = selecionado

        if st.button("Avaliar PVL", use_container_width=True):
            item = mapa.get(st.session_state.pvl_selected_key)
            if not item:
                st.error("Selecione um PVL válido para avaliação.")
                return
            resultado = diagnosticar_item_pvl(item, "resultado em memória da pesquisa API")
            c1, c2 = st.columns(2)
            blocos = [
                ("Dados do pleito", "dados_pleito"),
                ("Checklist esperado", "checklist_esperado"),
                ("Pendências prováveis", "pendencias_provaveis"),
                ("Inconsistências detectadas", "inconsistencias_detectadas"),
            ]
            for i, (titulo, chave) in enumerate(blocos):
                with (c1 if i % 2 == 0 else c2):
                    with st.container(border=True):
                        st.markdown(f"### {titulo}")
                        for item_txt in resultado.get(chave, []):
                            st.markdown(f"- {item_txt}")
            st.markdown("### Avaliação detalhada por aba/campo")
            st.dataframe(resultado["avaliacao_campos_df"], use_container_width=True, hide_index=True)
            with st.expander("Campos públicos presentes e ausentes"):
                st.markdown("### Presentes")
                for item_txt in resultado.get("campos_presentes", []):
                    st.markdown(f"- {item_txt}")
                st.markdown("### Ausentes")
                for item_txt in resultado.get("campos_ausentes", []):
                    st.markdown(f"- {item_txt}")
            with st.expander("Dados públicos retornados pela API"):
                st.caption(f"Fonte: {resultado.get('fonte_api')}")
                st.json(resultado.get("dados_brutos", {}))


aba1, aba2, aba3, aba4 = st.tabs(["Operações", "Upload do MIP", "SADIPEM", "Pesquisa PVL/API"])
with aba1:
    render_operacoes_tab()
with aba2:
    render_upload_tab()
with aba3:
    render_sadipem_tab()
with aba4:
    render_pesquisa_pvl_tab()
