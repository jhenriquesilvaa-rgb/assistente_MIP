import requests
from datetime import datetime
from urllib.parse import quote

from rules_operacoes_v10 import build_checklist_catalog

API_BASE = "https://apidatalake.tesouro.gov.br/ords/sadipem/tt"
ENDPOINTS = {
    "pvl": f"{API_BASE}/pvl",
    "resumo_cdp": f"{API_BASE}/resumo_cdp",
    "resumo_cp": f"{API_BASE}/resumo_cronograma_pagamentos",
    "oc_cp": f"{API_BASE}/operacoes_contratadas_cronograma_pagamentos",
    "oc_cl": f"{API_BASE}/operacoes_contratadas_cronograma_liberacoes",
    "oc_tx": f"{API_BASE}/operacoes_contratadas_taxas_cambio",
}

API_FIELD_MAP = {
    "id_pleito": "Identificação interna do PVL no SADIPEM",
    "tipo_interessado": "Tipo de interessado",
    "interessado": "Ente interessado",
    "cod_ibge": "Código IBGE",
    "uf": "UF do interessado",
    "num_pvl": "Número do PVL",
    "status": "Etapa/status atual do PVL",
    "num_processo": "Número do processo",
    "data_protocolo": "Data/hora do último envio à STN",
    "tipo_operacao": "Tipo da operação ou garantia",
    "finalidade": "Finalidade da operação",
    "tipo_credor": "Tipo do credor",
    "instituicao_credora": "Instituição credora",
    "credor": "Credor",
    "moeda": "Moeda da operação",
    "valor": "Valor informado",
    "pvl_assoc_divida": "Há dívida no CDP vinculada ao PVL (1/0)",
    "pvl_contratado_credor": "Credor informou contratação (1/0)",
    "data_status": "Data do status atual",
}

STATUS_GROUPS = {
    "inicial": {"Em preenchimento pelo credor", "Em preenchimento pelo interessado", "Assinado pelo interessado", "Pendente de distribuição (PVL-IF)", "Enviado à instituição financeira (PVL-IF)"},
    "analise": {"Em análise", "Em análise garantia da União", "Em análise PVL-IF", "Em consulta jurídica"},
    "retificacao": {"Em retificação pelo credor", "Em retificação pelo interessado", "Em retificação pelo credor (PVL-IF)", "Em retificação pelo interessado (PVL-IF)"},
    "final_favoravel": {"Deferido", "Deferido (PVL-IF)", "Deferido sem garantia da União", "Encaminhado à PGFN com manifestação técnica favorável", "Encaminhado à PGFN (decisão judicial)", "Regularizado", "Regular por decisão judicial"},
    "final_desfavoravel": {"Indeferido", "Indeferido (PVL-IF)", "Encaminhado à PGFN com manifestação técnica desfavorável", "Pendente de regularização"},
    "arquivamento": {"Arquivado", "Arquivado a pedido", "Arquivado a pedido (PVL-IF)", "Arquivado pela STN", "Arquivado por decurso de prazo", "Arquivado por decurso de prazo (PVL-IF)", "PVL cancelado"},
    "suspensao": {"Sobrestado", "Suspenso por decisão judicial"},
}


def normalizar_texto(valor):
    return str(valor or "").strip()


def normalizar_numero_pvl(valor):
    return normalizar_texto(valor)


def parse_data(valor):
    if not valor:
        return None
    s = str(valor).strip()
    candidatos = [s, s[:19], s[:10]]
    for cand in candidatos:
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y"):
            try:
                return datetime.strptime(cand, fmt)
            except Exception:
                pass
    return None


def formatar_data_api(d):
    return d.strftime("%Y-%m-%d") if d else None


def grupo_status(status):
    s = status or ""
    for grupo, conjunto in STATUS_GROUPS.items():
        if s in conjunto:
            return grupo
    return "desconhecido"


