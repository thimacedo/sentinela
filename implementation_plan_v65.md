# Plano de Implementação: Coleta Industrial (v65.0)

Este documento detalha as tarefas para elevar a resiliência, furtividade e eficiência do sistema Sentinela.

## Épico 1: Resiliência e Autocura (The Guardian)
*   **Task 1.1: Refatoração do Watchdog para Hot-Reload Real**
    *   Implementar detecção de mudança de código (watchdog nativo do Python) para que o `main_runner.py` reinicie automaticamente ao salvar arquivos, sem matar o watchdog principal.
*   **Task 1.2: Protocolo de Hibernação Inteligente**
    *   Se o scraper detectar 3 bloqueios de sessão seguidos (429 ou Login Wall), o sistema deve entrar em `SLEEP` por 60 minutos, registrando o evento no banco.
*   **Task 1.3: Limpeza Periódica de Processos Órfãos**
    *   Criar um hook no `BaseWorker` que executa `taskkill` (Windows) ou `pkill` (Linux) em processos de navegadores a cada 10 ciclos concluídos.

## Épico 2: Integridade Zero-Loss (The Vault)
*   **Task 2.1: Buffer Local via SQLite**
    *   Substituir o buffer JSON atual por um banco SQLite local (`runtime_state/buffer.db`).
    *   Garantir que os dados sejam deletados do SQLite APENAS após a confirmação (200 OK) do Supabase.
*   **Task 2.2: Sincronizador de Background**
    *   Criar um thread separado no `main_runner.py` que fica tentando "empurrar" dados do SQLite para o Supabase de 5 em 5 minutos, independente do ciclo de coleta.

## Épico 3: Furtividade e Stealth (The Ghost)
*   **Task 3.1: Aprimoramento do Fast-Skip Temporal**
    *   Mover a lógica de detecção de data do grid para o `InstagramWorker`, permitindo que ele pule o alvo inteiro se os primeiros 3 posts forem velhos, sem nem tentar abrir o modal.
*   **Task 3.2: Rotação Dinâmica de User-Agents e Viewports**
    *   Implementar uma lista de perfis de dispositivos (iPhone, Android, Desktop Windows/Mac) para cada sessão, evitando que todas as sessões pareçam vir da mesma máquina.

## Épico 4: Classificação em Cascata e Custo Zero (The Brain)
*   **Task 4.1: Filtro de Densidade Léxica (Pre-AI)**
    *   Implementar um filtro que descarta comentários com < 3 palavras ou compostos apenas por emojis, sem gastar tokens.
*   **Task 4.2: Classificação Híbrida (Local vs Cloud)**
    *   Integrar o Ollama (Llama 3 local) para classificação primária de "Relevância". 
    *   Apenas comentários marcados como "Políticos/Hostis" pelo modelo local são enviados para o Gemini (Cloud) para análise pericial MCA v2.2.
*   **Task 4.3: Identificador de Ataques Coordenados (Bot Detection)**
    *   Agrupar comentários por similaridade de string (Levenshtein distance). Se houver > 5 repetições, classificar o grupo inteiro como "BOT_CAMPANHA" com uma única chamada de IA.

---
**Status Previsto:** Operação autônoma de até 24h com 99.9% de retenção de dados e 60% de redução no custo de API.
