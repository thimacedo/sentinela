# ESPECIFICAÇÃO DE FALHA: INTEGRACÃO PGMQ E PERMISSÕES (PASA v50.0)

## 1. Visão Geral
O sistema PASA v50.0 está inoperante na camada de filas (PGMQ). O `main_runner` (através do `EventBus` e `AlertWorker`) falha persistentemente ao tentar acessar tabelas dentro do schema `pgmq` no Supabase.

## 2. Sintomas Técnicos
- **Erro de Acesso a Fila:** `EventBus` loga `relation "pgmq.q_classify_comments" does not exist` (código: `42P01`).
- **Erro de Permissão:** `AlertWorker` loga `permission denied for schema pgmq` ao tentar chamar `rpc/detect_worker_anomalies` (código: `42501`).
- **Status da API:** PostgREST retorna `404 Not Found` para requisições endereçadas ao schema `pgmq`.

## 3. Contexto de Infraestrutura
- **Banco de Dados:** Supabase (PostgreSQL).
- **Extensão:** `pgmq` foi instalada (confirmado via SQL).
- **Implementação:** Arquivo `pgmq_setup.sql` aplicado com sucesso (Schema criado, extensões instaladas, `pg_notify` enviado).
- **Componentes Afetados:**
  - `main_runner.py`: Falha ao consumir filas.
  - `workers/processors/alert_worker.py`: Falha ao chamar RPCs de monitoramento.

## 4. Hipóteses de Causa Raiz
1. **Cache de Schema do PostgREST:** O PostgREST não reconheceu as tabelas do schema `pgmq` apesar do `pg_notify('pgrst', 'reload schema')`.
2. **Schema não exposto:** O schema `pgmq` pode não estar listado na configuração de "Exposed Schemas" no Dashboard do Supabase.
3. **Privilégios de Role:** Os roles (`anon`, `authenticated`) não herdaram permissões de leitura/escrita no schema após a criação, mesmo com comandos `GRANT` genéricos.

## 5. Arquivos Envolvidos
- `pgmq_setup.sql`: Contém a definição das filas e schema.
- `workers/processors/alert_worker.py`: Onde ocorre a falha de RPC.
- `main_runner.py`: Onde ocorre a falha do EventBus.

## 6. Ações Necessárias (Checklist de Resolução)
- [ ] Verificar no Dashboard (Settings > API) se o schema `pgmq` está adicionado à lista de "Exposed Schemas".
- [ ] Executar permissões granulares especificamente no schema `pgmq`.
- [ ] Validar se o usuário utilizado pela aplicação (API Key) possui permissão direta ou se está sendo bloqueado por RLS (embora o erro seja no schema, não necessariamente na tabela).
- [ ] Reiniciar o pool de conexões se o PostgREST continuar com cache stale.

## 7. Notas do Operativo
O `BaseWorker` já foi corrigido para aceitar `**kwargs` e está estável. O foco atual é estritamente a visibilidade e permissão do schema `pgmq`.
