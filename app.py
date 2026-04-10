import streamlit as st
import pandas as pd
from datetime import date

from decision_engine_v10 import (
    buscar_pvls,
    consultar_detalhes_multifonte,
    diagnosticar_item,
)
from rules_operacoes_v10 import build_checklist_catalog

st.set_page_config(page_title="MIP PVL Assistant v12.5.1", layout="wide")


@st.cache_data(show_spinner=False)
def carregar_base_tabular():
    rows = []
    catalog = build_checklist_catalog()
    for modalidade, abas in catalog.items():
        for aba, janelas in abas.items():
            for janela, itens in janelas.items():
                for item in itens:
                    rows.append({
                        "modalidade": modalidade,
                        "aba": aba,
                        "janela": janela,
                        "item_checklist": item,
                    })
    return pd.DataFrame(rows)


def render_operacoes_tab():
    st.subheader("Operações")
    st.info("Nesta versão limpa, a prioridade foi sanear a aba SADIPEM com pesquisa real de PVL e diagnóstico técnico. A aba Operações foi mantida como placeholder de continuidade.")


def render_upload_tab():
    st.subheader("Upload do MIP")
    st.info("A rotina de upload do MIP pode ser reincorporada depois. Nesta v12.5.1 limpa, o foco foi estabilizar a pesquisa e o diagnóstico de PVLs pela API pública.")


def render_base_tabular_tab():
    st.subheader("Base tabular")
    df = carregar_base_tabular()
    c1, c2 = st.columns([2, 1])
    with c1:
        filtro_modalidade = st.text_input("Filtrar modalidade", value="")
    with c2:
        limite = st.number_input("Máx. linhas", min_value=10, max_value=5000, value=200, step=10)
    if filtro_modalidade:
        df = df[df["modalidade"].str.contains(filtro_modalidade, case=False, na=False)]
    st.dataframe(df.head(int(limite)), use_container_width=True, hide_index=True)


def render_sadipem_tab():
    st.subheader("SADIPEM")
    st.caption("Pesquisa real de PVLs com integração aos conjuntos públicos da API e diagnóstico técnico por modalidade, status, data e sinais multifonte.")

    c1, c2, c3 = st.columns(3)
    with c1:
        numero_pvl = st.text_input("Número do PVL")
        ente = st.text_input("Ente interessado")
        ano = st.text_input("Ano", placeholder="2025")
    with c2:
        num_processo = st.text_input("Número do processo")
        uf = st.text_input("UF", placeholder="PE")
        status = st.text_input("Status")
    with c3:
        tipo_operacao = st.text_input("Tipo de operação")
        limite = st.slider("Limite de resultados", min_value=1, max_value=50, value=15)
        data_ref = st.date_input("Data de referência", value=date.today())

    st.caption(f"Data de referência informada: {data_ref.strftime('%d/%m/%Y')}")

    if st.button("Pesquisar PVLs", type="primary", use_container_width=True):
        with st.spinner("Pesquisando PVLs na API pública do SADIPEM..."):
            busca = buscar_pvls(
                numero_pvl=numero_pvl,
                num_processo=num_processo,
                ente=ente,
                uf=uf,
                ano=ano,
                status=status,
                tipo_operacao=tipo_operacao,
                limit=limite,
            )

        if not busca.get("ok"):
            st.error(busca.get("erro", "Não foi possível pesquisar PVLs."))
            st.caption(busca.get("url", ""))
            return

        items = busca.get("items", [])
        st.success(f"{len(items)} PVL(s) localizado(s).")
        st.caption(f"Consulta principal: {busca.get('url', '')}")

        if not items:
            return

        resumo_df = pd.DataFrame(items)
        colunas_exibir = [
            c for c in [
                "num_pvl", "num_processo", "interessado", "uf", "status",
                "tipo_operacao", "data_status", "data_protocolo", "valor", "moeda"
            ] if c in resumo_df.columns
        ]
        if colunas_exibir:
            st.dataframe(resumo_df[colunas_exibir], use_container_width=True, hide_index=True)

        opcoes = []
        mapa = {}
        for idx, item in enumerate(items, start=1):
            label = f"{idx}. {item.get('num_pvl') or 'sem num_pvl'} | {item.get('interessado') or 'sem ente'} | {item.get('uf') or 'UF?'} | {item.get('status') or 'sem status'}"
            opcoes.append(label)
            mapa[label] = item

        escolhido = st.selectbox("Selecione o PVL para diagnóstico detalhado", opcoes)
        item = mapa[escolhido]

        with st.spinner("Consultando detalhes multifonte do PVL selecionado..."):
            detalhes_resp = consultar_detalhes_multifonte(
                num_pvl=item.get("num_pvl"),
                num_processo=item.get("num_processo"),
            )

        if not detalhes_resp.get("ok"):
            st.error(detalhes_resp.get("erro", "Falha ao consultar detalhes do PVL."))
            return

        detalhes = detalhes_resp.get("dados", {})
        resultado = diagnosticar_item(item, detalhes)

        blocos = [
            ("Dados do pleito", "dados_pleito"),
            ("Checklist esperado", "checklist_esperado"),
            ("Pendências prováveis", "pendencias_provaveis"),
            ("Inconsistências detectadas", "inconsistencias_detectadas"),
        ]
        cols = st.columns(2)
        for i, (titulo, chave) in enumerate(blocos):
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f"### {titulo}")
                    for linha in resultado.get(chave, []):
                        st.markdown(f"- {linha}")

        with st.expander("Integração com outros conjuntos públicos da API"):
            for nome, valor in resultado.get("resumo_multifonte", {}).items():
                st.markdown(f"- {nome}: {valor} registro(s)")

        with st.expander("Mapeamento dos campos públicos da API"):
            st.markdown("### Campos presentes")
            for linha in resultado.get("campos_presentes", []):
                st.markdown(f"- {linha}")
            st.markdown("### Campos ausentes")
            for linha in resultado.get("campos_ausentes", []):
                st.markdown(f"- {linha}")

        with st.expander("Dados públicos retornados pela consulta"):
            st.json(resultado.get("dados_brutos", {}))


def main():
    st.title("MIP PVL Assistant v12.5.1")
    st.caption("Versão saneada para publicação: aba SADIPEM reconstruída com busca real por PVL, ente, ano, status, UF e tipo de operação.")

    with st.sidebar:
        st.markdown("## Base normativa")
        st.write("Versão da base: v12.5.1")
        st.write("Foco da versão: estabilizar a aba SADIPEM para pesquisa real de PVLs e diagnóstico técnico publicável no GitHub/Streamlit.")

    tab1, tab2, tab3, tab4 = st.tabs(["Operações", "Upload do MIP", "SADIPEM", "Base tabular"])
    with tab1:
        render_operacoes_tab()
    with tab2:
        render_upload_tab()
    with tab3:
        render_sadipem_tab()
    with tab4:
        render_base_tabular_tab()


if __name__ == "__main__":
    main()
