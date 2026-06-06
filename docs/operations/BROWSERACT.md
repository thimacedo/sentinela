# Integrações: BrowserAct

- Protocolo: CDP (Chrome DevTools Protocol)
- Endpoint WebSocket: `wss://api.browseract.com/connect?apiKey=<KEY>`
- Autenticação: Via Query String (Parâmetro `apiKey`) - Necessário para evitar erro 401.
- Documentação MCP: https://docs.browseract.com/workflow/learn/integrations/mcp
- Objetivo: Evasão Antibot, Stealth Mode, Bypass de 429 e Login Walls no Instagram Scraper V2.
- Status da Chave: Armazenada com segurança no `.env` sob `BROWSERACT_API_KEY`.
