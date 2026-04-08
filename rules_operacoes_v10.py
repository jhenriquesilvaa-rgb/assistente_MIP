import pandas as pd

RULES_VERSION = "v11.5"


def get_operacoes_rules():
    return {
        "interna_sem_garantia": {
            "label": "Operação de crédito interna sem garantia da União",
            "canal_principal": "SADIPEM",
            "origem_envio": "IF credora (ou EF, se não houver IF do SFN)",
            "garantia_uniao": False,
            "family": "ordinaria_sem_gu",
            "keywords": ["operação de crédito interno", "sem garantia da união", "pvl-if", "instituição financeira"],
            "expected_sections": ["6", "6.4", "6.5", "7", "4.5.1.1"],
            "documentos_base": [
                "Lei autorizadora.",
                "Parecer do órgão jurídico.",
                "Parecer do órgão técnico.",
                "Certidão do Tribunal de Contas.",
                "Anexo 1 da Lei 4.320/1964 até 30/03, quando aplicável.",
            ],
        },
        "interna_com_gu": {
            "label": "Operação de crédito interna com garantia da União",
            "canal_principal": "SADIPEM",
            "origem_envio": "IF credora",
            "garantia_uniao": True,
            "family": "ordinaria_com_gu",
            "keywords": ["operação de crédito interna com garantia da união", "garantia da união", "pgfn", "contragarantia"],
            "expected_sections": ["6.3", "11", "11.3", "11.4", "4.5.2.2", "4.7.9"],
            "documentos_base": [
                "Lei autorizadora com previsão de contragarantias.",
                "Parecer do órgão jurídico.",
                "Parecer do órgão técnico.",
                "Certidão do Tribunal de Contas.",
                "Anexo 1 da Lei 4.320/1964 até 30/03, quando aplicável.",
                "Dados para análise de CAPAG e custo efetivo.",
            ],
        },
        "externa": {
            "label": "Operação de crédito externa",
            "canal_principal": "SADIPEM + Fale conosco em etapas complementares",
            "origem_envio": "EF interessado",
            "garantia_uniao": True,
            "family": "externa_com_gu",
            "keywords": ["operação de crédito externo", "cofiex", "sce-crédito", "registro declaratório", "garantia da união"],
            "expected_sections": ["9", "11", "11.6"],
            "documentos_base": [
                "Lei autorizadora.",
                "Parecer jurídico.",
                "Parecer técnico.",
                "Certidão do Tribunal de Contas.",
                "Resolução COFIEX.",
                "Informação do registro no SCE-Crédito.",
            ],
        },
    }


def build_operacoes_df():
    rows = []
    for k, v in get_operacoes_rules().items():
        rows.append({
            "codigo": k,
            "operacao": v["label"],
            "familia_logica": v.get("family"),
            "canal_principal": v.get("canal_principal"),
            "origem_envio": v.get("origem_envio"),
            "garantia_uniao": v.get("garantia_uniao"),
            "expected_sections": ", ".join(v.get("expected_sections", [])),
        })
    return pd.DataFrame(rows)


