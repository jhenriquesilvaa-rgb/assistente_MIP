
# MIP PVL Assistant v11

Protótipo em Streamlit para apoio ao envio de PVLs com base no MIP 2026.

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estrutura

- `app.py`: interface principal
- `rules/rules_operacoes_v10.py`: base de regras por tipo de operação e matriz SADIPEM
- `services/decision_engine_v10.py`: motor de decisão temporal, upload do MIP e plano campo a campo do SADIPEM

## Destaques desta versão

- aba **Operações** com fluxo resumido, documentos-base e gatilhos por data
- aba **Upload do MIP** com revisão de cobertura e sugestões de atualização da base
- aba **SADIPEM** com:
  - leitura por tipo de operação + data de referência
  - indicação de RREO/RGF/Anexo 1 por período
  - plano de ação campo a campo
  - exportação CSV do plano
