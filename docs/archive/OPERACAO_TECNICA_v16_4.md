# Procedimento Operacional Padrão (POP) - Sentinela v16.4
**Título:** Fluxo de Inteligência Híbrida e Persistência de Evidências
**Versão:** 16.4.0 (Hybrid & Forensic)

## 1. Ciclo de Vida do Dado (Pipeline)

### Etapa 1: Extração e Coleta (Scraping)
- **Worker:** elite_collector.py
- **Mecanismo:** Utiliza Sessão do Instagram (SessionID) + Browserbase para contornar bloqueios.
- **Entrada:** Lista de alvos (Candidatos) sincronizada via Supabase.
- **Saída:** Inserção no SQLite local (data/odio_politica.db) com processado_ia = 0.

### Etapa 2: Classificação Híbrida (Intelligence)
- **Worker:** ollama_intelligence.py
- **Camada 1 (Triagem - Qwen 3B):** Classificação rápida e descarte de neutros.
- **Camada 2 (Peritagem - Gemma 9B):** Análise de falácias e performatividade para casos de is_hate=true.
- **Persistência Local:** Atualização das colunas is_hate, categoria_ia e nalise_pericial no SQLite.

### Etapa 3: Injeção na Nuvem (Sync)
- **Worker:** cloud_injector.py
- **Mecanismo:** Sincronização delta (apenas novos vereditos) para o Supabase.
- **Segurança:** Uso de Service Role Key e Headers de API restritos.

## 2. Persistência Técnica

| Nível | Tecnologia | Função |
| :--- | :--- | :--- |
| **Local (Hot)** | SQLite 3 | Cache de processamento e backlog de IA. |
| **Cloud (Cold/Analytic)** | Supabase (Postgres) | Fonte da verdade para o Dashboard e App Mobile. |
| **Arquivos (Evidence)** | JSON / PDF | Relatórios periciais brutos e logs de raspagem. |

## 3. Implementação no Banco de Dados (Schema)
As principais tabelas envolvidas no fluxo são:
- comentarios: Registro de todas as postagens e vereditos.
- candidatos: Alvos monitorados e seus respectivos acumuladores (KPIs).
- logs_processamento: Trilha de auditoria das IAs.

---
