# MIP PVL Assistant v12.5

Versão focada em **restaurar o catálogo de operações** na aba Operações, mantendo a arquitetura e a lógica da v11.6.

Inclui novamente operações como:
- PEF;
- LC 156/2016;
- LC 159/2017;
- LC 178/2021;
- LC 212/2025;
- ARO;
- regularização;
- reestruturação;
- consórcio público;
- concessão de garantia por ente.

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```


## Novidade da v12.5

Aprofundamento da lógica da operação de **reestruturação e recomposição do principal de dívidas**, além de ampliar a cobertura mínima das demais operações especiais.

## Novidade da v12.5

Aprofundamento adicional das operações especiais: ARO, regularização, consórcio público, concessão de garantia por ente e blocos LC 156/159/178/PEF/212.


## Novidade da v12.5

- Novo módulo **Consulta PVL + Diagnóstico**, posicionado ao lado de SADIPEM.
- Entrada por número do PVL.
- Saída em quatro blocos: dados do pleito, checklist esperado, pendências prováveis e inconsistências detectadas.
- Aba **Base tabular** removida da visualização.

## Novidade da v12.5

- Integração real inicial do módulo **Consulta PVL + Diagnóstico** com a API pública do SADIPEM.
- Consulta por número do PVL ou processo.
- Identificação preliminar da família da operação e montagem de checklist esperado.
- Inferência inicial de pendências prováveis e inconsistências detectadas a partir dos dados públicos.

## Novidade da v12.5

- Diagnóstico calibrado por **status do PVL**, **data do status** e **tipo de operação**.
- Checklist esperado agora varia conforme o período inferido no exercício.
- Pendências prováveis passam a considerar família da operação e início do exercício.
- Inconsistências detectadas foram refinadas com base na coerência entre modalidade, vínculo com dívida e contratação informada pelo credor.

## Novidade da v12.5

- Mapeamento mais explícito dos campos públicos da API do SADIPEM, com contagem de campos presentes e ausentes.
- Agrupamento de status em cenários processuais para endurecer o diagnóstico.
- Regras de pendência e inconsistência mais estritas por combinação de **família da operação x grupo de status x data do status**.
- Exposição em tela do mapeamento dos campos efetivamente retornados pela API.

## Novidade da v12.5

- Busca ampliada de PVLs por **número do PVL, número do processo, ente, UF, ano, status e tipo de operação**.
- Integração com outros conjuntos públicos da API do SADIPEM, incluindo **Resumo-CDP**, **Resumo-cronograma de pagamentos**, **Operações Contratadas-cronograma de pagamentos**, **Operações Contratadas-cronograma de liberações** e **taxas de câmbio**.
- Diagnóstico detalhado agora pode partir de uma lista de resultados filtrados, e não apenas de um número exato de PVL.
- Regras de diagnóstico passaram a considerar ausência/presença dos dados multifonte retornados pelos endpoints públicos.

## Novidade da v12.5

- Motor técnico de diagnóstico reforçado por **tipo de operação**.
- Regras específicas adicionais para operações internas, externas, reestruturação, ARO, regularização, consórcio, garantia por ente e leis complementares.
- O diagnóstico passa a combinar **família da operação + grupo de status + sinais multifonte da API pública** para elevar o valor técnico da análise.
