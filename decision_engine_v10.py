import io
import re
from datetime import date
from typing import Dict, List, Tuple

import pandas as pd


def _month_day(d: date) -> str:
    return d.strftime("%m-%d")


def _bucket(ref_date: date) -> Dict:
    m = ref_date.month
    d = ref_date.day
    if (m, d) <= (1, 30):
        return {"code": "janeiro", "label": "Entre 01/01 e 30/01"}
    if (m, d) <= (3, 30):
        return {"code": "pos_3001", "label": "Após 30/01 e até 30/03"}
    if (m, d) <= (5, 30):
        return {"code": "pos_3003", "label": "Após 30/03 e até 30/05"}
    if (m, d) <= (7, 30):
        return {"code": "pos_3005", "label": "Após 30/05 e até 30/07"}
    if (m, d) <= (9, 30):
        return {"code": "pos_3007", "label": "Após 30/07 e até 30/09"}
    if (m, d) <= (11, 30):
        return {"code": "pos_3009", "label": "Após 30/09 e até 30/11"}
    return {"code": "pos_3011", "label": "Após 30/11"}


def evaluate_operation(op_key: str, ref_date: date, operacoes_rules: Dict):
    regra = operacoes_rules[op_key]
    bucket = _bucket(ref_date)
    return {"regra": regra, "gatilhos_ativos": [{"nome": bucket['label'], "descricao": "Janela temporal considerada para os checklists condicionais por aba."}]}


