import io
import re
from datetime import date
from typing import Dict, List, Tuple

import pandas as pd


def _month_day(d: date) -> str:
    return d.strftime("%m-%d")


def _in_range_md(target_md: str, start_md: str, end_md: str) -> bool:
    return start_md <= target_md <= end_md


def evaluate_operation(op_key: str, ref_date: date, operacoes_rules: Dict):
    regra = operacoes_rules[op_key]
    active = []
    md = _month_day(ref_date)

    for g in regra.get("gatilhos_data", []):
        tipo = g.get("tipo")
        if tipo == "range_md" and _in_range_md(md, g["inicio"], g["fim"]):
            active.append(g)
        elif tipo == "after_md" and md > g["data"]:
            active.append(g)

    return {"regra": regra, "gatilhos_ativos": active}


def get_reference_period_rules(op_key: str, ref_date: date) -> List[Dict]:
    md = _month_day(ref_date)
    after_0130 = md > "01-30"
    after_0330 = md > "03-30"

    common_jan = {
        "RREO_ultimo_exercicio_anterior": "6º bimestre do exercício anterior (se ainda não publicado, manter a referência ao 6º bimestre)",
        "RREO_exigivel_corrente": "Até 30/03: usar o Anexo 1 da Lei 4.320/1964 publicado com a LOA do exercício em curso",
        "RREO_RCL_corrente": "5º bimestre do exercício anterior; usar o 6º bimestre se já estiver publicado",
        "RGF_exigivel": "2º quadrimestre do exercício anterior; ou 1º semestre do exercício anterior para município optante do art. 63; usar o 3º quadrimestre / 2º semestre se já publicado",
        "observacao": "Regra de transição de janeiro do MIP, aplicada especialmente à aba Informações contábeis e aos cronogramas/declarações.",
    }

    common_after_0130 = {
        "RREO_ultimo_exercicio_anterior": "6º bimestre do exercício anterior homologado no Siconfi",
        "RREO_exigivel_corrente": "Último RREO exigível do exercício em curso; até 30/03 ainda pode haver uso do Anexo 1 da LOA para o exercício corrente",
        "RREO_RCL_corrente": "Último RREO exigível, com o exercício anterior fechado já refletido",
        "RGF_exigivel": "3º quadrimestre do exercício anterior; ou 2º semestre do exercício anterior para município optante do art. 63",
        "observacao": "Após 30/01, passam a valer os relatórios do exercício anterior fechado e novas certidões/declarações podem ser exigidas.",
    }

    def build_dynamic_after_0330(target_date: date):
        month = target_date.month
        day = target_date.day

        if (month, day) <= (5, 30):
            rreo_bim = "1º bimestre do exercício em curso homologado no Siconfi"
            rreo_rcl = "1º bimestre do exercício em curso"
            etapa_extra = "Março até 30/05"
        elif (month, day) <= (7, 30):
            rreo_bim = "2º bimestre do exercício em curso homologado no Siconfi"
            rreo_rcl = "2º bimestre do exercício em curso"
            etapa_extra = "Após 30/05 até 30/07"
        elif (month, day) <= (9, 30):
            rreo_bim = "3º bimestre do exercício em curso homologado no Siconfi"
            rreo_rcl = "3º bimestre do exercício em curso"
            etapa_extra = "Após 30/07 até 30/09"
        elif (month, day) <= (11, 30):
            rreo_bim = "4º bimestre do exercício em curso homologado no Siconfi"
            rreo_rcl = "4º bimestre do exercício em curso"
            etapa_extra = "Após 30/09 até 30/11"
        else:
            rreo_bim = "5º bimestre do exercício em curso homologado no Siconfi"
            rreo_rcl = "5º bimestre do exercício em curso"
            etapa_extra = "Após 30/11"

        if (month, day) <= (7, 30):
            rgf = "3º quadrimestre do exercício anterior; ou 2º semestre do exercício anterior para município optante do art. 63"
        elif (month, day) <= (9, 30):
            rgf = "1º semestre do exercício em curso para município optante do art. 63; ou último RGF exigível aplicável no período"
        else:
            rgf = "2º quadrimestre do exercício em curso; ou 1º semestre do exercício em curso para município optante do art. 63"

        return {
            "RREO_ultimo_exercicio_anterior": "6º bimestre do exercício anterior homologado no Siconfi",
            "RREO_exigivel_corrente": rreo_bim,
            "RREO_RCL_corrente": rreo_rcl,
            "RGF_exigivel": rgf,
            "observacao": f"Após 30/03, o Anexo 1 deixa de ser a base ordinária. A referência do exercício corrente passa a acompanhar o último RREO/RGF exigível na data ({etapa_extra}).",
        }

    common_after_0330 = build_dynamic_after_0330(ref_date)

    base_sem_gu = {
        "ate_0130": common_jan,
        "apos_0130": common_after_0130,
        "apos_0330": common_after_0330,
        "declaracao_chefe": {
            "ate_0130": "Preencher nova declaração no novo exercício; atualizar inclusão orçamentária e quadro de despesas com pessoal quando couber.",
            "apos_0130": "Atualizar quadro de despesas com pessoal para o 3º quadrimestre / 2º semestre do exercício anterior e demais campos afetados.",
            "apos_0330": "Manter declaração aderente ao último RREO/RGF exigível e à situação do exercício em curso.",
        },
        "documentos": {
            "ate_0130": [
                "Anexo 1 da LOA do exercício em curso",
                "Parecer jurídico do exercício corrente",
                "Certidão/declaração do TC sobre art. 167-A até o último RREO exigível",
            ],
            "apos_0130": [
                "Certidão do TC do art. 167, III para o exercício anterior",
                "RREO do 6º bimestre do exercício anterior homologado no Siconfi",
                "Nova certidão do TC para art. 52, art. 23 e art. 55 da LRF, conforme aplicável",
            ],
            "apos_0330": [
                "Usar o último RREO exigível do exercício em curso na data de referência",
                "Atualizar as Informações contábeis com base no RREO/RGF exigíveis",
                "Se houver moeda estrangeira, atualizar câmbio na aba Resumo",
            ],
        },
    }

    base_com_gu = {
        "ate_0130": common_jan,
        "apos_0130": common_after_0130,
        "apos_0330": common_after_0330,
        "declaracao_chefe": {
            "ate_0130": "Preencher nova declaração no novo exercício; atualizar inclusão orçamentária e declarações correlatas à garantia da União.",
            "apos_0130": "Atualizar também o campo de exercício anterior não analisado pelo TC, quando aplicável.",
            "apos_0330": "Ajustar a declaração ao último RREO/RGF exigível e às condições da verificação complementar, se houver.",
        },
        "documentos": {
            "ate_0130": [
                "Anexo 1 da LOA do exercício em curso",
                "Parecer jurídico / declaração conforme modelo de verificação complementar, se for o caso",
                "Certidão do TC sobre art. 167-A",
                "Certidão do TC sobre arts. 198 e 212 da Constituição até o exercício anterior fechado",
            ],
            "apos_0130": [
                "Certidão do TC do art. 167, III para o exercício anterior",
                "RREO do 6º bimestre do exercício anterior homologado no Siconfi",
                "Certidões atualizadas do TC para art. 52, art. 23, art. 55, art. 167-A e, quando aplicável, saúde/educação",
                "Homologação do CDP do exercício anterior após 30/01",
            ],
            "apos_0330": [
                "Usar o último RREO exigível do exercício em curso na data de referência",
                "MSC até o último mês exigível",
                "Encaminhamentos SIOPE/SIOPS conforme o último bimestre exigível",
                "Atualização do câmbio nas abas Operações contratadas e Resumo, se houver moeda estrangeira",
            ],
        },
    }

    base_externa = {
        "ate_0130": common_jan,
        "apos_0130": common_after_0130,
        "apos_0330": common_after_0330,
        "declaracao_chefe": base_com_gu["declaracao_chefe"],
        "documentos": {
            "ate_0130": [
                "Anexo 1 da LOA do exercício em curso",
                "Resolução COFIEX",
                "Informação/registro SCE-Crédito nas Notas explicativas",
                "Certidão do TC sobre arts. 198 e 212, se houver garantia da União",
            ],
            "apos_0130": [
                "Certidão do TC do art. 167, III para o exercício anterior",
                "RREO do 6º bimestre do exercício anterior homologado no Siconfi",
                "Documentação complementar enviada pelo próprio EF nas hipóteses de verificação complementar",
            ],
            "apos_0330": [
                "Usar o último RREO exigível do exercício em curso na data de referência",
                "Atualização das Informações contábeis",
                "Atualização dos dados complementares e de câmbio, se houver",
            ],
        },
    }

    mapping = {
        "interna_sem_garantia": base_sem_gu,
        "interna_com_gu": base_com_gu,
        "externa": base_externa,
        "consorcio": base_sem_gu,
        "reestruturacao": base_sem_gu,
        "regularizacao": base_sem_gu,
    }

    if op_key not in mapping:
        return []

    base = mapping[op_key]

    if after_0330:
        stage = "apos_0330"
        etapa = "Após 30/03"
    elif after_0130:
        stage = "apos_0130"
        etapa = "Após 30/01"
    else:
        stage = "ate_0130"
        etapa = "Entre 01/01 e 30/01"

    info = base[stage]
    doc_info = base.get("documentos", {}).get(stage, [])
    decl = base.get("declaracao_chefe", {}).get(stage, "")

    rows = [
        {
            "aba": "Informações contábeis",
            "campo": "Balanço orçamentário do último RREO do exercício anterior",
            "valor_referencia": info.get("RREO_ultimo_exercicio_anterior", "-"),
            "fonte_mip": "MIP 4.7.8 / 4.8 / 5.13",
            "etapa_data": etapa,
        },
        {
            "aba": "Informações contábeis",
            "campo": "Balanço orçamentário do último RREO exigível (ou Anexo 1 da LOA, quando couber)",
            "valor_referencia": info.get("RREO_exigivel_corrente", "-"),
            "fonte_mip": "MIP 4.7.8 / 4.8.1",
            "etapa_data": etapa,
        },
        {
            "aba": "Informações contábeis",
            "campo": "Demonstrativo da Receita Corrente Líquida do último RREO exigível",
            "valor_referencia": info.get("RREO_RCL_corrente", "-"),
            "fonte_mip": "MIP 4.7.8 / 4.8.1 / 5.3",
            "etapa_data": etapa,
        },
        {
            "aba": "Informações contábeis",
            "campo": "Demonstrativo da Dívida Consolidada Líquida do último RGF exigível",
            "valor_referencia": info.get("RGF_exigivel", "-"),
            "fonte_mip": "MIP 4.7.8 / 4.8 / 5.4",
            "etapa_data": etapa,
        },
        {
            "aba": "Declaração do chefe do Poder Executivo",
            "campo": "Atualização anual / quadro de pessoal / inclusão orçamentária",
            "valor_referencia": decl or "Verificar necessidade de nova declaração",
            "fonte_mip": "MIP 4.7.3 / 4.8",
            "etapa_data": etapa,
        },
        {
            "aba": "Documentos",
            "campo": "Documentos críticos para o período",
            "valor_referencia": " ; ".join(doc_info) if doc_info else "Sem gatilho documental específico mapeado",
            "fonte_mip": "MIP 4.5 / 4.7 / 4.8 / 6.4 / 11.3",
            "etapa_data": etapa,
        },
    ]
    return rows


