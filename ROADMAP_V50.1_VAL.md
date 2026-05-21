# Roadmap Sentinela v50.1 - Dia 21/05

## Status Atual
- **Infraestrutura:** v50.1 Operacional.
- **Extração Real:** Integrada no `IGZyteWorker`.
- **Persistência:** Validada com schema real do Supabase (`data_coleta`, `data_publicacao`, `post_shortcode`).
- **IA/MCA:** Validada com Mistral (Groq em 400).
- **Sessões:** Rotação por slots funcional (Slot 1: Original, Slot 2: Fornecido pelo usuário).
- **Bloqueio:** Instagram detectou Login Wall mesmo com o novo sessionid (Slot 2).

## Próximos Passos (Amanhã)

### 1. Depuração de Sessão
- Verificar se o `sessionid` fornecido (`1651539386:LU06podkTnyCO7:29:AYjOkxoOL1zXhByZiy87DA45WuiBpH8U8-4Ts6NXzw`) está realmente ativo ou se requer cookies adicionais (ex: `ds_user_id`, `csrftoken`).
- Testar a extração com `use_browser=False` (API Direta) forçando o `X-IG-App-ID` correto.

### 2. Expansão de Fallbacks
- Se o Zyte Browser falhar (Login Wall), tentar o `IGHeadlessWorker` (Playwright) se disponível no ambiente.
- Implementar captura de `screenshot` no Zyte para diagnosticar visualmente o Login Wall.

### 3. Estabilização de Produção
- Ativar o `main_runner.py` em modo persistente.
- Monitorar o `RewardEngine` para garantir que o score não seja zerado por falhas de extração (ajustar pesos se necessário).

## Comandos Úteis
- `python run_validation_cycle.py`: Valida o fluxo completo de extração.
- `python validate_db_ia_flow.py`: Valida apenas DB + IA com dados mockados.
- `python fix_env.py`: Limpa caracteres nulos do `.env`.
