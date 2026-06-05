## 2026-06-05T15:21:27Z

Você é o Worker 1 (teamwork_preview_worker). Seu diretório de trabalho é c:\Projetos\sentinela\.agents\worker_1.

Sua missão é implementar as melhorias de resiliência e estabilização no Watchdog do Sentinela em c:\Projetos\sentinela\watchdog\__init__.py, conforme detalhado nos requisitos R1, R2 e R3 do ORIGINAL_REQUEST.md e as descobertas contidas em c:\Projetos\sentinela\.agents\explorer_1\handoff.md.

Instruções Detalhadas de Implementação:
1. **R1. Estabilização do Loop do Guardião**:
   - Envolva a fase de inicialização da função `guard()` (que chama `run_startup_health_checks()` e `get_python_executable()`) para evitar que qualquer falha impeça a thread de iniciar. Se falhar na inicialização, registre em log de erro e tente novamente após 5 segundos, sem derrubar a thread.
   - Na checagem `if not state.should_run:` no início do loop principal, verifique se o status já é um status de erro específico (começando com "PARADO -", ex: "PARADO - ERRO CODIGO", "PARADO - OOM") para evitar sobrescrevê-lo pelo valor genérico "PARADO".
   - Quando `state.should_run` transitar de False para True (o que ocorre quando o loop de espera do estado parado encerra por intervenção do usuário), resete `consecutive_code_errors = 0`, `state.fast_crashes = 0` e a métrica `code_errors` para 0.
   - Na detecção de OOM fatal (`healing_action == "fatal"`), chame `state.update_metrics(status="PARADO - OOM")` antes de alterar `state.should_run = False`.

2. **R2. Sincronização SQLite Assíncrona**:
   - Modifique o trecho de sincronização Datasette local/Supabase (`export_to_sqlite()`) na parte final do loop do guardião para que ele execute assincronamente em uma thread daemon separada (`threading.Thread(target=..., daemon=True).start()`), evitando assim qualquer bloqueio de rede ou de disco na thread de monitoramento principal.

3. **R3. Hibernação Interrompível**:
   - Ao entrar na hibernação defensiva de 1 hora (`fast_crashes >= 3`), configure o estado como não devendo rodar (`state.should_run = False` ou usando `state.update_metrics(..., should_run=False)`).
   - Altere a condição do loop de hibernação para que ele continue dormindo apenas enquanto o tempo limite não for atingido e `state.should_run` permanecer `False`: `while elapsed < hibernate_seconds and not state.should_run:`. Isso garante que, se o usuário clicar em "Iniciar" ou "Reiniciar" no painel (definindo `state.should_run = True`), o loop seja interrompido imediatamente.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Ao final, execute a suíte de testes do projeto usando `pytest` para certificar-se de que os 12 testes continuam passando perfeitamente (100% de sucesso).
Crie o arquivo de relatório em c:\Projetos\sentinela\.agents\worker_1\handoff.md em português brasileiro contendo:
- O sumário das alterações feitas (incluindo patches/diffs).
- O logs da execução do `pytest` com o comando utilizado e a contagem de sucessos/falhas.
Responda a esta conversa contendo o link do handoff.md e um sumário.
