# Postmortem v90.2: Resolução de Crash Loop, Malha de IA e Integração BrowserAct

**Data:** 05 de Junho de 2026

## 1. O Problema do "Falso Positivo de Estabilidade"
O sistema reportava "OPERACIONAL" no terminal, mas não extraía dados.
* **Diagnóstico:** O `process_cleaner.py` estava matando o processo pai do Python no boot porque as verificações de PID não consideravam o `os.getppid()`. Ao mesmo tempo, faltava a dependência `psutil` no ambiente virtual (`uv` vs `venv`).
* **Solução:** Foi instalada a biblioteca `psutil` globalmente e inserida a regra `if proc.info['pid'] == current_pid or proc.info['pid'] == os.getppid(): continue` no `process_cleaner.py`. Isso estancou o "suicídio" da aplicação.

## 2. Visibilidade do Dashboard Local
O `local_dashboard.html` abria vazio para o usuário (protocolo `file://`).
* **Solução:** Inserimos detecção de protocolo dinâmica via Javascript: `const API_BASE = window.location.protocol === 'file:' ? 'http://localhost:8001' : '';`. Agora os painéis buscam as métricas da porta 8001 mesmo se abertos direto do explorador de arquivos. Adicionamos alertas explícitos no topo para "SESSÕES EXPIRADAS" e "MALHA DE IA DEGRADADA".

## 3. Crash e Exaustão na Malha de Inteligência Artificial
Todos os provedores em nuvem (Groq, Maritaca, DeepSeek) batiam limite 429 e 403 simultaneamente.
* **Solução:**
  * O `QueueManager` recebeu o método `pre_warm_queues()` para evitar inicializações "a frio" e latências. (Houve um erro de tipagem de banco no atributo `_queue` que já foi sanado na v90.1).
  * Criamos a variável de ambiente `NUM_AI_WORKERS=2` para paralelismo seguro.
  * Lançamos o "Batch Processing" que usa `asyncio.Semaphore(5)` para não socar a rede de provedores gratuitos, agindo de forma constante em vez de explosiva.
  * A API do Gemini estava retornando `404 Not Found` para o modelo `gemini-1.5-flash`. Atualizamos os provedores de fallback para `gemini-2.5-flash`.

## 4. Integração do BrowserAct (Automação em Nuvem)
O usuário solicitou o bypass das proteções antibot do Instagram (Login Wall/Sessões Expiradas) via **BrowserAct**.
* **Tentativa via Playwright CDP Local:** Passamos a chave de API fornecida para o endpoint `wss://api.browseract.com/connect`. A conexão retornou erro `401 Unauthorized` mesmo variando o parâmetro da Query String (`token=` ou `apiKey=`) e usando Headers.
* **Resolução Arquitetural (Integração MCP):** Desabilitamos o gatilho falho do CDP no `instagram_scraper_v2.py`. Em vez disso, adotamos o Model Context Protocol (MCP). Modificamos o `.gemini/settings.json` local do agente para carregar a nuvem BrowserAct diretamente como uma ferramenta do Agent CLI. A chave reside salva sob a variável `BROWSERACT_API_KEY`.
