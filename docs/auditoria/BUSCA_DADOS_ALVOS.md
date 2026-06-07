# 🛡️ Auditoria de Dados: Busca e Integridade (PASA v92.8)

Este documento descreve os protocolos de auditoria, busca de dados e integridade pericial utilizados pelos subagentes do ecossistema Sentinela.

---

## 1. Subagente de Dados: SaConsultaBanco
O `SaConsultaBanco` é a interface primária para consultas analíticas no banco de dados local (Datasette/SQLite).

### 1.1 Protocolo de Busca (FTS5)
As buscas textuais utilizam o motor FTS5 para alta performance.
- **Sanitização**: Todos os termos de busca são sanitizados contra SQL Injection (escape de aspas simples e duplas).
- **Escopo**: A busca é realizada na tabela `comentarios_fts` e cruzada com a tabela original de comentários.

### 1.2 Integridade de Conexão
O subagente gerencia o ciclo de vida do cliente HTTP (`httpx.AsyncClient`) via context manager assíncrono (`__aenter__`/`__aexit__`), garantindo que não existam conexões órfãs ou vazamentos de recursos.

---

## 2. Auditoria Cruzada: SaAuditaClassificacoes
Responsável por validar a calibragem da malha de IA de produção.

### 2.1 Taxonomia MCA v2.2
A auditoria foi migrada para operar exclusivamente na taxonomia moderna:
- **Categorias Críticas**: `ODIO_IDENTITARIO`, `VIOLENCIA_GENERO`, `AMEACA`.
- **Comparação**: O auditor compara a `categoria_ia` atribuída pelo modelo de produção contra o veredito de um modelo de auditoria de alta escala (ex: Llama 3 70B via Groq).

### 2.2 Detecção de Drift
- **Threshold de Confiança**: Apenas amostras com `confianca_ia >= 0.85` são auditadas.
- **Alerta de Desvio**: Se a divergência superar 20%, o subagente gera uma sugestão de prioridade `HIGH` na tabela `worker_suggestions`.

---

## 3. Inteligência Linguística: SaVoyant
O SaVoyant atua como a primeira linha de defesa léxica.

### 3.1 Processamento Incremental
Utiliza checkpoints persistentes salvos na tabela `system_events` (`event_type: voyant_checkpoint`). Isso garante que o sistema não processe dados em duplicidade e sobreviva a reinícios sem perder o progresso.

### 3.2 Extração de Slogans (N-gramas)
Implementa extração local de bigramas utilizando uma lista centralizada de `STOP_WORDS_PT`, permitindo identificar padrões de slogans coordenados antes da análise semântica por LLM.

---

## 4. Governança e Autocura: WkAplicaSugestoes
Consome as recomendações geradas pelo `AIAdvisor` e aplica ajustes operacionais.
- **IPC (Inter-Process Communication)**: Migrado de variáveis de ambiente para `MemoryStore` (Redis/Shared Memory pattern).
- **Transparência**: Toda ação automática é registrada no campo `suggestion` com o prefixo `[AUTO_APPLIED]`, preservando o histórico original da recomendação da IA.

---
_Documentação de Engenharia — Protocolo de Auditoria v92.8_
