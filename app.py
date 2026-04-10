from datetime import date

import pandas as pd
import streamlit as st

from rules_operacoes_v10 import (
    RULES_VERSION,
    build_operacoes_df,
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
    build_structured_update_suggestions,
    get_reference_period_rules,
    build_sadipem_action_plan,
    build_conditional_checklist_dataframe,
)

st.set_page_config(page_title="MIP PVL Assistant v12.5", layout="wide")

st.title("MIP PVL Assistant v12.5")
st.caption("Cobertura ampliada operação por operação, aprofundando ARO, regularização, consórcio, garantias por ente e blocos das leis complementares.")

operacoes_rules = get_operacoes_rules()
operacoes_df = build_operacoes_df()
sadipem_df = get_sadipem_field_matrix()

with st.sidebar:
    st.subheader("Base normativa")
    st.write(f"Versão da base: **{RULES_VERSION}**")
    st.write("Foco da versão: restaurar todas as operações relevantes na aba Operações, preservando a lógica da v11.6.")

aba1, aba2, aba3, aba4 = st.tabs(["Operações", "Upload do MIP", "SADIPEM", "Base tabular"])

with aba1:
    st.subheader("Consulta operacional")
    c1, c2 = st.columns([2, 1])
    with c1:
        op_label = st.selectbox("Tipo de operação", options=list(operacoes_rules.keys()), format_func=lambda x: operacoes_rules[x]["label"])
    with c2:
        data_ref = st.date_input("Data de referência", value=date.today(), format="DD/MM/YYYY")
    result = evaluate_operation(op_label, data_ref, operacoes_rules)
    regra = result["regra"]
    st.write(f"**Canal principal:** {regra.get('canal_principal')}  ")
    st.write(f"**Origem do envio:** {regra.get('origem_envio')}  ")
    st.write(f"**Família lógica:** {regra.get('family')}  ")
    st.write(f"**Exige garantia da União:** {regra.get('garantia_uniao')}  ")
    for item in regra.get('documentos_base', []):
        st.markdown(f"- {item}")

with aba2:
    st.subheader("Upload do MIP")
    uploaded = st.file_uploader("Upload do MIP", type=["pdf", "txt", "md"], accept_multiple_files=False)
    if st.button("Analisar MIP") and uploaded is not None:
        txt, src = detect_text_from_uploaded_file(uploaded)
        comparison = compare_mip_text_to_rules(txt, operacoes_rules)
        review_df = build_review_dataframe(comparison, extract_section_titles(txt), extract_change_signals(txt))
        st.write(f"Fonte: {src}")
        st.dataframe(review_df, use_container_width=True, hide_index=True)

with aba3:
    st.subheader("SADIPEM")
    s1, s2 = st.columns([2, 1])
    with s1:
        op_sadipem = st.selectbox("Tipo de operação", options=list(operacoes_rules.keys()), key="sadipem_select", format_func=lambda x: operacoes_rules[x]["label"])
    with s2:
        data_ref_sadipem = st.date_input("Data de referência", value=date.today(), key="sadipem_date", format="DD/MM/YYYY")

    plano = pd.DataFrame(build_sadipem_action_plan(op_sadipem, data_ref_sadipem, sadipem_df, operacoes_rules))
    checklist_df = build_conditional_checklist_dataframe(op_sadipem, data_ref_sadipem, operacoes_rules)
    filtro = sadipem_df[sadipem_df["operacao_codigo"] == op_sadipem].copy()

    st.markdown("### Checklist condicional por modalidade")
    if not checklist_df.empty:
        st.dataframe(checklist_df, use_container_width=True, hide_index=True)
    else:
        st.info("Esta modalidade ainda não possui checklist condicional detalhado por aba além do catálogo básico.")

    st.markdown("### Plano de ação por campo")
    if not plano.empty:
        st.dataframe(plano, use_container_width=True, hide_index=True)
        st.download_button(
            "Baixar plano SADIPEM em CSV",
            data=plano.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"sadipem_plano_{op_sadipem}_{data_ref_sadipem.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.info("Sem matriz detalhada para esta modalidade nesta versão.")

    st.markdown("### Matriz estrutural da operação no SADIPEM")
    if not filtro.empty:
        st.dataframe(filtro, use_container_width=True, hide_index=True)
    else:
        st.info("Esta modalidade não possui matriz estrutural detalhada do SADIPEM nesta versão.")

with aba4:
    st.subheader("Base tabular")
    st.dataframe(operacoes_df, use_container_width=True, hide_index=True)
    st.dataframe(sadipem_df, use_container_width=True, hide_index=True)


# ============================
# Módulo Consulta PVL + Diagnóstico (v12.5)
# ============================
import re
from typing import Dict, Any

def normalizar_numero_pvl(raw: str) -> str:
    if not raw:
        return ""
    return re.sub(r"[^0-9/.-]", "", raw.strip())

def diagnostico_placeholder(numero_pvl: str, dados_pvl: Dict[str, Any] | None = None) -> Dict[str, Any]:
    dados_pvl = dados_pvl or {}
    tipo = dados_pvl.get('tipo_operacao', 'Não identificado')
    status = dados_pvl.get('status', 'Não identificado')
    data_base = dados_pvl.get('data_base', 'Não identificada')
    return {
        'dados_pleito': [
            f'Número do PVL informado: {numero_pvl}',
            f'Tipo de operação identificado: {tipo}',
            f'Status atual identificado: {status}',
            f'Data-base considerada: {data_base}',
        ],
        'checklist_esperado': [
            'Aplicar o checklist da modalidade segundo o tipo de operação e a data-base.',
            'Verificar fluxo/canal correto (SADIPEM, Fale Conosco ou rito específico).',
            'Conferir documentos esperados para a operação e para o período do exercício.',
            'Conferir coerência entre Resumo, Operações Contratadas, Operações não Contratadas e documentos.',
        ],
        'pendencias_provaveis': [
            'Preencher integração com API/consulta pública do SADIPEM para identificar dados efetivos do PVL.',
            'Inferir ausência provável de documentos a partir da modalidade, do status e da data.',
            'Marcar itens que dependem de leitura humana dos anexos/documentos.',
        ],
        'inconsistencias_detectadas': [
            'Reservado para conflitos entre tipo de operação, status, cronogramas e regras do MIP.',
        ],
    }

def render_consulta_pvl_ui(st):
    st.subheader('Consulta PVL + Diagnóstico')
    st.caption('Entrada por número do PVL e saída em quatro blocos: dados do pleito, checklist esperado, pendências prováveis e inconsistências detectadas.')
    numero_pvl = st.text_input('Número do PVL', placeholder='Ex.: PVL02.001234/2026-11 ou formato equivalente')
    acionar = st.button('Consultar e diagnosticar', type='primary', use_container_width=True)
    if acionar:
        numero = normalizar_numero_pvl(numero_pvl)
        if not numero:
            st.warning('Informe um número de PVL válido.')
            return
        resultado = diagnostico_placeholder(numero)
        blocos = [
            ('Dados do pleito', 'dados_pleito'),
            ('Checklist esperado', 'checklist_esperado'),
            ('Pendências prováveis', 'pendencias_provaveis'),
            ('Inconsistências detectadas', 'inconsistencias_detectadas'),
        ]
        cols = st.columns(2)
        for i, (titulo, chave) in enumerate(blocos):
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f'### {titulo}')
                    for item in resultado.get(chave, []):
                        st.markdown(f'- {item}')


# ============================
# Integração real inicial do PVL (v12.5)
# ============================
import requests
import pandas as pd

SADIPEM_PVL_BASE_URL = "https://apidatalake.tesouro.gov.br/ords/sadipem/tt/pvl"

STATUS_DOCUMENTAL = {
    'Aguardando apresentação de documentos': ['Há indício forte de pendência documental no PVL.'],
    'Em retificação pelo interessado': ['Há indício de necessidade de ajuste documental ou confirmação pelo ente interessado.'],
    'Em retificação pelo credor': ['Há indício de necessidade de ajuste documental pelo credor.'],
    'Pendente de regularização': ['O PVL aponta regularização pendente, o que pode impedir novos pleitos.'],
    'Indeferido': ['O PVL foi indeferido; revisar integralmente o enquadramento, os dados e os documentos.'],
}

def consultar_pvl_api(numero_pvl: str):
    numero = normalizar_numero_pvl(numero_pvl)
    if not numero:
        return {'ok': False, 'erro': 'Número do PVL inválido.'}

    candidatos = [
        f"{SADIPEM_PVL_BASE_URL}?num_pvl=eq.{numero}",
        f"{SADIPEM_PVL_BASE_URL}?num_processo=eq.{numero}",
    ]

    headers = {'accept': 'application/json'}
    for url in candidatos:
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.ok:
                data = resp.json()
                items = data.get('items', data if isinstance(data, list) else [])
                if items:
                    return {'ok': True, 'items': items, 'url': url}
        except Exception as e:
            last_error = str(e)
    return {'ok': False, 'erro': locals().get('last_error', 'PVL não localizado na API pública.')}

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
        'finalidade': item.get('finalidade'),
        'valor': item.get('valor'),
        'moeda': item.get('moeda'),
        'pvl_assoc_divida': item.get('pvl_assoc_divida'),
        'pvl_contratado_credor': item.get('pvl_contratado_credor'),
    }

def inferir_familia_por_tipo(tipo_operacao: str) -> str:
    t = (tipo_operacao or '').lower()
    if 'reestrutura' in t or 'recomposi' in t:
        return 'reestruturacao'
    if 'antecipação de receita orçamentária' in t or 'aro' in t:
        return 'aro'
    if 'regulariza' in t:
        return 'regularizacao'
    if 'consórcio' in t:
        return 'consorcio'
    if 'garantia' in t and ('estado' in t or 'município' in t or 'municipio' in t):
        return 'garantia_ente'
    if 'lc 156' in t:
        return 'lc_156'
    if 'lc 159' in t:
        return 'lc_159'
    if 'lc 178' in t or 'pef' in t:
        return 'lc_178'
    if 'lc 212' in t:
        return 'lc_212'
    if 'extern' in t:
        return 'externa'
    return 'interna'

