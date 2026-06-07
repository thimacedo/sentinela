# 🕵️ Subagente: SaVoyant (Linguística Pericial)
**Versão:** PASA v92.5
**Diretório:** `workers/ai/sa_voyant.py`
**Interface de Dados:** `core/voyant_service.py`

---

## 1. Missão e Objetivo
O **SaVoyant** é o Subagente Especialista em Linguística do Sentinela. Sua missão é atuar como a primeira linha de defesa analítica, utilizando Processamento de Linguagem Natural (PLN) determinístico para:
1.  **Reduzir Custos Cloud**: Filtrar lotes de comentários neutros (Fast-Drop) sem acionar LLMs caros.
2.  **Perícia Léxica & Slogans**: Identificar picos de ódio e ataques coordenados via TF-IDF e extração local de **Bigramas**.
3.  **Processamento Incremental**: Analisar apenas dados novos desde o último ciclo, garantindo escala e zero redundância.
4.  **Resiliência Ativa**: Monitorar e reconectar automaticamente ao VoyantServer local.

---

## 2. Conexões e Dependências

### 2.1 Fluxo de Comunicação
*   **Orchestrator**: Registrado no `main_runner.py`, executa ciclos automáticos de análise.
*   **VoyantServer (Trombone API)**: Backend Java na porta **8888**.
*   **Supabase (DB)**: Consumo incremental da tabela `comentarios` (via `data_coleta`) e persistência em `system_events`.

---

## 3. Lógica Operacional (v92.5)

### 3.1 Tracking Incremental
O SaVoyant mantém um checkpoint em memória (`_last_processed_ts`). A cada ciclo, ele busca apenas registros com `data_coleta` superior a este marcador, evitando re-análise de dados e desperdício de tokens/CPU.

### 3.2 Extração de Bigramas
Além dos termos isolados do Voyant, o subagente extrai localmente os 10 bigramas mais frequentes. Isso permite ao LLM identificar slogans de milícias digitais (ex: "urna fraudada", "intervenção militar") com precisão cirúrgica.

---

## 4. Sistema de Recompensas
O SaVoyant é integrado ao motor de XP:
*   **Ciclo de Triagem**: +5.0 XP.
*   **Descoberta de Insight Crítico (Relevância > 0.6)**: +15.0 XP.
    *   *Mecânica:* O `xp_delta` é injetado no metadata para processamento pelo `RewardEngine`.

---
_Documentação Técnica PASA v92.5 — SaVoyant Agent_
