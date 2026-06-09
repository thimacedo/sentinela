# Diagnóstico: Sistema Decision Room (Dashboard Local)

## Resumo das Falhas Ocorridas
O Dashboard local (`Decision Room`) apresentou instabilidade operacional, paradas prematuras e erros de exibição.

### 1. Falha: Conexão Local (API/Watchdog)
- **Sintoma:** Dashboard Offline, dados não carregando.
- **Causa:** O servidor web local (FastAPI no `watchdog`) falhava ao iniciar ou perdia a vinculação com a porta 8001 devido a processos Python zumbis ou corrupção de cache (`__pycache__`).
- **Contexto de Correção:** Implementação de `kill_process_on_port(8001)` no boot e purga agressiva de `__pycache__` antes da inicialização.

### 2. Falha: Erro de Query Supabase (500)
- **Sintoma:** Erro `SyncSelectRequestBuilder object is not callable` e falha ao carregar auditoria.
- **Causa:** Uso incorreto da sintaxe `.not_('processado_ia', 'is', None)` do Supabase Python SDK, que não era compatível com o ambiente instalado.
- **Contexto de Correção:** Ajuste da query para uma sintaxe encadeada estável e filtro Python pós-execução, eliminando a dependência de filtros complexos do SDK na camada de query.

### 3. Falha: Voyant Server em Loop
- **Sintoma:** Múltiplas janelas Java aparecendo, erro 500 no endpoint `/trombone`.
- **Causa:** O `VoyantServer.jar` não conseguia localizar seu arquivo `server-settings.txt` por estar sendo executado fora do seu diretório raiz (`tools/voyant`). Além disso, o servidor tentava abrir uma interface gráfica (AWT) em ambiente sem display.
- **Contexto de Correção:** Configuração da flag `cwd=voyant_dir` na chamada `subprocess.Popen` e re-implementação do modo *headless*.

### 4. Falha: AttributeError (`VoyantService` sem `ping`)
- **Sintoma:** O worker `SaVoyant` travava o orquestrador ao tentar verificar a conexão.
- **Causa:** Regressão de código durante a implementação do *Circuit Breaker*. O método `ping()` foi removido da classe.
- **Contexto de Correção:** Restauração explícita do método `ping()` na classe `VoyantService`.

### 5. Falha: Performance/UI (Dashboard)
- **Sintoma:** Dados repetidos, piscando, ou não atualizando.
- **Causa:** Consulta direta e frequente ao Supabase no frontend, sem verificação de estado.
- **Contexto de Correção:** Implementação de endpoint de cache (`/api/v1/auditoria`) com ttl de 30s e lógica de idempotência visual (`lastAlertsHash`) no frontend para evitar re-renderizações desnecessárias.

## Solicitações Pendentes (Backlog de UX/Funcionalidade)
As seguintes funcionalidades foram solicitadas, mas ainda não foram totalmente integradas à interface do Dashboard ou demandam maior complexidade de implementação:
- **Sala de Controle Granular**: Atualmente temos apenas botões de 'restart' para workers específicos. A solicitação é de uma interface mais abrangente para acionar qualquer worker ou subagente (SA) diretamente.
- **Coleta Direcionada**: Interface dedicada (input field) para o operador inserir um novo alvo (username/URL) e disparar a coleta imediatamente, sem depender do fluxo automático da fila.