def coletar_checklist_esperado(familia: str):
    try:
        catalog = build_checklist_catalog()
        fam = catalog.get(familia, {})
        out = []
        for aba, fases in fam.items():
            jan = fases.get('janeiro', [])
            for item in jan[:4]:
                out.append(f'[{aba}] {item}')
        return out or ['Não foi possível montar checklist esperado para a família identificada.']
    except Exception:
        return ['Não foi possível montar checklist esperado para a família identificada.']

def diagnosticar_pvl_real(numero_pvl: str):
    consulta = consultar_pvl_api(numero_pvl)
    if not consulta.get('ok'):
        return {'ok': False, 'erro': consulta.get('erro', 'Falha na consulta do PVL.')}

    item = consulta['items'][0]
    dados = extrair_dados_pvl(item)
    familia = inferir_familia_por_tipo(dados.get('tipo_operacao'))
    checklist = coletar_checklist_esperado(familia)

    dados_pleito = [
        f"Número do PVL: {dados.get('num_pvl') or 'Não informado'}",
        f"Processo: {dados.get('num_processo') or 'Não informado'}",
        f"Interessado: {dados.get('interessado') or 'Não informado'} / UF: {dados.get('uf') or 'N/I'}",
        f"Tipo de operação: {dados.get('tipo_operacao') or 'Não informado'}",
        f"Status atual: {dados.get('status') or 'Não informado'}",
        f"Data do status: {dados.get('data_status') or 'Não informada'}",
        f"Credor: {dados.get('credor') or 'Não informado'}",
        f"Valor/moeda: {dados.get('valor') or 'Não informado'} / {dados.get('moeda') or 'N/I'}",
    ]

    pendencias = []
    inconsistencias = []

    st = dados.get('status') or ''
    pendencias.extend(STATUS_DOCUMENTAL.get(st, []))

    if dados.get('pvl_assoc_divida') in (1, '1') and familia != 'reestruturacao':
        inconsistencias.append('Há vínculo com dívida no CDP; revisar se a natureza da operação está adequadamente refletida no enquadramento.')
    if dados.get('pvl_contratado_credor') in (1, '1') and 'não contratad' in (dados.get('status') or '').lower():
        inconsistencias.append('O credor informou contratação, mas o status pode sugerir situação ainda não consolidada; conferir coerência do PVL.')
    if not pendencias:
        pendencias.append('Nenhuma pendência provável inferida apenas pelos dados públicos do PVL; ainda é necessária conferência documental.')
    if not inconsistencias:
        inconsistencias.append('Nenhuma inconsistência evidente inferida apenas com base nos dados públicos e nas regras atuais.')

    return {
        'ok': True,
        'dados_pleito': dados_pleito,
        'checklist_esperado': checklist,
        'pendencias_provaveis': pendencias,
        'inconsistencias_detectadas': inconsistencias,
        'dados_brutos': dados,
        'familia_identificada': familia,
        'fonte_api': consulta.get('url'),
    }

def render_consulta_pvl_ui(st):
    st.subheader('Consulta PVL + Diagnóstico')
    st.caption('Consulta real inicial na API pública do SADIPEM por número do PVL/processo, com diagnóstico estruturado em quatro blocos.')
    numero_pvl = st.text_input('Número do PVL ou processo', placeholder='Ex.: PVL02.001234/2026-11')
    acionar = st.button('Consultar e diagnosticar', type='primary', use_container_width=True)
    if acionar:
        numero = normalizar_numero_pvl(numero_pvl)
        if not numero:
            st.warning('Informe um número de PVL válido.')
            return
        with st.spinner('Consultando API pública do SADIPEM...'):
            resultado = diagnosticar_pvl_real(numero)
        if not resultado.get('ok'):
            st.error(resultado.get('erro', 'Não foi possível consultar o PVL.'))
            return
        st.success(f"Consulta realizada. Família identificada: {resultado.get('familia_identificada')}")
        blocos = [
            ('Dados do pleito', 'dados_pleito'),
            ('Checklist esperado', 'checklist_esperado'),
            ('Pendências prováveis', 'pendencias_provaveis'),
            ('Inconsistências detectadas', 'inconsistencias_detectadas'),
        ]
        cols = st.columns(2)
        for i, (titulo, chave) in enumerate(blocos):
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f'### {titulo}')
                    for item in resultado.get(chave, []):
                        st.markdown(f'- {item}')
        with st.expander('Dados públicos retornados pela consulta'):
            st.json(resultado.get('dados_brutos', {}))
            st.caption(f"Fonte consultada: {resultado.get('fonte_api')}")


# ============================
# Integração calibrada por status, data e tipo (v12.5)
# ============================
import requests
from datetime import datetime

SADIPEM_PVL_BASE_URL = "https://apidatalake.tesouro.gov.br/ords/sadipem/tt/pvl"

STATUS_HINTS = {
    'Em análise': {
        'pendencias': ['PVL em análise pode voltar para retificação caso a STN/IF solicite correções ou incremento de informações.'],
        'inconsistencias': []
    },
    'Em análise garantia da União': {
        'pendencias': ['A operação aparenta já ter avançado nos limites e condições, mas a análise da garantia da União ainda pode demandar complementação.'],
        'inconsistencias': []
    },
    'Em retificação pelo interessado': {
        'pendencias': ['Há indício forte de correção documental ou confirmação pendente pelo ente interessado.'],
        'inconsistencias': []
    },
    'Em retificação pelo credor': {
        'pendencias': ['Há indício forte de ajuste documental ou de dados pendente pelo credor.'],
        'inconsistencias': []
    },
    'Assinado pelo interessado': {
        'pendencias': ['O PVL foi assinado pelo interessado e tende a depender de avanço pelo credor ou do início da análise.'],
        'inconsistencias': []
    },
    'Pendente de regularização': {
        'pendencias': ['A regularização pendente pode obstar novas operações de crédito até saneamento da situação.'],
        'inconsistencias': []
    },
    'Indeferido': {
        'pendencias': ['Revisar integralmente o enquadramento, os dados declarados e a documentação da operação.'],
        'inconsistencias': ['O status final de indeferimento indica desconformidade relevante com os requisitos do pleito.']
    },
    'Deferido': {
        'pendencias': ['Verificar prazo de validade da análise e necessidade de atualização documental se a contratação ainda não ocorreu.'],
        'inconsistencias': []
    },
}

def parse_data(valor):
    if not valor:
        return None
    for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%d/%m/%Y'):
        try:
            return datetime.strptime(str(valor)[:19], fmt)
        except Exception:
            pass
    return None

def periodo_referencia(data_obj):
    if not data_obj:
        return 'indefinido'
    md = data_obj.month * 100 + data_obj.day
    if md <= 301:
        return 'ate_3003'
    if md <= 531:
        return 'pos_3003'
    if md <= 731:
        return 'pos_3005'
    if md <= 930:
        return 'pos_3007'
    if md <= 1130:
        return 'pos_3009'
    return 'pos_3011'

def consultar_pvl_api(numero_pvl: str):
    numero = normalizar_numero_pvl(numero_pvl)
    if not numero:
        return {'ok': False, 'erro': 'Número do PVL inválido.'}
    candidatos = [
        f"{SADIPEM_PVL_BASE_URL}?num_pvl=eq.{numero}",
        f"{SADIPEM_PVL_BASE_URL}?num_processo=eq.{numero}",
    ]
    headers = {'accept': 'application/json'}
    last_error = None
    for url in candidatos:
        try:
            resp = requests.get(url, headers=headers, timeout=20)
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
        'finalidade': item.get('finalidade'),
        'valor': item.get('valor'),
        'moeda': item.get('moeda'),
        'pvl_assoc_divida': item.get('pvl_assoc_divida'),
        'pvl_contratado_credor': item.get('pvl_contratado_credor'),
    }

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
    if 'pef' in t:
        return 'pef'
    if 'lc 212' in t:
        return 'lc_212'
    if 'extern' in t:
        return 'externa'
    return 'interna'

def coletar_checklist_esperado_calibrado(familia: str, data_status_str: str):
    try:
        catalog = build_checklist_catalog()
        fam = catalog.get(familia, {})
        data_obj = parse_data(data_status_str)
        periodo = periodo_referencia(data_obj)
        itens = []
        for aba, fases in fam.items():
            lista = fases.get(periodo) or fases.get('janeiro') or []
            for item in lista[:4]:
                itens.append(f'[{aba}] {item}')
        if data_obj and data_obj.month <= 3:
            itens.append('[Documentos] Entre 01/01 e 30/03, revisar exigências ligadas ao exercício anterior fechado e documentos sazonais da modalidade, quando aplicáveis.')
        return itens or ['Não foi possível montar checklist esperado para a família identificada.']
    except Exception:
        return ['Não foi possível montar checklist esperado para a família identificada.']

def calibrar_pendencias_por_familia(familia: str, dados: dict, data_obj):
    pend = []
    tipo = (dados.get('tipo_operacao') or '').lower()
    status = dados.get('status') or ''
    if familia == 'reestruturacao':
        pend += [
            'Verificar se a operação está efetivamente caracterizada como troca de dívida e não como operação ordinária.',
            'Verificar documentação da dívida antiga, aditivos, saldo atualizado e fluxo comparativo da dívida antiga com a nova operação.'
        ]
    elif familia == 'aro':
        pend += [
            'Verificar rito específico da ARO e aderência às vedações temporais e condicionantes próprias da modalidade.',
            'Confirmar documentação específica da ARO, inclusive declaração de não reciprocidade e cronograma de reembolso.'
        ]
    elif familia == 'regularizacao':
        pend += [
            'Confirmar documentos da operação irregular e, se aplicável, termo de quitação ou elementos de saneamento da pendência.'
        ]
    elif familia == 'consorcio':
        pend += [
            'Confirmar se cada ente participante possui PVL próprio e se há coerência entre todos os PVL do consórcio.'
        ]
    elif familia in {'lc_156','lc_159','lc_178','pef','lc_212'}:
        pend += [
            'Verificar a documentação específica da lei complementar aplicável e a aderência à hipótese legal correspondente.'
        ]
    elif familia == 'garantia_ente':
        pend += [
            'Verificar autorização legislativa, limite global de garantias e suficiência de contragarantias do tomador.'
        ]
    if data_obj and data_obj.month <= 3:
        pend += ['Por estar no período de início do exercício, revisar documentos vinculados ao exercício anterior fechado e exigências sazonais do MIP.']
    if 'garantia da união' in status.lower():
        pend += ['A análise da garantia da União pode exigir documentação adicional específica além do núcleo da operação de crédito.']
    return pend

