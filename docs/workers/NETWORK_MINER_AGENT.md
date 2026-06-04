# NetworkMinerAgent - Documentação de Análise de Redes Coordenadas

**Versão:** PASA v88.1  
**Arquivo Fonte:** [network_agent.py](file:///c:/projetos/sentinela/workers/analytics/network_agent.py)  
**Status:** ✅ Operacional (Subagente reativo / sob demanda)  
**Última Atualização:** Junho 2026

---

## 🎯 Visão Geral

O **NetworkMinerAgent** é um subagente analítico especializado na mineração de **redes coordenadas** e **detecção de clusters** na plataforma Sentinela. Seu objetivo é:

- **Analisar grafos de interação** entre autores de comentários classificados como ódio e candidatos políticos alvos.
- **Identificar comunidades suspeitas** (clusters) que indicam coordenação organizada ou comportamento inautêntico.
- **Quantificar o risco** de campanhas de ataque organizadas.
- **Alimentar o frontend** com dados estruturados sobre redes de influência via tabela `redes_coordenadas` e relatórios em formato JSON/Markdown.

A análise é executada em segundo plano de forma reativa após ciclos de classificação de IA bem-sucedidos ou sob demanda via API/Dashboard.

---

## 🏗️ Fluxo de Processamento e Design

```
┌────────────────────────────────────────────────────────┐
│ 1. COLETA DE DADOS                                     │
│   • Busca comentários classificados como ódio          │
│   • Filtra registros das últimas N horas/dias          │
└────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────┐
│ 2. CONSTRUÇÃO DO GRAFO (NetworkX)                      │
│   • Cria grafo de conexões (Autor ↔ Candidato Alvo)    │
│   • Adiciona arestas pesadas pela frequência de ataque │
└────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────┐
│ 3. DETECÇÃO DE COMUNIDADES                             │
│   • Identifica componentes conexas no grafo            │
│   • Filtra interações menores (menos de 3 nós)         │
└────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────┐
│ 4. SCORING DE RISCO E RANKING                          │
│   • Score = min(100, len(nós)*5 + interações//10)      │
│   • Seleciona o principal cluster crítico              │
└────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────┐
│ 5. PERSISTÊNCIA E RELATÓRIO                            │
│   • Grava dados estruturados na tabela Supabase         │
│   • Gera arquivos network_YYYY-MM-DD em reports/       │
└────────────────────────────────────────────────────────┘
```

---

## 🧬 Métodos Principais

### `run_analysis()`
Executa todo o pipeline de detecção de clusters coordenadas.
- **Retorno**: Um dicionário com metadados do processamento (quantidade de clusters identificados, score do top cluster, etc.).

### `_generate_physical_reports(cluster_data)`
Gera arquivos em `frontend/public/reports/` nos formatos JSON e Markdown contendo detalhes analíticos do cluster mapeado.

---

## ⚙️ Configuração

O subagente aceita parâmetros em seu construtor:
- `lookback_days` (padrão: 7): Janela de dias para coleta de dados históricos.
- `min_similarity` (padrão: 0.8): Similaridade léxica (reservado para futuras atualizações de clustering de posts).