def build_sadipem_action_plan(
    op_key: str, ref_date: date, sadipem_df: pd.DataFrame
) -> List[Dict]:
    md = _month_day(ref_date)

    if md <= "01-30":
        etapa = "Entre 01/01 e 30/01"
    elif md <= "03-30":
        etapa = "Após 30/01 e até 30/03"
    else:
        etapa = "Após 30/03"

    period_rules = get_reference_period_rules(op_key, ref_date)
    period_map = {f"{r['aba']}|{r['campo']}": r["valor_referencia"] for r in period_rules}

    action_rows = []
    df = sadipem_df[sadipem_df["operacao_codigo"] == op_key].copy()

    for _, row in df.iterrows():
        aba = row["aba"]
        campo = row["campo"]
        chave = None
        valor_ref = "Revisar manualmente"
        acao_pratica = "Verificar aderência do campo ao tipo de operação e à data."
        fonte = "MIP"

        if aba == "Informações contábeis":
            if (
                "último rreo do exercício anterior" in campo.lower()
                or "rreo, rgf, rcl, dcl, balanço orçamentário" in campo.lower()
            ):
                chave = "Informações contábeis|Balanço orçamentário do último RREO do exercício anterior"
            elif "último rreo exigível" in campo.lower() or "anexo 1" in campo.lower():
                chave = "Informações contábeis|Balanço orçamentário do último RREO exigível (ou Anexo 1 da LOA, quando couber)"
            elif "receita corrente líquida" in campo.lower() or "rcl" in campo.lower():
                chave = "Informações contábeis|Demonstrativo da Receita Corrente Líquida do último RREO exigível"
            elif "dívida consolidada líquida" in campo.lower() or "dcl" in campo.lower():
                chave = "Informações contábeis|Demonstrativo da Dívida Consolidada Líquida do último RGF exigível"

        if aba == "Declaração do chefe do Poder Executivo":
            chave = "Declaração do chefe do Poder Executivo|Atualização anual / quadro de pessoal / inclusão orçamentária"
            acao_pratica = "Gerar/atualizar a declaração conforme o exercício e os relatórios exigíveis do período."
            fonte = "MIP 4.7.3 / 4.8"

        if aba == "Documentos":
            chave = "Documentos|Documentos críticos para o período"
            acao_pratica = "Revisar anexos obrigatórios e substituir/incluir versões atualizadas conforme o marco temporal."
            fonte = "MIP 4.5 / 4.7 / 4.8 / 6.4 / 11.3"

        if aba == "Dados complementares":
            acao_pratica = (
                "Revisar ano de início, ano de término e condições financeiras; "
                "na virada de exercício, verificar se o cronograma continua coerente."
            )
            fonte = "MIP 4.7.1 / 4.7.2"
            valor_ref = "Ajustar validade e cronograma ao exercício corrente"

        if aba == "Cronograma financeiro":
            acao_pratica = (
                "Atualizar primeiro ano de liberação/reembolso e conferir "
                "reflexos na aba Resumo."
            )
            fonte = "MIP 4.7.2 / 3.12"
            valor_ref = "Ajustar cronograma ao exercício corrente e às liberações programadas"

        if aba == "Operações não contratadas":
            acao_pratica = (
                "Revisar seleção das operações em tramitação e deferidas não contratadas; "
                "atualizar cronogramas quando necessário."
            )
            fonte = "MIP 3.14"
            valor_ref = (
                "Selecionar operações em tramitação e deferidas ainda não contratadas "
                "pertinentes ao cálculo"
            )

        if aba == "Notas explicativas":
            acao_pratica = (
                "Registrar informações complementares específicas do fluxo "
                "(ex.: SCE-Crédito, consórcio público)."
            )
            fonte = "MIP 9 / 13"
            valor_ref = "Inserir observação específica da modalidade"

        if chave and chave in period_map:
            valor_ref = period_map[chave]
            if aba == "Informações contábeis":
                acao_pratica = f"Preencher este campo usando: {valor_ref}."
                fonte = "MIP 4.7.8 / 4.8 / 5.3 / 5.4"

        action_rows.append(
            {
                "aba": aba,
                "campo": campo,
                "etapa_data": etapa,
                "o_que_usar_na_data": valor_ref,
                "acao_pratica": acao_pratica,
                "fonte_normativa": fonte,
                "observacao": row.get("observacao", ""),
            }
        )

    return action_rows


