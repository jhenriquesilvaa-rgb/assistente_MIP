import io
import re
from datetime import date
from typing import Dict, List, Tuple

import pandas as pd


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


def _base_checklists() -> Dict:
    common_contratadas = {
        "janeiro": [
            "Adequar o cronograma de liberações das operações contratadas ao novo exercício.",
            "Adequar o cronograma de pagamentos das operações contratadas ao novo exercício.",
            "No cronograma de pagamentos, observar a compatibilidade com a DC do exercício anterior; em janeiro, o MIP admite a lógica de transição até a publicação final do RGF, conforme o caso.",
            "Registrar em Notas Explicativas valores do período final do exercício anterior quando exigido pela lógica de janeiro.",
        ],
        "pos_3001": [
            "Compatibilizar o cronograma de pagamentos com o DDCL/RGFs do exercício anterior fechado.",
            "Remover ajustes transitórios de janeiro se o RGF final do exercício anterior já está refletido nas bases.",
        ],
        "pos_3003": [
            "Manter cronogramas atualizados após o 1º bimestre do exercício em curso.",
            "Se houver operação em moeda estrangeira, adequar taxas de câmbio às referências do período aplicável.",
        ],
        "pos_3005": [
            "Atualizar cronogramas após o 2º bimestre do exercício em curso.",
            "Compatibilizar pagamentos com o último RGF exigível do período.",
        ],
        "pos_3007": [
            "Atualizar cronogramas após o 3º bimestre do exercício em curso.",
            "Para município optante do art. 63, verificar reflexos do RGF do 1º semestre, quando aplicável.",
        ],
        "pos_3009": [
            "Atualizar cronogramas após o 4º bimestre do exercício em curso.",
            "Compatibilizar pagamentos com o RGF do 2º quadrimestre do exercício em curso, quando aplicável.",
        ],
        "pos_3011": [
            "Atualizar cronogramas após o 5º bimestre do exercício em curso.",
            "Preparar consistência para o fechamento anual e o novo exercício.",
        ],
    }

    common_nao_contratadas = {
        "janeiro": [
            "Selecionar todas as operações em tramitação que já tenham sido enviadas à análise.",
            "Selecionar as operações deferidas ainda não contratadas, salvo aquelas cuja não contratação tenha sido declarada expressamente.",
            "Revisar se houve mudança de exercício que exija atualização/reinserção dos cronogramas das operações não contratadas.",
        ],
        "pos_3001": [
            "Manter selecionadas as operações em tramitação e as deferidas não contratadas ainda relevantes para o cálculo de limites.",
            "Se uma operação deferida não contratada precisar de atualização de cronograma no novo exercício, usar a lógica de atualização própria da aba.",
        ],
        "pos_3003": ["Revisar a lista após o 1º bimestre do exercício em curso, excluindo operações já contratadas e mantendo as materialmente relevantes."],
        "pos_3005": ["Revisar a seleção das operações em tramitação e deferidas ainda não contratadas após o 2º bimestre."],
        "pos_3007": ["Revisar a seleção das operações em tramitação e deferidas ainda não contratadas após o 3º bimestre."],
        "pos_3009": ["Revisar a seleção das operações em tramitação e deferidas ainda não contratadas após o 4º bimestre."],
        "pos_3011": ["Revisar a seleção das operações em tramitação e deferidas ainda não contratadas após o 5º bimestre.", "Preparar a consistência da aba para o fechamento anual e a virada do exercício."],
    }
    return common_contratadas, common_nao_contratadas


