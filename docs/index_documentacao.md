# MANIFESTO E ÍNDICE DE DOCUMENTAÇÃO - SENTINELA
_Guia de Onboarding para Design e Engenharia (v84.0)_

Bem-vindo(a) ao projeto Sentinela Democrática. Este documento serve como índice para a documentação técnica central do sistema, orientando novos designers e desenvolvedores na compreensão da arquitetura, regras de negócio e estado atual do projeto.

---

## 📚 1. Core Operacional (A Fonte de Verdade)

Estes são os documentos dinâmicos que ditam o rumo do projeto e refletem a realidade do código em produção. Devem ser consultados antes de iniciar qualquer nova interface ou feature.

*   **[`STATE.md`](../STATE.md)**: O coração do projeto. Contém o status operacional em tempo real de cada subsistema (Frontend, Orquestrador, IA, Fila), a arquitetura técnica atualizada e o histórico das "Descobertas Técnicas" das últimas sessões de engenharia.
*   **[`ROADMAP.md`](../ROADMAP.md)**: O mapa do tesouro. Lista tudo o que foi concluído (Fases 1 a 6) e o planejamento estratégico para as próximas iterações (Fase 7 e além).
*   **[`GEMINI.md`](../GEMINI.md)**: O Protocolo de Engenharia. Define as regras estritas de desenvolvimento, limites de atuação autônoma da IA e diretrizes jurídicas/forenses da plataforma.

---

## 🏗️ 2. Especificações Técnicas (Integração e UI)

Estes documentos foram criados especificamente para auxiliar a equipe de Frontend e Design na construção do "War Room".

*   **[`docs/ARCHITECTURE_PASA_V84.md`](ARCHITECTURE_PASA_V84.md)**: A Visão Geral e a camada God Mode. Descreve a interação entre os sistemas (Next.js Frontend Premium e Orquestrador/Workers Backend).
*   **[`docs/database_schema_v58.md`](database_schema_v58.md)**: O mapa de dados. Contém o modelo relacional (Mermaid), tabelas, colunas (com tipos) e os relacionamentos do banco PostgreSQL/Supabase. Essencial para planejar endpoints e consumo de estado.
*   **[`docs/project_functions_v58.md`](project_functions_v58.md)**: O mapeamento lógico. Explica como os motores "pensam". Detalha o funcionamento do Orquestrador, Motor de Coleta V2 (Playwright), Serviço de IA (MCA v2.2) e do Supervisor de Saúde (Watchdog).

---

## 📋 3. Referenciais Analíticos e Metodologia

Arquivos que definem como o Sentinela classifica e entende o ambiente político. Úteis para pensar na UX de exibição de dados e alertas.

*   **`MCA v2.2 (Metodologia de Classificação)`**: Incorporada ao `project_functions_v58.md` e ao `ai_service.py`. Define como o sistema classifica ódio, ironia e comportamento de robôs (Campanhas Coordenadas). A interface deve estar preparada para exibir categorias como:
    *   *Insulto Ad Hominem*
    *   *Campanha Coordenada (Bots)*
    *   *Ataque Institucional*
    *   *Milícia Digital*

---

## 🎨 4. Diretrizes de Design ("War Room")

Para a construção de interfaces, o sistema adotou a estética de um **Centro de Comando Moderno**.
*   **Paleta Principal**: Slate (Ardósia) para fundos (`#0f172a`) e Emerald (Esmeralda) para destaques operacionais (`#10b981`).
*   **Conceito**: Eliminação de poluição visual. Informação densa, porém clara. Uso de tipografia Monoespacada para dados técnicos.
*   **Modularidade**: Telas divididas por foco de ação (Panorama, Perícia, Alvos, Alertas). Módulos sem dados devem exibir estados de "Calibração/Manutenção" (com efeito de desfoque) em vez de páginas vazias ou erros.

---
_Aviso: A arquitetura está em constante evolução. Consulte o `STATE.md` para as últimas atualizações de status._