def get_sadipem_field_matrix():
    rows = []
    def add(op, aba, campo, papel, quando, obs):
        rows.append({
            "operacao_codigo": op,
            "aba": aba,
            "campo": campo,
            "papel_do_campo": papel,
            "quando_alterar": quando,
            "observacao": obs,
        })

    # Abas críticas comuns
    for op in ["interna_sem_garantia", "interna_com_gu", "externa"]:
        add(op, "Informações Contábeis", "Balanço orçamentário do último RREO do exercício anterior", "Base do exercício anterior fechado.", "Conforme marcos do calendário fiscal.", "Tipicamente remete ao 6º bimestre do exercício anterior.")
        add(op, "Informações Contábeis", "Balanço orçamentário do último RREO exigível (ou Anexo 1 da LOA, quando couber)", "Base do exercício corrente.", "Conforme janeiro, pós-30/01, pós-30/03 e demais janelas.", "Até 30/03 pode haver uso do Anexo 1 da LOA.")
        add(op, "Informações Contábeis", "Demonstrativo da Receita Corrente Líquida do último RREO exigível", "Base da RCL para limites.", "Conforme o último RREO exigível.", "A referência muda ao longo do exercício.")
        add(op, "Informações Contábeis", "Demonstrativo da Dívida Consolidada Líquida do último RGF exigível", "Base da DCL e da dívida consolidada.", "Conforme o último RGF exigível.", "Considerar art. 63 da LRF quando aplicável.")

        add(op, "Declaração do Chefe do Poder Executivo", "Limites da despesa com pessoal / quadro de pessoal", "Base da verificação do art. 23 da LRF e correlatos.", "Na virada do exercício e conforme o último RGF exigível.", "Para contratação, observar o Poder Executivo conforme o MIP atual.")
        add(op, "Declaração do Chefe do Poder Executivo", "Inclusão orçamentária / LOA / PLOA", "Base da declaração de inclusão de recursos no orçamento.", "Na virada do exercício e quando a 1ª liberação ocorrer no exercício seguinte.", "Pode exigir referência ao PLOA em vez da LOA, conforme o caso.")
        add(op, "Declaração do Chefe do Poder Executivo", "Deduções / informações da regra de ouro", "Base para os painéis da regra de ouro na aba Resumo.", "Sempre que mudar exercício, LOA ou base fiscal.", "Dialoga com Anexo 1, RREO e certidões do TC.")

        add(op, "Documentos", "Lei autorizadora", "Documento essencial do pleito.", "Sempre que houver nova lei, alteração ou necessidade de nova operação.", "Em operações com garantia da União, deve prever contragarantias.")
        add(op, "Documentos", "Parecer do órgão jurídico", "Ateste jurídico dos requisitos legais.", "No exercício corrente e sempre que houver necessidade de atualização.", "Na virada do exercício, o parecer deve ser do novo exercício.")
        add(op, "Documentos", "Parecer do órgão técnico", "Ateste técnico da relação custo-benefício e interesse.", "Conforme mudanças materiais do pleito.", "Em geral acompanha o envio/retificação do PVL.")
        add(op, "Documentos", "Certidão do Tribunal de Contas", "Ateste dos requisitos certificados pelo TC.", "Conforme o período do ano e o último exercício fechado.", "Para garantia da União, incluir requisitos constitucionais adicionais.")
        add(op, "Documentos", "Anexo 1 da Lei 4.320/1964 / LOA", "Base provisória do exercício corrente até 30/03.", "Principalmente entre 01/01 e 30/03.", "Após 30/03 tende a ser substituído por RREO exigível.")

        add(op, "Resumo", "Regra de ouro do exercício anterior", "Painel de verificação com base no exercício anterior.", "Sempre que houver atualização do exercício anterior fechado.", "Usa RREO do 6º bimestre e campos da Declaração.")
        add(op, "Resumo", "Regra de ouro do exercício corrente", "Painel de verificação com base no exercício corrente.", "Conforme LOA/Anexo 1 ou RREO exigível do exercício corrente.", "Até 30/03 pode se apoiar no Anexo 1 da LOA.")
        add(op, "Resumo", "MGA/RCL", "Limite de fluxo anual de operações de crédito.", "Quando mudarem cronogramas, operações contratadas/não contratadas e RCL.", "É alimentado por Cronograma Financeiro, Operações Contratadas, Operações não Contratadas e Informações Contábeis.")
        add(op, "Resumo", "CAED/RCL", "Limite de comprometimento anual com amortizações e encargos.", "Quando mudarem cronogramas e RCL projetada.", "Dialoga com Cronograma Financeiro e Operações Contratadas.")
        add(op, "Resumo", "DCL/RCL", "Limite de estoque da dívida.", "Quando mudarem DCL, valor do pleito ou operações relevantes.", "Depende da aba Informações Contábeis e do valor da operação.")
        add(op, "Resumo", "CDP e pendências de regularização", "Checagem consolidada do cadastro e impedimentos.", "Quando houver atualização do CDP, regularização ou mudança de status.", "O MIP destaca que o painel depende de atualização/salvamento.")

    return pd.DataFrame(rows)
