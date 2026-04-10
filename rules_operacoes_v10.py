RULES_VERSION = "v12.5.2"

from datetime import date


def _janela_por_data(data_ref):
    if data_ref.month <= 3:
        return "janeiro", "De 01/01 até 30/03"
    return "pos_3003", "Após 30/03"


def build_checklist_catalog():
    base_interna = {
        "Informações Contábeis": {
            "janeiro": [
                "Usar informações do exercício anterior fechado quando exigível.",
                "Avaliar qual RREO do exercício em curso já pode substituir referências anuais, conforme a janela temporal.",
                "Conferir qual RGF exigível está vigente para o período do pleito.",
            ],
            "pos_3003": [
                "Substituir referências anuais por demonstrativos bimestrais do exercício em curso quando cabível.",
                "Atualizar RCL e DCL conforme período aplicável.",
                "Verificar a manutenção do RGF exigível para o período corrente.",
            ],
        },
        "Declaração do Chefe do Poder Executivo": {
            "janeiro": [
                "Manter aderência da declaração ao exercício anterior fechado, quando aplicável.",
            ],
            "pos_3003": [
                "Ajustar referências da declaração ao exercício corrente e aos demonstrativos mais recentes.",
            ],
        },
        "Documentos": {
            "janeiro": [
                "Entre 01/01 e 30/03, pode haver uso do Anexo 1 da LOA e de documentos do exercício anterior fechado, conforme o MIP.",
                "Conferir certidões e declarações do período aplicável.",
                "Verificar consistência entre declaração, contabilidade e certidão do TC.",
            ],
            "pos_3003": [
                "Após 30/03, substituir referências anuais quando o MIP exigir atualização para o exercício em curso.",
                "Atualizar documentos sazonais após o primeiro bimestre, quando aplicável.",
                "Revalidar coerência documental do pleito com o exercício corrente.",
            ],
        },
        "Operações Contratadas": {
            "janeiro": [
                "Conferir cronogramas existentes e eventuais contratos já firmados.",
                "Se houver moeda estrangeira, verificar necessidade de taxas de câmbio no período aplicável.",
            ],
            "pos_3003": [
                "Manter cronogramas compatíveis com as informações mais recentes do exercício em curso.",
                "Se houver moeda estrangeira, adequar taxas de câmbio às referências do período aplicável.",
            ],
        },
    }

    return {
        "interna": base_interna,
        "externa": base_interna,
        "reestruturacao": base_interna,
        "aro": base_interna,
        "regularizacao": base_interna,
        "consorcio": base_interna,
        "garantia_ente": base_interna,
        "lc_156": base_interna,
        "lc_159": base_interna,
        "lc_178": base_interna,
        "lc_212": base_interna,
        "pef": base_interna,
    }


def explain_period_rules(modalidade, data_ref):
    catalog = build_checklist_catalog()
    base = catalog.get(modalidade, {})
    janela, janela_label = _janela_por_data(data_ref)

    observacoes_gerais = []
    if janela == "janeiro":
        observacoes_gerais = [
            "Nesta janela, a data específica serve para interpretar as regras do período, não para pesquisar PVLs na API.",
            "Entre 01/01 e 30/03, o MIP pode admitir referências do exercício anterior fechado e o uso do Anexo 1 da LOA em situações aplicáveis.",
            "A verificação de RREO e RGF deve considerar a janela temporal do pleito e a exigibilidade do demonstrativo para o período.",
        ]
    else:
        observacoes_gerais = [
            "Após 30/03, a tendência é migrar para referências do exercício em curso, conforme o MIP.",
            "A leitura de RREO, RGF e demais demonstrativos deve ser atualizada para o período aplicável.",
            "A data específica continua sendo um insumo normativo, não um filtro de pesquisa factual do PVL na API.",
        ]

    linhas = []
    for aba, janelas in base.items():
        for item in janelas.get(janela, []):
            linhas.append({
                "aba": aba,
                "janela": janela_label,
                "item_checklist": item,
            })

    return {
        "modalidade": modalidade,
        "janela": janela,
        "janela_label": janela_label,
        "observacoes_gerais": observacoes_gerais,
        "linhas": linhas,
    }
