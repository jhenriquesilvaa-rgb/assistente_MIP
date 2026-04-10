# MIP PVL Assistant v12.6.2

## Correções principais
- Bloqueia consulta sem filtro para evitar retorno de toda a base pública.
- Corrige a busca por número/processo com tentativas explícitas e sem fallback massivo.
- Reintroduz filtros adicionais: ente, UF, status, tipo de operação e período.
- Mantém os resultados da pesquisa em memória de sessão.
- Corrige o fluxo de seleção e o botão `Avaliar PVL`.

## Execução
```bash
pip install -r requirements.txt
streamlit run app.py
```
