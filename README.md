# MIP PVL Assistant v12.5.2

Versão recomposta para publicação manual no GitHub e deploy no Streamlit.

## Estrutura da interface

- `Operações`: visão normativa por tipo de operação e data de referência.
- `Upload do MIP`: área visualmente restaurada para manter o fluxo.
- `SADIPEM`: visão normativa com checklist do período.
- `Pesquisa PVL/API`: pesquisa factual dos PVLs com filtro por período.
- `Base tabular`: catálogo tabular preservado.

## Ponto central desta versão

A data específica ficou restrita à interpretação normativa do período. A pesquisa factual de PVLs na API passou a usar período, com data inicial e data final, aplicado em `data_status`, `data_protocolo` ou ambos.
