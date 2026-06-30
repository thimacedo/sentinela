# Integração Stanford NLP no Sentinela (v98.6)

Este documento descreve as novas funcionalidades e a arquitetura do ecossistema de Processamento de Linguagem Natural (PLN) introduzidas no projeto **Sentinela** (PASA v98.6), cobrindo o Stanford Stanza, DSPy e o GloVe.

---

## 📋 Índice
1. [Visão Geral](#1-visão-geral)
2. [Componente 1: Stanza NLP Engine](#2-componente-1-stanza-nlp-engine)
3. [Componente 2: DSPy Structured Predictor](#3-componente-2-dspy-structured-predictor)
4. [Componente 3: DataMiner & GloVe](#4-componente-3-dataminer--glove)
5. [Alterações no Banco de Dados (Supabase)](#5-alterações-no-banco-de-dados-supabase)
6. [Resiliência Operacional e CPU-only](#6-resiliência-operacional-e-cpu-only)
7. [Validação e Testes](#7-validação-e-testes)

---

## 1. Visão Geral

A integração da malha do **Stanford NLP** moderniza as camadas analíticas e de inteligência do Sentinela, adicionando recursos determinísticos locais ao processamento de linguagem natural:
*   **Lematização e POS Tagging neurais:** Reduzem variações morfológicas a suas raízes lexicais nos comentários, otimizando detecções.
*   **Análise Sintática (UD):** Identifica relações de dependência entre sujeitos, verbos e adjetivos de forma local.
*   **Assinaturas e Chain of Thought com DSPy:** Substitui prompts estáticos por contratos estruturados e tipados para as IAs, preservando o mesh de resiliência.
*   **Embeddings locais com GloVe:** Agrupa discursos de ódio por afinidade semântica densa localmente, sem custos extras de API externa.

```
                  ┌───────────────────────────────┐
                  │      Comentário Coletado      │
                  └───────────────┬───────────────┘
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                           AI PROCESSOR                           │
│  1. Limpeza e Decode de Leetspeak                                │
│  2. Classificação de IA (DSPy Signature + AIService Cascade)     │
│  3. Análise Morfossintática (Stanza POS & Lemmas)                │
└───────────────────────────────┬──────────────────────────────────┘
                                  ▼
                  ┌───────────────────────────────┐
                  │   Supabase: analise_ling (J)  │
                  └───────────────┬───────────────┘
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                            DATAMINER                             │
│  1. Consome Lemmas Unificados do Banco                           │
│  2. Vetorização Densa (GloVe Embeddings local)                    │
│  3. KMeans Clustering → Grupos Temáticos de Ódio                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Componente 1: Stanza NLP Engine

A classe `StanzaNLPEngine` em `core/stanza_nlp.py` fornece uma API simplificada em português (`pt`) para a execução do pipeline de processamento do Stanford Stanza.

### Características Técnicas
*   **Localização:** [core/stanza_nlp.py](file:///c:/projetos/sentinela/core/stanza_nlp.py)
*   **Processadores Carregados por Padrão:** `tokenize,mwt,pos,lemma` (pipeline leve para CPU).
*   **Processadores Carregados sob Demanda:** `tokenize,mwt,pos,lemma,depparse` (para parsing sintático completo).
*   **Fronteiras de Sentenças:** O método `extrair_ngrams` respeita estritamente a delimitação de sentenças geradas pela rede neural do Stanza, garantindo que n-gramas nunca cruzem limites de ponto final.

---

## 3. Componente 2: DSPy Structured Predictor

O framework **DSPy** substitui os prompts ad-hoc por lógica de programação declarativa. No Sentinela, a integração foi desenvolvida para se acoplar diretamente à arquitetura de resiliência preexistente.

### Arquitetura de Integração
*   **Localização:** [core/dspy_integration.py](file:///c:/projetos/sentinela/core/dspy_integration.py)
*   **Assinatura PASA:** `ClassificarComentarioPASA` define formalmente os campos de entrada (`texto`, `contexto_forense`) e saída estruturada (`is_hate`, `categoria_ia`, `confianca_ia`, `analise_pericial`).
*   **LM Customizada (`SentinelaLM`):** Adaptador que herda de `dspy.LM`. O DSPy interage com a classe enviando a string do prompt de inferência, e a `SentinelaLM` despacha a chamada para a cascata de redundância do `ai_service`. Isso mantém ativos todos os logs, timeouts, circuit breakers e chaves de rotação.
*   **Isolamento Multithread:** Para evitar conflitos ou travamentos em loops de eventos `asyncio` rodando na thread de execução do orquestrador ou de testes, o método `__call__` do `SentinelaLM` dispara uma thread própria com loop isolado (`asyncio.new_event_loop()`), retornando o resultado de forma síncrona.

---

## 4. Componente 3: DataMiner & GloVe

O worker de clusterização temática em lote (`DataMiner`) foi modificado para utilizar a normalização linguística e representação densa local.

### Funcionamento
*   **Localização:** [processing/data_miner.py](file:///c:/projetos/sentinela/processing/data_miner.py)
*   **Lematização Temática:** Em vez de rodar a vetorização sobre o texto bruto do comentário (gerando dispersão entre termos como *roubou*, *rouba*, *roubando*), o `DataMiner` lê a coluna `analise_linguistica` do Supabase e executa o algoritmo sobre os lemmas consolidados (ex: *roubar*), aumentando consideravelmente a qualidade dos clusters.
*   **GloVe Embeddings (`data/glove_s50.txt`):** Se os vetores do GloVe estiverem presentes localmente na máquina, o `DataMiner` calcula o vetor médio de embeddings do comentário, realizando a clusterização KMeans no espaço vetorial semântico denso.
*   **Fallback Resiliente:** Caso o arquivo do GloVe não seja encontrado em disco, o minerador realiza o fallback silencioso para a matriz TF-IDF baseada nos lemmas do Stanza, garantindo resiliência operacional contínua.

---

## 5. Alterações no Banco de Dados (Supabase)

Para armazenar a estrutura de metadados linguísticos gerada pelo Stanza, foi criada uma nova coluna na tabela `comentarios`.

### Definição DDL
*   **Coluna Adicionada:** `analise_linguistica` (tipo `JSONB`)
*   **Migration SQL:** [20260630000001_add_analise_linguistica.sql](file:///c:/projetos/sentinela/supabase/migrations/20260630000001_add_analise_linguistica.sql)
*   **Schema JSON Gravado:**
    ```json
    {
      "lemmas": ["texto", "teste", "pipeline"],
      "sentences": [["texto", "teste", "pipeline"]],
      "pos_tags": [
        {
          "text": "teste",
          "lemma": "teste",
          "pos": "NOUN"
        }
      ],
      "dependencies": [
         {
           "word": "candidato",
           "pos": "NOUN",
           "lemma": "candidato",
           "deprel": "nsubj",
           "head_text": "imbecil",
           "head_pos": "NOUN"
         }
      ],
      "success": true
    }
    ```

---

## 6. Resiliência Operacional e CPU-only

Em conformidade com as regras Diamond do projeto (resiliência operacional priorizada sobre a velocidade bruta):
1.  **Forçamento de CPU:** O Stanza é instanciado sempre com `use_gpu=False`. Isso elimina conflitos de CUDA/drivers e torna a execução viável em qualquer servidor comum ou ambiente de desenvolvimento local.
2.  **Fallback de Falha de PLN:** Caso o Stanza encontre erros críticos de download ou arquivos corrompidos, o método `processar_texto` faz o fallback automático dividindo o texto original por espaços ASCII, impedindo que o fluxo principal de classificação caia.

---

## 7. Validação e Testes

Foram criados dois scripts específicos para validar o pipeline linguístico:
*   [test_linguistic_pipeline.py](file:///c:/projetos/sentinela/scratch/test_linguistic_pipeline.py): Valida a inicialização básica do Stanza, as dependências do DSPy e a persistência da coluna `analise_linguistica` (JSONB) no Supabase remoto de produção.
*   [test_pending_comments_nlp.py](file:///c:/projetos/sentinela/scratch/test_pending_comments_nlp.py): Realiza auditoria real consumindo dados diretamente da fila do banco remoto, processando-os com Stanza e validando a inferência estruturada DSPy de forma offline com um adaptador local de MockLM.
