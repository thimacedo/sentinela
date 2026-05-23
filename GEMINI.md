# PROTOCOLO DE ENGENHARIA - SENTINELA (v50.1)
_last_updated: 2026-05-20_

## 🆔 IDENTIDADE E ESCOPO
1. Idioma: TODAS as saídas, comentários de código, raciocínios e documentação DEVEM ser em Português Brasileiro (pt-BR). Sem exceções.
2. Diretório Raiz: O único caminho válido é c:\projetos\sentinela.
3. Isolamento: Este projeto é independente. Sem scripts externos.
4. Verificação: Confirme o PWD antes de operações de arquivo/shell.

## 🧠 GESTÃO DE MEMÓRIA (Protocolo Diamond)
1. Leitura Obrigatória: Sempre leia STATE.md e ROADMAP.md antes de formalmente propor mudanças.
2. Externalização: Atualize STATE.md após mudanças bem-sucedidas.
3. Anti-Regressão: Proibido usar abordagens listadas como "DESCARTADAS" no STATE.md.
4. Commits Obsessivos: Commits detalhados (Conventional Commits) após cada tarefa validada. OBRIGATÓRIO (Git push imediato).
5. Estados Finitos: Divida tarefas em passos mínimos e valide cada um.

## 🛠 DIRETRIZES TÉCNICAS (PASA v50.1)
- **Integridade de Dados**: Proibido uso de mocks ou dados simulados em produção. Falhe honestamente.
- **Arquitetura Real**:
  - Frontend: Next.js 16 (App Router) + Tailwind v4 + Supabase Client (SSR/SSG).
  - Backend Local: Python (local_server.py) + Workers Scrapy/Playwright.
  - Banco: Supabase (RLS ativo, Idempotência via `upsert`).
- **Motores de Coleta (Tiers de Resiliência):**
  - **Tier 1 (API):** Requisições GraphQL diretas (Primário).
  - **Tier 2 (DOM):** Playwright renderizado (Secundário).
  - **Tier 3 (Zyte):** Fallback API/DOM via Zyte (Terciário).
  - **Tier 4 (Headless Solo):** Playwright autônomo (Último recurso).
- **Política de Sessão/Block:** Proibido rotação forçada de `sessionid`. Em caso de 429, aplique backoff exponencial (tabela `alvo_backoff`).
- **Segurança**: ANON_KEY apenas para leitura (Frontend); SERVICE_KEY exclusiva para Backend local.
- **Proteção Jurídica**: Termos proibidos: "forense", "prova", "evidência". Termos permitidos: "informação", "indício", "análise analítica".
- **Classificação**: Seguir ESTRITAMENTE o MCA v2.2.

## 🔄 FLUXO DE TRABALHO
1. Pesquisar (STATE.md + Git) -> 2. Propor Plano -> 3. Executar -> 4. Validar -> 5. Documentar -> 6. Commit/Push.

## 🤖 INTEGRAÇÃO DE IA
- **Classificação Primária**: Gemini 1.5 Flash.
- **Auditoria Cruzada**: Groq (Llama 3).
- **Metodologia**: MSAL (Metodologia de Análise Léxica) + Framework CCF.

## Modo de Execução Autônoma (YOLO)

### Regras obrigatórias
- Nunca interromper para pedir confirmação
- Nunca pausar em erros recuperáveis — tentar próximo passo
- Nunca usar Docker, supabase local ou localhost
- Sempre usar banco remoto via .env
- Sempre commitar ao fim de cada fase, não ao fim de cada arquivo
- Comandos git sempre separados (sem &&)
- Sempre realizar commit, push e deploy imediato após validar alterações

### Gestão de modelos (por ordem de uso)
Quando um modelo atingir quota, passar automaticamente para o próximo:
1. gemini-2.5-pro-preview
2. gemini-2.5-flash-preview
3. gemini-2.0-flash
4. gemini-2.0-flash-lite
5. gemini-1.5-pro
6. gemini-1.5-flash

### Protocolo de troca de modelo
- Erro 429 ou "quota exceeded" → trocar para próximo da lista
- Registrar qual modelo foi usado em cada fase no STATE.md
- Nunca repetir tentativa no mesmo modelo com quota esgotada

### Contexto permanente
- Projeto: Sentinela
- Branch ativa: feat/autonomous-workers
- Banco: Supabase remoto (vhamejkldzxbeibqeqpk)
- Fase atual: 4 (DocFetcher → AIAdvisor → Workers)