def _conditional_checklists() -> Dict:
    return {
        "ordinaria_sem_gu": {
            "Informações Contábeis": {
                "janeiro": [
                    "Usar, em 'Balanço orçamentário do último RREO do exercício anterior', a lógica do 6º bimestre do exercício anterior; se ainda não publicado, observar a disciplina do MIP para janeiro.",
                    "Usar, em 'Balanço orçamentário do último RREO exigível', o Anexo 1 da Lei 4.320/1964 publicado com a LOA do exercício em curso.",
                    "Usar, em RCL do último RREO exigível, o 5º bimestre do exercício anterior; se o 6º já estiver publicado, usar o 6º bimestre.",
                    "Usar, em DDCL/RGF, o 2º quadrimestre do exercício anterior; ou 1º semestre do exercício anterior, se município optante do art. 63 da LRF; se o RGF final já estiver publicado, usar o mais recente.",
                ],
                "pos_3001": [
                    "Atualizar para refletir o exercício anterior fechado, com RREO do 6º bimestre homologado no Siconfi.",
                    "Manter no campo do exercício corrente o Anexo 1 da LOA até 30/03.",
                    "Usar o RGF final do exercício anterior (3º quadrimestre ou 2º semestre, conforme o caso).",
                ],
                "pos_3003": [
                    "Substituir o Anexo 1 por informações do RREO do 1º bimestre do exercício em curso, homologado no Siconfi.",
                    "Atualizar RCL para o 1º bimestre do exercício em curso.",
                    "Manter DDCL com base no último RGF exigível aplicável ao período.",
                ],
                "pos_3005": [
                    "Atualizar RREO e RCL para o 2º bimestre do exercício em curso.",
                    "Atualizar DDCL com base no RGF do 1º quadrimestre do exercício em curso, se exigível/applicável.",
                ],
                "pos_3007": [
                    "Atualizar RREO e RCL para o 3º bimestre do exercício em curso.",
                    "Se município optante do art. 63 da LRF, atualizar DDCL com base no RGF do 1º semestre do exercício em curso.",
                ],
                "pos_3009": [
                    "Atualizar RREO e RCL para o 4º bimestre do exercício em curso.",
                    "Atualizar DDCL com base no RGF do 2º quadrimestre do exercício em curso, se aplicável.",
                ],
                "pos_3011": [
                    "Atualizar RREO e RCL para o 5º bimestre do exercício em curso.",
                    "Manter DDCL com base no último RGF exigível aplicável do exercício em curso.",
                ],
            },
            "Declaração do Chefe do Poder Executivo": {
                "janeiro": [
                    "Emitir nova declaração no exercício corrente, se houve virada de exercício.",
                    "Atualizar o quadro de pessoal e referências de 'ano em curso'/'exercício corrente'.",
                    "Atestar inclusão orçamentária com base na LOA vigente.",
                ],
                "pos_3001": [
                    "Atualizar os campos que dependem do exercício anterior fechado.",
                    "Revisar o quadro de pessoal com base no último RGF exigível final do exercício anterior.",
                ],
                "pos_3003": [
                    "Ajustar referências do exercício corrente conforme o 1º bimestre do exercício em curso.",
                    "Manter consistência entre declaração, informações contábeis e certidão do TC.",
                ],
                "pos_3005": [
                    "Atualizar o quadro de despesa com pessoal do Poder Executivo com base no último RGF exigível do período.",
                ],
                "pos_3007": [
                    "Para município optante do art. 63, usar o 1º semestre do exercício em curso para o quadro de pessoal.",
                ],
                "pos_3009": [
                    "Atualizar a declaração segundo o último RGF exigível do exercício em curso (incluindo 2º quadrimestre, se aplicável).",
                ],
                "pos_3011": [
                    "Manter a declaração alinhada ao último RREO/RGF exigível do exercício em curso, preparando a transição para o fechamento anual.",
                ],
            },
            "Documentos": {
                "janeiro": [
                    "Anexar lei autorizadora, parecer jurídico do exercício corrente, parecer técnico, certidão do TC e Anexo 1 da LOA do exercício em curso.",
                    "Revisar se a certidão do TC ainda atende ao período de janeiro e ao fechamento do exercício anterior, conforme o MIP.",
                ],
                "pos_3001": [
                    "Atualizar a certidão do TC para refletir o exercício anterior fechado.",
                    "Verificar homologação do RREO do 6º bimestre do exercício anterior e do CDP do exercício anterior.",
                    "Manter Anexo 1 da LOA até 30/03.",
                ],
                "pos_3003": [
                    "Após 30/03, substituir a dependência do Anexo 1 por referências do RREO do 1º bimestre do exercício em curso.",
                    "Verificar documentos e certidões exigíveis do período.",
                ],
                "pos_3005": [
                    "Atualizar certidões e bases documentais para o 2º bimestre e RGF exigível correspondente.",
                ],
                "pos_3007": [
                    "Atualizar certidões e bases documentais para o 3º bimestre; para município do art. 63, observar 1º semestre.",
                ],
                "pos_3009": [
                    "Atualizar certidões e bases documentais para o 4º bimestre e RGF correspondente.",
                ],
                "pos_3011": [
                    "Atualizar certidões e bases documentais para o 5º bimestre do exercício em curso.",
                ],
            },
            "Resumo": {
                "janeiro": [
                    "Conferir se a regra de ouro do exercício corrente está apoiada no Anexo 1 da LOA do exercício em curso.",
                    "Conferir se os cronogramas foram adequados ao novo exercício.",
                    "Verificar CDP e pendências de regularização após salvar o PVL.",
                ],
                "pos_3001": [
                    "Conferir regra de ouro do exercício anterior com base no exercício anterior fechado.",
                    "Conferir se o Resumo reflete o RREO do 6º bimestre e o RGF final do exercício anterior.",
                ],
                "pos_3003": [
                    "Conferir atualização da regra de ouro do exercício corrente com base no RREO do 1º bimestre.",
                    "Conferir painéis de MGA/RCL, CAED/RCL e DCL/RCL após atualizar informações contábeis e cronogramas.",
                ],
                "pos_3005": [
                    "Conferir painéis usando 2º bimestre e último RGF exigível do período.",
                ],
                "pos_3007": [
                    "Conferir painéis usando 3º bimestre; para município do art. 63, considerar reflexos do 1º semestre.",
                ],
                "pos_3009": [
                    "Conferir painéis usando 4º bimestre e último RGF exigível do exercício em curso.",
                ],
                "pos_3011": [
                    "Conferir painéis usando 5º bimestre do exercício em curso e preparar consistência para o fechamento anual.",
                ],
            },
        },
        "ordinaria_com_gu": {
            "Informações Contábeis": {
                "janeiro": [
                    "Aplicar a mesma lógica da operação ordinária, mas com atenção reforçada à operação com garantia da União.",
                    "Usar Anexo 1 da LOA do exercício em curso para o exercício corrente até 30/03.",
                ],
                "pos_3001": [
                    "Atualizar para o exercício anterior fechado, inclusive refletindo o RREO do 6º bimestre e o RGF final do exercício anterior.",
                ],
                "pos_3003": [
                    "Substituir o Anexo 1 por dados do RREO do 1º bimestre do exercício em curso.",
                ],
                "pos_3005": ["Atualizar para o 2º bimestre do exercício em curso e o RGF exigível correspondente."],
                "pos_3007": ["Atualizar para o 3º bimestre do exercício em curso; municípios do art. 63 podem demandar 1º semestre."],
                "pos_3009": ["Atualizar para o 4º bimestre do exercício em curso e o RGF correspondente."],
                "pos_3011": ["Atualizar para o 5º bimestre do exercício em curso."],
            },
            "Declaração do Chefe do Poder Executivo": {
                "janeiro": [
                    "Emitir nova declaração no exercício corrente.",
                    "Revisar inclusão orçamentária e quadro de pessoal do Poder Executivo.",
                ],
                "pos_3001": [
                    "Atualizar os campos associados ao exercício anterior fechado.",
                    "Se a operação estiver em verificação complementar, alinhar a declaração aos requisitos do novo exercício.",
                ],
                "pos_3003": ["Ajustar a declaração às referências do 1º bimestre do exercício em curso."],
                "pos_3005": ["Atualizar despesa com pessoal com base no último RGF exigível do período."],
                "pos_3007": ["Para município do art. 63, usar o 1º semestre quando aplicável."],
                "pos_3009": ["Atualizar com base no último RGF exigível do exercício em curso."],
                "pos_3011": ["Manter coerência entre declaração, exercício em curso e bases contábeis mais recentes."],
            },
            "Documentos": {
                "janeiro": [
                    "Além dos documentos-base ordinários, revisar documentos específicos da garantia da União.",
                    "Anexar certidão do TC que ateste saúde e educação para o exercício anterior fechado, inclusive em janeiro.",
                ],
                "pos_3001": [
                    "Atualizar certidão do TC para regra de ouro do exercício anterior fechado.",
                    "Atualizar certidão do TC relativa aos arts. 198 e 212 da Constituição para o exercício anterior fechado.",
                ],
                "pos_3003": [
                    "Substituir a base do exercício corrente do Anexo 1 pelo RREO do 1º bimestre, quando aplicável.",
                    "Verificar exigências adicionais de garantia da União no período.",
                ],
                "pos_3005": ["Atualizar certidões/documentos para 2º bimestre e RGF exigível correspondente."],
                "pos_3007": ["Atualizar certidões/documentos para 3º bimestre e, se aplicável, 1º semestre do município do art. 63."],
                "pos_3009": ["Atualizar certidões/documentos para 4º bimestre e RGF correspondente."],
                "pos_3011": ["Atualizar certidões/documentos para 5º bimestre do exercício em curso."],
            },
            "Resumo": {
                "janeiro": [
                    "Conferir regra de ouro do exercício corrente com base na LOA/Anexo 1.",
                    "Conferir CDP, pendências e painéis consolidados após salvar as abas-base.",
                ],
                "pos_3001": [
                    "Conferir regra de ouro do exercício anterior fechado e refletir exercício anterior encerrado.",
                    "Conferir se os painéis já refletem a base fiscal final do exercício anterior.",
                ],
                "pos_3003": ["Conferir atualização da regra de ouro do exercício corrente com base no 1º bimestre do exercício em curso."],
                "pos_3005": ["Conferir painéis com base no 2º bimestre e no RGF exigível correspondente."],
                "pos_3007": ["Conferir painéis com base no 3º bimestre e, se aplicável, no 1º semestre."],
                "pos_3009": ["Conferir painéis com base no 4º bimestre e RGF correspondente."],
                "pos_3011": ["Conferir painéis com base no 5º bimestre do exercício em curso."],
            },
        },
        "externa_com_gu": {
            "Informações Contábeis": {
                "janeiro": [
                    "Usar Anexo 1 da LOA do exercício em curso como base do exercício corrente até 30/03, quando aplicável.",
                    "Manter coerência com o exercício anterior fechado e com a lógica do EF interessado.",
                ],
                "pos_3001": ["Atualizar a base do exercício anterior fechado com RREO 6º bimestre e RGF final do exercício anterior."],
                "pos_3003": ["Atualizar a base corrente com o RREO do 1º bimestre do exercício em curso."],
                "pos_3005": ["Atualizar a base corrente com o 2º bimestre do exercício em curso."],
                "pos_3007": ["Atualizar a base corrente com o 3º bimestre do exercício em curso."],
                "pos_3009": ["Atualizar a base corrente com o 4º bimestre do exercício em curso."],
                "pos_3011": ["Atualizar a base corrente com o 5º bimestre do exercício em curso."],
            },
            "Declaração do Chefe do Poder Executivo": {
                "janeiro": [
                    "Emitir declaração do exercício corrente.",
                    "Ajustar referências de inclusão orçamentária e do novo exercício.",
                ],
                "pos_3001": ["Atualizar campos ligados ao exercício anterior fechado."],
                "pos_3003": ["Ajustar a declaração à base do 1º bimestre do exercício em curso, quando aplicável."],
                "pos_3005": ["Ajustar a declaração à base do 2º bimestre do exercício em curso, quando aplicável."],
                "pos_3007": ["Ajustar a declaração à base do 3º bimestre do exercício em curso, quando aplicável."],
                "pos_3009": ["Ajustar a declaração à base do 4º bimestre do exercício em curso, quando aplicável."],
                "pos_3011": ["Ajustar a declaração à base do 5º bimestre do exercício em curso, quando aplicável."],
            },
            "Documentos": {
                "janeiro": [
                    "Anexar lei autorizadora, parecer jurídico, parecer técnico, certidão do TC, COFIEX e elementos do fluxo externo.",
                    "Se houver garantia da União, revisar também requisitos específicos de garantia.",
                ],
                "pos_3001": ["Atualizar certidão do TC e bases documentais para o exercício anterior fechado."],
                "pos_3003": ["Após 30/03, substituir dependência do Anexo 1 pelas bases do 1º bimestre, quando aplicável."],
                "pos_3005": ["Atualizar certidões/documentos com base no 2º bimestre do exercício em curso."],
                "pos_3007": ["Atualizar certidões/documentos com base no 3º bimestre do exercício em curso."],
                "pos_3009": ["Atualizar certidões/documentos com base no 4º bimestre do exercício em curso."],
                "pos_3011": ["Atualizar certidões/documentos com base no 5º bimestre do exercício em curso."],
            },
            "Resumo": {
                "janeiro": [
                    "Conferir regra de ouro do exercício corrente com base na LOA/Anexo 1, quando aplicável.",
                    "Conferir taxa de câmbio, cronogramas e painéis após salvar o PVL.",
                ],
                "pos_3001": ["Conferir painéis com base no exercício anterior fechado e nos cronogramas atualizados."],
                "pos_3003": ["Conferir atualização dos painéis com base no 1º bimestre do exercício em curso."],
                "pos_3005": ["Conferir atualização dos painéis com base no 2º bimestre do exercício em curso."],
                "pos_3007": ["Conferir atualização dos painéis com base no 3º bimestre do exercício em curso."],
                "pos_3009": ["Conferir atualização dos painéis com base no 4º bimestre do exercício em curso."],
                "pos_3011": ["Conferir atualização dos painéis com base no 5º bimestre do exercício em curso."],
            },
        },
    }


