# Regras de Negócio e Operacionais — Sentinela

## 🛡️ Diretrizes Inegociáveis de Coleta e Raspagem (Scraping)

* **Resiliência e Persistência**: Nossas coletas são resilientes, não importa a velocidade. Precisamos de resistência, persistência e profundidade. O scraper precisa rodar por períodos longos, independente de ter alguns pequenos espaços entre cada coleta.

## 🤖 Diretrizes de Codificação & Autocura

* **Status de Execução em `CycleResult`**: O assistente deve lembrar que a classe `CycleResult` não possui uma propriedade `.success`. Para avaliar o sucesso de um ciclo de worker, verifique as propriedades `db_success`, `success` ou a ausência de mensagens de falha (`result.error is None`).
* **Erros de Negócio vs. Falhas de Infraestrutura**: Erros legítimos de negócio da fila (como `no_posts_found` ou `no_new_comments` quando um perfil de candidato está atualizado e sem novos dados) não devem ser classificados como falhas reais de infraestrutura. Eles não devem incrementar os contadores de bloqueio consecutivo (`consecutive_blocks`) para evitar suspensões indevidas (`PAUSED`).
* **Propagação de `worker_id` em Locks**: Em claims e releases atômicos (`QueueManager`), garanta que o mesmo `worker_id` obtido no claim seja passado no release (`release_atomic(queue_id, status, worker_id)`). Caso contrário, as travas atômicas do Supabase não serão removidas, deixando alvos presos.
* **Codificação de Headers no Ntfy**: Sempre codifique cabeçalhos HTTP contendo textos customizados com emojis ou caracteres especiais (como `Title` e `Tags` do Ntfy) no formato MIME Header (`email.header.Header`) para evitar exceções de codificação `latin-1` ao rodar no Windows.