def api_get(url):
    headers = {"accept": "application/json"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data.get("items", data if isinstance(data, list) else [])


def montar_filtros_pvl(numero_pvl=None, num_processo=None, ente=None, uf=None, status=None, tipo_operacao=None, data_inicio=None, data_fim=None, campo_periodo=None):
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

    dt_ini = formatar_data_api(data_inicio)
    dt_fim = formatar_data_api(data_fim)
    if dt_ini and dt_fim:
        if campo_periodo == "Apenas data_status":
            filtros.append(f"data_status=gte.{dt_ini}")
            filtros.append(f"data_status=lte.{dt_fim}")
        elif campo_periodo == "Apenas data_protocolo":
            filtros.append(f"data_protocolo=gte.{dt_ini}")
            filtros.append(f"data_protocolo=lte.{dt_fim}")
        else:
            filtros.append(f"or=(and(data_status.gte.{dt_ini},data_status.lte.{dt_fim}),and(data_protocolo.gte.{dt_ini},data_protocolo.lte.{dt_fim}))")
    return filtros


def buscar_pvls(numero_pvl=None, num_processo=None, ente=None, uf=None, status=None, tipo_operacao=None, data_inicio=None, data_fim=None, campo_periodo=None, limit=30):
    filtros = montar_filtros_pvl(numero_pvl, num_processo, ente, uf, status, tipo_operacao, data_inicio, data_fim, campo_periodo)
    query = "&".join(filtros + [f"limit={limit}"]) if filtros else f"limit={limit}"
    url = f"{ENDPOINTS['pvl']}?{query}"
    try:
        items = api_get(url)
        return {"ok": True, "items": items, "url": url}
    except Exception as e:
        return {"ok": False, "erro": str(e), "url": url}


def consultar_detalhes_multifonte(num_pvl=None, num_processo=None):
    chave = normalizar_numero_pvl(num_pvl or num_processo or "")
    if not chave:
        return {"ok": False, "erro": "Chave de consulta inválida."}
    pvl = buscar_pvls(numero_pvl=num_pvl, num_processo=num_processo, limit=5)
    if not pvl.get("ok") or not pvl.get("items"):
        return {"ok": False, "erro": pvl.get("erro", "PVL não localizado."), "fonte_pvl": pvl.get("url")}
    item = pvl["items"][0]
    num_pvl_real = item.get("num_pvl") or chave
    detalhes = {"pvl": item, "fonte_pvl": pvl.get("url")}
    for nome, endpoint in ENDPOINTS.items():
        if nome == "pvl":
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
        detalhes[f"fonte_{nome}"] = usado
    return {"ok": True, "dados": detalhes}


def extrair_dados_pvl(item):
    dados = {k: item.get(k) for k in API_FIELD_MAP.keys()}
    if not dados.get("credor"):
        dados["credor"] = item.get("instituicao_credora")
    return dados


def campos_presentes_ausentes(dados):
    presentes, ausentes = [], []
    for k, desc in API_FIELD_MAP.items():
        v = dados.get(k)
        if v is None or v == "":
            ausentes.append(f"{k} - {desc}")
        else:
            presentes.append(f"{k} - {desc}: {v}")
    return presentes, ausentes


def inferir_familia_por_tipo(tipo_operacao):
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
    if "pef" in t:
        return "pef"
    if "lc 212" in t:
        return "lc_212"
    if "extern" in t:
        return "externa"
    return "interna"


def coletar_checklist_esperado_calibrado(familia, data_status_str):
    try:
        catalog = build_checklist_catalog()
        fam = catalog.get(familia, {})
        data_obj = parse_data(data_status_str)
        itens = []
        chave_periodo = "janeiro" if (data_obj and data_obj.month <= 3) else "pos_3003"
        for aba, fases in fam.items():
            lista = fases.get(chave_periodo) or []
            for item in lista[:4]:
                itens.append(f"[{aba}] {item}")
        return itens or ["Não foi possível montar checklist esperado para a família identificada."]
    except Exception:
        return ["Não foi possível montar checklist esperado para a família identificada."]


def resumo_multifonte(detalhes):
    return {
        "resumo_cdp": len(detalhes.get("resumo_cdp", []) or []),
        "resumo_cp": len(detalhes.get("resumo_cp", []) or []),
        "oc_cp": len(detalhes.get("oc_cp", []) or []),
        "oc_cl": len(detalhes.get("oc_cl", []) or []),
        "oc_tx": len(detalhes.get("oc_tx", []) or []),
    }


def regras_por_cenario(familia, status, dados, detalhes):
    grupo = grupo_status(status)
    pend, inc = [], []
    counts = resumo_multifonte(detalhes)
    if grupo == "retificacao":
        pend.append("O cenário de retificação sugere exigência anterior não integralmente atendida; revisar documentos e dados antes de novo envio.")
    if grupo == "analise":
        pend.append("O cenário de análise sugere que o pleito já superou a fase inicial, mas ainda pode receber exigências complementares.")
    if grupo == "final_desfavoravel":
        inc.append("O cenário do status atual é materialmente desfavorável ao pleito e exige revisão de enquadramento ou saneamento.")
    if familia == "reestruturacao" and dados.get("pvl_assoc_divida") not in (1, "1"):
        inc.append("Reestruturação sem indicação pública de dívida associada no CDP; cenário tecnicamente sensível.")
    if familia == "externa" and (dados.get("moeda") and str(dados.get("moeda")).upper() not in {"REAL", "BRL", "R$"}) and counts["oc_tx"] == 0:
        inc.append("Operação externa/moeda estrangeira sem retorno de taxas de câmbio públicas; conferir integração e consistência do cadastro.")
    if counts["oc_cp"] > 0 and counts["oc_cl"] == 0:
        pend.append("Há cronograma público de pagamentos sem cronograma público de liberações correspondente; conferir a natureza da operação.")
    if dados.get("pvl_assoc_divida") in (1, "1") and counts["resumo_cdp"] == 0:
        pend.append("O PVL indica vínculo com dívida/CDP, mas não foram retornadas informações públicas do Resumo-CDP.")
    return list(dict.fromkeys(pend)), list(dict.fromkeys(inc)), counts


def diagnosticar_item(item, detalhes):
    dados = extrair_dados_pvl(item)
    familia = inferir_familia_por_tipo(dados.get("tipo_operacao"))
    presentes, ausentes = campos_presentes_ausentes(dados)
    checklist = coletar_checklist_esperado_calibrado(familia, dados.get("data_status"))
    pendencias, inconsistencias, counts = regras_por_cenario(familia, dados.get("status") or "", dados, detalhes)
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
        pendencias.append("Nenhuma pendência provável inferida apenas pelos dados públicos do PVL; ainda é necessária conferência documental.")
    if not inconsistencias:
        inconsistencias.append("Nenhuma inconsistência evidente inferida apenas com base nos dados públicos e nas regras técnicas atuais.")
    return {
        "dados_pleito": dados_pleito,
        "checklist_esperado": checklist,
        "pendencias_provaveis": pendencias,
        "inconsistencias_detectadas": inconsistencias,
        "dados_brutos": dados,
        "campos_presentes": presentes,
        "campos_ausentes": ausentes,
        "familia_identificada": familia,
        "resumo_multifonte": counts,
    }
