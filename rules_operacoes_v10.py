import pandas as pd

RULES_VERSION = "v11.9"


def get_operacoes_rules():
    return {
        "interna_sem_garantia": {
            "label": "Operação de crédito interna sem garantia da União",
            "canal_principal": "SADIPEM",
            "origem_envio": "IF credora (ou EF, se não houver IF do SFN)",
            "garantia_uniao": False,
            "family": "ordinaria_sem_gu",
            "keywords": ["operação de crédito interno", "sem garantia da união", "pvl-if"],
            "expected_sections": ["6", "7"],
            "documentos_base": ["Lei autorizadora", "Parecer jurídico", "Parecer técnico", "Certidão do TC", "Anexo 1 até 30/03, quando aplicável"],
        },
        "interna_com_gu": {
            "label": "Operação de crédito interna com garantia da União",
            "canal_principal": "SADIPEM",
            "origem_envio": "IF credora",
            "garantia_uniao": True,
            "family": "ordinaria_com_gu",
            "keywords": ["operação interna com garantia da união", "garantia da união"],
            "expected_sections": ["6.3", "11"],
            "documentos_base": ["Lei autorizadora com contragarantias", "Parecer jurídico", "Parecer técnico", "Certidão do TC", "Anexo 1 até 30/03, quando aplicável"],
        },
        "externa": {
            "label": "Operação de crédito externa",
            "canal_principal": "SADIPEM + Fale conosco em etapas complementares",
            "origem_envio": "EF interessado",
            "garantia_uniao": True,
            "family": "externa_com_gu",
            "keywords": ["operação de crédito externo", "cofiex", "sce-crédito"],
            "expected_sections": ["9", "11"],
            "documentos_base": ["Lei autorizadora", "Parecer jurídico", "Parecer técnico", "Certidão do TC", "Resolução COFIEX", "Registro SCE-Crédito"],
        },
        "reestruturacao": {
            "label": "Reestruturação e recomposição do principal de dívidas",
            "canal_principal": "SADIPEM",
            "origem_envio": "IF credora ou EF, conforme a natureza",
            "garantia_uniao": "depende",
            "family": "reestruturacao",
            "keywords": ["reestruturação", "recomposição do principal"],
            "expected_sections": ["10"],
            "documentos_base": ["Contrato da dívida antiga a ser reestruturada", "Todos os aditivos da dívida antiga", "Ofício com saldo devedor atualizado, fluxos e identificação CDP/processos", "Parecer técnico específico", "Parecer jurídico", "Documentos/minuta da nova operação", "Documentos de garantia da União e contragarantia, se houver"],
        },
        "aro": {
            "label": "Antecipação de Receita Orçamentária (ARO)",
            "canal_principal": "Fale conosco de operações de crédito e CDP",
            "origem_envio": "IF / EF após protocolo de intenções aprovado no BCB",
            "garantia_uniao": False,
            "family": "aro",
            "keywords": ["aro", "antecipação de receita orçamentária"],
            "expected_sections": ["6.8"],
            "documentos_base": ["Solicitação da IF/proposta firme", "Declaração de não reciprocidade", "Lei autorizadora", "Certidão do TC", "Documentos exigidos para ARO nos termos da LRF e RSF 43/2001"],
        },
        "regularizacao": {
            "label": "Regularização de operação de crédito",
            "canal_principal": "SADIPEM",
            "origem_envio": "EF e, se houver, IF",
            "garantia_uniao": False,
            "family": "regularizacao",
            "keywords": ["regularização", "operação irregular"],
            "expected_sections": ["8"],
            "documentos_base": ["Contrato/termo da dívida a regularizar", "Aditivos/termos correlatos", "Lei autorizadora", "Parecer jurídico", "Parecer técnico", "Documentos exigidos para demonstrar a regularização"],
        },
        "garantia_ente": {
            "label": "Concessão de garantia por estado ou município",
            "canal_principal": "SADIPEM",
            "origem_envio": "EF garantidor",
            "garantia_uniao": False,
            "family": "garantia_ente",
            "keywords": ["concessão de garantia por estado", "concessão de garantia por município"],
            "expected_sections": ["12"],
            "documentos_base": ["Autorização legislativa específica", "Documento do garantidor sobre garantias prestadas", "Documento sobre contragarantias", "Certidão/declaração de adimplência do tomador"],
        },
        "consorcio": {
            "label": "Operação de crédito por consórcio público",
            "canal_principal": "SADIPEM",
            "origem_envio": "Cada EF consorciado (e IF, se interna)",
            "garantia_uniao": "depende",
            "family": "consorcio",
            "keywords": ["consórcio público"],
            "expected_sections": ["13"],
            "documentos_base": ["Um PVL por EF participante", "Nota explicativa identificando o consórcio", "Documentos individualizados por quota-parte/quota de investimento", "Coerência entre todos os PVL do consórcio"],
        },
        "lc_156": {
            "label": "Operações no âmbito da LC 156/2016",
            "canal_principal": "Fale conosco de operações de crédito e CDP",
            "origem_envio": "EF interessado / IF / CAIXA, conforme o caso",
            "garantia_uniao": "depende",
            "family": "lc_156",
            "keywords": ["lc 156/2016"],
            "expected_sections": ["14"],
            "documentos_base": ["Lei autorizadora específica", "Declaração do chefe do Poder Executivo", "Certidão do TC"],
        },
        "lc_159": {
            "label": "Operações no âmbito da LC 159/2017 (RRF)",
            "canal_principal": "Fale conosco de operações de crédito e CDP",
            "origem_envio": "IF credora ou EF, conforme o caso",
            "garantia_uniao": True,
            "family": "lc_159",
            "keywords": ["lc 159/2017", "rrf", "regime de recuperação fiscal"],
            "expected_sections": ["15"],
            "documentos_base": ["Ofício do pleito", "Lei autorizadora", "Declaração do chefe do Poder Executivo", "Certidão do TC", "Manifestação do Conselho de Supervisão do RRF"],
        },
        "lc_178": {
            "label": "Operações no âmbito da LC 178/2021",
            "canal_principal": "Fale conosco de operações de crédito e CDP",
            "origem_envio": "EF / IF / STN, conforme a hipótese legal",
            "garantia_uniao": "depende",
            "family": "lc_178",
            "keywords": ["lc 178/2021"],
            "expected_sections": ["16"],
            "documentos_base": ["Lei autorizadora específica", "Declaração do chefe do Poder Executivo", "Certidão do TC"],
        },
        "pef": {
            "label": "Operações no âmbito do PEF (LC 178/2021)",
            "canal_principal": "Fale conosco de operações de crédito e CDP",
            "origem_envio": "IF credora ou EF, conforme a operação",
            "garantia_uniao": True,
            "family": "pef",
            "keywords": ["pef", "plano de promoção do equilíbrio fiscal"],
            "expected_sections": ["16.2.4", "16.2.5", "16.3.2"],
            "documentos_base": ["Ofício do pleito", "Lei autorizadora do PEF", "Declaração do chefe do Poder Executivo", "Certidão do TC", "Comprovação do critério do PEF"],
        },
        "lc_212": {
            "label": "Operações no âmbito da LC 212/2025 (Propag)",
            "canal_principal": "Fale conosco de operações de crédito e CDP",
            "origem_envio": "Estado ou DF interessado",
            "garantia_uniao": False,
            "family": "lc_212",
            "keywords": ["lc 212/2025", "propag"],
            "expected_sections": ["17"],
            "documentos_base": ["Lei autorizadora específica", "Declaração do chefe do Poder Executivo", "Certidão do TC", "Anexo 1 da LOA entre 01/01 e 30/03"],
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

    # operações ordinárias e externas
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
        add(op, "Operações Contratadas", "Cronograma de liberações das operações já contratadas", "Compõe fluxo consolidado e MGA/RCL.", "Virada de exercício, nova contratação e atualização contratual.", "Em janeiro, deve-se adequar o cronograma ao novo exercício.")
        add(op, "Operações Contratadas", "Cronograma de pagamentos das operações já contratadas", "Compõe CAED/RCL, estoque e consistência com DDCL.", "Virada de exercício, novo RGF e atualização dos pagamentos.", "Compatibilizar com a DC do RGF/DDCL, conforme o período.")
        add(op, "Operações não Contratadas", "Operações em tramitação", "Integra o cálculo de limites das operações ainda não contratadas.", "Quando novos PVLs passarem a ter materialidade processual.", "Operação em preenchimento ainda não integra essa aba.")
        add(op, "Operações não Contratadas", "Operações deferidas ainda não contratadas", "Integra o cálculo de limites das operações deferidas pendentes de contratação.", "Quando houver deferimento, contratação ou desistência expressa.", "Se houver atualização do cronograma, pode ser necessária reinserção/atualização manual.")
        add(op, "Resumo", "Regra de ouro do exercício anterior", "Painel de verificação com base no exercício anterior.", "Sempre que houver atualização do exercício anterior fechado.", "Usa RREO do 6º bimestre e campos da Declaração.")
        add(op, "Resumo", "Regra de ouro do exercício corrente", "Painel de verificação com base no exercício corrente.", "Conforme LOA/Anexo 1 ou RREO exigível do exercício corrente.", "Até 30/03 pode se apoiar no Anexo 1 da LOA.")
        add(op, "Resumo", "MGA/RCL", "Limite de fluxo anual de operações de crédito.", "Quando mudarem cronogramas, operações contratadas/não contratadas e RCL.", "É alimentado por Cronograma Financeiro, Operações Contratadas, Operações não Contratadas e Informações Contábeis.")
        add(op, "Resumo", "CAED/RCL", "Limite de comprometimento anual com amortizações e encargos.", "Quando mudarem cronogramas e RCL projetada.", "Dialoga com Cronograma Financeiro e Operações Contratadas.")
        add(op, "Resumo", "DCL/RCL", "Limite de estoque da dívida.", "Quando mudarem DCL, valor do pleito ou operações relevantes.", "Depende da aba Informações Contábeis e do valor da operação.")
        add(op, "Resumo", "CDP e pendências de regularização", "Checagem consolidada do cadastro e impedimentos.", "Quando houver atualização do CDP, regularização ou mudança de status.", "O MIP destaca que o painel depende de atualização/salvamento.")

    # operações especiais aparecem na aba Operações, mesmo com menor detalhamento de matriz Sadipem
    for op in ["reestruturacao", "aro", "regularizacao", "garantia_ente", "consorcio", "lc_156", "lc_159", "lc_178", "pef", "lc_212"]:
        add(op, "Fluxo / Canal", "Canal principal e modo de envio", "Identifica se a tramitação é por SADIPEM, Fale conosco ou rito híbrido.", "Sempre que o usuário selecionar a modalidade.", "Operações especiais podem fugir do rito ordinário do PVL comum.")
        add(op, "Documentos", "Checklist documental base da modalidade", "Resume a documentação nuclear da operação especial.", "Conforme o tipo da operação e a data de referência.", "A lógica fina da modalidade especial deve ser refinada em versões seguintes.")

    return pd.DataFrame(rows)
