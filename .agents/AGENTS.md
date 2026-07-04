# Regras de Negócio e Operacionais — Sentinela

## 🛡️ Diretrizes Inegociáveis de Coleta e Raspagem (Scraping)

* **Resiliência e Persistência**: Nossas coletas são resilientes, não importa a velocidade. Precisamos de resistência, persistência e profundidade. O scraper precisa rodar por períodos longos, independente de ter alguns pequenos espaços entre cada coleta.

## 🤖 Diretrizes de Codificação & Autocura

* **Status de Execução em `CycleResult`**: O assistente deve lembrar que a classe `CycleResult` não possui uma propriedade `.success`. Para avaliar o sucesso de um ciclo de worker, verifique as propriedades `db_success`, `success` ou a ausência de mensagens de falha (`result.error is None`).
* **Erros de Negócio vs. Falhas de Infraestrutura**: Erros legítimos de negócio da fila (como `no_posts_found` ou `no_new_comments` quando um perfil de candidato está atualizado e sem novos dados) não devem ser classificados como falhas reais de infraestrutura. Eles não devem incrementar os contadores de bloqueio consecutivo (`consecutive_blocks`) para evitar suspensões indevidas (`PAUSED`).
* **Propagação de `worker_id` em Locks**: Em claims e releases atômicos (`QueueManager`), garanta que o mesmo `worker_id` obtido no claim seja passado no release (`release_atomic(queue_id, status, worker_id)`). Caso contrário, as travas atômicas do Supabase não serão removidas, deixando alvos presos.
* **Codificação de Headers no Ntfy**: Sempre codifique cabeçalhos HTTP contendo textos customizados com emojis ou caracteres especiais (como `Title` e `Tags` do Ntfy) no formato MIME Header (`email.header.Header`) para evitar exceções de codificação `latin-1` ao rodar no Windows.

## 🛡️ Diretrizes de SRE, Graceful Shutdown & Console Windows

* **Prevenção de UnicodeEncodeError no Windows (CP1252)**: Sistemas executados sob consoles Windows (com codificação nativa CP1252) podem sofrer crashes fatais ao tentar logar ou dar print em emojis ou caracteres Unicode especiais (ex: 🔑, 💥, 🌙, 🛡️, →).
  - *Ação:* Sempre adicione o tratamento de reconfiguration de streams no topo dos pontos de entrada (`entrypoints` e `main` scripts):
    ```python
    import sys
    if sys.platform.startswith("win"):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
            sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
        except AttributeError:
            pass
    ```
  - *Logging:* Certifique-se de que os manipuladores de arquivo (`FileHandler`) e streams de logs no Python configurem explicitamente a codificação UTF-8 (`encoding="utf-8"`).

* **Graceful Shutdown Assíncrono para Locks Ativos**: Tarefas de scraping e workers de filas com locks atômicos no banco de dados Supabase remoto devem implementar tratamento seguro de encerramento sob sinais `SIGINT` (Ctrl+C) e `SIGTERM` (kill).
  - *Ação:* Garanta que o target ativo sob claim seja salvo em tempo de execução e que signal handlers do Python combinados a blocos `finally` do loop `asyncio` realizem a liberação assíncrona (`release_atomic`) na nuvem para evitar travas órfãs permanentemente em `EM_CURSO`.

* **Logs Explicativos em Hibernações e Sleeps Longos**: Sleepings de resguardo e controle de fluxo assíncronos longos (como Modo Noturno de scrapers entre 23h e 5h ou resguardo por Circuit Breaker aberto) **nunca** devem rodar de forma silenciosa no terminal.
  - *Ação:* Sempre exiba um log descritivo antes do sleep (`self.logger.info` ou `warning`) explicitando a razão do resguardo, a hora atual e o tempo estimado restante do sleep. Isso previne que o operador envie sinais de interrupção forçada por falso travamento síncrono.

