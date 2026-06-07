# 🕵️ Subagente: SaVoyant (Linguística Pericial)
**Versão:** PASA v92.3.1
**Diretório:** `workers/ai/sa_voyant.py`
**Interface de Dados:** `core/voyant_service.py`

---

## 1. Missão e Objetivo
O **SaVoyant** é o Subagente Especialista em Linguística do Sentinela. Sua missão é atuar como a primeira linha de defesa analítica, utilizando Processamento de Linguagem Natural (PLN) determinístico para:
1.  **Reduzir Custos Cloud**: Filtrar lotes de comentários neutros (Fast-Drop) sem acionar LLMs caros.
2.  **Perícia Léxica**: Identificar picos de ódio, xenofobia e ataques coordenados através de estatística computacional (TF-IDF e N-gramas).
3.  **Insights Periciais**: Gerar inteligência sobre o *modus operandi* linguístico de agressores, cruzando dados reais com a **Bíblia Linguística Forense PASA**.

---

## 2. Conexões e Dependências

### 2.1 Fluxo de Comunicação
*   **Orchestrator**: O SaVoyant é registrado no `main_runner.py` e executa ciclos automáticos de análise a cada pulso do orquestrador.
*   **VoyantServer (Trombone API)**: Backend Java rodando localmente na porta **8888**.
*   **Supabase (DB)**: Persistência de insights na tabela `system_events` e consumo de dados da tabela `comentarios`.
*   **AI Service**: Acionado para transformar dados estatísticos brutos em insights periciais legíveis por humanos.

### 2.2 Requisitos de Infraestrutura
*   **Java JRE 11+**: Necessário para rodar o `VoyantServer.jar`.
*   **Porta 8888**: Deve estar liberada para tráfego local (127.0.0.1).
*   **Headless Mode**: O servidor deve ser iniciado sem interface gráfica para não travar o boot do Watchdog.

---

## 3. Lógica Operacional

### 3.1 O Algoritmo de Triage (Fast-Drop)
O SaVoyant envia lotes de comentários (geralmente 100 por ciclo) para o Voyant Tools. O sistema calcula a **proporção de agressividade léxica**:
*   **Agressividade < 8%**: O lote é considerado "RUÍDO NEUTRO". O SaVoyant marca todos no banco como `NEUTRO` e encerra o ciclo (**Zero custo cloud**).
*   **Agressividade >= 8%**: O lote contém termos do `HOSTILE_LEXICON`. O SaVoyant sinaliza que o lote requer classificação profunda via LLM.

### 3.2 Geração de Insights Periciais
Ao detectar anomalias linguísticas (ex: um pico súbito da palavra "fraude" ou "golpe"), o SaVoyant:
1.  Extrai o vocabulário TF-IDF do lote.
2.  Carrega regras da `BIBLIA_LINGUISTICA_FORENSE_PASA.md`.
3.  Solicita ao `ai_service` uma análise qualitativa baseada nos dados quantitativos do Voyant.
4.  Gera um evento de sistema (`linguistic_insight`) com severidade e categoria MCA.

---

## 4. Configurações e Variantes
Variáveis suportadas no `.env`:
*   `VOYANT_BASE_URL`: URL da API Trombone (Padrão: `http://127.0.0.1:8888/trombone`).
*   `VOYANT_HOSTILE_THRESHOLD`: Limite para fast-drop (Padrão: `0.08`).
*   `VOYANT_TIMEOUT`: Tempo limite para indexação JVM (Padrão: `8.0s`).

---

## 5. Detalhamento Técnico (Data Schema)

### 5.1 Exemplo de Insight Gerado
```json
{
  "titulo": "Suspeita de Coordenação: Ataque Institucional",
  "resumo": "Identificado N-grama recorrente 'urna fraudada' em 15% do lote atual. Padrão compatível com diretrizes de milícia digital.",
  "severidade": 90,
  "relevancia": 0.98,
  "categoria_mca": "ATAQUE_INSTITUCIONAL",
  "metadata": {
    "hostile_ratio": 0.15,
    "top_terms": ["urna", "fraudada", "roubo", "stf"]
  }
}
```

### 5.2 Sistema de Recompensas
O SaVoyant é um cidadão de primeira classe no motor de reputação:
*   **Ciclo de Triagem**: +5.0 XP.
*   **Descoberta de Insight Crítico (Relevância > 0.8)**: +15.0 XP.

---

## 6. Manutenção (SRE)
Para reiniciar o motor analítico do SaVoyant isoladamente:
```powershell
# 1. Matar processos antigos
Stop-Process -Name java -Force

# 2. Iniciar Voyant Server
java -Djava.awt.headless=true -Xmx1024m -jar tools/voyant/VoyantServer.jar headless=true
```

---
_Documentação Técnica PASA v92.3 — SaVoyant Agent_