def detect_text_from_uploaded_file(uploaded_file) -> Tuple[str, str]:
    if uploaded_file is None:
        return "", ""

    name = uploaded_file.name.lower()
    file_bytes = uploaded_file.read()

    if name.endswith(".txt") or name.endswith(".md"):
        try:
            return file_bytes.decode("utf-8"), "arquivo texto"
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1", errors="ignore"), "arquivo texto"

    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(file_bytes))
            pages = []
            for p in reader.pages:
                txt = p.extract_text() or ""
                pages.append(txt)
            return "\\n".join(pages), "PDF via pypdf"
        except Exception:
            try:
                text = file_bytes.decode("latin-1", errors="ignore")
                return text, "PDF bruto (fallback textual)"
            except Exception:
                return "", "PDF sem extração disponível"

    return "", "formato não suportado"


def normalize_text(text: str) -> str:
    text = text or ""
    text = text.lower().replace("\\xa0", " ")
    text = re.sub(r"\\s+", " ", text)
    return text


def extract_section_titles(text: str) -> List[str]:
    titles = []
    for line in (text or "").splitlines():
        s = line.strip()
        if not s:
            continue
        if re.match(r"^(\\d+(?:\\.\\d+){0,3})\\s+.+", s):
            titles.append(s)
        elif re.match(r"^[A-ZÁÀÃÂÉÊÍÓÔÕÚÇ]\\s*$", s):
            titles.append(s)
        elif re.match(r"^[A-ZÁÀÃÂÉÊÍÓÔÕÚÇa-záàãâéêíóôõúç ]{4,}$", s) and len(s) < 120:
            if s == s.title() or s.isupper():
                titles.append(s)

    dedup = []
    for t in titles:
        if t not in dedup:
            dedup.append(t)
    return dedup