def calibrar_inconsistencias(familia: str, dados: dict):
    inc = []
    status = (dados.get('status') or '').lower()
    tipo = (dados.get('tipo_operacao') or '').lower()
    if dados.get('pvl_assoc_divida') in (1, '1') and familia not in {'reestruturacao', 'regularizacao'}:
        inc.append('Há associação com dívida no CDP em modalidade que não é tipicamente de reestruturação/regularização; conferir enquadramento.')
    if dados.get('pvl_contratado_credor') in (1, '1') and 'não contratad' in status:
        inc.append('O registro do credor sugere contratação, mas o status aparenta manutenção como não contratada; conferir coerência do PVL.')
    if 'aro' in tipo and familia != 'aro':
        inc.append('O tipo textual sugere ARO, mas a família inferida não ficou coerente; revisar mapeamento do tipo de operação.')
    return inc

def diagnosticar_pvl_real(numero_pvl: str):
    consulta = consultar_pvl_api(numero_pvl)
    if not consulta.get('ok'):
        return {'ok': False, 'erro': consulta.get('erro', 'Falha na consulta do PVL.')}
    item = consulta['items'][0]
    dados = extrair_dados_pvl(item)
    familia = inferir_familia_por_tipo(dados.get('tipo_operacao'))
    data_obj = parse_data(dados.get('data_status'))
    checklist = coletar_checklist_esperado_calibrado(familia, dados.get('data_status'))
    dados_pleito = [
        f"Número do PVL: {dados.get('num_pvl') or 'Não informado'}",
        f"Processo: {dados.get('num_processo') or 'Não informado'}",
        f"Interessado: {dados.get('interessado') or 'Não informado'} / UF: {dados.get('uf') or 'N/I'}",
        f"Tipo de operação: {dados.get('tipo_operacao') or 'Não informado'}",
        f"Família inferida: {familia}",
        f"Status atual: {dados.get('status') or 'Não informado'}",
        f"Data do status: {dados.get('data_status') or 'Não informada'}",
        f"Credor: {dados.get('credor') or 'Não informado'}",
        f"Valor/moeda: {dados.get('valor') or 'Não informado'} / {dados.get('moeda') or 'N/I'}",
    ]
    pendencias = []
    inconsistencias = []
    status_hints = STATUS_HINTS.get(dados.get('status') or '', {})
    pendencias.extend(status_hints.get('pendencias', []))
    inconsistencias.extend(status_hints.get('inconsistencias', []))
    pendencias.extend(calibrar_pendencias_por_familia(familia, dados, data_obj))
    inconsistencias.extend(calibrar_inconsistencias(familia, dados))
    # deduplicate while preserving order
    pendencias = list(dict.fromkeys(pendencias))
    inconsistencias = list(dict.fromkeys(inconsistencias))
    if not pendencias:
        pendencias.append('Nenhuma pendência provável inferida apenas pelos dados públicos do PVL; ainda é necessária conferência documental.')
    if not inconsistencias:
        inconsistencias.append('Nenhuma inconsistência evidente inferida apenas com base nos dados públicos e nas regras calibradas atuais.')
    return {
        'ok': True,
        'dados_pleito': dados_pleito,
        'checklist_esperado': checklist,
        'pendencias_provaveis': pendencias,
        'inconsistencias_detectadas': inconsistencias,
        'dados_brutos': dados,
        'familia_identificada': familia,
        'fonte_api': consulta.get('url'),
    }

def render_consulta_pvl_ui(st):
    st.subheader('Consulta PVL + Diagnóstico')
    st.caption('Consulta calibrada por número do PVL/processo, status, data do status e tipo de operação, com diagnóstico em quatro blocos.')
    numero_pvl = st.text_input('Número do PVL ou processo', placeholder='Ex.: PVL02.001234/2026-11')
    acionar = st.button('Consultar e diagnosticar', type='primary', use_container_width=True)
    if acionar:
        numero = normalizar_numero_pvl(numero_pvl)
        if not numero:
            st.warning('Informe um número de PVL válido.')
            return
        with st.spinner('Consultando API pública do SADIPEM e calibrando o diagnóstico...'):
            resultado = diagnosticar_pvl_real(numero)
        if not resultado.get('ok'):
            st.error(resultado.get('erro', 'Não foi possível consultar o PVL.'))
            return
        st.success(f"Consulta realizada. Família identificada: {resultado.get('familia_identificada')}")
        blocos = [
            ('Dados do pleito', 'dados_pleito'),
            ('Checklist esperado', 'checklist_esperado'),
            ('Pendências prováveis', 'pendencias_provaveis'),
            ('Inconsistências detectadas', 'inconsistencias_detectadas'),
        ]
        cols = st.columns(2)
        for i, (titulo, chave) in enumerate(blocos):
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f'### {titulo}')
                    for item in resultado.get(chave, []):
                        st.markdown(f'- {item}')
        with st.expander('Dados públicos retornados pela consulta'):
            st.json(resultado.get('dados_brutos', {}))
            st.caption(f"Fonte consultada: {resultado.get('fonte_api')}")


# ============================
# Integração endurecida por cenários e campos reais (v12.5)
# ============================
import requests
from datetime import datetime

SADIPEM_PVL_BASE_URL = "https://apidatalake.tesouro.gov.br/ords/sadipem/tt/pvl"

API_FIELD_MAP = {
    'id_pleito': 'Identificação interna do PVL no SADIPEM',
    'tipo_interessado': 'Tipo de interessado',
    'interessado': 'Ente interessado',
    'cod_ibge': 'Código IBGE',
    'uf': 'UF do interessado',
    'num_pvl': 'Número do PVL',
    'status': 'Etapa/status atual do PVL',
    'num_processo': 'Número do processo',
    'data_protocolo': 'Data/hora do último envio à STN',
    'tipo_operacao': 'Tipo da operação ou garantia',
    'finalidade': 'Finalidade da operação',
    'tipo_credor': 'Tipo do credor',
    'instituicao_credora': 'Instituição credora',
    'credor': 'Credor',
    'moeda': 'Moeda da operação',
    'valor': 'Valor informado',
    'pvl_assoc_divida': 'Há dívida no CDP vinculada ao PVL (1/0)',
    'pvl_contratado_credor': 'Credor informou contratação (1/0)',
    'data_status': 'Data do status atual',
}

STATUS_GROUPS = {
    'inicial': {'Em preenchimento pelo credor', 'Em preenchimento pelo interessado', 'Assinado pelo interessado', 'Enviado à STN', 'Formalizado', 'Formalizado com pendências', 'Pendente de distribuição (PVL-IF)', 'Enviado à instituição financeira (PVL-IF)'},
    'analise': {'Em análise', 'Em análise garantia da União', 'Em análise PVL-IF', 'Em triagem', 'Em consulta jurídica'},
    'retificacao': {'Em retificação pelo credor', 'Em retificação pelo interessado', 'Em retificação pelo credor (PVL-IF)', 'Em retificação pelo interessado (PVL-IF)'},
    'final_favoravel': {'Deferido', 'Deferido (PVL-IF)', 'Deferido sem garantia da União', 'Encaminhado à PGFN com manifestação técnica favorável', 'Encaminhado à PGFN (decisão judicial)', 'Regularizado', 'Regular por decisão judicial'},
    'final_desfavoravel': {'Indeferido', 'Indeferido (PVL-IF)', 'Encaminhado à PGFN com manifestação técnica desfavorável', 'Pendente de regularização'},
    'arquivamento': {'Arquivado', 'Arquivado a pedido', 'Arquivado a pedido (PVL-IF)', 'Arquivado pela STN', 'Arquivado por decurso de prazo', 'Arquivado por decurso de prazo (PVL-IF)', 'PVL cancelado'},
    'suspensao': {'Sobrestado', 'Suspenso por decisão judicial'},
}

def parse_data(valor):
    if not valor:
        return None
    s = str(valor).strip()
    candidatos = [s, s[:19], s[:10]]
    for cand in candidatos:
        for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%d/%m/%Y'):
            try:
                return datetime.strptime(cand, fmt)
            except Exception:
                pass
    return None

def periodo_referencia(data_obj):
    if not data_obj:
        return 'indefinido'
    md = data_obj.month * 100 + data_obj.day
    if md <= 301:
        return 'ate_3003'
    if md <= 531:
        return 'pos_3003'
    if md <= 731:
        return 'pos_3005'
    if md <= 930:
        return 'pos_3007'
    if md <= 1130:
        return 'pos_3009'
    return 'pos_3011'

def grupo_status(status):
    s = status or ''
    for grupo, conjunto in STATUS_GROUPS.items():
        if s in conjunto:
            return grupo
    return 'desconhecido'

def consultar_pvl_api(numero_pvl: str):
    numero = normalizar_numero_pvl(numero_pvl)
    if not numero:
        return {'ok': False, 'erro': 'Número do PVL inválido.'}
    candidatos = [
        f"{SADIPEM_PVL_BASE_URL}?num_pvl=eq.{numero}",
        f"{SADIPEM_PVL_BASE_URL}?num_processo=eq.{numero}",
    ]
    headers = {'accept': 'application/json'}
    last_error = None
    for url in candidatos:
        try:
            resp = requests.get(url, headers=headers, timeout=20)
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
    dados = {k: item.get(k) for k in API_FIELD_MAP.keys()}
    if not dados.get('credor'):
        dados['credor'] = item.get('instituicao_credora')
    return dados

