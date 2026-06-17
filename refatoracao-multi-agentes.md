# Implementação da Arquitetura Multi-Agentes (Sentinela)

## Goal
Refatorar módulos engessados, fechar lacunas de resiliência e migrar a lógica do projeto para um Sistema Multi-Agentes (MAS) unificado sob o padrão OODA.

## Tasks

### Fase 1: Dívida Técnica e Refatorações (Scraper & API)
- [ ] Refatorar `core/instagram_service.py` -> Aprofundar o parser de `xdt_` (GraphQL) para diminuir falhas na API Interna.
  - Verify: Executar scraping num post e garantir extração via API sem recorrer ao DOM.
- [ ] Otimizar Payload em `api/index.py` -> Remover o retorno pesado de `texto_bruto` na visualização agregada.
  - Verify: Chamada no endpoint de dashboard retorna JSON apenas com metadados/counts.

### Fase 2: Lacunas e Resiliência Multimodal
- [ ] Implementar Fallback Multimodal no `core/ai_service_vision_patch.py` -> Em caso de 503 no Gemini, tentar outro modelo de visão configurado.
  - Verify: Forçar erro (mock) no Gemini e checar se o sistema roteia para fallback no DOM Healing.
- [ ] Criar Documentação `docs/SESSION_MANAGEMENT.md` -> Explicar a injeção em massa de cookies/sessões sem depender do `.env`.
  - Verify: Arquivo Markdown criado e comissionado.

### Fase 3: Migração de Scripts para Agentes SRE/Cognitivos
- [ ] Migrar `watchdog_duplicate_killer.py` para o `SRE Agent` -> O `core/autopilot/sre_agent.py` absorve a checagem de PIDs e `taskkill`.
  - Verify: Rodar `main_runner` duplicado; SRE Agent detecta no log e mata um deles.
- [ ] Refatorar `core/behavior_engine.py` (Solenya) -> Trocar Spacy NLP (Bag-of-Words) por um Agente Cognitivo Baseado em Embeddings/LLM que avalia o subtexto da campanha.
  - Verify: Rodar script com 10 comentários modificados por sinônimos; Agente identifica coordenação semântica.

### Fase 4: OODA Loop Universal
- [ ] Integrar OODA no `core/intelligence_service.py` -> Separar as fases de `Observe` (Bio/IG), `Orient` (Verificar se é Alvo Político), `Decide` (Aprovar ou buscar na Web) e `Act` (Upsert).
  - Verify: Passar "Juliano (Engenheiro)" -> Rejeita rápido. Passar "Flávio Dino" -> Enriquece e Aceita.
- [ ] Refatorar `workers/ai/sa_fast_drop.py` para OODA -> Transformar validação de lista estática num agente reativo que dropa conteúdo irrelevante sem onerar fila.
  - Verify: Teste unitário passando comentários curtos/inúteis; sa_fast_drop elimina da fila.

## Done When
- [ ] Todos os itens marcados.
- [ ] Nenhuma quebra no `main_runner.py` ao rodar.
- [ ] OODA integrado transversalmente na camada de avaliação de comentários e perfis.
