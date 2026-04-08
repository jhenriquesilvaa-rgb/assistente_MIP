
from datetime import date

import pandas as pd
import streamlit as st

from rules.rules_operacoes_v10 import (
    RULES_VERSION,
    build_operacoes_df,
    get_operacoes_rules,
    get_sadipem_field_matrix,
)
from services.decision_engine_v10 import (
    evaluate_operation,
    build_review_dataframe,
    compare_mip_text_to_rules,
    extract_section_titles,
    extract_change_signals,
    detect_text_from_uploaded_file,
    build_structured_update_suggestions,
    get_reference_period_rules,
    build_sadipem_action_plan,
)

st.set_page_config(page_title="MIP PVL Assistante", layout="wide")

st.title("MIP PVL Assistante")
st.caption("Protótipo para apoio ao envio de PVL com lógica por tipo de operação, data de referência, canal e orientação campo a campo do SADIPEM.")

operacoes_rules = get_operacoes_rules()
operacoes_df = build_operacoes_df()
sadipem_df = get_sadipem_field_matrix()

with st.sidebar:
    st.subheader("Base normativa")
    st.write(f"Versão da base: **{RULES_VERSION}**")
    st.write(f"Operações mapeadas: **{len(operacoes_rules)}**")
    st.write("A aba SADIPEM agora cruza tipo de operação e data de referência para sugerir o que fazer em cada campo crítico.")

aba1, aba2, aba3, aba4 = st.tabs([
    "Operações",
    "Upload do MIP",
    "SADIPEM",
    "Base tabular",
])

with aba1:
    st.subheader("Consulta operacional")

    c1, c2 = st.columns([2, 1])
    with c1:
        op_label = st.selectbox(
            "Tipo de operação",
            options=list(operacoes_rules.keys()),
            format_func=lambda x: operacoes_rules[x]["label"],
        )
    with c2:
        data_ref = st.date_input("Data de referência", value=date.today(), format="DD/MM/YYYY")

    result = evaluate_operation(op_label, data_ref, operacoes_rules)
    regra = result["regra"]

    m1, m2, m3 = st.columns(3)
    m1.metric("Canal principal", str(regra.get("canal_principal", "-")))
    m2.metric("Origem do envio", str(regra.get("origem_envio", "-")))
    m3.metric("Exige garantia da União", "Sim" if regra.get("garantia_uniao") is True else ("Não" if regra.get("garantia_uniao") is False else "Depende"))

    with st.expander("Fluxo resumido", expanded=True):
        for item in regra.get("fluxo_resumido", []):
            st.markdown(f"- {item}")

    col_a, col_b = st.columns(2)
    with col_a:
        with st.expander("Documentos-base", expanded=True):
            for item in regra.get("documentos_base", []):
                st.markdown(f"- {item}")
    with col_b:
        with st.expander("Ações / observações", expanded=True):
            for item in regra.get("observacoes", []):
                st.markdown(f"- {item}")

    st.subheader("Gatilhos por data")
    gatilhos = result.get("gatilhos_ativos", [])
    if gatilhos:
        for g in gatilhos:
            st.markdown(f"- **{g['nome']}**: {g['descricao']}")
    else:
        st.info("Nenhum gatilho temporal específico ativado para a data informada.")