def campos_presentes_ausentes(dados: dict):
    presentes = []
    ausentes = []
    for k, desc in API_FIELD_MAP.items():
        v = dados.get(k)
        if v is None or v == '':
            ausentes.append(f'{k} - {desc}')
        else:
            presentes.append(f'{k} - {desc}: {v}')
    return presentes, ausentes

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
    if 'pef' in t:
        return 'pef'
    if 'lc 212' in t:
        return 'lc_212'
    if 'extern' in t:
        return 'externa'
    return 'interna'

def coletar_checklist_esperado_calibrado(familia: str, data_status_str: str):
    try:
        catalog = build_checklist_catalog()
        fam = catalog.get(familia, {})
        data_obj = parse_data(data_status_str)
        periodo = periodo_referencia(data_obj)
        itens = []
        for aba, fases in fam.items():
            lista = fases.get(periodo) or fases.get('janeiro') or []
            for item in lista[:4]:
                itens.append(f'[{aba}] {item}')
        if data_obj and data_obj.month <= 3:
            itens.append('[Documentos] Entre 01/01 e 30/03, revisar exigências ligadas ao exercício anterior fechado e documentos sazonais da modalidade, quando aplicáveis.')
        return itens or ['Não foi possível montar checklist esperado para a família identificada.']
    except Exception:
        return ['Não foi possível montar checklist esperado para a família identificada.']

def regras_por_cenario(familia: str, status: str, dados: dict, data_obj):
    grupo = grupo_status(status)
    pend = []
    inc = []
    if grupo == 'retificacao':
        pend.append('O cenário de retificação sugere exigência anterior não integralmente atendida; revisar documentos e dados do sistema antes de novo envio.')
    if grupo == 'analise':
        pend.append('O cenário de análise sugere que o pleito já superou a fase inicial, mas ainda pode receber exigências complementares.')
    if grupo == 'final_favoravel' and dados.get('pvl_contratado_credor') not in (1, '1'):
        pend.append('Status favorável sem contratação informada pelo credor pode indicar operação ainda não efetivada; acompanhar prazo de validade da análise.')
    if grupo == 'final_desfavoravel':
        inc.append('O cenário do status atual é materialmente desfavorável ao pleito e exige revisão de enquadramento ou saneamento.')
    if grupo == 'arquivamento':
        pend.append('O cenário de arquivamento exige avaliar reabertura, novo PVL ou perda de utilidade da análise anterior.')
    if grupo == 'suspensao':
        pend.append('Há suspensão/sobrestamento; conferir motivo processual antes de qualquer conclusão operacional.')

    if familia == 'reestruturacao':
        pend += [
            'Confirmar documentação da dívida antiga, aditivos, saldo atualizado e demonstração de troca de dívida.',
            'Verificar se o enquadramento especial não está sendo usado para operação que, na prática, se comporta como crédito ordinário.'
        ]
        if dados.get('pvl_assoc_divida') not in (1, '1'):
            inc.append('A família inferida é de reestruturação, mas não há indicação de dívida vinculada no CDP; conferir coerência dos dados públicos.')
    elif familia == 'aro':
        pend += [
            'Confirmar rito específico da ARO, cronograma de reembolso e documentos próprios da modalidade.',
            'Revisar aderência às restrições temporais da ARO.'
        ]
        if dados.get('moeda') and str(dados.get('moeda')).upper() not in {'REAL', 'BRL', 'R$'}:
            inc.append('ARO com moeda não usual para a modalidade; conferir consistência do cadastro.')
    elif familia == 'regularizacao':
        pend.append('Confirmar documentos da operação irregular, pareceres e eventual termo de quitação ou regularização.')
    elif familia == 'consorcio':
        pend.append('Confirmar coerência entre o PVL consultado e os demais PVL dos entes participantes do consórcio.')
    elif familia == 'garantia_ente':
        pend.append('Confirmar autorização legislativa, contragarantias e limite global de garantias concedidas.')
    elif familia in {'lc_156','lc_159','lc_178','pef','lc_212'}:
        pend.append('Confirmar aderência estrita à hipótese legal da lei complementar aplicável e aos documentos específicos da modalidade.')

    if data_obj and data_obj.month <= 3:
        pend.append('Como a data do status está no início do exercício, revisar documentos sensíveis ao exercício anterior fechado e exigências sazonais do MIP.')

    if dados.get('pvl_assoc_divida') in (1, '1') and familia not in {'reestruturacao', 'regularizacao'}:
        inc.append('Há vínculo com dívida no CDP em modalidade não tipicamente associada a reestruturação/regularização; conferir enquadramento.')
    if dados.get('pvl_contratado_credor') in (1, '1') and grupo in {'inicial', 'retificacao'}:
        inc.append('Há informação de contratação pelo credor em cenário processual ainda inicial/retificatório; conferir coerência temporal do PVL.')
    if not dados.get('num_pvl') and not dados.get('num_processo'):
        inc.append('Os dados públicos retornados não trouxeram identificação suficiente do PVL/processo; consulta deve ser revista.')
    if not dados.get('status'):
        inc.append('O campo status não foi retornado; o diagnóstico fica materialmente prejudicado.')
    if not dados.get('tipo_operacao'):
        inc.append('O campo tipo_operacao não foi retornado; a inferência da família ficou prejudicada.')
    return list(dict.fromkeys(pend)), list(dict.fromkeys(inc))

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
    pendencias, inconsistencias = regras_por_cenario(familia, dados.get('status') or '', dados, data_obj)

    dados_pleito = [
        f"Número do PVL: {dados.get('num_pvl') or 'Não informado'}",
        f"Processo: {dados.get('num_processo') or 'Não informado'}",
        f"Interessado: {dados.get('interessado') or 'Não informado'} / UF: {dados.get('uf') or 'N/I'}",
        f"Tipo do interessado: {dados.get('tipo_interessado') or 'Não informado'}",
        f"Tipo de operação: {dados.get('tipo_operacao') or 'Não informado'}",
        f"Finalidade: {dados.get('finalidade') or 'Não informada'}",
        f"Família inferida: {familia}",
        f"Status atual: {dados.get('status') or 'Não informado'} / Grupo de status: {grupo_status(dados.get('status'))}",
        f"Data do status: {dados.get('data_status') or 'Não informada'} / Data de protocolo: {dados.get('data_protocolo') or 'Não informada'}",
        f"Credor: {dados.get('credor') or 'Não informado'} / Tipo de credor: {dados.get('tipo_credor') or 'Não informado'}",
        f"Valor/moeda: {dados.get('valor') or 'Não informado'} / {dados.get('moeda') or 'N/I'}",
        f"Campos públicos presentes: {len(presentes)} / Campos públicos ausentes: {len(ausentes)}",
    ]

    if not pendencias:
        pendencias.append('Nenhuma pendência provável inferida apenas pelos dados públicos do PVL; ainda é necessária conferência documental.')
    if not inconsistencias:
        inconsistencias.append('Nenhuma inconsistência evidente inferida apenas com base nos dados públicos e nas regras endurecidas atuais.')

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
    }

def render_consulta_pvl_ui(st):
    st.subheader('Consulta PVL + Diagnóstico')
    st.caption('Consulta endurecida por cenários, com melhor mapeamento dos campos públicos da API do SADIPEM e diagnóstico por combinação de status, data e tipo de operação.')
    numero_pvl = st.text_input('Número do PVL ou processo', placeholder='Ex.: PVL02.001234/2026-11')
    acionar = st.button('Consultar e diagnosticar', type='primary', use_container_width=True)
    if acionar:
        numero = normalizar_numero_pvl(numero_pvl)
        if not numero:
            st.warning('Informe um número de PVL válido.')
            return
        with st.spinner('Consultando API pública do SADIPEM e processando cenários...'):
            resultado = diagnosticar_pvl_real(numero)
        if not resultado.get('ok'):
            st.error(resultado.get('erro', 'Não foi possível consultar o PVL.'))
            return
        st.success(f"Consulta realizada. Família identificada: {resultado.get('familia_identificada')}")
        blocos = [
            ('Dados do pleito', 'dados_pleito'),
            ('Checklist esperado', 'checklist_esperado'),
            ('Pendências prováveis', 'pendencias_provaveis'),
            ('Inconsistências detectadas', 'inconsistencias_detectadas'),
        ]
        cols = st.columns(2)
        for i, (titulo, chave) in enumerate(blocos):
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f'### {titulo}')
                    for item in resultado.get(chave, []):
                        st.markdown(f'- {item}')
        with st.expander('Mapeamento dos campos públicos da API'):
            st.markdown('### Campos presentes')
            for item in resultado.get('campos_presentes', []):
                st.markdown(f'- {item}')
            st.markdown('### Campos ausentes')
            for item in resultado.get('campos_ausentes', []):
                st.markdown(f'- {item}')
        with st.expander('Dados públicos retornados pela consulta'):
            st.json(resultado.get('dados_brutos', {}))
            st.caption(f"Fonte consultada: {resultado.get('fonte_api')}")


# ============================
# Busca ampliada e integração multi-endpoint (v12.5)
# ============================
import requests
from datetime import datetime
from urllib.parse import quote

API_BASE = "https://apidatalake.tesouro.gov.br/ords/sadipem/tt"
ENDPOINTS = {
    'pvl': f"{API_BASE}/pvl",
    'resumo_cdp': f"{API_BASE}/resumo_cdp",
    'resumo_cp': f"{API_BASE}/resumo_cronograma_pagamentos",
    'oc_cp': f"{API_BASE}/operacoes_contratadas_cronograma_pagamentos",
    'oc_cl': f"{API_BASE}/operacoes_contratadas_cronograma_liberacoes",
    'oc_tx': f"{API_BASE}/operacoes_contratadas_taxas_cambio",
}