def extract_change_signals(text: str) -> List[str]:
    signals = []
    patterns = [
        r"principais alterações desta edição.*",
        r"foi incluíd[ao].*",
        r"foi reforçad[ao].*",
        r"foi ressaltad[ao].*",
        r"exclusão da seção.*",
        r"ajuste[s]? de forma.*",
        r"ajuste no artigo.*",
        r"necessidade de envio.*",
        r"não serão aceitas.*",
        r"deverá ser realizada pela própria instituição financeira.*",
        r"a partir de 01/01.*",
    ]

    for line in (text or "").splitlines():
        s = line.strip()
        low = s.lower()
        if s and any(re.search(p, low) for p in patterns):
            signals.append(s)

    dedup = []
    for s in signals:
        if s not in dedup:
            dedup.append(s)
    return dedup


def compare_mip_text_to_rules(mip_text: str, operacoes_rules: Dict):
    norm = normalize_text(mip_text)
    theme_results = []

    for key, rule in operacoes_rules.items():
        present_keywords = [kw for kw in rule.get("keywords", []) if kw.lower() in norm]
        expected_sections = rule.get("expected_sections", [])
        found_sections = [sec for sec in expected_sections if sec.lower() in norm]

        coverage = "ok" if present_keywords else "revisar"
        if expected_sections and not found_sections and not present_keywords:
            coverage = "não detectado"

        theme_results.append(
            {
                "tema": rule.get("label", key),
                "codigo": key,
                "status": coverage,
                "keywords_detectadas": ", ".join(present_keywords) if present_keywords else "",
                "secoes_esperadas": ", ".join(expected_sections),
                "secoes_detectadas": ", ".join(found_sections),
                "acao_sugerida": (
                    "Validar aderência fina da regra."
                    if coverage == "ok"
                    else (
                        "Revisar regra e capítulo correspondente."
                        if coverage == "revisar"
                        else "Checar se o tema mudou de nomenclatura, foi removido ou não foi extraído do arquivo."
                    )
                ),
            }
        )

    return {
        "theme_results": theme_results,
        "summary": {
            "total_themes": len(theme_results),
            "present_themes": sum(1 for x in theme_results if x["status"] == "ok"),
            "missing_themes": sum(1 for x in theme_results if x["status"] == "não detectado"),
        },
    }


