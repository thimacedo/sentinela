# Plano de Implementação — Estabilização do Watchdog

## R1. Estabilização do Loop do Guardião
- Envolver a inicialização de `guard()` (que chama `run_startup_health_checks` e `get_python_executable`) em um loop `while python_exe is None` com `try-except` capturando qualquer exceção, registrando no log de erro e aguardando 5 segundos antes de tentar novamente.
- Modificar o início do loop `while True` para verificar se `not state.should_run` e, se for o caso, apenas atualizar o status para `"PARADO"` se ele já não começar com `"PARADO -"`.
- Ao sair do loop de bloqueio `while not state.should_run:`, resetar `consecutive_code_errors = 0`, `state.fast_crashes = 0` e o status/métrica `code_errors` para 0.
- Na detecção de OOM fatal (`healing_action == "fatal"`), definir `state.update_metrics(status="PARADO - OOM")` antes de fazer `state.should_run = False`.

## R2. Sincronização SQLite Assíncrona
- Isolar a importação e chamada de `export_to_sqlite()` dentro de uma função aninhada `run_sync()`.
- Executar essa função em uma thread daemon separada usando `Thread(target=run_sync, daemon=True).start()`.

## R3. Hibernação Interrompível
- No bloco `if state.fast_crashes >= 3`, atualizar as métricas com `status="HIBERNANDO - INIT LOOP"` e `should_run=False`.
- Mudar a condição do loop de hibernação para `while elapsed < hibernate_seconds and not state.should_run:`.

## Verificação e Qualidade
- Executar a suíte de testes com `pytest` e garantir que todos os 12 testes passem.
- Corrigir eventuais violações de lint.