def get_reference_period_rules(op_key: str, ref_date: date) -> List[Dict]:
    b = _bucket(ref_date)
    return [{
        "aba": "Janela temporal",
        "campo": "Período ativo",
        "valor_referencia": b["label"],
        "fonte_mip": "MIP 4.7 / 4.8 / 11.3",
        "etapa_data": b["label"],
    }]


def build_sadipem_action_plan(op_key: str, ref_date: date, sadipem_df: pd.DataFrame, operacoes_rules: Dict) -> List[Dict]:
    b = _bucket(ref_date)
    family = operacoes_rules[op_key]["family"]
    checklists = _conditional_checklists()[family]
    df = sadipem_df[sadipem_df["operacao_codigo"] == op_key].copy()
    result = []

    for _, row in df.iterrows():
        aba = row["aba"]
        campo = row["campo"]
        checklist = checklists.get(aba, {}).get(b["code"], ["Revisar manualmente conforme o MIP."])
        result.append({
            "aba": aba,
            "campo": campo,
            "etapa_data": b["label"],
            "checklist_condicional": "\n".join([f"- {x}" for x in checklist]),
            "acao_pratica": f"Aplicar o checklist da aba '{aba}' para a janela {b['label']}.",
            "fonte_normativa": row.get("observacao", "MIP"),
            "observacao": row.get("observacao", ""),
        })
    return result


