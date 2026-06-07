## Fluxo de Processamento v92.3 (Intelligence Governance Edition)

O fluxo foi aprimorado para maximizar a resiliência e reduzir custos operacionais via PLN determinístico local.

1. **Extração (V2)**: O `WkColetaInstagram` acessa perfis via Playwright (Tier 2), extraindo posts e comentários com ID determinístico (hash) para garantir zero duplicidade.
2. **Triagem Léxica (Voyant)**: O `AIService` envia lotes de 100 comentários para o `VoyantService` (porta 8888). Lotes neutros (< 8% agressividade) sofrem **Fast-Drop** e são classificados localmente como NEUTRO.
3. **Classificação Profunda (LLM)**: Somente lotes com vocabulário hostil são delegados à cascata de IA (Ollama -> Maritaca -> Cloud).
4. **Insights Periciais (SaVoyant)**: O Subagente Linguista cruza as métricas do Voyant com a 'Bíblia Linguística Forense' e gera eventos de sistema com alta relevância.
5. **Auditoria e Recompensas**: Subagentes auditam classificações e geram XP para o sistema, garantindo a evolução contínua da malha.
6. **Visualização Realtime**: O Watchdog transmite os eventos via SSE para o Dashboard local, enquanto o Datasette (WAL Mode) permite exploração SQL sem travar o pipeline.
