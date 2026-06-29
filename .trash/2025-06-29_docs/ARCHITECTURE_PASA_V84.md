# Arquitetura PASA v84.11 - Sentinela

Este documento descreve a arquitetura macro atualizada da plataforma Sentinela, codinome "God Mode Data Layer + Frontend Premium".

## 1. Visão Geral (O Sistema Nervoso Central)
O Sentinela atua como um observatório de integridade discursiva em redes sociais, voltado primariamente ao cenário político brasileiro. Ele possui dois grandes pilares que operam independentemente:
1. **O Motor de Coleta e IA (Backend Python)**: Executa varreduras contínuas (24/7), analisando postagens e perfis usando uma malha de inteligência artificial dupla.
2. **O Frontend UI (Next.js)**: Uma interface SAAS de alta velocidade, responsável por exibir os dados, métricas de rede e gerar relatórios em tempo real.

---

## 2. O God Mode Data Layer (Backend)
Escrito em Python, o ecossistema backend é baseado numa arquitetura modular de "Workers", orquestrados por um `Watchdog`.

### 2.1. Workers Ativos
- **Motor Scraper V2**: Realiza a navegação headless via Playwright. Foca em coletar dados limpos contornando bloqueios de forma "stealth".
- **TargetResearchWorker**: Um agente autônomo que caça e enriquece novos perfis políticos usando a API do Gemini. Mantém o banco de dados dinâmico alimentando as filas.
- **AIAdvisor & DocFetcher**: Agentes de suporte anexados ao log de erros, capazes de realizar auto-healing (cura automática) investigando documentações quando scripts quebram.
- **RewardEngine**: Um sistema que atribui XP aos workers/proxies dependendo da qualidade do payload retornado, penalizando rotas ineficientes.

### 2.2. Classificação Semântica (Protocolo MCA v2.2)
Toda string coletada passa por duas barreiras:
1. **MSAL (Metodologia de Análise Léxica)**: Um modelo rápido local filtra sujeira e metadados.
2. **Gemini 1.5 Pro / Flash**: Atua como o cérebro final para categorizar a hostilidade do texto (Ad Hominem, Institucional, Ódio ou Neutro), retornando o escore de confiança e justificativa pericial.

---

## 3. O Frontend Premium (Next.js 16)
O painel de monitoramento do Sentinela foi movido da stack legado para o **Next.js 16 (App Router)**.

### 3.1. Stack Tecnológica
- **Framework**: Next.js 16 App Router.
- **Estilização**: TailwindCSS v4 com modo escuro/claro nativo, focado no uso de painéis *glassmorphism* (SAAS Look).
- **Gerenciamento de Estado**: React Hooks estritos e React Query para cache.
- **Banco de Dados/Auth**: Supabase Client (usando anon_key). Regras fortes de Row Level Security (RLS) protegem as tabelas.

### 3.2. Arquitetura de UI e Monetização
- **Componentização Total**: Telas divididas em tabs (`AlertsTab`, `TargetsTab`, `NetworkTab`, `DossiersTab`).
- **Google AdSense (Monetização)**: Injetado via `AdSenseSlot.tsx` em todas as rotas primárias e secundárias com suporte a placeholders visuais, impedindo colapsos estruturais da página sob uso de AdBlockers.

---

## 4. Pipeline e Testes (CI/CD)
O código segue um padrão de resiliência restrito:
- O backend não pode expor a `SERVICE_KEY` publicamente.
- O frontend é auditado via **Playwright Crawler E2E**, que navega autonomamente por todos os botões e rotas identificando `400/404` e crashes de renderização.
- Rigor estrito de TypeScript e pureza do React (impedindo funções como `Date.now()` no render).

*Assinado:* Equipe de Engenharia Autônoma do Sentinela.
