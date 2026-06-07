# SaMineracaoRedes — Análise de Redes Coordenadas
_version: 90.8 | last_updated: 2026-06-07 | status: Ativo (Sob Demanda)_

## 1. Visão Geral

**SaMineracaoRedes** é o subagente especializado em mineração de grafos e detecção de ataques coordenados. Ele analisa a similaridade entre comentários, a frequência de ataques a múltiplos alvos e a conexão entre perfis suspeitos para identificar comunidades de hostilidade (Astroturfing/Bot Rings).

### Informações Básicas
- **ID do Subagente**: `sa-mineracao-redes`
- **Localização**: `workers/analytics/sa_mineracao_redes.py`
- **Classe**: `SaMineracaoRedes` (herda de `BaseSubAgent`)
- **Engine**: NetworkX + Pandas
- **Trigger**: Disparado reativamente pelo `WkClassificaComentarios` via EventBus, ou sob demanda
- **Status**: 🟢 Ativo sob demanda

---

## 2. Responsabilidades

### 1. Detecção de Clusters
- Identifica contas que atacam múltiplos candidatos monitorados simultaneamente
- Cria grafos de interações entre autores e alvos
- Detecta componentes conectados (comunidades) que operam de forma síncrona ou coordenada

### 2. Cálculo de Score de Perigo
- Atribui um score de 0 a 100 para cada cluster detectado
- Baseado no tamanho da rede, volume de interações e densidade de conexões coordenadas

### 3. Exportação de Relatórios
- Persiste os dados dos clusters na tabela `redes_coordenadas` do Supabase
- Gera arquivos físicos (`.json` e `.md`) em `frontend/public/reports/` para consumo do dashboard

---

## 3. Algoritmo de Análise

1. **Ingestão**: Recupera comentários classificados como ódio (`is_hate=True`) dos últimos 7 dias
2. **Filtragem de Atacantes**: Identifica `multi_attackers` (usuários que atacaram > 1 candidato)
3. **Construção do Grafo**: Nodos = Autores + Candidatos; Arestas = ações hostis
4. **Detecção de Comunidades**: Utiliza `nx.connected_components` para isolar grupos
5. **Classificação da Coordenação**:
   - `MULTI_TARGET`: atacantes operando em múltiplos alvos
   - `SINGLE_TARGET`: cluster focado em um único alvo com volume anormal

---

## 4. Execução

### Sob Demanda (Bandeja do Watchdog)
```bash
python scripts/run_mineracao_redes.py
```
Menu: `SUBAGENTES (SA)` → `Executar SaMineracaoRedes`

### Via Código
```python
from workers.analytics.sa_mineracao_redes import SaMineracaoRedes

sa = SaMineracaoRedes()
await sa.run_analysis()
```

---

## 5. Monitoramento

```bash
tail -f logs/main_runner.json | grep SaMineracaoRedes
```

### Dashboard Watchdog
```
Watchdog → Subagentes
├─ SaMineracaoRedes
│  ├─ Status: Idle / Running
│  ├─ Clusters: N
│  └─ Last Run: X minutes ago
```

---

## 6. Troubleshooting

### "Relatório de rede não atualiza"
1. Verificar se existem comentários marcados como `is_hate=True` nos últimos 7 dias
2. Verificar se o `WkClassificaComentarios` está rodando e concluindo ciclos
3. Verificar volume mínimo (10 comentários de ódio) para disparar a mineração

---

## 7. Changelog

### v90.8 (2026-06-07)
- [x] Corrigido path: `workers/analytics/sa_mineracao_redes.py`
- [x] Classe renomeada: `SaMineracaoRedes`
- [x] Herança `BaseSubAgent` documentada

---

**Última Revisão**: 2026-06-07
**PASA Version**: v88.1 → v90.8
