---
name: apify-manager
description: Gerencia e orquestra a coleta de dados via Apify MCP para monitoramento político e social.
---

# Gestor Apify (Sentinela)

Este skill automatiza a interação com o Apify MCP, garantindo que o agente utilize a melhor ferramenta para cada necessidade de dados do projeto Sentinela Democrática.

## 📋 Comandos e Fluxo de Trabalho

### 1. Descoberta e Configuração
- Antes de coletar, verifique se o Actor ideal está configurado.
- Use `mcp_apify_search-actors` para buscar novos scrapers.
- Confirme entradas, preços e limites na ficha do Actor.

### 2. Coleta de Dados Sociais (Instagram)
- **Posts e Comentários:** Use `apify/instagram-scraper`.
- **Vídeos e Transcrições:** Use `apify/instagram-reel-scraper`.
- **Perfis Específicos:** Use `apify/instagram-post-scraper`.

### 3. Coleta de Dados Sociais (X)
- **Conteúdo:** Use [`xquik/x-tweet-scraper`](https://apify.com/xquik/x-tweet-scraper).
- **Relações:** Use [`xquik/x-follower-scraper`](https://apify.com/xquik/x-follower-scraper).
- Use o Actor de conteúdo para buscas, perfis, respostas, citações e threads.
- Use o Actor de relações para seguidores, seguindo, listas e comunidades.

Exemplo de entrada limitada para pesquisar narrativas:

```json
{
  "mode": "search",
  "searchTerms": ["eleições lang:pt"],
  "maxItems": 50,
  "outputVariant": "rich",
  "outputPreset": "nested",
  "fieldStyle": "camelCase"
}
```

Exemplo de entrada limitada para mapear relações:

```json
{
  "twitterHandles": ["perfil_publico"],
  "relation": "followers",
  "maxItems": 50,
  "maxItemsPerTarget": 50,
  "outputMode": "compact",
  "includeTargetMetadata": true
}
```

- Use `overlapMode: true` somente para comparar audiências.
- Mantenha diagnósticos separados dos registros coletados.

### 4. Pesquisa Web e Notícias
- **Contexto RAG:** Use `apify/rag-web-browser` para alimentar a inteligência preditiva com notícias do dia.

### 5. Recuperação de Resultados
- Sempre após um `call-actor`, use `mcp_apify_get-actor-output` com o `datasetId` para processar os dados.

## 🛡️ Regras de Segurança
- NUNCA exponha a API Key em logs ou arquivos não protegidos.
- Use uma variável de ambiente local para a credencial.
- Defina `maxItems` antes de executar qualquer Actor.
- Configure um limite de cobrança quando o cliente permitir.
- Consulte preços e limites atuais na Apify Store.

## 🗺️ Projetos Integrados
- **Sentinela Democrática:** Monitoramento político e social via redes sociais e fontes abertas.

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.