def build_review_dataframe(
    comparison: Dict, section_titles: List[str], change_signals: List[str]
) -> pd.DataFrame:
    rows = []

    for item in comparison.get("theme_results", []):
        rows.append(
            {
                "tipo": "tema",
                "referencia": item["tema"],
                "status": item["status"],
                "detalhe": item.get("keywords_detectadas")
                or item.get("secoes_detectadas")
                or item.get("secoes_esperadas"),
                "acao": item["acao_sugerida"],
            }
        )

    for t in section_titles[:80]:
        rows.append(
            {
                "tipo": "secao_detectada",
                "referencia": t,
                "status": "identificada",
                "detalhe": "Título/seção detectado no texto do MIP.",
                "acao": "Validar se há regra correspondente ou necessidade de nova regra.",
            }
        )

    for s in change_signals[:80]:
        rows.append(
            {
                "tipo": "sinal_de_alteracao",
                "referencia": s[:120],
                "status": "mudança detectada",
                "detalhe": s,
                "acao": "Conferir impacto sobre documentos, canal, gatilhos de data e fluxo.",
            }
        )

    return pd.DataFrame(rows)


def _contains_all(norm_text: str, fragments: List[str]) -> bool:
    return all(f.lower() in norm_text for f in fragments)


def build_structured_update_suggestions(
    mip_text: str, operacoes_rules: Dict
) -> pd.DataFrame:
    norm = normalize_text(mip_text)
    suggestions = []

    if _contains_all(norm, ["pvl-if", "análise complementar", "própria instituição financeira"]):
        suggestions.append(
            {
                "operacao_codigo": "interna_sem_garantia",
                "operacao": operacoes_rules["interna_sem_garantia"]["label"],
                "campo_sugerido": "observacoes / regra complementar",
                "acao_estruturada": "Atualizar regra para explicitar que, em PVL-IF, a análise complementar após virada de exercício deve ser realizada pela própria IF.",
                "evidencia_detectada": "PVL-IF + análise complementar + própria instituição financeira",
                "prioridade": "alta",
            }
        )

    if _contains_all(norm, ["art. 198", "art. 212"]) and (
        "a partir de 01/01" in norm or "a partir do primeiro dia do exercício em curso" in norm
    ):
        suggestions.append(
            {
                "operacao_codigo": "interna_com_gu",
                "operacao": operacoes_rules["interna_com_gu"]["label"],
                "campo_sugerido": "gatilhos_data / documentos_base",
                "acao_estruturada": "Reforçar gatilho de janeiro e observações para exigir certidão do TC atestando arts. 198 e 212 até o exercício anterior fechado, inclusive durante janeiro.",
                "evidencia_detectada": "art. 198 + art. 212 + a partir de 01/01",
                "prioridade": "alta",
            }
        )
        suggestions.append(
            {
                "operacao_codigo": "externa",
                "operacao": operacoes_rules["externa"]["label"],
                "campo_sugerido": "gatilhos_data / documentos_base",
                "acao_estruturada": "Reforçar, para operações com garantia da União, a necessidade de certidão do TC sobre saúde e educação do exercício anterior fechado desde 01/01.",
                "evidencia_detectada": "art. 198 + art. 212 + a partir de 01/01",
                "prioridade": "alta",
            }
        )

    if _contains_all(norm, ["17.3", "anexo 1", "loa do exercício em curso"]) and (
        "1º de janeiro" in norm or "1 de janeiro" in norm
    ) and ("30 de março" in norm or "30 de marco" in norm):
        suggestions.append(
            {
                "operacao_codigo": "lc_212",
                "operacao": operacoes_rules["lc_212"]["label"],
                "campo_sugerido": "gatilhos_data / documentos_base",
                "acao_estruturada": "Adicionar ou validar gatilho temporal de 01/01 a 30/03 para exigir Anexo 1 da LOA do exercício em curso nas análises da LC 212/2025.",
                "evidencia_detectada": "17.3 + Anexo 1 + LOA do exercício em curso + 1º de janeiro a 30 de março",
                "prioridade": "alta",
            }
        )

    return pd.DataFrame(suggestions).drop_duplicates() if suggestions else pd.DataFrame()
