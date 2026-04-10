import streamlit as st
import pandas as pd
from datetime import date

from decision_engine_v10 import (
    buscar_pvls,
    consultar_detalhes_multifonte,
    diagnosticar_item,
)
from rules_operacoes_v10 import build_checklist_catalog, explain_period_rules

st.set_page_config(page_title="MIP PVL Assistant v12.5.2", layout="wide")


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
    st.subheader("Operações e validações")
    st.caption("Visão normativa por tipo de operação, preservando a lógica de orientações e validações do MIP.")
    catalog = build_checklist_catalog()
    modalidades = sorted(catalog.keys())
    modalidade = st.selectbox("Tipo de operação", modalidades, index=modalidades.index("interna") if "interna" in modalidades else 0)
    data_ref = st.date_input("Data de referência normativa", value=date.today(), key="op_data_ref")
    explicacao = explain_period_rules(modalidade, data_ref)
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.container(border=True):
            st.markdown("### Janela normativa")
            st.write(f"Modalidade: {modalidade}")
            st.write(f"Data de referência: {data_ref.strftime('%d/%m/%Y')}")
            st.write(f"Janela ativa: {explicacao['janela_label']}")
    with c2:
        with st.container(border=True):
            st.markdown("### Regras e observações")
            for linha in explicacao["observacoes_gerais"]:
                st.markdown(f"- {linha}")
    st.markdown("### Checklist condicional por modalidade")
    df = pd.DataFrame(explicacao["linhas"])
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)


def render_upload_tab():
    st.subheader("Upload do MIP")
    st.caption("Área preservada para reincorporar o fluxo documental do MIP sem perder a nova pesquisa de PVL/API.")
    arquivo = st.file_uploader("Envie um arquivo do MIP (PDF/XLSX/CSV)", type=["pdf", "xlsx", "csv"])
    if arquivo is not None:
        st.success(f"Arquivo recebido: {arquivo.name}")
        st.info("Nesta v12.5.2, a área foi recomposta visualmente para preservar o fluxo. O tratamento analítico do upload será reconectado na próxima iteração.")
    else:
        st.info("Selecione um arquivo para manter o fluxo de upload disponível na interface.")


def render_sadipem_normativo_tab():
    st.subheader("SADIPEM normativo")
    st.caption("Aba normativa preservada: mostra o que deve ser observado por tipo de operação e pela data de referência do período.")
    catalog = build_checklist_catalog()
    modalidades = sorted(catalog.keys())
    modalidade = st.selectbox("Tipo de operação da aba SADIPEM", modalidades, index=modalidades.index("interna") if "interna" in modalidades else 0, key="sadipem_modalidade")
    data_ref = st.date_input("Data específica para regras do período", value=date.today(), key="sadipem_data_ref")
    explicacao = explain_period_rules(modalidade, data_ref)

    c1, c2 = st.columns([1, 2])
    with c1:
        with st.container(border=True):
            st.markdown("### Leitura do período")
            st.write(f"Janela ativa: {explicacao['janela_label']}")
            st.write(f"Data de referência: {data_ref.strftime('%d/%m/%Y')}")
    with c2:
        with st.container(border=True):
            st.markdown("### Exemplos de interpretação")
            for linha in explicacao["observacoes_gerais"]:
                st.markdown(f"- {linha}")

    st.markdown("### Checklist condicional por modalidade")
    df = pd.DataFrame(explicacao["linhas"])
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)


def render_pesquisa_pvl_api_tab():
    st.subheader("Pesquisa PVL/API")
    st.caption("Pesquisa factual dos PVLs na API pública, separada da data normativa. Aqui o filtro temporal é por período de consulta.")

    c1, c2, c3 = st.columns(3)
    with c1:
        numero_pvl = st.text_input("Número do PVL")
        ente = st.text_input("Ente interessado")
        data_inicio = st.date_input("Data inicial do período", value=date(date.today().year, 1, 1), key="api_data_inicio")
    with c2:
        num_processo = st.text_input("Número do processo")
        uf = st.text_input("UF", placeholder="PE")
        data_fim = st.date_input("Data final do período", value=date.today(), key="api_data_fim")
    with c3:
        tipo_operacao = st.text_input("Tipo de operação")
        status = st.text_input("Status")
        campo_periodo = st.selectbox("Aplicar período em", ["Ambos (data_status e data_protocolo)", "Apenas data_status", "Apenas data_protocolo"])
        limite = st.slider("Limite de resultados", min_value=1, max_value=100, value=20)

    if st.button("Pesquisar PVLs na API", type="primary", use_container_width=True):
        with st.spinner("Pesquisando PVLs por período na API pública do SADIPEM..."):
            busca = buscar_pvls(
                numero_pvl=numero_pvl,
                num_processo=num_processo,
                ente=ente,
                uf=uf,
                status=status,
                tipo_operacao=tipo_operacao,
                data_inicio=data_inicio,
                data_fim=data_fim,
                campo_periodo=campo_periodo,
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


def main():
    st.title("MIP PVL Assistant v12.5.2")
    st.caption("Versão recomposta: Operações e SADIPEM normativa preservadas, Upload visível, Base tabular mantida e Pesquisa PVL/API separada com filtro por período.")

    with st.sidebar:
        st.markdown("## Base normativa")
        st.write("Versão da base: v12.5.2")
        st.write("Foco da versão: restaurar a visão normativa e separar a pesquisa factual de PVL por período na API pública.")

    tabs = st.tabs(["Operações", "Upload do MIP", "SADIPEM", "Pesquisa PVL/API", "Base tabular"])
    with tabs[0]:
        render_operacoes_tab()
    with tabs[1]:
        render_upload_tab()
    with tabs[2]:
        render_sadipem_normativo_tab()
    with tabs[3]:
        render_pesquisa_pvl_api_tab()
    with tabs[4]:
        render_base_tabular_tab()


if __name__ == "__main__":
    main()
