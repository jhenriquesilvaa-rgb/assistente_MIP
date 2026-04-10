from datetime import date, datetime
import io
import re
from typing import Dict, Any, List

import pandas as pd
import requests
import streamlit as st

from rules_operacoes_v10 import (
    RULES_VERSION,
    build_operacoes_df,
    get_operacoes_rules,
    get_sadipem_field_matrix,
    build_checklist_catalog,
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

st.set_page_config(page_title="MIP PVL Assistant v12.6.0", layout="wide")

st.title("MIP PVL Assistant v12.6.0")
st.caption("Arquitetura redesenhada com quatro abas funcionais: Operações, Upload do MIP, SADIPEM e Pesquisa PVL/API.")

operacoes_rules = get_operacoes_rules()
operacoes_df = build_operacoes_df()
sadipem_df = get_sadipem_field_matrix()
checklist_catalog = build_checklist_catalog()

with st.sidebar:
    st.subheader("Base normativa")
    st.write(f"Versão da base: **{RULES_VERSION}**")
    st.write("Foco da versão: arquitetura redesenhada por função de trabalho, com resgate da avaliação do PVL e exclusão da aba Base tabular.")

# ============================
# Utilidades PVL/API
# ============================
SADIPEM_PVL_BASE_URL = "https://apidatalake.tesouro.gov.br/ords/sadipem/tt/pvl"


def normalizar_numero_pvl(raw: str) -> str:
    if not raw:
        return ""
    return re.sub(r"[^0-9A-Za-z/_.-]", "", raw.strip())


def parse_data(valor):
    if not valor:
        return None
    txt = str(valor).strip()
    for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%d/%m/%Y'):
        try:
            return datetime.strptime(txt[:26], fmt)
        except Exception:
            pass
    return None


def periodo_referencia(data_obj):
    if not data_obj:
        return 'janeiro'
    md = data_obj.month * 100 + data_obj.day
    if md <= 331:
        return 'janeiro'
    return 'apos_3003'


def inferir_familia_por_tipo(tipo_operacao: str) -> str:
    t = (tipo_operacao or '').lower()
    if 'reestrutura' in t or 'recomposi' in t:
        return 'reestruturacao'
    if 'antecipação de receita orçamentária' in t or 'antecipacao de receita orcamentaria' in t or 'aro' in t:
        return 'aro'
    if 'regulariza' in t:
        return 'regularizacao'
    if 'consórcio' in t or 'consorcio' in t:
        return 'consorcio'
    if 'garantia' in t and ('estado' in t or 'município' in t or 'municipio' in t):
        return 'garantia_ente'
    if 'lc 156' in t:
        return 'lc_156'
    if 'lc 159' in t:
        return 'lc_159'
    if 'lc 178' in t:
        return 'lc_178'
    if 'lc 212' in t:
        return 'lc_212'
    if 'extern' in t:
        return 'externa'
    return 'interna'


def grupo_status(status: str) -> str:
    s = (status or '').lower()
    if any(x in s for x in ['preenchimento', 'assinado pelo interessado']):
        return 'inicial'
    if 'retificação' in s or 'retificacao' in s:
        return 'retificacao'
    if 'análise' in s or 'analise' in s:
        return 'analise'
    if any(x in s for x in ['deferido', 'encaminhado pgfn']):
        return 'final_favoravel'
    if any(x in s for x in ['indeferido', 'pendente de regularização', 'pendente de regularizacao']):
        return 'final_desfavoravel'
    if any(x in s for x in ['arquivado', 'cancelado']):
        return 'arquivamento'
    if any(x in s for x in ['suspenso', 'sobrestado']):
        return 'suspensao'
    return 'nao_classificado'


def consultar_pvl_api(numero_pvl: str):
    numero = normalizar_numero_pvl(numero_pvl)
    if not numero:
        return {'ok': False, 'erro': 'Número do PVL inválido.'}
    candidatos = [
        f"{SADIPEM_PVL_BASE_URL}?num_pvl=eq.{numero}",
        f"{SADIPEM_PVL_BASE_URL}?num_processo=eq.{numero}",
        f"{SADIPEM_PVL_BASE_URL}?like_num_pvl={numero}",
    ]
    headers = {'accept': 'application/json'}
    last_error = None
    for url in candidatos:
        try:
            resp = requests.get(url, headers=headers, timeout=25)
            if resp.ok:
                data = resp.json()
                items = data.get('items', data if isinstance(data, list) else [])
                if items:
                    return {'ok': True, 'items': items, 'url': url}
            last_error = f'HTTP {resp.status_code}'
        except Exception as e:
            last_error = str(e)
    return {'ok': False, 'erro': last_error or 'PVL não localizado na API pública.'}


def extrair_dados_pvl(item: dict):
    return {
        'id_pleito': item.get('id_pleito'),
        'num_pvl': item.get('num_pvl'),
        'num_processo': item.get('num_processo'),
        'interessado': item.get('interessado'),
        'uf': item.get('uf'),
        'tipo_interessado': item.get('tipo_interessado'),
        'tipo_operacao': item.get('tipo_operacao'),
        'status': item.get('status'),
        'credor': item.get('instituicao_credora') or item.get('credor'),
        'data_status': item.get('data_status'),
        'data_protocolo': item.get('data_protocolo'),
        'finalidade': item.get('finalidade'),
        'valor': item.get('valor'),
        'moeda': item.get('moeda'),
        'tipo_credor': item.get('tipo_credor'),
        'pvl_assoc_divida': item.get('pvl_assoc_divida'),
        'pvl_contratado_credor': item.get('pvl_contratado_credor'),
    }


def campos_presentes_ausentes(dados: dict):
    presentes, ausentes = [], []
    for k, v in dados.items():
        if v in (None, '', [], {}):
            ausentes.append(k)
        else:
            presentes.append(k)
    return presentes, ausentes


def coletar_checklist_esperado_calibrado(familia: str, data_status_str: str) -> List[str]:
    fam = checklist_catalog.get(familia, {})
    data_obj = parse_data(data_status_str)
    janela = periodo_referencia(data_obj)
    itens = []
    for aba, fases in fam.items():
        lista = fases.get(janela) or fases.get('janeiro') or []
        for item in lista:
            itens.append(f'[{aba}] {item}')
    if data_obj and data_obj.month <= 3:
        itens.append('[Documentos] Entre 01/01 e 30/03, revisar exigências do exercício anterior fechado e documentos sazonais da modalidade.')
    return itens or ['Não foi possível montar checklist esperado para a família identificada.']


def avaliar_campos_pvl(dados: dict) -> pd.DataFrame:
    familia = inferir_familia_por_tipo(dados.get('tipo_operacao'))
    data_obj = parse_data(dados.get('data_status'))
    janela = periodo_referencia(data_obj)
    linhas = []
    catalogo = checklist_catalog.get(familia, {})
    for aba, regras in catalogo.items():
        for item in regras.get(janela, regras.get('janeiro', [])):
            status_campo = 'Não verificável pela API'
            evidencia = ''
            item_low = item.lower()
            if 'rreo' in item_low and dados.get('data_status'):
                status_campo = 'Depende de documento/anexo'
                evidencia = 'A API pública do PVL não comprova sozinha o conteúdo do RREO.'
            elif 'rgf' in item_low and dados.get('data_status'):
                status_campo = 'Depende de documento/anexo'
                evidencia = 'A API pública do PVL não comprova sozinha o conteúdo do RGF.'
            elif 'declara' in item_low and dados.get('status'):
                status_campo = 'Provavelmente exigível'
                evidencia = f"Status atual: {dados.get('status')}"
            elif 'document' in aba.lower() or 'document' in item_low:
                status_campo = 'Depende de documento/anexo'
                evidencia = 'Necessita conferência documental no SADIPEM/SEI.'
            linhas.append({
                'aba_sadipem': aba,
                'item_mip': item,
                'avaliacao': status_campo,
                'evidencia_publica': evidencia,
            })
    if not linhas:
        linhas.append({
            'aba_sadipem': 'Geral',
            'item_mip': 'Sem checklist calibrado para a família identificada.',
            'avaliacao': 'Não verificável pela API',
            'evidencia_publica': '',
        })
    return pd.DataFrame(linhas)


def diagnosticar_pvl_real(numero_pvl: str):
    consulta = consultar_pvl_api(numero_pvl)
    if not consulta.get('ok'):
        return {'ok': False, 'erro': consulta.get('erro', 'Falha na consulta do PVL.')}
    item = consulta['items'][0]
    dados = extrair_dados_pvl(item)
    familia = inferir_familia_por_tipo(dados.get('tipo_operacao'))
    data_obj = parse_data(dados.get('data_status'))
    presentes, ausentes = campos_presentes_ausentes(dados)
    checklist = coletar_checklist_esperado_calibrado(familia, dados.get('data_status'))
    grupo = grupo_status(dados.get('status'))

    pendencias = []
    inconsistencias = []
    if grupo == 'retificacao':
        pendencias.append('O PVL está em retificação; há indício de exigência não integralmente atendida.')
    if grupo == 'analise':
        pendencias.append('O PVL está em análise; ainda pode receber exigências complementares.')
    if grupo == 'final_desfavoravel':
        inconsistencias.append('O status atual é materialmente desfavorável ao pleito e exige revisão do enquadramento ou saneamento.')
    if data_obj and data_obj.month <= 3:
        pendencias.append('Como a data do status está no início do exercício, revisar documentos sensíveis ao exercício anterior fechado.')
    if not dados.get('tipo_operacao'):
        inconsistencias.append('Campo tipo_operacao não retornado; a inferência normativa ficou prejudicada.')
    if not dados.get('status'):
        inconsistencias.append('Campo status não retornado; o diagnóstico fica prejudicado.')

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
        pendencias.append('Nenhuma pendência provável inferida apenas pelos dados públicos; ainda é necessária conferência documental.')
    if not inconsistencias:
        inconsistencias.append('Nenhuma inconsistência evidente inferida apenas com base nos dados públicos disponíveis.')
    return {
        'ok': True,
        'dados_pleito': dados_pleito,
        'checklist_esperado': checklist,
        'pendencias_provaveis': pendencias,
        'inconsistencias_detectadas': inconsistencias,
        'dados_brutos': dados,
        'campos_presentes': presentes,
        'campos_ausentes': ausentes,
        'familia_identificada': familia,
        'fonte_api': consulta.get('url'),
        'avaliacao_campos_df': avaliar_campos_pvl(dados),
    }

# ============================
# Renderização das abas
# ============================

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
            for item in result.get('observacoes', []):
                st.markdown(f"- {item}")

    st.markdown("### Documentos e providências")
    for item in regra.get('documentos_base', []):
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
    filtro = sadipem_df[sadipem_df["operacao_codigo"] == op_sadipem].copy()

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
    st.caption("Localize o PVL pela API pública e, quando encontrado, faça a avaliação detalhada conforme o MIP.")
    numero_pvl = st.text_input("Número do PVL ou processo", placeholder="Ex.: PVL02.001234/2026-11")
    acionar = st.button("Pesquisar PVL", type='primary')
    if acionar:
        numero = normalizar_numero_pvl(numero_pvl)
        if not numero:
            st.warning('Informe um número de PVL válido.')
            return
        with st.spinner('Consultando API pública do SADIPEM...'):
            consulta = consultar_pvl_api(numero)
        if not consulta.get('ok'):
            st.error(consulta.get('erro', 'Não foi possível localizar o PVL.'))
            return
        item = consulta['items'][0]
        dados = extrair_dados_pvl(item)
        st.success('PVL localizado na API pública.')
        st.json(dados)
        if st.button('Avaliar PVL', use_container_width=True):
            with st.spinner('Aplicando regras do MIP ao PVL localizado...'):
                resultado = diagnosticar_pvl_real(numero)
            if not resultado.get('ok'):
                st.error(resultado.get('erro', 'Falha na avaliação do PVL.'))
                return
            c1, c2 = st.columns(2)
            blocos = [
                ('Dados do pleito', 'dados_pleito'),
                ('Checklist esperado', 'checklist_esperado'),
                ('Pendências prováveis', 'pendencias_provaveis'),
                ('Inconsistências detectadas', 'inconsistencias_detectadas'),
            ]
            for i, (titulo, chave) in enumerate(blocos):
                with (c1 if i % 2 == 0 else c2):
                    with st.container(border=True):
                        st.markdown(f"### {titulo}")
                        for item in resultado.get(chave, []):
                            st.markdown(f"- {item}")
            st.markdown('### Avaliação detalhada por aba/campo')
            st.dataframe(resultado['avaliacao_campos_df'], use_container_width=True, hide_index=True)
            with st.expander('Campos públicos presentes e ausentes'):
                st.markdown('### Presentes')
                for item in resultado.get('campos_presentes', []):
                    st.markdown(f'- {item}')
                st.markdown('### Ausentes')
                for item in resultado.get('campos_ausentes', []):
                    st.markdown(f'- {item}')
            with st.expander('Dados públicos retornados pela API'):
                st.caption(f"Fonte: {resultado.get('fonte_api')}")
                st.json(resultado.get('dados_brutos', {}))


aba1, aba2, aba3, aba4 = st.tabs(["Operações", "Upload do MIP", "SADIPEM", "Pesquisa PVL/API"])

with aba1:
    render_operacoes_tab()
with aba2:
    render_upload_tab()
with aba3:
    render_sadipem_tab()
with aba4:
    render_pesquisa_pvl_tab()
