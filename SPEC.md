# SPEC: Dashboard de Telemetria Multi-Agente (MAS)

## 1. Visão Geral
Construir uma nova interface no `Decision Room` (Dashboard Administrativo do Sentinela) para monitorar em tempo real a saúde, o consumo de tokens e a eficácia do recém implementado Sistema Multi-Agentes (MAS) e do Loop OODA.

## 2. Objetivos e Funcionalidades
- **Monitoramento de OODA Loops**: Visualizar a esteira de `Observe -> Orient -> Decide -> Act` do Agente de Inteligência e do `SaFastDrop`.
- **Telemetria de Resiliência (Fallback Multimodal)**: Exibir contadores de quantas vezes o fallback do Gemini para o Claude 3.5 Sonnet foi acionado pelo `DOM Healer`.
- **Rastreamento de Zumbis (SRE Agent)**: Log em tempo real das intervenções do SRE Agent (ex: PIDs mortos via `tool_kill_duplicate_processes`).
- **Visualização Cognitiva (Behavior Engine)**: Interface em grafo ou tabela mostrando os "clusters semânticos" detectados pelo Agente Cognitivo de desinformação.

## 3. Escopo Técnico
- **Frontend**: Next.js App Router (React), Tailwind CSS, Lucide Icons, Recharts para gráficos de série temporal.
- **Backend (API)**: Novos endpoints FastAPI em `api/index.py` para extrair telemetria dos logs ou do Supabase.
- **Integração**: Conectar o frontend aos logs dos agentes via banco de dados (tabela de eventos de telemetria a ser definida).

## 4. Quality Gates (AgentFlow)
- O código TypeScript deve compilar sem erros (`tsc --noEmit`).
- O linter (`eslint`) não deve retornar _warnings_ de dependências.
- Novos arquivos devem manter coesão com a arquitetura `layout.tsx` e `globals.css` atuais.

## 5. Critérios de Aceitação
- A tela `/admin/agentes` exibe o status ao vivo dos workers.
- Gráfico de pizza ou barras exibe as economias de tokens/resoluções via filtros determinísticos VS LLM.
- O código passa na revisão adversarial de segurança/performance.
