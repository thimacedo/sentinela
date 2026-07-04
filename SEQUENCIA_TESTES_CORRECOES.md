# SEQUENCIA DE TESTES E CORRECOES — SENTINELA v100+
## Protocolo para garantir 100% de integridade do codigo

**Versao:** 1.0
**Data:** 2026-07-03
**Estado base:** v100.0 (SRE completo operacional)

---

## FLUXO DE VALIDACAO

```
PASSO 1: Testes Estaticos (Sintaxe + Patches)
         |
         v
PASSO 2: Testes de Dependencias (Bibliotecas)
         |
         v
PASSO 3: Testes de Conectividade (Supabase)
         |
         v
PASSO 4: Testes de Integracao (Workers + SRE)
         |
         v
PASSO 5: Correcoes Automaticas
         |
         v
PASSO 6: Re-teste (confirmar 100%)
         |
         v
PASSO 7: Deploy em Producao
```

---

## PASSO 1: TESTES ESTATICOS

### 1.1 Verificar sintaxe de todos os arquivos criticos

```powershell
cd C:\Projetos\sentinela
python sentinela_test_suite.py --test-scraper
python sentinela_test_suite.py --test-queue
python sentinela_test_suite.py --test-agent
python sentinela_test_suite.py --test-sre
```

**Esperado:** Todos os testes de sintaxe PASSAM

### 1.2 Verificar patches aplicados

| Patch | Arquivo | Como verificar |
|-------|---------|---------------|
| ExtractionFailure | `core/instagram_scraper_v2.py` | `grep -n 'raise ExtractionFailure'` |
| success=True | `core/instagram_scraper_v2.py` | `grep -n 'success'` |
| Stats reset | `core/instagram_scraper_v2.py` | `grep -n 'self.stats ='` |
| release_atomic | `core/queue_manager.py` | `grep -n 'release_atomic'` |
| _ensure_queue_populated | `core/queue_manager.py` | `grep -n '_ensure_queue_populated'` |
| IDLE state | `sentinela_autonomous_agent.py` | `grep -n 'IDLE'` |
| save_status | `sentinela_autonomous_agent.py` | `grep -n 'save_status'` |
| SRE workers | `workers/sre/` | `ls workers/sre/*.py` |

---

## PASSO 2: TESTES DE DEPENDENCIAS

```powershell
python sentinela_test_suite.py --test-deps
```

**Esperado:**
- requests: OK
- playwright: OK
- supabase: OK
- pystray: OK (opcional)
- pillow: OK (opcional)

---

## PASSO 3: TESTES DE CONECTIVIDADE

```powershell
python sentinela_test_suite.py --test-deps
```

**Esperado:**
- SUPABASE_URL e SUPABASE_KEY encontrados no .env
- Conexao REST com Supabase retorna status 200
- Tabela fila_coleta acessivel

---

## PASSO 4: TESTES DE INTEGRACAO

### 4.1 Testar worker de SRE: Health Check

```powershell
python workers/sre/cj_sre_health_check.py
```

**Esperado:**
- Verifica locks orfaos
- Libera itens presos > 30min
- Reporta status no console

### 4.2 Testar worker de SRE: Backup Sync

```powershell
python workers/sre/cj_sre_backup_sync.py
```

**Esperado:**
- Le SQLite local
- Envia para Supabase via bulk upsert
- Limpa cache SQLite apos sync

### 4.3 Testar agente autonomo (dry-run)

```powershell
python sentinela_autonomous_agent.py --dry-run --max-cycles 3
```

**Esperado:**
- Inicializa sem erros
- Processa 3 ciclos
- Gera agent.status.json
- Icone da tray aparece (se pystray instalado)

---

## PASSO 5: CORRECOES AUTOMATICAS

Se algum teste falhou, aplicar correcoes:

```powershell
python sentinela_correcao.py --all
```

**O que corrige:**
- Import faltante de ExtractionFailure no scraper
- Campo success=True no retorno do scraper
- Reset de self.stats no scraper
- Metodo save_status no agente

**Backups:** Todos os arquivos modificados sao backupados em `backups/correcoes/`

---

## PASSO 6: RE-TESTE (CONFIRMACAO)

Apos correcoes, executar TODOS os testes novamente:

```powershell
python sentinela_test_suite.py --all
```

**Esperado:** 100% dos testes PASSAM

---

## PASSO 7: DEPLOY EM PRODUCAO

### 7.1 Parar agente atual

```powershell
# Clique direito no icone da tray -> Parar
# Ou matar processo:
taskkill /F /IM python.exe  # CUIDADO: mata todos os python
```

### 7.2 Verificar fila antes de iniciar

```powershell
python sentinela_diagnostico_repop.py --check-all
```

**Esperado:**
- Itens PENDENTES > 0
- Locks orfaos = 0
- Candidatos ATIVOS > 0

### 7.3 Iniciar agente autonomo

```powershell
python sentinela_autonomous_agent.py --env .env
```

### 7.4 Monitorar primeiros 5 minutos

Verificar:
- Icone da tray: verde (RUNNING) ou azul (IDLE)
- Ntfy: notificacao de inicio recebida
- Logs: `logs/main_runner.json` sem erros
- agent.status.json: atualizado a cada ciclo
- Fila: itens sendo processados (status mudando de PENDENTE para CONCLUIDO)

---

## CHECKLIST FINAL

- [ ] Todos os testes estaticos PASSAM
- [ ] Todas as dependencias instaladas
- [ ] Conexao com Supabase OK
- [ ] SRE workers funcionam (health check + backup sync)
- [ ] Agente inicia sem erros
- [ ] Icone da tray aparece
- [ ] Ntfy envia notificacoes
- [ ] Fila sendo processada
- [ ] agent.status.json gerado
- [ ] Nenhum lock orfao na fila
- [ ] Backup do SQLite funciona

---

*Documento gerado em 2026-07-03 para o projeto Sentinela v100+*