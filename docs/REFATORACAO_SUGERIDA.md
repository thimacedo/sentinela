# Sugestões de Refatoração para Workers

## Observações Gerais
- Padronizar tratamento de exceções e logs.
- Evitar estado volátil (sets em memória) que não persiste entre reinícios.
- Separar responsabilidades: busca, persistência, classificação.
- Utilizar métodos abstratos ou interface para forçar implementação em subclasses.

## Específico: `IGZyteWorker`
1. **Estado de visto volátil**  
   - `self.seen_queue_ids` e `self.seen_targets` são perdidos ao reiniciar, causando reprocessamento de alvos.  
   - Sugestão: Persistir esses IDs em tabela de controle ou usar marcação na própria fila (ex: campo `processed_at`).

2. **Método `fetch_comments_via_zyte` retorna lista vazia proposital**  
   - Atualmente simula falta de parser. Melhorar lançando `NotImplementedError` ou usando flag explícita para indicar fase de desenvolvimento.  
   - Isso deixa o comportamento mais explícito e evita confusão com resultado real vazio.

3. **Atributo `last_fetch_status` usado sem inicialização**  
   - Definido apenas dentro de `fetch_comments_via_zyte`. Se acessado antes (improvável), causa `AttributeError`.  
   - Inicializar em `__init__` ou garantir uso somente após chamada.

4. **Duplicação na lógica de obtenção de alvo manual**  
   - Trecho que trata `manual_target` aparece também em outros workers (se houver).  
   - Sugerir extrair para método utilitário ou classe base.

5. **Rotação de fila via delete/insert pode causar perda de dados**  
   - Se houver falha entre delete e insert, o registro some.  
   - Sugerir atualizar status (ex: `status = 'ROTATED'`) ou usar tabela de histórico.

6. **Tratamento de exceções genérico em `run_cycle`**  
   - `except Exception as ex:` captura tudo, inclusive erros de programação que deveriam interromper.  
   - Considerar expor somente exceções esperadas (HTTP, DB, etc.) e deixar inesperadas bubblarem.

## Específico: `IGHeadlessWorker`
1. **Implementação de placeholder**  
   - Atualmente somente retorna resultado simulado com mensagem de erro fixa.  
   - Quando for integrado, deverá substituir por chamada real ao Playwright e processamento.  
   - Sugerir manter a mesma estrutura de retorno (`CycleResult`) para facilitar transição.

2. **Falta de hooks de setup/teardown específicos**  
   - Pode ser necessário inicializar e fechar navegador.  
   - Sugerir sobrescrever `setup` e `teardown` para gerenciamento de recursos.

## Recomendações de Arquitetura
- Definir classe abstrata `BaseScraperWorker` com métodos abstratos: `fetch`, `persist`, `classify`.  
- Forçar implementação e garantir contrato.  
- Utilizar dependency injection para clientes (httpx, supabase) para facilitar testes.

## Testabilidade
- Injetar dependências (HTTP client, DB client) ao invés de criar dentro dos métodos.  
- Isso permitirá mock em testes unitários.

---
*Este documento contém apenas sugestões. Nenhuma alteração foi aplicada ao código-fonte neste momento.*