API_FIELD_MAP = {
    'id_pleito': 'Identificação interna do PVL no SADIPEM',
    'tipo_interessado': 'Tipo de interessado',
    'interessado': 'Ente interessado',
    'cod_ibge': 'Código IBGE',
    'uf': 'UF do interessado',
    'num_pvl': 'Número do PVL',
    'status': 'Etapa/status atual do PVL',
    'num_processo': 'Número do processo',
    'data_protocolo': 'Data/hora do último envio à STN',
    'tipo_operacao': 'Tipo da operação ou garantia',
    'finalidade': 'Finalidade da operação',
    'tipo_credor': 'Tipo do credor',
    'instituicao_credora': 'Instituição credora',
    'credor': 'Credor',
    'moeda': 'Moeda da operação',
    'valor': 'Valor informado',
    'pvl_assoc_divida': 'Há dívida no CDP vinculada ao PVL (1/0)',
    'pvl_contratado_credor': 'Credor informou contratação (1/0)',
    'data_status': 'Data do status atual',
}

STATUS_GROUPS = {
    'inicial': {'Em preenchimento pelo credor', 'Em preenchimento pelo interessado', 'Assinado pelo interessado', 'Pendente de distribuição (PVL-IF)', 'Enviado à instituição financeira (PVL-IF)'},
    'analise': {'Em análise', 'Em análise garantia da União', 'Em análise PVL-IF', 'Em consulta jurídica'},
    'retificacao': {'Em retificação pelo credor', 'Em retificação pelo interessado', 'Em retificação pelo credor (PVL-IF)', 'Em retificação pelo interessado (PVL-IF)'},
    'final_favoravel': {'Deferido', 'Deferido (PVL-IF)', 'Deferido sem garantia da União', 'Encaminhado à PGFN com manifestação técnica favorável', 'Encaminhado à PGFN (decisão judicial)', 'Regularizado', 'Regular por decisão judicial'},
    'final_desfavoravel': {'Indeferido', 'Indeferido (PVL-IF)', 'Encaminhado à PGFN com manifestação técnica desfavorável', 'Pendente de regularização'},
    'arquivamento': {'Arquivado', 'Arquivado a pedido', 'Arquivado a pedido (PVL-IF)', 'Arquivado pela STN', 'Arquivado por decurso de prazo', 'Arquivado por decurso de prazo (PVL-IF)', 'PVL cancelado'},
    'suspensao': {'Sobrestado', 'Suspenso por decisão judicial'},
}

def parse_data(valor):
    if not valor:
        return None
    s = str(valor).strip()
    candidatos = [s, s[:19], s[:10]]
    for cand in candidatos:
        for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%d/%m/%Y'):
            try:
                return datetime.strptime(cand, fmt)
            except Exception:
                pass
    return None

def periodo_referencia(data_obj):
    if not data_obj:
        return 'indefinido'
    md = data_obj.month * 100 + data_obj.day
    if md <= 301:
        return 'ate_3003'
    if md <= 531:
        return 'pos_3003'
    if md <= 731:
        return 'pos_3005'
    if md <= 930:
        return 'pos_3007'
    if md <= 1130:
        return 'pos_3009'
    return 'pos_3011'

def grupo_status(status):
    s = status or ''
    for grupo, conjunto in STATUS_GROUPS.items():
        if s in conjunto:
            return grupo
    return 'desconhecido'

def api_get(url):
    headers = {'accept': 'application/json'}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data.get('items', data if isinstance(data, list) else [])

def montar_filtros_pvl(numero_pvl=None, num_processo=None, ente=None, uf=None, ano=None, status=None, tipo_operacao=None):
    filtros = []
    if numero_pvl:
        filtros.append(f"num_pvl=eq.{normalizar_numero_pvl(numero_pvl)}")
    if num_processo:
        filtros.append(f"num_processo=eq.{normalizar_numero_pvl(num_processo)}")
    if ente:
        filtros.append(f"interessado=ilike.*{quote(str(ente))}*")
    if uf:
        filtros.append(f"uf=eq.{quote(str(uf).upper())}")
    if status:
        filtros.append(f"status=ilike.*{quote(str(status))}*")
    if tipo_operacao:
        filtros.append(f"tipo_operacao=ilike.*{quote(str(tipo_operacao))}*")
    if ano:
        filtros.append(f"or=(data_status.like.{ano}-%25,data_protocolo.like.{ano}-%25,num_pvl.like.%25/{ano}-%25,num_processo.like.%25{ano}%25)")
    return filtros

def buscar_pvls(numero_pvl=None, num_processo=None, ente=None, uf=None, ano=None, status=None, tipo_operacao=None, limit=30):
    filtros = montar_filtros_pvl(numero_pvl, num_processo, ente, uf, ano, status, tipo_operacao)
    query = '&'.join(filtros + [f'limit={limit}']) if filtros else f'limit={limit}'
    url = f"{ENDPOINTS['pvl']}?{query}"
    try:
        items = api_get(url)
        return {'ok': True, 'items': items, 'url': url}
    except Exception as e:
        return {'ok': False, 'erro': str(e), 'url': url}

def consultar_detalhes_multifonte(num_pvl=None, num_processo=None):
    chave = normalizar_numero_pvl(num_pvl or num_processo or '')
    if not chave:
        return {'ok': False, 'erro': 'Chave de consulta inválida.'}
    pvl = buscar_pvls(numero_pvl=num_pvl, num_processo=num_processo, limit=5)
    if not pvl.get('ok') or not pvl.get('items'):
        return {'ok': False, 'erro': pvl.get('erro', 'PVL não localizado.'), 'fonte_pvl': pvl.get('url')}
    item = pvl['items'][0]
    num_pvl_real = item.get('num_pvl') or chave
    detalhes = {'pvl': item, 'fonte_pvl': pvl.get('url')}
    for nome, endpoint in ENDPOINTS.items():
        if nome == 'pvl':
            continue
        urls = [
            f"{endpoint}?num_pvl=eq.{quote(str(num_pvl_real))}&limit=200",
            f"{endpoint}?num_processo=eq.{quote(str(item.get('num_processo') or chave))}&limit=200",
        ]
        coletado = []
        usado = None
        for url in urls:
            try:
                dados = api_get(url)
                if dados:
                    coletado = dados
                    usado = url
                    break
            except Exception:
                pass
        detalhes[nome] = coletado
        detalhes[f'fonte_{nome}'] = usado
    return {'ok': True, 'dados': detalhes}

def extrair_dados_pvl(item: dict):
    dados = {k: item.get(k) for k in API_FIELD_MAP.keys()}
    if not dados.get('credor'):
        dados['credor'] = item.get('instituicao_credora')
    return dados

def campos_presentes_ausentes(dados: dict):
    presentes = []
    ausentes = []
    for k, desc in API_FIELD_MAP.items():
        v = dados.get(k)
        if v is None or v == '':
            ausentes.append(f'{k} - {desc}')
        else:
            presentes.append(f'{k} - {desc}: {v}')
    return presentes, ausentes

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
    if 'pef' in t:
        return 'pef'
    if 'lc 212' in t:
        return 'lc_212'
    if 'extern' in t:
        return 'externa'
    return 'interna'

def coletar_checklist_esperado_calibrado(familia: str, data_status_str: str):
    try:
        catalog = build_checklist_catalog()
        fam = catalog.get(familia, {})
        data_obj = parse_data(data_status_str)
        periodo = periodo_referencia(data_obj)
        itens = []
        chave_periodo = 'janeiro' if periodo == 'ate_3003' else periodo
        for aba, fases in fam.items():
            lista = fases.get(chave_periodo) or fases.get('janeiro') or []
            for item in lista[:4]:
                itens.append(f'[{aba}] {item}')
        if data_obj and data_obj.month <= 3:
            itens.append('[Documentos] Entre 01/01 e 30/03, revisar exigências ligadas ao exercício anterior fechado e documentos sazonais da modalidade, quando aplicáveis.')
        return itens or ['Não foi possível montar checklist esperado para a família identificada.']
    except Exception:
        return ['Não foi possível montar checklist esperado para a família identificada.']

def resumir_multifonte(detalhes):
    resumo = []
    for k in ['resumo_cdp', 'resumo_cp', 'oc_cp', 'oc_cl', 'oc_tx']:
        itens = detalhes.get(k, []) or []
        resumo.append(f'{k}: {len(itens)} registro(s)')
    return resumo

def regras_por_cenario(familia: str, status: str, dados: dict, data_obj, detalhes: dict):
    grupo = grupo_status(status)
    pend = []
    inc = []
    resumo_cp = detalhes.get('resumo_cp', []) or []
    resumo_cdp = detalhes.get('resumo_cdp', []) or []
    oc_cp = detalhes.get('oc_cp', []) or []
    oc_cl = detalhes.get('oc_cl', []) or []
    oc_tx = detalhes.get('oc_tx', []) or []

    if grupo == 'retificacao':
        pend.append('O cenário de retificação sugere exigência anterior não integralmente atendida; revisar documentos e dados do sistema antes de novo envio.')
    if grupo == 'analise':
        pend.append('O cenário de análise sugere que o pleito já superou a fase inicial, mas ainda pode receber exigências complementares.')
    if grupo == 'final_favoravel' and dados.get('pvl_contratado_credor') not in (1, '1'):
        pend.append('Status favorável sem contratação informada pelo credor pode indicar operação ainda não efetivada; acompanhar prazo de validade da análise.')
    if grupo == 'final_desfavoravel':
        inc.append('O cenário do status atual é materialmente desfavorável ao pleito e exige revisão de enquadramento ou saneamento.')
    if grupo == 'arquivamento':
        pend.append('O cenário de arquivamento exige avaliar reabertura, novo PVL ou perda de utilidade da análise anterior.')

    if familia == 'reestruturacao':
        pend += ['Confirmar documentação da dívida antiga, aditivos, saldo atualizado e demonstração de troca de dívida.']
        if dados.get('pvl_assoc_divida') not in (1, '1'):
            inc.append('A família inferida é de reestruturação, mas não há indicação de dívida vinculada no CDP; conferir coerência dos dados públicos.')
    elif familia == 'aro':
        pend += ['Confirmar rito específico da ARO, cronograma de reembolso e documentos próprios da modalidade.']
    elif familia == 'regularizacao':
        pend += ['Confirmar documentos da operação irregular e eventual termo de quitação/regularização.']
    elif familia == 'consorcio':
        pend += ['Confirmar coerência do PVL com os demais PVL dos entes participantes do consórcio.']
    elif familia == 'garantia_ente':
        pend += ['Confirmar autorização legislativa, contragarantias e limite global de garantias concedidas.']
    elif familia in {'lc_156','lc_159','lc_178','pef','lc_212'}:
        pend += ['Confirmar aderência estrita à hipótese legal da lei complementar aplicável e aos documentos específicos da modalidade.']

    if data_obj and data_obj.month <= 3:
        pend.append('Como a data do status está no início do exercício, revisar documentos sensíveis ao exercício anterior fechado e exigências sazonais do MIP.')

    if dados.get('pvl_assoc_divida') in (1, '1') and familia not in {'reestruturacao', 'regularizacao'}:
        inc.append('Há vínculo com dívida no CDP em modalidade não tipicamente associada a reestruturação/regularização; conferir enquadramento.')
    if dados.get('pvl_contratado_credor') in (1, '1') and grupo in {'inicial', 'retificacao'}:
        inc.append('Há informação de contratação pelo credor em cenário processual ainda inicial/retificatório; conferir coerência temporal do PVL.')
    if grupo in {'final_favoravel', 'analise'} and not resumo_cp and not oc_cp:
        pend.append('Não foram localizados cronogramas públicos de pagamento; conferir se a ausência decorre do estágio do PVL ou de falta de integração dos dados públicos.')
    if oc_cp and not oc_cl:
        pend.append('Há cronograma de pagamentos em Operações Contratadas sem cronograma de liberações público correspondente; conferir se isso decorre da natureza da operação.')
    if oc_cp and dados.get('moeda') and str(dados.get('moeda')).upper() not in {'REAL', 'BRL', 'R$'} and not oc_tx:
        inc.append('Há indício de operação em moeda estrangeira sem taxas de câmbio públicas retornadas; conferir integração dos dados.')
    if dados.get('pvl_assoc_divida') in (1, '1') and not resumo_cdp:
        pend.append('O PVL indica vínculo com dívida/CDP, mas não foram retornadas informações públicas do Resumo-CDP; conferir disponibilidade do endpoint.')
    return list(dict.fromkeys(pend)), list(dict.fromkeys(inc))