def _conditional_checklists() -> Dict:
    common_contratadas, common_nao_contratadas = _base_checklists()

    generic_special = {
        "janeiro": ["Revisar a documentação e o canal principal da operação especial no novo exercício."],
        "pos_3001": ["Revisar a documentação e os requisitos do exercício anterior fechado para a operação especial."],
        "pos_3003": ["Revisar a documentação da operação especial após 30/03, considerando bases correntes exigíveis."],
        "pos_3005": ["Revisar a documentação da operação especial após 30/05, considerando bases correntes exigíveis."],
        "pos_3007": ["Revisar a documentação da operação especial após 30/07, considerando bases correntes exigíveis."],
        "pos_3009": ["Revisar a documentação da operação especial após 30/09, considerando bases correntes exigíveis."],
        "pos_3011": ["Revisar a documentação da operação especial após 30/11, preparando transição para o fechamento anual."],
    }

    catalog = {
        "ordinaria_sem_gu": {},
        "ordinaria_com_gu": {},
        "externa_com_gu": {},
        "reestruturacao": {"Fluxo / Canal": generic_special, "Documentos": generic_special},
        "aro": {"Fluxo / Canal": generic_special, "Documentos": generic_special},
        "regularizacao": {"Fluxo / Canal": generic_special, "Documentos": generic_special},
        "garantia_ente": {"Fluxo / Canal": generic_special, "Documentos": generic_special},
        "consorcio": {"Fluxo / Canal": generic_special, "Documentos": generic_special},
        "lc_156": {"Fluxo / Canal": generic_special, "Documentos": generic_special},
        "lc_159": {"Fluxo / Canal": generic_special, "Documentos": generic_special},
        "lc_178": {"Fluxo / Canal": generic_special, "Documentos": generic_special},
        "pef": {"Fluxo / Canal": generic_special, "Documentos": generic_special},
        "lc_212": {"Fluxo / Canal": generic_special, "Documentos": generic_special},
    }

    catalog["ordinaria_sem_gu"] = {
        "Informações Contábeis": {
            "janeiro": ["Usar a lógica do 6º bimestre do exercício anterior para o exercício anterior fechado.", "Usar Anexo 1 da LOA do exercício em curso para o exercício corrente até 30/03.", "Usar 5º bimestre do exercício anterior para a RCL do último RREO exigível; usar o 6º, se já publicado.", "Usar o 2º quadrimestre do exercício anterior, ou 1º semestre para município do art. 63, no DDCL/RGF, salvo relatório final já disponível."],
            "pos_3001": ["Atualizar para refletir o exercício anterior fechado com RREO do 6º bimestre homologado no Siconfi.", "Manter Anexo 1 da LOA até 30/03 para o exercício corrente.", "Usar o RGF final do exercício anterior."],
            "pos_3003": ["Substituir o Anexo 1 por informações do RREO do 1º bimestre do exercício em curso.", "Atualizar RCL para o 1º bimestre.", "Manter DDCL com base no último RGF exigível do período."],
            "pos_3005": ["Atualizar RREO/RCL para o 2º bimestre.", "Atualizar DDCL com base no RGF do 1º quadrimestre, se aplicável."],
            "pos_3007": ["Atualizar RREO/RCL para o 3º bimestre.", "Se município do art. 63, atualizar DDCL com base no 1º semestre."],
            "pos_3009": ["Atualizar RREO/RCL para o 4º bimestre.", "Atualizar DDCL com base no RGF do 2º quadrimestre, se aplicável."],
            "pos_3011": ["Atualizar RREO/RCL para o 5º bimestre.", "Manter DDCL com base no último RGF exigível do exercício em curso."],
        },
        "Declaração do Chefe do Poder Executivo": {
            "janeiro": ["Emitir nova declaração no exercício corrente, se houve virada de exercício.", "Atualizar quadro de pessoal e referências de ano em curso.", "Atestar inclusão orçamentária com base na LOA vigente."],
            "pos_3001": ["Atualizar os campos dependentes do exercício anterior fechado.", "Revisar quadro de pessoal com base no último RGF exigível final do exercício anterior."],
            "pos_3003": ["Ajustar referências do exercício corrente conforme o 1º bimestre.", "Manter consistência entre declaração, contabilidade e certidão do TC."],
            "pos_3005": ["Atualizar quadro de despesa com pessoal com base no último RGF exigível do período."],
            "pos_3007": ["Para município do art. 63, usar o 1º semestre do exercício em curso para o quadro de pessoal."],
            "pos_3009": ["Atualizar a declaração segundo o último RGF exigível do exercício em curso."],
            "pos_3011": ["Manter a declaração alinhada ao último RREO/RGF exigível do exercício em curso."],
        },
        "Documentos": {
            "janeiro": ["Anexar lei autorizadora, parecer jurídico do exercício corrente, parecer técnico, certidão do TC e Anexo 1 da LOA do exercício em curso.", "Revisar se a certidão do TC atende ao período de janeiro e ao fechamento do exercício anterior."],
            "pos_3001": ["Atualizar a certidão do TC para refletir o exercício anterior fechado.", "Verificar homologação do RREO do 6º bimestre do exercício anterior e do CDP.", "Manter Anexo 1 da LOA até 30/03."],
            "pos_3003": ["Após 30/03, substituir a dependência do Anexo 1 por referências do RREO do 1º bimestre.", "Verificar documentos e certidões exigíveis do período."],
            "pos_3005": ["Atualizar certidões e bases documentais para o 2º bimestre e RGF correspondente."],
            "pos_3007": ["Atualizar certidões e bases documentais para o 3º bimestre; para município do art. 63, observar 1º semestre."],
            "pos_3009": ["Atualizar certidões e bases documentais para o 4º bimestre e RGF correspondente."],
            "pos_3011": ["Atualizar certidões e bases documentais para o 5º bimestre do exercício em curso."],
        },
        "Operações Contratadas": common_contratadas,
        "Operações não Contratadas": common_nao_contratadas,
        "Resumo": {
            "janeiro": ["Conferir se a regra de ouro do exercício corrente está apoiada no Anexo 1 da LOA.", "Conferir se os cronogramas das Operações Contratadas foram adequados ao novo exercício.", "Conferir se a aba Operações não Contratadas reflete corretamente operações em tramitação e deferidas não contratadas.", "Verificar CDP e pendências de regularização após salvar o PVL."],
            "pos_3001": ["Conferir regra de ouro do exercício anterior com base no exercício anterior fechado.", "Conferir se o Resumo reflete o RREO do 6º bimestre e o RGF final do exercício anterior.", "Conferir se os painéis de MGA/RCL e CAED/RCL capturam corretamente Operações Contratadas e Operações não Contratadas."],
            "pos_3003": ["Conferir atualização da regra de ouro do exercício corrente com base no RREO do 1º bimestre.", "Conferir painéis de MGA/RCL, CAED/RCL e DCL/RCL após atualizar Informações Contábeis, Operações Contratadas e Operações não Contratadas."],
            "pos_3005": ["Conferir painéis usando 2º bimestre e último RGF exigível do período, com reflexo correto das operações contratadas e não contratadas."],
            "pos_3007": ["Conferir painéis usando 3º bimestre; para município do art. 63, considerar reflexos do 1º semestre e das operações selecionadas nas abas correspondentes."],
            "pos_3009": ["Conferir painéis usando 4º bimestre e último RGF exigível do exercício em curso, inclusive consolidação de operações contratadas e não contratadas."],
            "pos_3011": ["Conferir painéis usando 5º bimestre do exercício em curso e preparar consistência para o fechamento anual das abas Operações Contratadas e Operações não Contratadas."],
        },
    }

    # reuso simplificado das famílias principais
    catalog["ordinaria_com_gu"] = {
        **catalog["ordinaria_sem_gu"],
        "Documentos": {
            "janeiro": ["Além dos documentos-base ordinários, revisar documentos específicos da garantia da União.", "Anexar certidão do TC que ateste saúde e educação para o exercício anterior fechado, inclusive em janeiro."],
            "pos_3001": ["Atualizar certidão do TC para regra de ouro do exercício anterior fechado.", "Atualizar certidão do TC relativa aos arts. 198 e 212 da Constituição para o exercício anterior fechado."],
            "pos_3003": ["Substituir a base do exercício corrente do Anexo 1 pelo RREO do 1º bimestre, quando aplicável.", "Verificar exigências adicionais de garantia da União no período."],
            "pos_3005": ["Atualizar certidões/documentos para 2º bimestre e RGF exigível correspondente."],
            "pos_3007": ["Atualizar certidões/documentos para 3º bimestre e, se aplicável, 1º semestre do município do art. 63."],
            "pos_3009": ["Atualizar certidões/documentos para 4º bimestre e RGF correspondente."],
            "pos_3011": ["Atualizar certidões/documentos para 5º bimestre do exercício em curso."],
        },
    }

    catalog["externa_com_gu"] = {
        **catalog["ordinaria_com_gu"],
        "Operações Contratadas": {
            **common_contratadas,
            "janeiro": common_contratadas["janeiro"] + ["Se houver operações em moeda estrangeira, adequar taxas de câmbio usadas nas operações contratadas e no Resumo ao período aplicável."],
            "pos_3003": common_contratadas["pos_3003"] + ["Ajustar câmbio das operações contratadas para a data-base do período, quando houver dívida em moeda estrangeira."],
            "pos_3005": common_contratadas["pos_3005"] + ["Ajustar câmbio das operações contratadas para a data-base do 2º bimestre, quando houver dívida em moeda estrangeira."],
            "pos_3007": common_contratadas["pos_3007"] + ["Ajustar câmbio das operações contratadas para a data-base do 3º bimestre, quando houver dívida em moeda estrangeira."],
            "pos_3009": common_contratadas["pos_3009"] + ["Ajustar câmbio das operações contratadas para a data-base do 4º bimestre, quando houver dívida em moeda estrangeira."],
            "pos_3011": common_contratadas["pos_3011"] + ["Ajustar câmbio das operações contratadas para a data-base do 5º bimestre, quando houver dívida em moeda estrangeira."],
        },
        "Resumo": {
            "janeiro": ["Conferir regra de ouro do exercício corrente com base na LOA/Anexo 1, quando aplicável.", "Conferir taxa de câmbio, cronogramas e painéis após salvar o PVL.", "Conferir se Operações Contratadas e Operações não Contratadas estão corretamente refletidas nos painéis consolidados."],
            "pos_3001": ["Conferir painéis com base no exercício anterior fechado e nos cronogramas atualizados.", "Conferir reflexo das operações contratadas e não contratadas nos painéis consolidados."],
            "pos_3003": ["Conferir atualização dos painéis com base no 1º bimestre do exercício em curso.", "Conferir atualização de taxas de câmbio e reflexos de Operações Contratadas/Não Contratadas."],
            "pos_3005": ["Conferir atualização dos painéis com base no 2º bimestre do exercício em curso, inclusive câmbio e operações selecionadas."],
            "pos_3007": ["Conferir atualização dos painéis com base no 3º bimestre do exercício em curso, inclusive câmbio e operações selecionadas."],
            "pos_3009": ["Conferir atualização dos painéis com base no 4º bimestre do exercício em curso, inclusive câmbio e operações selecionadas."],
            "pos_3011": ["Conferir atualização dos painéis com base no 5º bimestre do exercício em curso, inclusive câmbio e operações selecionadas, preparando consistência para o fechamento anual."],
        },
    }

    
    catalog["reestruturacao"] = {
        "Fluxo / Canal": {
            "janeiro": [
                "Confirmar se o pleito tramita pelo SADIPEM como finalidade 'Reestruturação e recomposição do principal de dívidas'.",
                "Definir se a operação é interna ou externa e se há garantia da União, pois isso altera o fluxo documental complementar.",
                "Verificar desde o início se a operação pretende usufruir do enquadramento excepcional do § 7º do art. 7º da RSF 43/2001.",
            ],
            "pos_3001": [
                "Manter a finalidade específica no cadastro e revisar se a estratégia continua sendo de troca de dívida, e não de operação ordinária.",
                "Se houver garantia da União, alinhar o fluxo com os requisitos da seção 11 do MIP.",
            ],
            "pos_3003": ["Revisar o enquadramento da operação frente ao novo exercício e aos efeitos nos demais PVL do ente."],
            "pos_3005": ["Revisar o enquadramento da operação e os documentos financeiros da dívida antiga e da nova dívida."],
            "pos_3007": ["Revisar o enquadramento da operação e a aderência às premissas de reestruturação no exercício em curso."],
            "pos_3009": ["Revisar o enquadramento da operação e preparar atualização documental, se ainda pendente de contratação."],
            "pos_3011": ["Revisar o enquadramento da operação e os efeitos de fechamento anual/virada de exercício."],
        },
        "Documentos": {
            "janeiro": [
                "Anexar o contrato da dívida antiga a ser reestruturada.",
                "Anexar todos os termos aditivos e documentos que alteraram a dívida antiga.",
                "Anexar ofício do chefe do Poder Executivo com saldo devedor atualizado, prazos, taxas, encargos, condições de pré-pagamento e identificação do número da dívida no CDP e dos processos anteriores na STN.",
                "Anexar parecer técnico demonstrando relação custo-benefício da troca da dívida.",
                "Anexar parecer jurídico e, se aplicável, documentos de garantia da União.",
                "Em caso de operação interna, anexar minuta/condições da nova operação; em caso de externa, observar o rito próprio e a documentação correlata.",
            ],
            "pos_3001": [
                "Revalidar saldo devedor atualizado da dívida antiga e consistência do ofício explicativo.",
                "Revisar se a documentação da dívida antiga e da nova operação continua íntegra e suficiente para demonstrar troca de dívida.",
            ],
            "pos_3003": ["Atualizar os documentos financeiros da dívida antiga e da nova operação, se a negociação ou o saldo tiverem mudado."],
            "pos_3005": ["Atualizar documentos e informações da dívida antiga e da nova operação conforme o período e a negociação."],
            "pos_3007": ["Revisar documentos da dívida antiga e da nova operação, inclusive custo-benefício."],
            "pos_3009": ["Atualizar documentação e ofício com saldo e fluxos, se ainda houver pendência de contratação."],
            "pos_3011": ["Preparar documentação para eventual virada de exercício, se a contratação não ocorrer no exercício corrente."],
        },
        "Operações Contratadas": {
            "janeiro": [
                "Verificar se a dívida antiga está corretamente refletida nas operações contratadas quando ainda compõe o estoque/fluxo relevante do ente.",
                "Se a nova dívida já tiver sido contratada, revisar cronogramas para evitar dupla contagem indevida.",
            ],
            "pos_3001": ["Compatibilizar a presença da dívida antiga e/ou da nova dívida com a base fiscal do exercício anterior fechado."],
            "pos_3003": ["Conferir se a nova dívida passou a compor corretamente os cronogramas das operações contratadas, quando já formalizada."],
            "pos_3005": ["Conferir consistência entre dívida antiga, nova dívida e cronogramas das operações contratadas."],
            "pos_3007": ["Conferir consistência entre dívida antiga, nova dívida e cronogramas das operações contratadas."],
            "pos_3009": ["Conferir consistência entre dívida antiga, nova dívida e cronogramas das operações contratadas."],
            "pos_3011": ["Conferir consistência da migração da dívida antiga para a nova dívida nas operações contratadas, inclusive para fechamento anual."],
        },
        "Operações não Contratadas": {
            "janeiro": [
                "Se a nova operação ainda estiver em tramitação ou deferida não contratada, garantir sua correta seleção na aba Operações não Contratadas.",
                "Evitar inconsistência entre a dívida antiga e a nova operação durante a fase de transição.",
            ],
            "pos_3001": ["Conferir se a nova operação continua corretamente selecionada entre as não contratadas enquanto não formalizada."],
            "pos_3003": ["Conferir a permanência/retirada da nova operação da aba conforme contratação, deferimento ou alteração do cronograma."],
            "pos_3005": ["Conferir a permanência/retirada da nova operação da aba conforme contratação, deferimento ou alteração do cronograma."],
            "pos_3007": ["Conferir a permanência/retirada da nova operação da aba conforme contratação, deferimento ou alteração do cronograma."],
            "pos_3009": ["Conferir a permanência/retirada da nova operação da aba conforme contratação, deferimento ou alteração do cronograma."],
            "pos_3011": ["Conferir a permanência/retirada da nova operação da aba e preparar consistência para o fechamento anual."],
        },
        "Resumo": {
            "janeiro": [
                "Validar se a operação atende às premissas para enquadramento excepcional como reestruturação de dívida: troca de dívida, inexistência de novos recursos, foco em principal, custo/encargos mais favoráveis, ausência de desenho incompatível.",
                "Conferir se a operação não está sendo tratada como operação ordinária por falha documental ou por descumprimento das premissas.",
                "Conferir impactos da dívida antiga e da nova dívida sobre os painéis consolidados.",
            ],
            "pos_3001": [
                "Revalidar o enquadramento excepcional com base no exercício anterior fechado e na documentação atualizada.",
                "Conferir se há reflexos da nova dívida e da dívida antiga nos painéis consolidados sem distorções.",
            ],
            "pos_3003": ["Conferir se a operação continua devidamente enquadrada como reestruturação e se os painéis consolidam corretamente a nova dívida e a dívida antiga."],
            "pos_3005": ["Conferir o enquadramento e o reflexo da operação reestruturada nos painéis do Resumo."],
            "pos_3007": ["Conferir o enquadramento e o reflexo da operação reestruturada nos painéis do Resumo."],
            "pos_3009": ["Conferir o enquadramento e o reflexo da operação reestruturada nos painéis do Resumo."],
            "pos_3011": ["Conferir o enquadramento e o reflexo da operação reestruturada nos painéis do Resumo, preparando eventual virada de exercício."],
        },
    }

    catalog["aro"] = {
        "Fluxo / Canal": generic_special,
        "Documentos": {
            "janeiro": ["Checar janela legal de contratação, vedação temporal, protocolo de intenções no BCB e tramitação via Fale conosco."],
            "pos_3001": ["Checar prazo, requisitos específicos da ARO e documentos da IF e do EF."],
            "pos_3003": ["Checar requisitos específicos da ARO no exercício corrente."],
            "pos_3005": ["Checar requisitos específicos da ARO no exercício corrente."],
            "pos_3007": ["Checar requisitos específicos da ARO no exercício corrente."],
            "pos_3009": ["Checar requisitos específicos da ARO no exercício corrente."],
            "pos_3011": ["Checar requisitos específicos da ARO no exercício corrente."],
        },
    }

    catalog["regularizacao"] = {
        "Fluxo / Canal": generic_special,
        "Documentos": {
            "janeiro": ["Exigir contrato/termo da dívida a regularizar, lei autorizadora, parecer jurídico, parecer técnico e documentos da operação irregular."],
            "pos_3001": ["Revisar suficiência documental para regularização e efeitos sobre novos pleitos."],
            "pos_3003": ["Revisar suficiência documental para regularização e efeitos sobre novos pleitos."],
            "pos_3005": ["Revisar suficiência documental para regularização e efeitos sobre novos pleitos."],
            "pos_3007": ["Revisar suficiência documental para regularização e efeitos sobre novos pleitos."],
            "pos_3009": ["Revisar suficiência documental para regularização e efeitos sobre novos pleitos."],
            "pos_3011": ["Revisar suficiência documental para regularização e efeitos sobre novos pleitos."],
        },
    }

    catalog["garantia_ente"] = {
        "Fluxo / Canal": generic_special,
        "Documentos": {
            "janeiro": ["Exigir autorização legislativa específica, demonstrativo das garantias prestadas, documento sobre contragarantias e documento/certidão de adimplência do tomador perante o garantidor."],
            "pos_3001": ["Revisar documentação e limite das garantias concedidas."],
            "pos_3003": ["Revisar documentação e limite das garantias concedidas."],
            "pos_3005": ["Revisar documentação e limite das garantias concedidas."],
            "pos_3007": ["Revisar documentação e limite das garantias concedidas."],
            "pos_3009": ["Revisar documentação e limite das garantias concedidas."],
            "pos_3011": ["Revisar documentação e limite das garantias concedidas."],
        },
    }

    catalog["consorcio"] = {
        "Fluxo / Canal": {
            "janeiro": ["Lembrar que cada ente participante deve ter seu próprio PVL, conforme quota-parte ou quota de investimento.", "Verificar se a finalidade do PVL está correta para consórcio público."],
            "pos_3001": ["Revisar a consistência entre todos os PVL dos entes consorciados e o prazo de validade das análises."],
            "pos_3003": ["Revisar a consistência entre todos os PVL dos entes consorciados e o prazo de validade das análises."],
            "pos_3005": ["Revisar a consistência entre todos os PVL dos entes consorciados e o prazo de validade das análises."],
            "pos_3007": ["Revisar a consistência entre todos os PVL dos entes consorciados e o prazo de validade das análises."],
            "pos_3009": ["Revisar a consistência entre todos os PVL dos entes consorciados e o prazo de validade das análises."],
            "pos_3011": ["Revisar a consistência entre todos os PVL dos entes consorciados, o prazo de validade e a virada do exercício."],
        },
        "Documentos": {
            "janeiro": ["Em cada PVL, exigir documentos individualizados pela quota-parte/quota de investimento do ente e nota explicativa identificando o consórcio, CNPJ e valor total da operação."],
            "pos_3001": ["Revisar documentos individualizados de cada ente participante e coerência entre os PVL."],
            "pos_3003": ["Revisar documentos individualizados de cada ente participante e coerência entre os PVL."],
            "pos_3005": ["Revisar documentos individualizados de cada ente participante e coerência entre os PVL."],
            "pos_3007": ["Revisar documentos individualizados de cada ente participante e coerência entre os PVL."],
            "pos_3009": ["Revisar documentos individualizados de cada ente participante e coerência entre os PVL."],
            "pos_3011": ["Revisar documentos individualizados de cada ente participante e coerência entre os PVL na virada do exercício."],
        },
    }

    catalog["aro"] = {
        "Fluxo / Canal": {
            "janeiro": [
                "Confirmar que a tramitação da ARO ocorrerá fora do SADIPEM, por meio do Fale conosco de operações de crédito e CDP, após a comunicação do BCB sobre a aprovação do protocolo de intenções.",
                "Verificar se a contratação não está vedada no período e se a operação respeita as restrições temporais próprias da ARO.",
            ],
            "pos_3001": ["Manter o rito específico da ARO via Fale conosco e reavaliar a janela temporal legal da contratação."],
            "pos_3003": ["Verificar o rito específico da ARO e as condições temporais aplicáveis no exercício corrente."],
            "pos_3005": ["Verificar o rito específico da ARO e as condições temporais aplicáveis no exercício corrente."],
            "pos_3007": ["Verificar o rito específico da ARO e as condições temporais aplicáveis no exercício corrente."],
            "pos_3009": ["Verificar o rito específico da ARO e as condições temporais aplicáveis no exercício corrente."],
            "pos_3011": ["Verificar o rito específico da ARO e as condições temporais aplicáveis no exercício corrente."],
        },
        "Documentos": {
            "janeiro": [
                "Exigir documentação prevista no art. 22 da RSF 43/2001 e no art. 38 da LRF, conforme aplicável.",
                "Exigir solicitação da IF contendo cronograma de reembolso, montante, prazo, juros e garantias.",
                "Exigir documento assinado pelo chefe do Poder Executivo com concordância às condições da operação.",
                "Exigir declaração de não reciprocidade assinada pelo representante da IF e pelo chefe do Poder Executivo.",
                "Validar lei autorizadora e certidão do TC aplicáveis à ARO.",
            ],
            "pos_3001": ["Revalidar toda a documentação da ARO, inclusive condições financeiras, cronograma e declaração de não reciprocidade."],
            "pos_3003": ["Revalidar documentação da ARO e sua aderência às vedações e condições legais."],
            "pos_3005": ["Revalidar documentação da ARO e sua aderência às vedações e condições legais."],
            "pos_3007": ["Revalidar documentação da ARO e sua aderência às vedações e condições legais."],
            "pos_3009": ["Revalidar documentação da ARO e sua aderência às vedações e condições legais."],
            "pos_3011": ["Revalidar documentação da ARO e sua aderência às vedações e condições legais."],
        },
        "Resumo": {
            "janeiro": ["Conferir limite de ARO em relação à RCL e vedação de contratação em situações impeditivas previstas no MIP."],
            "pos_3001": ["Conferir limite de ARO em relação à RCL e vedações legais vigentes."],
            "pos_3003": ["Conferir limite de ARO em relação à RCL e vedações legais vigentes."],
            "pos_3005": ["Conferir limite de ARO em relação à RCL e vedações legais vigentes."],
            "pos_3007": ["Conferir limite de ARO em relação à RCL e vedações legais vigentes."],
            "pos_3009": ["Conferir limite de ARO em relação à RCL e vedações legais vigentes."],
            "pos_3011": ["Conferir limite de ARO em relação à RCL e vedações legais vigentes."],
        },
    }

    catalog["regularizacao"] = {
        "Fluxo / Canal": {
            "janeiro": ["Tramitar a regularização pelo SADIPEM, observando se a operação irregular está ou não quitada e qual o tipo de credor envolvido."],
            "pos_3001": ["Manter a regularização no SADIPEM e revisar se a documentação permite concluir a baixa do impedimento."],
            "pos_3003": ["Manter a regularização no SADIPEM e revisar se a documentação permite concluir a baixa do impedimento."],
            "pos_3005": ["Manter a regularização no SADIPEM e revisar se a documentação permite concluir a baixa do impedimento."],
            "pos_3007": ["Manter a regularização no SADIPEM e revisar se a documentação permite concluir a baixa do impedimento."],
            "pos_3009": ["Manter a regularização no SADIPEM e revisar se a documentação permite concluir a baixa do impedimento."],
            "pos_3011": ["Manter a regularização no SADIPEM e revisar se a documentação permite concluir a baixa do impedimento."],
        },
        "Documentos": {
            "janeiro": [
                "Anexar contrato/termo de assunção, reconhecimento ou confissão da dívida e eventuais aditivos.",
                "Anexar lei específica que autorizou a operação irregular ou sua regularização, conforme o caso.",
                "Anexar parecer jurídico referindo-se expressamente à regularização da operação.",
                "Anexar parecer técnico atestando relação custo-benefício e interesse econômico-social, quando aplicável.",
                "Se a operação já estiver quitada, anexar termo de quitação da dívida, conforme orientação do MIP.",
            ],
            "pos_3001": ["Revalidar documentos da operação irregular, inclusive contrato, aditivos, pareceres e eventuais comprovantes de quitação."],
            "pos_3003": ["Revalidar documentos e situação da operação irregular à luz do exercício corrente."],
            "pos_3005": ["Revalidar documentos e situação da operação irregular à luz do exercício corrente."],
            "pos_3007": ["Revalidar documentos e situação da operação irregular à luz do exercício corrente."],
            "pos_3009": ["Revalidar documentos e situação da operação irregular à luz do exercício corrente."],
            "pos_3011": ["Revalidar documentos e situação da operação irregular à luz do exercício corrente."],
        },
        "Resumo": {
            "janeiro": ["Conferir se a operação permanece pendente de regularização, regularizada ou amparada por decisão judicial, e os efeitos sobre novos PVL."],
            "pos_3001": ["Conferir o status da regularização e o impacto sobre a contratação de novas operações."],
            "pos_3003": ["Conferir o status da regularização e o impacto sobre a contratação de novas operações."],
            "pos_3005": ["Conferir o status da regularização e o impacto sobre a contratação de novas operações."],
            "pos_3007": ["Conferir o status da regularização e o impacto sobre a contratação de novas operações."],
            "pos_3009": ["Conferir o status da regularização e o impacto sobre a contratação de novas operações."],
            "pos_3011": ["Conferir o status da regularização e o impacto sobre a contratação de novas operações."],
        },
    }

    catalog["garantia_ente"] = {
        "Fluxo / Canal": {
            "janeiro": ["Tramitar pelo SADIPEM como concessão de garantia, observando limites e contragarantias do tomador."],
            "pos_3001": ["Revisar o fluxo da garantia concedida e sua aderência ao limite global de garantias."],
            "pos_3003": ["Revisar o fluxo da garantia concedida e sua aderência ao limite global de garantias."],
            "pos_3005": ["Revisar o fluxo da garantia concedida e sua aderência ao limite global de garantias."],
            "pos_3007": ["Revisar o fluxo da garantia concedida e sua aderência ao limite global de garantias."],
            "pos_3009": ["Revisar o fluxo da garantia concedida e sua aderência ao limite global de garantias."],
            "pos_3011": ["Revisar o fluxo da garantia concedida e sua aderência ao limite global de garantias."],
        },
        "Documentos": {
            "janeiro": [
                "Exigir autorização específica do órgão legislativo.",
                "Exigir documento assinado pelo responsável pela administração financeira relacionando as garantias prestadas pelo EF.",
                "Exigir documento declarando o oferecimento de contragarantias suficientes pelo tomador.",
                "Exigir certidão do TC ou declaração/ certidão de adimplência do tomador perante o garantidor e entidades por ele controladas.",
                "Se houver pedido de elevação do limite de garantias, exigir documentação adicional correspondente.",
            ],
            "pos_3001": ["Revalidar documentos da concessão de garantia, inclusive limite global e suficiência de contragarantias."],
            "pos_3003": ["Revalidar documentos da concessão de garantia, inclusive limite global e suficiência de contragarantias."],
            "pos_3005": ["Revalidar documentos da concessão de garantia, inclusive limite global e suficiência de contragarantias."],
            "pos_3007": ["Revalidar documentos da concessão de garantia, inclusive limite global e suficiência de contragarantias."],
            "pos_3009": ["Revalidar documentos da concessão de garantia, inclusive limite global e suficiência de contragarantias."],
            "pos_3011": ["Revalidar documentos da concessão de garantia, inclusive limite global e suficiência de contragarantias."],
        },
        "Resumo": {
            "janeiro": ["Conferir o limite global de garantias concedidas em relação à RCL e a suficiência das contragarantias oferecidas pelo tomador."],
            "pos_3001": ["Conferir o limite global de garantias concedidas em relação à RCL e a suficiência das contragarantias oferecidas pelo tomador."],
            "pos_3003": ["Conferir o limite global de garantias concedidas em relação à RCL e a suficiência das contragarantias oferecidas pelo tomador."],
            "pos_3005": ["Conferir o limite global de garantias concedidas em relação à RCL e a suficiência das contragarantias oferecidas pelo tomador."],
            "pos_3007": ["Conferir o limite global de garantias concedidas em relação à RCL e a suficiência das contragarantias oferecidas pelo tomador."],
            "pos_3009": ["Conferir o limite global de garantias concedidas em relação à RCL e a suficiência das contragarantias oferecidas pelo tomador."],
            "pos_3011": ["Conferir o limite global de garantias concedidas em relação à RCL e a suficiência das contragarantias oferecidas pelo tomador."],
        },
    }

    catalog["consorcio"] = {
        "Fluxo / Canal": {
            "janeiro": [
                "Garantir que cada EF consorciado participante tenha seu próprio PVL no valor da respectiva quota-parte ou quota de investimento.",
                "Garantir que todos os PVL da mesma operação identifiquem o consórcio, o valor total da operação e a forma de apropriação do valor entre os entes.",
                "Conferir se a contratação pelo consórcio só ocorrerá quando todos os PVL relevantes estiverem deferidos e com prazo de validade vigente.",
            ],
            "pos_3001": ["Revisar coerência entre todos os PVL do consórcio e prazos de validade das análises."],
            "pos_3003": ["Revisar coerência entre todos os PVL do consórcio e prazos de validade das análises."],
            "pos_3005": ["Revisar coerência entre todos os PVL do consórcio e prazos de validade das análises."],
            "pos_3007": ["Revisar coerência entre todos os PVL do consórcio e prazos de validade das análises."],
            "pos_3009": ["Revisar coerência entre todos os PVL do consórcio e prazos de validade das análises."],
            "pos_3011": ["Revisar coerência entre todos os PVL do consórcio, prazos de validade e virada do exercício."],
        },
        "Documentos": {
            "janeiro": [
                "Em cada PVL, exigir documentos próprios do EF consorciado, com valor correspondente à sua quota-parte ou quota de investimento.",
                "Na nota explicativa, identificar o consórcio, CNPJ, valor total da operação e regra de apropriação entre entes.",
                "Garantir consistência entre todos os documentos dos entes participantes e a estrutura global da operação do consórcio.",
            ],
            "pos_3001": ["Revalidar documentos individualizados de cada ente participante e coerência global da operação do consórcio."],
            "pos_3003": ["Revalidar documentos individualizados de cada ente participante e coerência global da operação do consórcio."],
            "pos_3005": ["Revalidar documentos individualizados de cada ente participante e coerência global da operação do consórcio."],
            "pos_3007": ["Revalidar documentos individualizados de cada ente participante e coerência global da operação do consórcio."],
            "pos_3009": ["Revalidar documentos individualizados de cada ente participante e coerência global da operação do consórcio."],
            "pos_3011": ["Revalidar documentos individualizados de cada ente participante e coerência global da operação do consórcio."],
        },
        "Resumo": {
            "janeiro": ["Conferir se todos os PVL participantes do consórcio estão coerentes e se a operação só será contratada quando todos estiverem aptos."],
            "pos_3001": ["Conferir coerência dos PVL do consórcio e o prazo de validade das análises."],
            "pos_3003": ["Conferir coerência dos PVL do consórcio e o prazo de validade das análises."],
            "pos_3005": ["Conferir coerência dos PVL do consórcio e o prazo de validade das análises."],
            "pos_3007": ["Conferir coerência dos PVL do consórcio e o prazo de validade das análises."],
            "pos_3009": ["Conferir coerência dos PVL do consórcio e o prazo de validade das análises."],
            "pos_3011": ["Conferir coerência dos PVL do consórcio e o prazo de validade das análises na virada do exercício."],
        },
    }

    for fam in ["lc_156", "lc_159", "lc_178", "pef", "lc_212"]:
        catalog[fam] = {
            "Fluxo / Canal": generic_special,
            "Documentos": {
                "janeiro": ["Aplicar a documentação específica da lei complementar correspondente, com lei autorizadora específica, declaração do chefe do Poder Executivo, certidão do TC e demais documentos próprios da hipótese legal, conforme o caso.", "Se o período for entre 01/01 e 30/03, verificar se também é necessário o Anexo 1 da LOA, conforme a modalidade."],
                "pos_3001": ["Revisar a documentação específica da lei complementar correspondente com base no exercício anterior fechado."],
                "pos_3003": ["Revisar a documentação específica da lei complementar correspondente após 30/03, com base fiscal corrente."],
                "pos_3005": ["Revisar a documentação específica da lei complementar correspondente."],
                "pos_3007": ["Revisar a documentação específica da lei complementar correspondente."],
                "pos_3009": ["Revisar a documentação específica da lei complementar correspondente."],
                "pos_3011": ["Revisar a documentação específica da lei complementar correspondente e preparar eventual virada de exercício."],
            },
        }

    return catalog


