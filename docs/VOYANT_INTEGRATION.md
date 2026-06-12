# [DEPRECADO / HISTÓRICO] Voyant Tools - Integração e Funcionamento (Sentinela v50.1)

> [!WARNING]
> **ESTA INTEGRAÇÃO COM VOYANT SERVER (JAVA) FOI TOTALMENTE EXPURGADA NA VERSÃO v96.2.**
> O servidor java `VoyantServer.jar` e a Trombone API local foram removidos do Watchdog e do pipeline ativo de triagem para liberar recursos de CPU e RAM no boot. Toda a triagem rápida léxica local agora é executada deterministicamente pelo subagente **SaFastDrop** (`workers/ai/sa_fast_drop.py`) em Python puro e sem dependências de rede ou JVM. Este arquivo serve exclusivamente para documentar o histórico de desenvolvimento.

O Voyant Tools é um componente de infraestrutura utilizado como motor de NLP (Processamento de Linguagem Natural) determinístico de alta performance para análise léxica.

## 1. Arquitetura e Referências
*   **Binário Base:** `tools/voyant/VoyantServer.jar` (Servidor Java autônomo).
*   **Gestão de Processos:** 
    *   `watchdog/voyant.py`: Lógica de inicialização (Headless/Background).
    *   `watchdog/__init__.py`: Integração com o Watchdog para controle do ciclo de vida.
*   **Interface Python:** `core/voyant_service.py` (`VoyantService` Singleton) - Interface HTTP com a Trombone API.
*   **Subagente:** `workers/ai/sa_voyant.py` - Consumidor dos resultados léxicos para triagem de comentários.

## 2. Algoritmos e Modelos
O Voyant **não é um LLM**. Ele executa algoritmos estatísticos clássicos:
*   **TF-IDF**: Identificação de termos relevantes baseada em frequência relativa.
*   **Colocação (Collocations)**: Mapeamento de co-ocorrência de termos.
*   **Análise de Frequência**: Contagem quantitativa para fast-drop de ruído.

## 3. Fluxo Operacional: O "Fast-Drop Triage"
O sistema utiliza o Voyant para reduzir custos e latência de IA Cloud:
1.  **Triagem Local:** `SaVoyant` envia textos para o Voyant Server.
2.  **Fast-Drop:** Se o texto for categorizado como neutro/inexistente de léxico ofensivo (baseado em peso determinístico), ele é classificado automaticamente como "NEUTRO" e removido da fila sem consultar a nuvem.
3.  **Encaminhamento para LLM Cloud:** Se o Voyant identificar termos de alta periculosidade ou alta densidade léxica, o texto é enviado para os modelos Cloud (Mistral/Gemini) para perícia semântica profunda.

## 4. Resiliência e Circuit Breaker
Para evitar paradas do sistema em caso de falha do motor léxico:
*   **Circuit Breaker**: Implementado em `core/voyant_service.py`. Após 3 falhas consecutivas (erro 500 ou timeout), o Voyant é marcado como `is_down` e o sistema redireciona automaticamente todas as requisições de triagem para o pipeline LLM Cloud até que um novo *ping* seja bem-sucedido após o período de cooldown (600s).
*   **Execução Headless**: O servidor Java é executado com flags de sistema (`creationflags=0x08000000` no Windows) e `javaw.exe` para garantir ausência de janelas.