def build_conditional_checklist_dataframe(op_key: str, ref_date: date, operacoes_rules: Dict) -> pd.DataFrame:
    b = _bucket(ref_date)
    family = operacoes_rules[op_key]["family"]
    checklists = _conditional_checklists()[family]
    rows = []
    for aba in ["Informações Contábeis", "Declaração do Chefe do Poder Executivo", "Documentos", "Resumo"]:
        for item in checklists.get(aba, {}).get(b["code"], []):
            rows.append({
                "aba": aba,
                "janela": b["label"],
                "item_checklist": item,
            })
    return pd.DataFrame(rows)


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
            return "", "PDF sem extração disponível"
    return "", "formato não suportado"


def normalize_text(text: str) -> str:
    text = text or ""
    text = text.lower().replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def extract_section_titles(text: str) -> List[str]:
    titles = []
    for line in (text or "").splitlines():
        s = line.strip()
        if not s:
            continue
        if re.match(r"^(\d+(?:\.\d+){0,3})\s+.+", s):
            titles.append(s)
    return list(dict.fromkeys(titles))


def extract_change_signals(text: str) -> List[str]:
    signals = []
    pats = [r"principais alterações desta edição.*", r"foi incluíd[ao].*", r"foi reforçad[ao].*", r"a partir de 01/01.*"]
    for line in (text or "").splitlines():
        s = line.strip()
        low = s.lower()
        if s and any(re.search(p, low) for p in pats):
            signals.append(s)
    return list(dict.fromkeys(signals))