def diagnosticar_item(item: dict, detalhes: dict):
    dados = extrair_dados_pvl(item)
    familia = inferir_familia_por_tipo(dados.get('tipo_operacao'))
    data_obj = parse_data(dados.get('data_status'))
    presentes, ausentes = campos_presentes_ausentes(dados)
    checklist = coletar_checklist_esperado_calibrado(familia, dados.get('data_status'))
    pendencias, inconsistencias = regras_por_cenario(familia, dados.get('status') or '', dados, data_obj, detalhes)
    dados_pleito = [
        f"Número do PVL: {dados.get('num_pvl') or 'Não informado'}",
        f"Processo: {dados.get('num_processo') or 'Não informado'}",
        f"Interessado: {dados.get('interessado') or 'Não informado'} / UF: {dados.get('uf') or 'N/I'}",
        f"Tipo do interessado: {dados.get('tipo_interessado') or 'Não informado'}",
        f"Tipo de operação: {dados.get('tipo_operacao') or 'Não informado'}",
        f"Finalidade: {dados.get('finalidade') or 'Não informada'}",
        f"Família inferida: {familia}",
        f"Status atual: {dados.get('status') or 'Não informado'} / Grupo de status: {grupo_status(dados.get('status'))}",
        f"Data do status: {dados.get('data_status') or 'Não informada'} / Data de protocolo: {dados.get('data_protocolo') or 'Não informada'}",
        f"Credor: {dados.get('credor') or 'Não informado'} / Tipo de credor: {dados.get('tipo_credor') or 'Não informado'}",
        f"Valor/moeda: {dados.get('valor') or 'Não informado'} / {dados.get('moeda') or 'N/I'}",
        f"Campos públicos presentes: {len(presentes)} / Campos públicos ausentes: {len(ausentes)}",
    ]
    if not pendencias:
        pendencias.append('Nenhuma pendência provável inferida apenas pelos dados públicos do PVL; ainda é necessária conferência documental.')
    if not inconsistencias:
        inconsistencias.append('Nenhuma inconsistência evidente inferida apenas com base nos dados públicos e nas regras atuais.')
    return {
        'dados_pleito': dados_pleito,
        'checklist_esperado': checklist,
        'pendencias_provaveis': pendencias,
        'inconsistencias_detectadas': inconsistencias,
        'dados_brutos': dados,
        'campos_presentes': presentes,
        'campos_ausentes': ausentes,
        'familia_identificada': familia,
        'resumo_multifonte': resumir_multifonte(detalhes),
    }

def render_consulta_pvl_ui(st):
    st.subheader('Consulta PVL + Diagnóstico')
    st.caption('Busca ampliada por número do PVL, processo, ente, UF, ano, status e tipo de operação, com integração aos demais conjuntos públicos da API do SADIPEM.')
    c1, c2, c3 = st.columns(3)
    with c1:
        numero_pvl = st.text_input('Número do PVL')
        ente = st.text_input('Ente interessado')
        ano = st.text_input('Ano', placeholder='2025')
    with c2:
        num_processo = st.text_input('Número do processo')
        uf = st.text_input('UF', placeholder='PE')
        status = st.text_input('Status')
    with c3:
        tipo_operacao = st.text_input('Tipo de operação')
        limite = st.slider('Limite de resultados', min_value=1, max_value=50, value=15)
    acionar = st.button('Pesquisar PVLs', type='primary', use_container_width=True)

    if acionar:
        with st.spinner('Pesquisando PVLs na API pública do SADIPEM...'):
            busca = buscar_pvls(numero_pvl=numero_pvl, num_processo=num_processo, ente=ente, uf=uf, ano=ano, status=status, tipo_operacao=tipo_operacao, limit=limite)
        if not busca.get('ok'):
            st.error(busca.get('erro', 'Não foi possível pesquisar PVLs.'))
            st.caption(busca.get('url'))
            return
        items = busca.get('items', [])
        st.success(f'{len(items)} PVL(s) localizado(s).')
        st.caption(f"Consulta principal: {busca.get('url')}")
        if not items:
            return
        opcoes = []
        mapa = {}
        for idx, item in enumerate(items, start=1):
            label = f"{idx}. {item.get('num_pvl') or 'sem num_pvl'} | {item.get('interessado') or 'sem ente'} | {item.get('uf') or 'UF?'} | {item.get('status') or 'sem status'}"
            opcoes.append(label)
            mapa[label] = item
        escolhido = st.selectbox('Selecione o PVL para diagnóstico detalhado', opcoes)
        item = mapa[escolhido]
        with st.spinner('Consultando detalhes multifonte do PVL selecionado...'):
            detalhes_resp = consultar_detalhes_multifonte(num_pvl=item.get('num_pvl'), num_processo=item.get('num_processo'))
        if not detalhes_resp.get('ok'):
            st.error(detalhes_resp.get('erro', 'Falha ao consultar detalhes do PVL.'))
            return
        detalhes = detalhes_resp.get('dados', {})
        resultado = diagnosticar_item(item, detalhes)
        blocos = [
            ('Dados do pleito', 'dados_pleito'),
            ('Checklist esperado', 'checklist_esperado'),
            ('Pendências prováveis', 'pendencias_provaveis'),
            ('Inconsistências detectadas', 'inconsistencias_detectadas'),
        ]
        cols = st.columns(2)
        for i, (titulo, chave) in enumerate(blocos):
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f'### {titulo}')
                    for item_txt in resultado.get(chave, []):
                        st.markdown(f'- {item_txt}')
        with st.expander('Integração com outros conjuntos públicos da API'):
            for linha in resultado.get('resumo_multifonte', []):
                st.markdown(f'- {linha}')
            for nome in ['fonte_resumo_cdp','fonte_resumo_cp','fonte_oc_cp','fonte_oc_cl','fonte_oc_tx']:
                if detalhes.get(nome):
                    st.caption(f"{nome}: {detalhes.get(nome)}")
        with st.expander('Mapeamento dos campos públicos da API'):
            st.markdown('### Campos presentes')
            for item_txt in resultado.get('campos_presentes', []):
                st.markdown(f'- {item_txt}')
            st.markdown('### Campos ausentes')
            for item_txt in resultado.get('campos_ausentes', []):
                st.markdown(f'- {item_txt}')
        with st.expander('Dados públicos retornados pela consulta'):
            st.json(resultado.get('dados_brutos', {}))


# ============================
# Motor técnico reforçado por operação (v12.5)
# ============================
import requests
from datetime import datetime
from urllib.parse import quote

API_BASE = "https://apidatalake.tesouro.gov.br/ords/sadipem/tt"
ENDPOINTS = {
    'pvl': f"{API_BASE}/pvl",
    'resumo_cdp': f"{API_BASE}/resumo_cdp",
    'resumo_cp': f"{API_BASE}/resumo_cronograma_pagamentos",
    'oc_cp': f"{API_BASE}/operacoes_contratadas_cronograma_pagamentos",
    'oc_cl': f"{API_BASE}/operacoes_contratadas_cronograma_liberacoes",
    'oc_tx': f"{API_BASE}/operacoes_contratadas_taxas_cambio",
}

API_FIELD_MAP = {
    'id_pleito': 'Identificação interna do PVL no SADIPEM',
    'tipo_interessado': 'Tipo de interessado',
    'interessado': 'Ente interessado',
    'cod_ibge': 'Código IBGE',
    'uf': 'UF do interessado',
    'num_pvl': 'Número do PVL',
    'status': 'Etapa/status atual do PVL',
    'num_processo': 'Número do processo',
    'data_protocolo': 'Data/hora do último envio à STN',
    'tipo_operacao': 'Tipo da operação ou garantia',
    'finalidade': 'Finalidade da operação',
    'tipo_credor': 'Tipo do credor',
    'instituicao_credora': 'Instituição credora',
    'credor': 'Credor',
    'moeda': 'Moeda da operação',
    'valor': 'Valor informado',
    'pvl_assoc_divida': 'Há dívida no CDP vinculada ao PVL (1/0)',
    'pvl_contratado_credor': 'Credor informou contratação (1/0)',
    'data_status': 'Data do status atual',
}

