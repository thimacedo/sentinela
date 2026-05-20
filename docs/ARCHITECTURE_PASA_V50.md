# Histórico de Arquitetura e Decisões (PASA v50.1)

Esta documentação persiste a estrutura final alcançada após a conclusão do Epic 19d172be.

## 1. Arquitetura do Proxy (Hardened Proxy)
O sistema foi migrado para um modelo "Hardened Edge Proxy" para eliminar injeções de SQL via frontend e proteger credenciais (Anthropic API Key).

- **Backend (`mcp-proxy`):** Roteamento determinístico por `action`. O frontend envia apenas `{ projectId, action }` e o backend mapeia para SQL estático pré-definido.
- **Frontend (`Dashboard.jsx`):** Refatorado para usar `callProxy`, eliminando qualquer envio de SQL bruto ou exposição de chaves de API.

## 2. Medidas de Segurança
- **Hardening:** SQL arbitrário bloqueado por validação no backend.
- **Segredo:** API Keys movidas estritamente para o ambiente de servidor (Supabase Edge Secrets).
- **Performance:** Chamadas de dados paralelizadas via `Promise.all` para otimização da interface.

## 3. Guia de Manutenção
- **Adicionar Consultas:** Atualize a constante `ROUTES` em `supabase/functions/mcp-proxy/index.ts`.
- **Compliance:** Toda nova interface DEVE seguir o padrão de `action` para manter a integridade da arquitetura hardened.

---
*Referência: Tickets 842307d7 (Backend) e b95403c6 (Frontend).*
