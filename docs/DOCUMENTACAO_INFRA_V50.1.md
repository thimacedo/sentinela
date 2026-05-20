# Documentação Técnica: Sentinela v50.1 (Infraestrutura Operacional)

## Visão Geral
A infraestrutura Sentinela v50.1 estabelece o contrato técnico fundamental para workers de coleta, focando em targeting real, rotatividade de fila e observabilidade honesta durante a fase de desenvolvimento (dry-run).

## Arquitetura de Observabilidade
O sistema foi refinado para garantir transparência total sobre o estado de execução, evitando logs ambíguos.

### Logs do Orquestrador
Os logs agora refletem o estado operacional real:
- **`simulado=True`**: Indica que o worker está operando em modo dry-run (coleta/persistência não realizada).
- **`db=n/a`, `ia=n/a`**: Indica que os subsistemas de banco e IA não foram acionados devido ao modo simulado.
- **`erro=<erro>`**: Registro explícito do motivo técnico da falha/simulação (ex: `zyte_fetch_not_implemented`).

### Filtragem do AIAdvisor
Para evitar poluição de dados, o `AIAdvisor` é automaticamente ignorado pelo orquestrador em ciclos onde `simulado=True`.

## Contratos Técnicos

### BaseWorker (Contrato Abstrato)
- Obriga a implementação de `setup()`, `teardown()`, `run_cycle()` e `describe()`.
- Garante que a limpeza de recursos ocorra sempre, mesmo em caso de exceções.

### IGZyteWorker (Contrato de Coleta)
Define o fluxo operacional para extração futura:
1. `claim_next_target()`: Seleção de alvos reais (via fila ou fallback).
2. `fetch_comments_via_zyte()`: (Stubs) Chamada à API Zyte.
3. `persist_comments()`: (Stubs) Persistência idempotente no Supabase.
4. `classify_comments()`: (Stubs) Integração com IA.
5. `run_cycle()`: Orquestração do fluxo com tratamento de erros.

## Estado Atual do Sistema
| Subsistema | Status |
| :--- | :--- |
| **Infraestrutura** | OK |
| **Targeting Real** | OK |
| **Observabilidade** | Honesta (n/a) |
| **Coleta Real** | Pendente |

## Próxima Fase: Extração Real
A transição para `simulated=False` ocorrerá quando:
- O motor `Zyte` for implementado com sucesso.
- A persistência de comentários for garantida com `upsert`.
- A classificação via IA for integrada e validada.
