# Plano de Execução - Resiliência do Watchdog e Backend do Sentinela

## Milestones de Desenvolvimento

### Milestone 1: Análise e Diagnóstico (Exploração)
* **Objetivo**: Mapear as vulnerabilidades do Watchdog, a integração com IA na thread do guardião, e o fluxo atual de hibernação em `watchdog/__init__.py`, `watchdog/__main__.py` e `watchdog/reloader.py`.
* **Subagente**: `teamwork_preview_explorer` (Explorer 1)
* **Critério de Aceitação**: Relatório técnico identificando onde o loop do guardião pode morrer, onde ocorrem chamadas síncronas bloqueantes de IA ou banco, e como a hibernação de 1 hora está implementada hoje.

### Milestone 2: Estabilização do Loop do Guardião e Hibernação Interrompível (Implementação)
* **Objetivo**: Tornar a thread principal do guardião imune a crashes fatais. Implementar a transição limpa para `state.should_run = False` em caso de erros recorrentes, mantendo a thread ativa. Implementar hibernação interrompível (acorda imediatamente com `state.should_run = True`).
* **Subagente**: `teamwork_preview_worker` (Worker 1)
* **Critério de Aceitação**: A thread principal do `guard` continua ativa mesmo após simulações de crash; e a hibernação de 1 hora é acordada instantaneamente ao mudar `state.should_run = True`.

### Milestone 3: Desacoplamento de IA e Sincronização Não-Bloqueante (Implementação)
* **Objetivo**: Delegar tarefas pesadas de classificação de IA ao `main_runner.py` e garantir que a escrita/leitura do banco de dados (SQLite/Datasette) no loop do guardião não seja bloqueante.
* **Subagente**: `teamwork_preview_worker` (Worker 2)
* **Critério de Aceitação**: Zero chamadas pesadas de IA síncronas/assíncronas no loop do `guard`; sincronização com banco rodando de forma resiliente e isolada.

### Milestone 4: Validação, Revisão e Auditoria (Verificação)
* **Objetivo**: Rodar todos os testes com `pytest` (12 testes verdes), fazer revisão cruzada de código e passar pela auditoria forense de integridade.
* **Subagentes**: `teamwork_preview_reviewer` (Reviewer 1, 2), `teamwork_preview_challenger` (Challenger 1, 2), `teamwork_preview_auditor` (Auditor)
* **Critério de Aceitação**:
  - `pytest` retorna 100% verde (12/12 testes passando).
  - Sem vetos de revisão.
  - Auditoria forense limpa (CLEAN).
