# Plano de Implementação: Escalabilidade, Desacoplamento e Resiliência (Fase 8)

Este documento centraliza as especificações estruturais para elevar a arquitetura do Sentinela Democrática, embasado na verificação e no estado real da base de código atual.

## 1. Desacoplamento entre Coleta (Scraping) e Processamento (IA)
- **Status Atual:** Acoplado. O `IGWorkerV2` (`workers/scrapers/ig_worker_v2.py`) executa o scraping e, logo em seguida, itera sobre os comentários inseridos chamando `ai_service.classify_text`. Isso mantém o worker ocupado e o contexto do navegador (Playwright) aberto desnecessariamente.
- **Viabilidade:** Alta. Podemos transformar o `IGWorkerV2` em apenas `InstagramScraperWorker` e criar um `AIClassificationWorker`.
- **Impacto:** Crítico. Reduzirá drasticamente o consumo de memória e CPU, permitindo que a coleta ocorra na velocidade máxima do I/O, enquanto a IA processa o backlog em seu próprio ritmo (rate limiting).

## 2. Paralelismo Assíncrono no Orchestrator
- **Status Atual:** Sequencial. O `Orchestrator.run_scraper` percorre os alvos em um loop `for` simples. Embora o `main_runner.py` suporte múltiplos workers, cada worker processa um alvo por vez.
- **Viabilidade:** Alta. Implementar `asyncio.Semaphore(3)` no loop de processamento de alvos é uma mudança simples no `orquestrador.py`.
- **Impacto:** Multiplica a taxa de ingestão por N (onde N é o limite do semáforo), otimizando o tempo de atividade da máquina.

## 3. Fila de Tarefas Distribuída (Message Broker)
- **Status Atual:** Simulado via Tabela. O `QueueManager` utiliza a tabela `fila_coleta` do Supabase. Embora funcional, o método `claim_next_target` não possui travas atômicas (como `SELECT FOR UPDATE` ou PGMQ), o que causará colisões se rodarmos o Sentinela em dois servidores simultâneos.
- **Viabilidade:** Média. Já existe um arquivo `pgmq_setup.sql` na raiz, indicando que o suporte a PGMQ (Postgres Message Queue) está no radar. Integrar isso ou Redis seria o próximo passo lógico.
- **Impacto:** Essencial para escalabilidade horizontal (Cluster de Sentinelas).

## 4. Rotação Dinâmica de Proxies e Fingerprints
- **Status Atual:** Parcial (Apenas Fingerprints). O `InstagramScraperV2` já possui o método `_generate_stealth_profile` que rotaciona User-Agents e viewports, mas não rotaciona IPs/Proxies. Ele depende apenas do IP da máquina local.
- **Viabilidade:** Alta. Precisamos acoplar um provedor de proxy (ex: Bright Data, Oxylabs ou ProxyRack) no `new_context` do Playwright dentro do `InstagramScraperV2`.
- **Impacto:** Aumenta a resiliência contra Shadowbans da Meta de "Médio" para "Extremo".

## 5. Encerramento Gracioso (Graceful Shutdown)
- **Status Atual:** Parcial. O `main_runner.py` já possui `setup_signal_handlers` capturando `SIGINT` e `SIGTERM`, mas o `IGWorkerV2` não possui um mecanismo de "checkpoint" para salvar exatamente onde parou em uma lista de 500 comentários, por exemplo.
- **Viabilidade:** Média. Requer que o loop de comentários salve o estado no `local_buffer` (SQLite) a cada lote pequeno.
- **Impacto:** Protege a integridade dos dados em caso de reinicializações do servidor ou atualizações automáticas.

## 6. Sistema de Circuit Breaker para a IA
- **Status Atual:** Implementado (v49). O `core/circuit_breaker.py` já existe e o `ai_service.py` já o utiliza (`ai_circuit_breaker`). Ele bloqueia chamadas se detectar falhas consecutivas ou erros 429/503.
- **Melhoria:** Podemos expandir esse Circuit Breaker para o próprio Supabase e para o Scraping (Zyte/Instagram).
- **Impacto:** Já mitigado para a IA, mas expansível para o resto da infraestrutura, garantindo proteção total contra instabilidade externa.
