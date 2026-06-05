# NetworkMinerAgent — Análise de Redes Coordenadas
_version: 88.1 | last_updated: 2026-06-04 | status: Ativo (Sob Demanda)_

## 1. Visão Geral

**NetworkMinerAgent** é o subagente especializado em mineração de grafos e detecção de ataques coordenados. Ele analisa a similaridade entre comentários, a frequência de ataques a múltiplos alvos e a conexão entre perfis suspeitos para identificar comunidades de hostilidade (Astroturfing/Bot Rings).

### Informações Básicas
- **ID do Agente**: `network-miner-agent`
- **Localização**: `workers/analytics/network_agent.py`
- **Engine**: NetworkX + Pandas
- **Trigger**: Disparado reativamente pelo `AIProcessorWorker` ou manualmente sob demanda.
- **Status**: 🟢 Ativo

---

## 2. Responsabilidades

### Responsabilidade 1: Detecção de Clusters
- Identifica contas que atacam múltiplos candidatos monitorados simultaneamente.
- Cria grafos de interações entre autores e alvos.
- Detecta componentes conectados (comunidades) que operam de forma síncrona ou coordenada.

### Responsabilidade 2: Cálculo de Score de Perigo
- Atribui um score de 0 a 100 para cada cluster detectado.
- O score baseia-se no tamanho da rede, volume de interações e densidade de conexões coordenadas.

### Responsabilidade 3: Exportação de Relatórios
- Persiste os dados dos clusters na tabela `redes_coordenadas` do Supabase.
- Gera arquivos físicos (`.json` e `.md`) em `frontend/public/reports/` para consumo do dashboard de analytics.

---

## 3. Algoritmo de Análise

1. **Ingestão**: Recupera até 2000 comentários classificados como ódio (`is_hate=True`) dos últimos 7 dias.
2. **Filtragem de Atacantes**: Identifica `multi_attackers` (usuários que atacaram > 1 candidato).
3. **Construção do Grafo**:
   - Nodos: Autores e Candidatos.
   - Arestas: Representam a ação de postar um comentário hostil.
4. **Detecção de Comunidades**: Utiliza `nx.connected_components` para isolar grupos de interação.
5. **Classificação da Coordenação**:
   - `MULTI_TARGET`: Se o cluster contém atacantes que operam em múltiplos alvos.
   - `SINGLE_TARGET`: Se o cluster é focado em um único alvo mas demonstra volume anormal.

---

## 4. Persistência e Saída

### Tabela: `redes_coordenadas`
O agente armazena o cluster mais crítico de cada ciclo:
- `id`: UUID v4 derivado do hash do nome da rede.
- `nodes`: Array de strings (usernames).
- `edges`: JSONB com o mapa de conexões.
- `score_perigoso`: Valor de 0-100.

### Relatórios Físicos
Arquivos gerados em `frontend/public/reports/network_YYYY-MM-DD.md`:
```markdown
# Relatorio de Analise de Redes Coordenadas
## Nome do Cluster: Cluster de Ataque #2 (42 nodes)
- **Tipo de Coordenacao:** MULTI_TARGET
- **Score de Perigo:** 100/100
- **Contas Suspeitas Envolvidas:** 42
- **Conexoes Identificadas:** 41
```

---

## 5. Configuração e Monitoramento

### Variáveis de Ambiente
- Não requer variáveis exclusivas, utiliza a `SERVICE_KEY` do Supabase via `core/db.py`.

### Monitoramento de Logs
```bash
tail -f logs/main_runner.json | grep NetworkMinerAgent
```

---

## 6. Integração

O `NetworkMinerAgent` é disparado automaticamente pelo orquestrador quando o `AIProcessorWorker` conclui um ciclo com sucesso:

```python
# workers/orchestrator/orchestrator.py
if "ai-processor" in result.worker_id and result.classifier_success:
    asyncio.create_task(NetworkMinerAgent().run_analysis())
```

---

## 7. Troubleshooting

### Problema: "Relatório de rede não atualiza"
**Sintomas**: Arquivos em `frontend/public/reports` com data antiga.
1. Verifique se existem comentários marcados como `is_hate=True` nos últimos 7 dias.
2. Verifique se o `AIProcessorWorker` está rodando e concluindo ciclos.
3. Verifique se o volume de dados atinge o mínimo (10 comentários de ódio) para disparar a mineração.

---

**Última Revisão**: 2026-06-04
**PASA Version**: v88.1
