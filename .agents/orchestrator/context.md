# Contexto do Projeto - Sentinela

## Estrutura Inicial Identificada
- **Diretório Raiz**: `c:\Projetos\sentinela`
- **Módulo Watchdog**: localizado em `watchdog/`, contendo `__init__.py`, `__main__.py` e `reloader.py`.
- **Configuração de Testes**: `pytest.ini` configurado para executar testes nas pastas `tests`, `scripts` e `tools` buscando arquivos do tipo `test_*.py` e `check_*.py`.
- **Requisitos do Usuário (ORIGINAL_REQUEST.md)**:
  1. Estabilização do Loop do Guardião (Watchdog): Thread do guardião nunca morre. Se crashar seguidamente ou tiver OOM, pausa de forma limpa mudando `state.should_run = False` e atualizando o status no Dashboard, mas mantendo a thread `guard` ativa.
  2. Evitar IA/processamento assíncrono complexo concorrente na thread `guard` (Watchdog). Delegar para `main_runner.py` e simplificar sincronização SQLite/Datasette.
  3. Hibernação responsiva e autocura: Hibernação interrompível imediatamente se o usuário redefinir `state.should_run = True` pelo Dashboard.
  4. Suíte de testes (12 testes pytest) passando em 100%.

## Restrições do Ambiente
- SO: Windows
- Sem uso de Docker ou localhost
- Utilizar Supabase remoto
- Idioma pt-BR
