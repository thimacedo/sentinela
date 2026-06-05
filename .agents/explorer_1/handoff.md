# Relatório de Handoff — Investigação do Watchdog (Explorer 1)

**Data**: 2026-06-05  
**Autor**: Explorer 1 (Codebase Researcher)  
**Status**: Concluído (Fase 4: Análise e Pesquisa de Código)  

---

## 1. Observação

Durante a investigação detalhada do código-fonte do Watchdog, foram analisados os seguintes arquivos e comportamentos:

### A. Estrutura de Threads e Controle do `guard`
- **Arquivo**: `c:\Projetos\sentinela\watchdog\__init__.py`
- **Linhas 562–565**: A função `guard()` executa verificações de inicialização fora do bloco de tratamento de exceções da thread:
  ```python
  def guard():
      # Garantir que serviços de IA estejam operacionais antes de iniciar o ciclo
      from core.health_check import run_startup_health_checks
      run_startup_health_checks()
      python_exe = get_python_executable()
      consecutive_code_errors = 0
  ```
- **Linhas 705–706**: O bloco `try-except` principal da thread `guard` captura exceções durante a execução do loop, mas falhas anteriores a esse bloco farão com que a thread aborte sem notificação ou reinício:
  ```python
  except Exception as e:
      state.add_log("error", f"[Watchdog] Exceção no guardião: {e}")
  ```

### B. Fluxo de Hibernação Interrompível
- **Arquivo**: `c:\Projetos\sentinela\watchdog\__init__.py`
- **Linhas 681–694**: O loop de hibernação por falhas rápidas consecutivas (`fast_crashes >= 3`) é estruturado da seguinte forma:
  ```python
  if state.fast_crashes >= 3:
      state.add_log("error", "[Watchdog] 3 falhas rapidas consecutivas. Hibernando por 1h.")
      send_whatsapp_alert("WATCHDOG: INIT LOOP - Servidor falhou ao iniciar 3x. Hibernando 1h.", category="runtime")
      state.update_metrics(status="HIBERNANDO - INIT LOOP")
      
      # Espera defensiva interrompível (1 hora / 3600 segundos)
      hibernate_seconds = 3600
      check_interval = 5
      elapsed = 0
      while elapsed < hibernate_seconds and state.should_run:
          time.sleep(check_interval)
          elapsed += check_interval
          
      state.fast_crashes = 0
  ```
- No entanto, a variável `state.should_run` permanece como `True` durante a ocorrência das falhas e ao entrar no bloco de hibernação.
- As rotas da API em `__init__.py` para iniciar/reiniciar o servidor (ex: `/api/server/start` e `/api/server/restart`, linhas 410–438) definem `state.should_run = True` (o qual já é `True`). Logo, clicar nesses botões no Dashboard não altera o estado do loop de hibernação, tornando-o ininterrupto por ações da interface gráfica.

### C. Chamadas de IA no Loop do Guard
- Nenhuma chamada síncrona ou assíncrona para serviços de classificação de IA (tais como `ai_service.classify_text` ou `ai_service.chat_completion`) foi identificada no loop de monitoramento da thread `guard` de `watchdog/__init__.py`. As chamadas de IA estão localizadas apenas em scripts secundários e workers processados em subprocessos separados (como `main_runner.py` e scripts executados pelos subprocessos do menu da bandeja).

### D. Bloqueio da Sincronização SQLite/Datasette
- **Arquivo**: `c:\Projetos\sentinela\watchdog\__init__.py` (Linhas 712–724)
- A sincronização de dados ocorre de maneira síncrona diretamente na thread principal do `guard`:
  ```python
  # Executa sincronização com o Datasette local durante o cooldown (repouso)
  if state.fast_crashes == 0 and consecutive_code_errors == 0:
      try:
          state.add_log("info", "[Watchdog] Sincronizando dados para o Datasette local...")
          from scripts.export_to_sqlite import export_to_sqlite
          export_to_sqlite()
          state.add_log("info", "[Watchdog] Sincronização Datasette concluída com sucesso durante o descanso.")
      except Exception as e:
  ```
- **Arquivo**: `c:\Projetos\sentinela\scripts\export_to_sqlite.py` (Linhas 40–47)
- A função `export_to_sqlite()` realiza requisições de rede HTTP síncronas bloqueantes ao Supabase para extrair dados:
  ```python
  cands_resp = supabase.table("candidatos").select("*").execute()
  ...
  coms_resp = supabase.table("comentarios").select("*").order("data_coleta", desc=True).limit(5000).execute()
  ```
- Se a API do Supabase demorar a responder, a thread do `guard` permanece bloqueada durante todo o timeout da requisição, atrasando o reinício do processo monitorado ou inviabilizando reações rápidas de parada/reinício comandadas pela interface.

