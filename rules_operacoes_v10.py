RULES_VERSION = "v12.5.1"


def build_checklist_catalog():
    base_interna = {
        "Informações Contábeis": {
            "janeiro": [
                "Usar informações do exercício anterior fechado quando exigível.",
                "Conferir RGF/RREO aplicáveis ao período.",
            ],
            "pos_3003": [
                "Substituir referências anuais por demonstrativos bimestrais do exercício em curso quando cabível.",
                "Atualizar RCL e DCL conforme período aplicável.",
            ],
        },
        "Documentos": {
            "janeiro": [
                "Conferir certidões e declarações do período aplicável.",
                "Verificar consistência entre declaração, contabilidade e certidão do TC.",
            ],
            "pos_3003": [
                "Atualizar documentos sazonais após o primeiro bimestre, quando aplicável.",
                "Revalidar coerência documental do pleito com o exercício corrente.",
            ],
        },
        "Operações Contratadas": {
            "janeiro": [
                "Conferir cronogramas existentes e eventuais contratos já firmados.",
            ],
            "pos_3003": [
                "Manter cronogramas compatíveis com as informações mais recentes do exercício em curso.",
            ],
        },
    }

    return {
        "interna": base_interna,
        "externa": {
            **base_interna,
            "Operações Contratadas": {
                "janeiro": [
                    "Conferir cronogramas e informações cambiais da operação externa.",
                ],
                "pos_3003": [
                    "Atualizar cronogramas e verificar taxas de câmbio quando aplicáveis.",
                ],
            },
        },
        "reestruturacao": {
            "Documentos": {
                "janeiro": [
                    "Conferir documentação da dívida antiga, saldo e instrumento de reestruturação.",
                ],
                "pos_3003": [
                    "Atualizar evidências de troca de dívida e saldo reestruturado.",
                ],
            },
            "Cadastro da Dívida": {
                "janeiro": [
                    "Verificar aderência entre PVL e dívida vinculada no CDP.",
                ],
                "pos_3003": [
                    "Conferir manutenção do vínculo entre PVL e dívida reestruturada.",
                ],
            },
        },
        "aro": {
            "Documentos": {
                "janeiro": [
                    "Conferir rito específico da ARO e documentos próprios da modalidade.",
                ],
                "pos_3003": [
                    "Revalidar condições temporais e cronograma de reembolso da ARO.",
                ],
            },
        },
        "regularizacao": {
            "Documentos": {
                "janeiro": [
                    "Conferir documentos da operação irregular e histórico do saneamento.",
                ],
                "pos_3003": [
                    "Atualizar documentos comprobatórios da regularização.",
                ],
            },
        },
        "consorcio": {
            "Documentos": {
                "janeiro": [
                    "Conferir consistência entre o PVL do consórcio e os entes participantes.",
                ],
                "pos_3003": [
                    "Revalidar documentação conjunta e responsabilidade entre partícipes.",
                ],
            },
        },
        "garantia_ente": {
            "Documentos": {
                "janeiro": [
                    "Conferir autorização legislativa, contragarantias e limite global de garantias.",
                ],
                "pos_3003": [
                    "Atualizar comprovações de garantias concedidas e contragarantias.",
                ],
            },
        },
        "lc_156": {"Documentos": {"janeiro": ["Conferir hipótese legal específica da LC 156."], "pos_3003": ["Atualizar documentos da LC 156 conforme o exercício."]}},
        "lc_159": {"Documentos": {"janeiro": ["Conferir hipótese legal específica da LC 159."], "pos_3003": ["Atualizar documentos da LC 159 conforme o exercício."]}},
        "lc_178": {"Documentos": {"janeiro": ["Conferir hipótese legal específica da LC 178."], "pos_3003": ["Atualizar documentos da LC 178 conforme o exercício."]}},
        "lc_212": {"Documentos": {"janeiro": ["Conferir hipótese legal específica da LC 212."], "pos_3003": ["Atualizar documentos da LC 212 conforme o exercício."]}},
        "pef": {"Documentos": {"janeiro": ["Conferir hipótese legal específica do PEF."], "pos_3003": ["Atualizar documentos do PEF conforme o exercício."]}},
    }