def get_reference_period_rules(op_key: str, ref_date: date) -> List[Dict]:
    b = _bucket(ref_date)
    return [{"aba": "Janela temporal", "campo": "Período ativo", "valor_referencia": b["label"], "fonte_mip": "MIP 4.7 / 4.8 / 11.3", "etapa_data": b["label"]}]


def build_sadipem_action_plan(op_key: str, ref_date: date, sadipem_df: pd.DataFrame, operacoes_rules: Dict) -> List[Dict]:
    b = _bucket(ref_date)
    family = operacoes_rules[op_key]["family"]
    checklists = _conditional_checklists().get(family, {})
    df = sadipem_df[sadipem_df["operacao_codigo"] == op_key].copy()
    result = []
    for _, row in df.iterrows():
        aba = row["aba"]
        checklist = checklists.get(aba, {}).get(b["code"], ["Revisar manualmente conforme o MIP."])
        result.append({
            "aba": aba,
            "campo": row["campo"],
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
    checklists = _conditional_checklists().get(family, {})
    rows = []
    abas_prioritarias = ["Informações Contábeis", "Declaração do Chefe do Poder Executivo", "Documentos", "Operações Contratadas", "Operações não Contratadas", "Resumo", "Fluxo / Canal"]
    for aba in abas_prioritarias:
        for item in checklists.get(aba, {}).get(b["code"], []):
            rows.append({"aba": aba, "janela": b["label"], "item_checklist": item})
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
        if s and re.match(r"^(\d+(?:\.\d+){0,3})\s+.+", s):
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
        theme_results.append({"tema": rule.get("label", key), "codigo": key, "status": coverage, "keywords_detectadas": ", ".join(present_keywords), "secoes_esperadas": ", ".join(expected_sections), "secoes_detectadas": ", ".join(found_sections), "acao_sugerida": "Validar aderência fina da regra." if coverage == "ok" else "Revisar regra e capítulo correspondente."})
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