with aba2:
    st.subheader("Upload do MIP")
    st.write(
        "Envie o MIP em PDF, TXT ou MD. O sistema extrai texto, compara com a base atual, detecta sinais de mudança e propõe ajustes estruturados por operação."
    )

    uploaded = st.file_uploader(
        "Upload do MIP",
        type=["pdf", "txt", "md"],
        accept_multiple_files=False,
    )

    texto_manual = st.text_area(
        "Ou cole o texto do MIP aqui (opcional)",
        height=180,
        placeholder="Cole aqui o texto integral ou parcial do MIP se quiser priorizar o conteúdo colado.",
    )

    usar_texto_colado = st.checkbox("Priorizar o texto colado acima", value=False)

    if st.button("Analisar MIP e gerar proposta de atualização"):
        mip_text = ""
        fonte_texto = ""

        if usar_texto_colado and texto_manual.strip():
            mip_text = texto_manual
            fonte_texto = "texto colado"
        elif uploaded is not None:
            mip_text, fonte_texto = detect_text_from_uploaded_file(uploaded)
            if not mip_text.strip() and texto_manual.strip():
                mip_text = texto_manual
                fonte_texto = "texto colado (fallback)"
        elif texto_manual.strip():
            mip_text = texto_manual
            fonte_texto = "texto colado"

        if not mip_text.strip():
            st.error("Não foi possível obter texto para análise. Faça upload de um arquivo legível ou cole o texto do MIP.")
        else:
            st.success(f"Texto carregado com sucesso via: {fonte_texto}.")

            comparison = compare_mip_text_to_rules(mip_text, operacoes_rules)
            section_titles = extract_section_titles(mip_text)
            change_signals = extract_change_signals(mip_text)
            review_df = build_review_dataframe(comparison, section_titles, change_signals)
            updates_df = build_structured_update_suggestions(mip_text, operacoes_rules)

            st.markdown("### Resumo da comparação")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Temas monitorados", comparison["summary"]["total_themes"])
            r2.metric("Cobertos no texto", comparison["summary"]["present_themes"])
            r3.metric("Não detectados", comparison["summary"]["missing_themes"])
            r4.metric("Sugestões estruturadas", len(updates_df))

            st.markdown("### Cobertura temática")
            comp_df = pd.DataFrame(comparison["theme_results"])
            st.dataframe(comp_df, use_container_width=True, hide_index=True)

            st.markdown("### Comparação fina")
            cf1, cf2 = st.columns(2)
            with cf1:
                st.markdown("**Seções/títulos detectados**")
                if section_titles:
                    for t in section_titles[:150]:
                        st.markdown(f"- {t}")
                else:
                    st.info("Nenhum título/seção detectado automaticamente.")
            with cf2:
                st.markdown("**Sinais de alteração detectados**")
                if change_signals:
                    for s in change_signals[:150]:
                        st.markdown(f"- {s}")
                else:
                    st.info("Nenhum sinal explícito de alteração detectado.")

            st.markdown("### Sugestões estruturadas de atualização da base")
            if not updates_df.empty:
                st.dataframe(updates_df, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma sugestão estruturada foi gerada automaticamente para o texto analisado.")

            st.markdown("### Lista de revisão humana")
            st.dataframe(review_df, use_container_width=True, hide_index=True)

            csv_review = review_df.to_csv(index=False).encode("utf-8-sig")
            csv_updates = updates_df.to_csv(index=False).encode("utf-8-sig") if not updates_df.empty else b""

            d1, d2 = st.columns(2)
            with d1:
                st.download_button(
                    "Baixar CSV de revisão",
                    data=csv_review,
                    file_name="revisao_mip_upload_v11.csv",
                    mime="text/csv",
                )
            with d2:
                if not updates_df.empty:
                    st.download_button(
                        "Baixar CSV de sugestões estruturadas",
                        data=csv_updates,
                        file_name="sugestoes_estruturadas_mip_v11.csv",
                        mime="text/csv",
                    )

with aba3:
    st.subheader("SADIPEM")
    st.write("Escolha o tipo de operação e a data de referência. A tela abaixo cruza regras do MIP para dizer o que fazer em cada campo crítico do SADIPEM.")

    s1, s2 = st.columns([2, 1])
    with s1:
        op_sadipem = st.selectbox(
            "Tipo de operação",
            options=list(operacoes_rules.keys()),
            key="sadipem_select",
            format_func=lambda x: operacoes_rules[x]["label"],
        )
    with s2:
        data_ref_sadipem = st.date_input("Data de referência", value=date.today(), key="sadipem_date", format="DD/MM/YYYY")

    filtro = sadipem_df[sadipem_df["operacao_codigo"] == op_sadipem].copy()
    referencias = pd.DataFrame(get_reference_period_rules(op_sadipem, data_ref_sadipem))
    plano = pd.DataFrame(build_sadipem_action_plan(op_sadipem, data_ref_sadipem, sadipem_df))

    st.markdown("### Leitura operacional da data")
    res_sad = evaluate_operation(op_sadipem, data_ref_sadipem, operacoes_rules)
    gatilhos_sad = res_sad.get("gatilhos_ativos", [])
    if gatilhos_sad:
        for g in gatilhos_sad:
            st.markdown(f"- **{g['nome']}**: {g['descricao']}")
    else:
        st.info("Sem gatilho temporal adicional mapeado para esta data.")

    st.markdown("### O que preencher / atualizar conforme a data de referência")
    if not referencias.empty:
        st.dataframe(referencias, use_container_width=True, hide_index=True)
    else:
        st.warning("Ainda não há regra temporal detalhada para esta operação. Precisamos modelar esse rito específico.")

    st.markdown("### Plano de ação campo a campo")
    if not plano.empty:
        st.dataframe(plano, use_container_width=True, hide_index=True)
        csv_plano = plano.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Baixar plano SADIPEM em CSV",
            data=csv_plano,
            file_name=f"sadipem_plano_{op_sadipem}_{data_ref_sadipem.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.warning("Ainda não há plano de ação detalhado para esta operação.")

    st.markdown("### Matriz estrutural da operação no SADIPEM")
    if not filtro.empty:
        st.dataframe(
            filtro[["aba", "campo", "papel_do_campo", "quando_alterar", "observacao"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Ainda não há matriz estrutural específica cadastrada para esta operação.")

    st.markdown("### Observações operacionais da modalidade")
    for obs in operacoes_rules[op_sadipem].get("sadipem_notas", []):
        st.markdown(f"- {obs}")

with aba4:
    st.subheader("Base tabular")
    st.markdown("**Operações**")
    st.dataframe(operacoes_df, use_container_width=True, hide_index=True)
    st.markdown("**Matriz SADIPEM**")
    st.dataframe(sadipem_df, use_container_width=True, hide_index=True)