STATUS_GROUPS = {
    'inicial': {'Em preenchimento pelo credor', 'Em preenchimento pelo interessado', 'Assinado pelo interessado', 'Pendente de distribuição (PVL-IF)', 'Enviado à instituição financeira (PVL-IF)'},
    'analise': {'Em análise', 'Em análise garantia da União', 'Em análise PVL-IF', 'Em consulta jurídica'},
    'retificacao': {'Em retificação pelo credor', 'Em retificação pelo interessado', 'Em retificação pelo credor (PVL-IF)', 'Em retificação pelo interessado (PVL-IF)'},
    'final_favoravel': {'Deferido', 'Deferido (PVL-IF)', 'Deferido sem garantia da União', 'Encaminhado à PGFN com manifestação técnica favorável', 'Encaminhado à PGFN (decisão judicial)', 'Regularizado', 'Regular por decisão judicial'},
    'final_desfavoravel': {'Indeferido', 'Indeferido (PVL-IF)', 'Encaminhado à PGFN com manifestação técnica desfavorável', 'Pendente de regularização'},
    'arquivamento': {'Arquivado', 'Arquivado a pedido', 'Arquivado a pedido (PVL-IF)', 'Arquivado pela STN', 'Arquivado por decurso de prazo', 'Arquivado por decurso de prazo (PVL-IF)', 'PVL cancelado'},
    'suspensao': {'Sobrestado', 'Suspenso por decisão judicial'},
}

def parse_data(valor):
    if not valor:
        return None
    s = str(valor).strip()
    candidatos = [s, s[:19], s[:10]]
    for cand in candidatos:
        for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%d/%m/%Y'):
            try:
                return datetime.strptime(cand, fmt)
            except Exception:
                pass
    return None

def periodo_referencia(data_obj):
    if not data_obj:
        return 'indefinido'
    md = data_obj.month * 100 + data_obj.day
    if md <= 301:
        return 'ate_3003'
    if md <= 531:
        return 'pos_3003'
    if md <= 731:
        return 'pos_3005'
    if md <= 930:
        return 'pos_3007'
    if md <= 1130:
        return 'pos_3009'
    return 'pos_3011'

def grupo_status(status):
    s = status or ''
    for grupo, conjunto in STATUS_GROUPS.items():
        if s in conjunto:
            return grupo
    return 'desconhecido'

def api_get(url):
    headers = {'accept': 'application/json'}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data.get('items', data if isinstance(data, list) else [])

def montar_filtros_pvl(numero_pvl=None, num_processo=None, ente=None, uf=None, ano=None, status=None, tipo_operacao=None):
    filtros = []
    if numero_pvl:
        filtros.append(f"num_pvl=eq.{normalizar_numero_pvl(numero_pvl)}")
    if num_processo:
        filtros.append(f"num_processo=eq.{normalizar_numero_pvl(num_processo)}")
    if ente:
        filtros.append(f"interessado=ilike.*{quote(str(ente))}*")
    if uf:
        filtros.append(f"uf=eq.{quote(str(uf).upper())}")
    if status:
        filtros.append(f"status=ilike.*{quote(str(status))}*")
    if tipo_operacao:
        filtros.append(f"tipo_operacao=ilike.*{quote(str(tipo_operacao))}*")
    if ano:
        filtros.append(f"or=(data_status.like.{ano}-%25,data_protocolo.like.{ano}-%25,num_pvl.like.%25/{ano}-%25,num_processo.like.%25{ano}%25)")
    return filtros

def buscar_pvls(numero_pvl=None, num_processo=None, ente=None, uf=None, ano=None, status=None, tipo_operacao=None, limit=30):
    filtros = montar_filtros_pvl(numero_pvl, num_processo, ente, uf, ano, status, tipo_operacao)
    query = '&'.join(filtros + [f'limit={limit}']) if filtros else f'limit={limit}'
    url = f"{ENDPOINTS['pvl']}?{query}"
    try:
        items = api_get(url)
        return {'ok': True, 'items': items, 'url': url}
    except Exception as e:
        return {'ok': False, 'erro': str(e), 'url': url}

def consultar_detalhes_multifonte(num_pvl=None, num_processo=None):
    chave = normalizar_numero_pvl(num_pvl or num_processo or '')
    if not chave:
        return {'ok': False, 'erro': 'Chave de consulta inválida.'}
    pvl = buscar_pvls(numero_pvl=num_pvl, num_processo=num_processo, limit=5)
    if not pvl.get('ok') or not pvl.get('items'):
        return {'ok': False, 'erro': pvl.get('erro', 'PVL não localizado.'), 'fonte_pvl': pvl.get('url')}
    item = pvl['items'][0]
    num_pvl_real = item.get('num_pvl') or chave
    detalhes = {'pvl': item, 'fonte_pvl': pvl.get('url')}
    for nome, endpoint in ENDPOINTS.items():
        if nome == 'pvl':
            continue
        urls = [
            f"{endpoint}?num_pvl=eq.{quote(str(num_pvl_real))}&limit=200",
            f"{endpoint}?num_processo=eq.{quote(str(item.get('num_processo') or chave))}&limit=200",
        ]
        coletado = []
        usado = None
        for url in urls:
            try:
                dados = api_get(url)
                if dados:
                    coletado = dados
                    usado = url
                    break
            except Exception:
                pass
        detalhes[nome] = coletado
        detalhes[f'fonte_{nome}'] = usado
    return {'ok': True, 'dados': detalhes}

def extrair_dados_pvl(item: dict):
    dados = {k: item.get(k) for k in API_FIELD_MAP.keys()}
    if not dados.get('credor'):
        dados['credor'] = item.get('instituicao_credora')
    return dados

def campos_presentes_ausentes(dados: dict):
    presentes = []
    ausentes = []
    for k, desc in API_FIELD_MAP.items():
        v = dados.get(k)
        if v is None or v == '':
            ausentes.append(f'{k} - {desc}')
        else:
            presentes.append(f'{k} - {desc}: {v}')
    return presentes, ausentes

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
    if 'pef' in t:
        return 'pef'
    if 'lc 212' in t:
        return 'lc_212'
    if 'extern' in t:
        return 'externa'
    return 'interna'

def coletar_checklist_esperado_calibrado(familia: str, data_status_str: str):
    try:
        catalog = build_checklist_catalog()
        fam = catalog.get(familia, {})
        data_obj = parse_data(data_status_str)
        periodo = periodo_referencia(data_obj)
        itens = []
        chave_periodo = 'janeiro' if periodo == 'ate_3003' else periodo
        for aba, fases in fam.items():
            lista = fases.get(chave_periodo) or fases.get('janeiro') or []
            for item in lista[:4]:
                itens.append(f'[{aba}] {item}')
        if data_obj and data_obj.month <= 3:
            itens.append('[Documentos] Entre 01/01 e 30/03, revisar exigências ligadas ao exercício anterior fechado e documentos sazonais da modalidade, quando aplicáveis.')
        return itens or ['Não foi possível montar checklist esperado para a família identificada.']
    except Exception:
        return ['Não foi possível montar checklist esperado para a família identificada.']

def resumo_multifonte(detalhes):
    return {
        'resumo_cdp': len(detalhes.get('resumo_cdp', []) or []),
        'resumo_cp': len(detalhes.get('resumo_cp', []) or []),
        'oc_cp': len(detalhes.get('oc_cp', []) or []),
        'oc_cl': len(detalhes.get('oc_cl', []) or []),
        'oc_tx': len(detalhes.get('oc_tx', []) or []),
    }

def regras_base_por_operacao(familia, dados, counts, data_obj):
    pend, inc = [], []
    if familia == 'interna':
        pend += ['Conferir coerência entre fluxo do PVL interno, credor informado e eventuais cronogramas públicos das operações contratadas.']
        if counts['oc_cp'] == 0 and dados.get('pvl_contratado_credor') in (1, '1'):
            pend.append('Credor informou contratação, mas não foram retornados cronogramas públicos de pagamento em operações contratadas; conferir estágio e integração dos dados.')
    elif familia == 'externa':
        pend += ['Conferir rito próprio da operação externa e compatibilidade com moeda, taxas de câmbio e exigências correlatas.']
        if (dados.get('moeda') and str(dados.get('moeda')).upper() not in {'REAL', 'BRL', 'R$'}) and counts['oc_tx'] == 0:
            inc.append('Operação externa/moeda estrangeira sem retorno de taxas de câmbio públicas; conferir integração e consistência do cadastro.')
    elif familia == 'reestruturacao':
        pend += ['Confirmar troca efetiva de dívida, documentação da dívida antiga e evidências de enquadramento especial da modalidade.']
        if dados.get('pvl_assoc_divida') not in (1, '1'):
            inc.append('Reestruturação sem indicação pública de dívida associada no CDP; cenário tecnicamente sensível.')
        if counts['resumo_cdp'] == 0:
            pend.append('Não foram localizadas informações públicas do Resumo-CDP para operação ligada a reestruturação; conferir endpoint e disponibilidade dos dados.')
    elif familia == 'aro':
        pend += ['Confirmar documentação específica da ARO, rito próprio e aderência às restrições temporais da modalidade.']
        if dados.get('moeda') and str(dados.get('moeda')).upper() not in {'REAL', 'BRL', 'R$'}:
            inc.append('ARO com moeda não usual para a modalidade; conferir consistência do cadastro.')
    elif familia == 'regularizacao':
        pend += ['Confirmar documentos da operação irregular e eventual termo de quitação/regularização.']
        if grupo_status(dados.get('status')) == 'final_favoravel' and 'Regularizado' not in str(dados.get('status') or ''):
            pend.append('Pleito de regularização com status favorável diferente de Regularizado; conferir desfecho material do processo.')
    elif familia == 'consorcio':
        pend += ['Confirmar existência e coerência dos PVL de todos os entes participantes do consórcio.']
    elif familia == 'garantia_ente':
        pend += ['Confirmar autorização legislativa, contragarantias e limite global de garantias concedidas.']
    elif familia in {'lc_156','lc_159','lc_178','pef','lc_212'}:
        pend += ['Confirmar enquadramento estrito na lei complementar aplicável e aderência à documentação própria da hipótese legal.']
        if data_obj and data_obj.month <= 3:
            pend.append('No início do exercício, revisar também exigências sazonais da modalidade especial, inclusive documentos ligados ao exercício anterior fechado.')
    return pend, inc

