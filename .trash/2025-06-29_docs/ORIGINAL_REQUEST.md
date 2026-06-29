# Original User Request

## Initial Request — 2026-06-05T12:10:54-03:00

Garantir que o backend e o Watchdog do Sentinela rodem de forma ininterrupta por horas, assegurando autocura resiliente e prevenindo travamentos de threads ou loops infinitos, mantendo a cadência lenta e constante de coletas para evitar bloqueios de cookies.

Working directory: c:/Projetos/sentinela
Integrity mode: development

## Requirements

### R1. Estabilização do Loop do Guardião (Watchdog)
O loop do guardião do Watchdog (`watchdog/__init__.py`) deve ser protegido para nunca interromper sua thread de monitoramento principal. Se houver falhas consecutivas de código ou OOM (Out Of Memory), o monitoramento deve ser pausado de forma limpa mudando `state.should_run = False` e colocando o status adequado no Dashboard, mas mantendo a thread `guard` ativa e pronta para receber o sinal de reinício manual via API ou painel.

### R2. Proteção contra Incompatibilidades de Event Loop e Deadlocks
Evitar a execução de manutenção pesada de IA (classificação/reanálise) ou quaisquer chamadas assíncronas concorrentes complexas diretamente dentro da thread de monitoramento `guard` do Watchdog, delegando processamentos pesados exclusivamente aos workers adequados de `main_runner.py` e simplificando a sincronização com SQLite/Datasette para ser resiliente e não-bloqueante.

### R3. Hibernação Responsiva e Autocura
O loop de hibernação em caso de falhas consecutivas rápidas (`fast_crashes >= 3`) deve ser implementado de forma interrompível, acordando instantaneamente se o usuário sinalizar inicialização ou reinício manual pelo Dashboard (`state.should_run` alterado para `True`).

## Acceptance Criteria

### Estabilização e Resiliência
- [ ] A thread principal do `guard` do Watchdog nunca morre por `break` no loop em caso de falhas consecutivas ou erros de código.
- [ ] O uvicorn do Dashboard permanece ativo e responsivo na porta 8001, respondendo aos comandos de Start/Stop/Restart mesmo sob crashes do runner.
- [ ] A hibernação de 1 hora do reloader pode ser interrompida imediatamente ao clicar em "Iniciar" ou "Reiniciar" no Dashboard.
- [ ] Todos os 12 testes da suíte `pytest` continuam passando com sucesso total (100% verde).