### E. Execução dos Testes (`pytest`)
- A execução da suíte de testes foi realizada usando o comando `pytest` no diretório raiz do projeto.
- **Resultado da execução do comando**:
  - Total de testes rodados: 12 testes.
  - Resultados: **12 passaram (100% de sucesso)**, com 15 avisos (warnings) normais de depreciação de bibliotecas (como Supabase Client `timeout`/`verify` e `utcnow` no Python 3.12).
  - Tempo total: 449.92s (aproximadamente 7 minutos e 29 segundos).
  - Testes executados:
    1. `tests/test_queue_manager.py::RotateTargetTest::test_high_frequency_quente` -> **PASSED**
    2. `tests/test_queue_manager.py::RotateTargetTest::test_no_comments_error_from_quente_results_in_morno` -> **PASSED**
    3. `tests/test_queue_manager.py::RotateTargetTest::test_no_comments_error_results_in_frio` -> **PASSED**
    4. `tests/test_queue_manager.py::RotateTargetTest::test_no_posts_no_dates_results_in_morno` -> **PASSED**
    5. `tests/test_queue_manager.py::RotateTargetTest::test_post_older_than_7_days_frio` -> **PASSED**
    6. `tests/test_queue_manager.py::RotateTargetTest::test_recent_post_less_than_7_days_morno` -> **PASSED**
    7. `scripts/test_advisor.py::test_advisor` -> **PASSED**
    8. `scripts/test_ai_calibration.py::test_ai_sensitivity` -> **PASSED**
    9. `scripts/test_ai_service.py::test_ai_routing` -> **PASSED**
    10. `scripts/test_fallbacks.py::test_fallbacks` -> **PASSED**
    11. `scripts/test_scraper_integrity.py::test_integrity` -> **PASSED**
    12. `scripts/test_scraper_v2.py::test_scraper_v2` -> **PASSED**

---

## 2. Cadeia de Raciocínio (Logic Chain)

1. **Vulnerabilidade de Morte da Thread `guard`**:
   - Como `run_startup_health_checks()` e `get_python_executable()` estão situadas fora da estrutura `while True:` com tratamento geral de exceções em `guard()`, qualquer erro nestes métodos causará a quebra imediata da thread `guard` em sua fase de inicialização (boot phase).
   - *Solução Proposta*: Mover a inicialização crítica para dentro do tratamento geral de exceção ou envolver a chamada inicial do `guard` em uma blindagem extra contra falhas (um bloco `try/except` robusto na thread inicial).

2. **Fluxo de Hibernação Ininterrupto**:
   - O loop de hibernação dorme enquanto `state.should_run` for verdadeiro (`True`). 
   - Ao iniciar o loop de hibernação, `state.should_run` já é `True` (pois o processo estava rodando).
   - O Dashboard e o Tray menu definem `should_run = True` ao tentar iniciar ou reiniciar.
   - Logo, redefinir `should_run = True` não altera a lógica do loop e não o interrompe.
   - *Solução Proposta*:
     - Definir `state.should_run = False` (ou utilizar `state.update_metrics(should_run=False)`) no momento em que entra na hibernação.
     - Ajustar a condição do loop de hibernação para:
       `while elapsed < hibernate_seconds and not state.should_run:`
     - Desta forma, quando o usuário sinaliza pelo Dashboard ou Menu para Iniciar/Reiniciar, `state.should_run` passa a ser `True`, quebrando instantaneamente o `while not state.should_run` e redefinindo `fast_crashes` para 0.

3. **Inexistência de IA no Guard**:
   - Varredura de strings e imports do loop principal do `guard()` confirma que nenhum endpoint de IA é consumido nessa thread. Logo, não há risco de bloqueio da thread `guard` devido a falhas na classificação de IA ou latência do modelo local/cloud.

4. **Bloqueio por Sincronização SQLite/Datasette**:
   - A chamada `export_to_sqlite()` é síncrona. Ela é chamada diretamente no contexto sequencial da thread `guard`.
   - Essa função efetua requisições web para buscar dados do Supabase. A latência de rede ou timeouts dessas conexões impedem a execução de passos sequenciais no `guard`.
   - *Solução Proposta*:
     - Executar a sincronização em uma thread separada em background:
       ```python
       from threading import Thread
       Thread(target=export_to_sqlite, daemon=True).start()
       ```
     - Isso desacopla totalmente a rede e o I/O de disco da execução do guardião.

---

## 3. Ressalvas (Caveats)

- A análise considerou o ambiente rodando no Windows. O comportamento de alguns subprocessos pode variar sob sistemas baseados em Linux/macOS, embora a maior parte do código use checagens multiplataforma (`os.name == 'nt'`).
- A suíte de testes do Playwright (`test_scraper_v2`) depende da integridade da conectividade de rede local e do carregamento do cookie de sessão correto. Em ambientes de CI, esse teste pode necessitar de mocks.

---

## 4. Conclusão