def regras_por_cenario(familia: str, status: str, dados: dict, data_obj, detalhes: dict):
    grupo = grupo_status(status)
    pend = []
    inc = []
    counts = resumo_multifonte(detalhes)

    if grupo == 'retificacao':
        pend.append('O cenário de retificação sugere exigência anterior não integralmente atendida; revisar documentos e dados do sistema antes de novo envio.')
    if grupo == 'analise':
        pend.append('O cenário de análise sugere que o pleito já superou a fase inicial, mas ainda pode receber exigências complementares.')
    if grupo == 'final_favoravel' and dados.get('pvl_contratado_credor') not in (1, '1'):
        pend.append('Status favorável sem contratação informada pelo credor pode indicar operação ainda não efetivada; acompanhar prazo de validade da análise.')
    if grupo == 'final_desfavoravel':
        inc.append('O cenário do status atual é materialmente desfavorável ao pleito e exige revisão de enquadramento ou saneamento.')
    if grupo == 'arquivamento':
        pend.append('O cenário de arquivamento exige avaliar reabertura, novo PVL ou perda de utilidade da análise anterior.')
    if grupo == 'suspensao':
        pend.append('Há suspensão/sobrestamento; conferir motivo processual antes de qualquer conclusão operacional.')

    pend_op, inc_op = regras_base_por_operacao(familia, dados, counts, data_obj)
    pend.extend(pend_op)
    inc.extend(inc_op)

    if data_obj and data_obj.month <= 3:
        pend.append('Como a data do status está no início do exercício, revisar documentos sensíveis ao exercício anterior fechado e exigências sazonais do MIP.')

    if dados.get('pvl_assoc_divida') in (1, '1') and familia not in {'reestruturacao', 'regularizacao'}:
        inc.append('Há vínculo com dívida no CDP em modalidade não tipicamente associada a reestruturação/regularização; conferir enquadramento.')
    if dados.get('pvl_contratado_credor') in (1, '1') and grupo in {'inicial', 'retificacao'}:
        inc.append('Há informação de contratação pelo credor em cenário processual ainda inicial/retificatório; conferir coerência temporal do PVL.')
    if grupo in {'final_favoravel', 'analise'} and counts['resumo_cp'] == 0 and counts['oc_cp'] == 0:
        pend.append('Não foram localizados cronogramas públicos de pagamento; conferir se a ausência decorre do estágio do PVL ou da integração dos dados públicos.')
    if counts['oc_cp'] > 0 and counts['oc_cl'] == 0:
        pend.append('Há cronograma público de pagamentos em Operações Contratadas sem cronograma público de liberações correspondente; conferir se isso decorre da natureza da operação.')
    if dados.get('pvl_assoc_divida') in (1, '1') and counts['resumo_cdp'] == 0:
        pend.append('O PVL indica vínculo com dívida/CDP, mas não foram retornadas informações públicas do Resumo-CDP; conferir disponibilidade do endpoint.')
    if not dados.get('num_pvl') and not dados.get('num_processo'):
        inc.append('Os dados públicos retornados não trouxeram identificação suficiente do PVL/processo; consulta deve ser revista.')
    if not dados.get('status'):
        inc.append('O campo status não foi retornado; o diagnóstico fica materialmente prejudicado.')
    if not dados.get('tipo_operacao'):
        inc.append('O campo tipo_operacao não foi retornado; a inferência da família ficou prejudicada.')
    return list(dict.fromkeys(pend)), list(dict.fromkeys(inc)), counts

def diagnosticar_item(item: dict, detalhes: dict):
    dados = extrair_dados_pvl(item)
    familia = inferir_familia_por_tipo(dados.get('tipo_operacao'))
    data_obj = parse_data(dados.get('data_status'))
    presentes, ausentes = campos_presentes_ausentes(dados)
    checklist = coletar_checklist_esperado_calibrado(familia, dados.get('data_status'))
    pendencias, inconsistencias, counts = regras_por_cenario(familia, dados.get('status') or '', dados, data_obj, detalhes)
    dados_pleito = [
        f"Número do PVL: {dados.get('num_pvl') or 'Não informado'}",
        f"Processo: {dados.get('num_processo') or 'Não informado'}",
        f"Interessado: {dados.get('interessado') or 'Não informado'} / UF: {dados.get('uf') or 'N/I'}",
        f"Tipo do interessado: {dados.get('tipo_interessado') or 'Não informado'}",
        f"Tipo de operação: {dados.get('tipo_operacao') or 'Não informado'}",
        f"Finalidade: {dados.get('finalidade') or 'Não informada'}",
        f"Família inferida: {familia}",
        f"Status atual: {dados.get('status') or 'Não informado'} / Grupo de status: {grupo_status(dados.get('status'))}",
        f"Data do status: {dados.get('data_status') or 'Não informada'} / Data de protocolo: {dados.get('data_protocolo') or 'Não informada'}",
        f"Credor: {dados.get('credor') or 'Não informado'} / Tipo de credor: {dados.get('tipo_credor') or 'Não informado'}",
        f"Valor/moeda: {dados.get('valor') or 'Não informado'} / {dados.get('moeda') or 'N/I'}",
        f"Resumo multifonte: Resumo-CDP={counts['resumo_cdp']}, Resumo-CP={counts['resumo_cp']}, OC-CP={counts['oc_cp']}, OC-CL={counts['oc_cl']}, OC-TX={counts['oc_tx']}",
        f"Campos públicos presentes: {len(presentes)} / Campos públicos ausentes: {len(ausentes)}",
    ]
    if not pendencias:
        pendencias.append('Nenhuma pendência provável inferida apenas pelos dados públicos do PVL; ainda é necessária conferência documental.')
    if not inconsistencias:
        inconsistencias.append('Nenhuma inconsistência evidente inferida apenas com base nos dados públicos e nas regras técnicas atuais.')
    return {
        'dados_pleito': dados_pleito,
        'checklist_esperado': checklist,
        'pendencias_provaveis': pendencias,
        'inconsistencias_detectadas': inconsistencias,
        'dados_brutos': dados,
        'campos_presentes': presentes,
        'campos_ausentes': ausentes,
        'familia_identificada': familia,
        'resumo_multifonte': counts,
    }

def render_consulta_pvl_ui(st):
    st.subheader('Consulta PVL + Diagnóstico')
    st.caption('Busca ampliada com motor técnico reforçado por tipo de operação, status, data e integração multifonte da API pública do SADIPEM.')
    c1, c2, c3 = st.columns(3)
    with c1:
        numero_pvl = st.text_input('Número do PVL')
        ente = st.text_input('Ente interessado')
        ano = st.text_input('Ano', placeholder='2025')
    with c2:
        num_processo = st.text_input('Número do processo')
        uf = st.text_input('UF', placeholder='PE')
        status = st.text_input('Status')
    with c3:
        tipo_operacao = st.text_input('Tipo de operação')
        limite = st.slider('Limite de resultados', min_value=1, max_value=50, value=15)
    acionar = st.button('Pesquisar PVLs', type='primary', use_container_width=True)
    if acionar:
        with st.spinner('Pesquisando PVLs na API pública do SADIPEM...'):
            busca = buscar_pvls(numero_pvl=numero_pvl, num_processo=num_processo, ente=ente, uf=uf, ano=ano, status=status, tipo_operacao=tipo_operacao, limit=limite)
        if not busca.get('ok'):
            st.error(busca.get('erro', 'Não foi possível pesquisar PVLs.'))
            st.caption(busca.get('url'))
            return
        items = busca.get('items', [])
        st.success(f'{len(items)} PVL(s) localizado(s).')
        st.caption(f"Consulta principal: {busca.get('url')}")
        if not items:
            return
        opcoes = []
        mapa = {}
        for idx, item in enumerate(items, start=1):
            label = f"{idx}. {item.get('num_pvl') or 'sem num_pvl'} | {item.get('interessado') or 'sem ente'} | {item.get('uf') or 'UF?'} | {item.get('status') or 'sem status'}"
            opcoes.append(label)
            mapa[label] = item
        escolhido = st.selectbox('Selecione o PVL para diagnóstico detalhado', opcoes)
        item = mapa[escolhido]
        with st.spinner('Consultando detalhes multifonte do PVL selecionado...'):
            detalhes_resp = consultar_detalhes_multifonte(num_pvl=item.get('num_pvl'), num_processo=item.get('num_processo'))
        if not detalhes_resp.get('ok'):
            st.error(detalhes_resp.get('erro', 'Falha ao consultar detalhes do PVL.'))
            return
        detalhes = detalhes_resp.get('dados', {})
        resultado = diagnosticar_item(item, detalhes)
        blocos = [
            ('Dados do pleito', 'dados_pleito'),
            ('Checklist esperado', 'checklist_esperado'),
            ('Pendências prováveis', 'pendencias_provaveis'),
            ('Inconsistências detectadas', 'inconsistencias_detectadas'),
        ]
        cols = st.columns(2)
        for i, (titulo, chave) in enumerate(blocos):
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f'### {titulo}')
                    for item_txt in resultado.get(chave, []):
                        st.markdown(f'- {item_txt}')
        with st.expander('Integração com outros conjuntos públicos da API'):
            for nome, valor in resultado.get('resumo_multifonte', {}).items():
                st.markdown(f'- {nome}: {valor} registro(s)')
        with st.expander('Mapeamento dos campos públicos da API'):
            st.markdown('### Campos presentes')
            for item_txt in resultado.get('campos_presentes', []):
                st.markdown(f'- {item_txt}')
            st.markdown('### Campos ausentes')
            for item_txt in resultado.get('campos_ausentes', []):
                st.markdown(f'- {item_txt}')
        with st.expander('Dados públicos retornados pela consulta'):
            st.json(resultado.get('dados_brutos', {}))
