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

st.set_page_config(page_title="MIP PVL Assistant v11.9", layout="wide")

st.title("MIP PVL Assistant v11.9")
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