O Watchdog do Sentinela possui um bom grau de resiliência a falhas internas do runner monitorado, mas apresenta dois gargalos críticos na thread controladora `guard`:
1. **Bloqueio por I/O e Rede**: A sincronização de dados do Supabase para SQLite local é executada de forma bloqueante na thread principal de monitoramento, o que pode atrasar ações e ciclos do guardião.
2. **Hibernação Ininterrupta**: A lógica de hibernação de 1h em caso de loop de falhas rápidas não pode ser interrompida pelas ações de controle do Dashboard ou Menu por inconsistência lógica na verificação de `state.should_run`.

### Proposta de Correção (Diff Patch Sketch)

#### Proposta 1: Tornar a Hibernação Interrompível
*Local*: `watchdog/__init__.py`, linhas 681–694

*Antes:*
```python
                    if state.fast_crashes >= 3:
                        state.add_log("error", "[Watchdog] 3 falhas rapidas consecutivas. Hibernando por 1h.")
                        send_whatsapp_alert("WATCHDOG: INIT LOOP - Servidor falhou ao iniciar 3x. Hibernando 1h.", category="runtime")
                        state.update_metrics(status="HIBERNANDO - INIT LOOP")
                        
                        # Espera defensiva interrompível (1 hora / 3600 segundos)
                        hibernate_seconds = 3600
                        check_interval = 5
                        elapsed = 0
                        while elapsed < hibernate_seconds and state.should_run:
                            time.sleep(check_interval)
                            elapsed += check_interval
                            
                        state.fast_crashes = 0
```

*Depois:*
```python
                    if state.fast_crashes >= 3:
                        state.add_log("error", "[Watchdog] 3 falhas rapidas consecutivas. Hibernando por 1h.")
                        send_whatsapp_alert("WATCHDOG: INIT LOOP - Servidor falhou ao iniciar 3x. Hibernando 1h.", category="runtime")
                        state.update_metrics(status="HIBERNANDO - INIT LOOP", should_run=False)
                        
                        # Espera defensiva interrompível (1 hora / 3600 segundos)
                        hibernate_seconds = 3600
                        check_interval = 5
                        elapsed = 0
                        while elapsed < hibernate_seconds and not state.should_run:
                            time.sleep(check_interval)
                            elapsed += check_interval
                            
                        state.fast_crashes = 0
```

#### Proposta 2: Sincronização Assíncrona Não-Bloqueante
*Local*: `watchdog/__init__.py`, linhas 712–724

*Antes:*
```python
        # Executa sincronização com o Datasette local durante o cooldown (repouso)
        if state.fast_crashes == 0 and consecutive_code_errors == 0:
            try:
                state.add_log("info", "[Watchdog] Sincronizando dados para o Datasette local...")
                from scripts.export_to_sqlite import export_to_sqlite
                export_to_sqlite()
                state.add_log("info", "[Watchdog] Sincronização Datasette concluída com sucesso durante o descanso.")
            except Exception as e:
                err_msg = str(e).lower()
                if any(t in err_msg for t in ["10060", "timed out", "timeout", "connection", "componente conectado não respondeu"]):
                    state.add_log("warn", "[Watchdog] Sincronização Datasette ignorada: Banco de dados/Rede offline.")
                else:
                    state.add_log("warn", f"[Watchdog] Falha ao sincronizar Datasette no cooldown: {e}")
```

*Depois:*
```python
        # Executa sincronização com o Datasette local durante o cooldown (repouso) de forma assíncrona (não-bloqueante)
        if state.fast_crashes == 0 and consecutive_code_errors == 0:
            def run_sync():
                try:
                    state.add_log("info", "[Watchdog] Sincronizando dados para o Datasette local (background)...")
                    from scripts.export_to_sqlite import export_to_sqlite
                    export_to_sqlite()
                    state.add_log("info", "[Watchdog] Sincronização Datasette concluída com sucesso.")
                except Exception as e:
                    err_msg = str(e).lower()
                    if any(t in err_msg for t in ["10060", "timed out", "timeout", "connection", "componente conectado não respondeu"]):
                        state.add_log("warn", "[Watchdog] Sincronização Datasette ignorada: Banco de dados/Rede offline.")
                    else:
                        state.add_log("warn", f"[Watchdog] Falha ao sincronizar Datasette no cooldown: {e}")
                        
            from threading import Thread
            Thread(target=run_sync, daemon=True).start()
```

---

## 5. Método de Verificação

Para verificar os comportamentos analisados e os testes:
1. **Comando de Teste do Projeto**:
   - Executar `pytest` no diretório raiz do projeto.
   - Confirmar o status passando os 12 testes coletados de `tests`, `scripts` e `tools`.
2. **Simulação de Travamento na Hibernação**:
   - É possível inspecionar o arquivo `watchdog/__init__.py` nas linhas indicadas para constatar a inconsistência do loop em relação à atualização da variável `state.should_run`.
3. **Checagem de Importação e Bloqueio**:
   - Inspecionar `scripts/export_to_sqlite.py` e verificar que todas as chamadas de rede e SQL são feitas de forma totalmente sequencial/bloqueante na mesma thread que o importa.