def compare_mip_text_to_rules(mip_text: str, operacoes_rules: Dict):
    norm = normalize_text(mip_text)
    theme_results = []
    for key, rule in operacoes_rules.items():
        present_keywords = [kw for kw in rule.get("keywords", []) if kw.lower() in norm]
        expected_sections = rule.get("expected_sections", [])
        found_sections = [sec for sec in expected_sections if sec.lower() in norm]
        coverage = "ok" if present_keywords else "revisar"
        theme_results.append({
            "tema": rule.get("label", key),
            "codigo": key,
            "status": coverage,
            "keywords_detectadas": ", ".join(present_keywords),
            "secoes_esperadas": ", ".join(expected_sections),
            "secoes_detectadas": ", ".join(found_sections),
            "acao_sugerida": "Validar aderência fina da regra." if coverage == "ok" else "Revisar regra e capítulo correspondente.",
        })
    return {"theme_results": theme_results, "summary": {"total_themes": len(theme_results), "present_themes": sum(1 for x in theme_results if x['status'] == 'ok')}}


def build_review_dataframe(comparison: Dict, section_titles: List[str], change_signals: List[str]) -> pd.DataFrame:
    rows = []
    for item in comparison.get("theme_results", []):
        rows.append({"tipo": "tema", "referencia": item['tema'], "status": item['status'], "detalhe": item.get('keywords_detectadas'), "acao": item['acao_sugerida']})
    for t in section_titles[:80]:
        rows.append({"tipo": "secao_detectada", "referencia": t, "status": "identificada", "detalhe": "Seção detectada", "acao": "Validar mapeamento"})
    for s in change_signals[:80]:
        rows.append({"tipo": "sinal_de_alteracao", "referencia": s[:120], "status": "mudança detectada", "detalhe": s, "acao": "Conferir impacto nas regras"})
    return pd.DataFrame(rows)


def build_structured_update_suggestions(mip_text: str, operacoes_rules: Dict) -> pd.DataFrame:
    return pd.DataFrame()
