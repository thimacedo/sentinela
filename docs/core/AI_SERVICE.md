# AIService - Documentação Completa

**Versão:** PASA v52.3  
**Arquivo Fonte:** `/workspace/core/ai_service.py`  
**Status:** ✅ Em Produção  
**Última Atualização:** Junho 2026

---

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Arquitetura Cascata de Provedores](#arquitetura-cascata-de-provedores)
3. [Fluxo de Classificação](#fluxo-de-classificação)
4. [Prompts de Sistema](#prompts-de-sistema)
5. [Categorias de Classificação](#categorias-de-classificação)
6. [Filtragem Léxica](#filtragem-léxica)
7. [Tratamento de Erros](#tratamento-de-erros)
8. [Circuit Breaker](#circuit-breaker)
9. [Enriquecimento de Prompts](#enriquecimento-de-prompts)
10. [Configuração](#configuração)
11. [Integração com Banco de Dados](#integração-com-banco-de-dados)
12. [Monitoramento e Observabilidade](#monitoramento-e-observabilidade)
13. [Troubleshooting](#troubleshooting)
14. [Performance e Otimizações](#performance-e-otimizações)
15. [Escalabilidade](#escalabilidade)
16. [Integração Stanford NLP (Stanza & DSPy)](#integração-stanford-nlp-stanza--dspy)

---

## 🎯 Visão Geral

O **AIService** é o motor de inteligência central da plataforma Sentinela responsável por **classificar comentários** como hostis ou neutros, seguindo o protocolo **MCA v2.2** (Metodologia de Classificação de Ataques) e **PASA v16.4** (Protocolo de Análise de Sentimento Assistido).

### Responsabilidades Principais

- **Classificação de Hostilidade:** Determinar se um comentário é hostil (is_hate: true/false)
- **Categorização:** Atribuir uma categoria precisa (ex: INSULTO_AD_HOMINEM)
- **Confiança:** Retornar score de confiança (0.0-1.0)
- **Análise Analítica:** Explicar o motivo da classificação
- **Cascata de Provedores:** Usar múltiplas LLMs in fallback automático
- **Filtragem Léxica:** Detectar lixo/spam antes de IA

### Necessidade de Negócio

A plataforma precisa detectar **ataques coordenados** contra candidatos políticos. A IA fornece:
- Detecção de padrões velados (ironias, acusações de crimes)
- Distinção entre crítica legítima e ataque
- Score de confiança para calibração
- Rastreabilidade da decisão

---

## 🏗️ Arquitetura: Cascata de Provedores

### Ordem de Fallback

```
┌─────────────────────────────────────────┐
│ CAMADA 1: FILTRAGEM LOCAL (OLLAMA)      │
│ • Modelo: qwen2.5-coder:3b (padrão)    │
│ • Latência: ~45s (timeout)              │
│ • Custo: R$ 0,00                         │
│ • Saída: NEUTRO, LIXO, SUSPEITO        │
│ • Se confiança >= 0.7 E categoria       │
│   IN (NEUTRO, LIXO) → RETORNA AQUI     │
└──────────────┬──────────────────────────┘
               ↓ (Se SUSPEITO ou incerteza)
┌─────────────────────────────────────────┐
│ CAMADA 2: ANÁLISE CLOUD (MISTRAL/GROQ)  │
│ • Mistral: open-mistral-nemo            │
│ • Groq: llama-3.3-70b-versatile        │
│ • Latência: 10-15s                      │
│ • Custo: R$ 0,001-0,005 por requisição │
│ • Saída: Categoria completa + análise  │
│ • RETORNA a primeira que suceder       │
└──────────────┬──────────────────────────┘
               ↓ (Se todos falharem)
┌─────────────────────────────────────────┐
│ CAMADA 3: FALLBACK PROFUNDO             │
│ • FallbackLLM (implementação local)     │
│ • Sem dependência de API externa        │
│ • Último recurso antes de falha total   │
└─────────────────────────────────────────┘
```

### Providers Configurados

```python
self.providers = [
    {
        "name": "ollama",
        "client": AsyncOpenAI(...),
        "model": os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b"),
        "timeout": 45.0  # Segundos
    },
    {
        "name": "mistral",
        "client": AsyncOpenAI(...),
        "model": "open-mistral-nemo",  # Ou FINETUNED_MODEL_NAME
        "timeout": 15.0
    },
    {
        "name": "groq",
        "client": AsyncOpenAI(...),
        "model": "llama-3.3-70b-versatile",
        "timeout": 10.0
    },
    {
        "name": "openrouter",
        "client": AsyncOpenAI(...),
        "model": "openrouter/free",
        "timeout": 20.0
    }
]
```

### Características de Cada Provedor

| Provedor | Tipo | Velocidade | Custo | Uso |
|----------|------|-----------|-------|-----|
| **Ollama** | Local | Rápido (45s) | Grátis | Triagem rápida |
| **Mistral** | Cloud | Médio (15s) | Low (~R$0.002) | Análise principal |
| **Groq** | Cloud | Muito Rápido (10s) | Low (~R$0.001) | Análise rápida |
| **OpenRouter** | Cloud | Médio (20s) | Variable | Fallback |

---

## 🔄 Fluxo de Classificação

### Método Principal: `classify_text()`

```python
async def classify_text(text: str, comment_id: str = "N/A", trace_id: str = None) -> Dict[str, Any]:
```

### Sequência de Execução

```
1. VALIDAÇÃO DO TEXTO
   ├─ Se vazio → retorna NEUTRO imediatamente
   ├─ Se > 8000 chars → trunca para 8000
   └─ Tipo conversão se não é string

2. FILTRAGEM LÉXICA
   ├─ Chama lexical_filter.is_junk(text)
   ├─ Se junk detectado → retorna NEUTRO (source: "lexical")
   └─ Evita processar spam/lixo

3. CAMADA 1: TRIAGEM LOCAL (OLLAMA)
   ├─ Executa LOCAL_SYSTEM_PROMPT
   ├─ Modelo retorna: NEUTRO | LIXO | SUSPEITO
   ├─ Se confiança >= 0.7 E categoria IN (NEUTRO, LIXO)
   │  └─ RETORNA AQUI (custo zero!) ✅
   └─ Se SUSPEITO ou incerteza → continua

4. CAMADA 2: ANÁLISA CLOUD
   ├─ Para cada provider (Mistral, Groq, OpenRouter)
   ├─ Executa SYSTEM_PROMPT completo
   ├─ Primeira que suceder RETORNA (categorias: ODIO_IDENTITARIO, etc)
   └─ Se todas falham → continua

5. CAMADA 3: FALLBACK LLM
   ├─ Último recurso antes de falha total
   ├─ FallbackLLM.classify(text)
   └─ Se isto falha → RuntimeError("Colapso total das APIs...")

6. RETORNO
   └─ {
       "is_hate": bool,
       "categoria_ia": str,
       "confianca_ia": float,
       "analise_pericial": str,
       "name": str  # Qual provider respondeu
     }
```

### Exemplo: Fluxo Real

```
[Input] text = "Esse deputado é um ladrão de merda!"
[t0] Validação: OK (38 chars)
[t1] Filtro léxico: Não é lixo
[t2] OLLAMA (Local): 
    - Responde em 2s: {"is_hate": true, "categoria_ia": "SUSPEITO", "confianca_ia": 0.6, ...}
    - Confiança 0.6 < 0.7 → não é decisão final
[t3] MISTRAL (Cloud):
    - Responde em 5s: {"is_hate": true, "categoria_ia": "DANO_A_IMAGEM", "confianca_ia": 0.95, ...}
    - ✅ RETORNA AQUI
[Output] is_hate=True, categoria=DANO_A_IMAGEM, confianca=0.95, source=mistral
```

---

## 📝 Prompts de Sistema

### LOCAL_SYSTEM_PROMPT (Para Ollama - Triagem Rápida)

```
Você é um classificador binário de hostilidade política. 
Analise se o texto contém: insultos reais, ameaças, acusações de atos ilícitos/corrupção ou deslegitimação institucional.
Responda APENAS com JSON:
{
  "is_hate": boolean,
  "categoria_ia": "NEUTRO|LIXO|SUSPEITO",
  "confianca_ia": float,
  "analise_pericial": "Motivo rápido (sem usar a palavra crime)"
}
IMPORTANTE: Se houver QUALQUER sinal de ataque ou hostilidade real, marque como "SUSPEITO" para análise posterior.
```

**Propósito:** Decisão rápida (custo zero), não precisa de categoria fina.

### SYSTEM_PROMPT (Para Mistral/Groq - Análise Completa)

```
Você é um analista especializado em Linguística Analítica Digital para identificação de ataques coordenados e hostilidade política.
Sua missão é classificar comentários com realismo absoluto, seguindo MCA v2.2 e PASA v16.4.

--- REGRAS DE OURO ---
1. REALISMO: Não ignore ataques velados, ironias destrutivas ou acusações
2. FALSAS ANÁLISES: Jargão jurídico para acusar de "crimes" = ataque direto (DANO_A_IMAGEM)
3. DISTINÇÃO: Crítica = ideias. Ataques = pessoas/instituições
4. COMUNICAÇÃO: Não use a palavra "crime" na análise
5. IDIOMA: Português Brasileiro (pt-BR)

--- CATEGORIZAÇÃO (MCA v2.2) ---
Se hostil, escolha UMA das categorias:
- ODIO_IDENTITARIO: Raça, religião, orientação sexual, misoginia, xenofobia
- VIOLENCIA_GENERO: Ofensas focadas na condição feminina
- AMEACA: Incitação a dano físico ou morte
- INSULTO_AD_HOMINEM: Desumanização, baixo calão, ataques à honra/competência
- ATAQUE_INSTITUCIONAL: Deslegitimação de órgãos/sistema democrático
- DANO_A_IMAGEM: Imputação de atos ilícitos, corrupção, roubo

Se NÃO for hostil:
- NEUTRO: Engajamento legítimo, críticas técnicas, slogans

--- RESPOSTA (JSON APENAS) ---
{
  "is_hate": boolean, 
  "categoria_ia": "...", 
  "confianca_ia": float,
  "analise_pericial": "Explicação breve"
}
```

---

## 🏷️ Categorias de Classificação

### Categorias Primárias (Para Hostis)

| Categoria | Descrição | Exemplos |
|-----------|-----------|----------|
| **ODIO_IDENTITARIO** | Ataque baseado em identidade (raça, religião, sexo, orientação) | "Negros são criminosos", "Judeus dominam o mundo" |
| **VIOLENCIA_GENERO** | Ataque focado na condição feminina | "Mulher não deve governar", "Não merece respeito" |
| **AMEACA** | Incitação a dano físico ou morte | "Mete uma bala nele", "Levem para a rua" |
| **INSULTO_AD_HOMINEM** | Ataque à pessoa, sem base ideológica | "Seu imbecil", "Feio desgraçado" |
| **ATAQUE_INSTITUCIONAL** | Deslegitimação de instituições democráticas | "Governo é uma ditadura", "STF é corrupto" |
| **DANO_A_IMAGEM** | Acusação de ato ilícito usando jargão jurídico | "Ladrão de merda", "Você é corrupto" |

### Categorias Secundárias (Para Triagem Local)

| Categoria | Uso |
|-----------|-----|
| **NEUTRO** | Conteúdo legítimo (crítica política, slogans, apoio) |
| **LIXO** | Spam, mensagens sem sentido |
| **SUSPEITO** | Pode ser hostil, precisa de análise |
| **ERRO** | Falha no parse JSON |

---

## 🚫 Filtragem Léxica

### Função: `lexical_filter.is_junk(text)`

Antes da IA rodar, AIService verifica se texto é "junk":

```python
from core.lexical_filter import lexical_filter
if lexical_filter.is_junk(text):
    return {"is_hate": False, "categoria_ia": "NEUTRO", ..., "name": "lexical"}
```

**Detecções:**
- Muito repetição de caracteres ("AAAAAAA")
- Apenas números/símbolos
- Muito curto/vazio
- URLs/links puros

---

## ❌ Tratamento de Erros

### Parser JSON Robusto

```python
def _parse_json_response(self, content: str) -> Dict[str, Any]:
    # Primeiro tenta parse direto
    parsed = json.loads(content)
    
    # Se falha, usa regex para extrair JSON
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        parsed = json.loads(match.group(0))
    
    # Valida categoria contra whitelist
    allowed = {...ODIO_IDENTITARIO..., DANO_A_IMAGEM, NEUTRO, ...}
    if category not in allowed:
        category = "ERRO"
    
    # Normaliza confiança
    confidence = max(0.0, min(float(confidence), 1.0))
    
    # Retorna com fallback seguro
    return {...}
```

### Circuit Breaker

```python
ai_circuit_breaker.can_execute(provider_name)
ai_circuit_breaker.record_success(provider_name)
ai_circuit_breaker.record_failure(provider_name, status_code=401)
```

Se provedor falha 5 vezes: disjuntor abre (fast-fail).

### Falhas Catastróficas

```python
except Exception as e:
    logger.error(f"❌ [AI] FallbackLLM falhou após colapso: {e}")
    raise RuntimeError("Colapso total das APIs de Inteligência Artificial")
```

Se tudo falha, retorna erro ao worker (não deve acontecer em produção).

---

## 🔌 Circuit Breaker

### Padrão

Evita enviar requisições para providers fora.

```python
# Status: CLOSED (funcionando) → OPEN (fora) → HALF_OPEN (testando)

if not ai_circuit_breaker.can_execute("mistral"):
    logger.warning("Disjuntor aberto para mistral. Pulando.")
    continue

# ... chamada
ai_circuit_breaker.record_success("mistral")  # Reseta contador
ai_circuit_breaker.record_failure("mistral", status_code=503)  # Incrementa
```

### Remoção de Provider

Se provider está fora permanentemente:

```python
def _remove_provider(self, name: str, reason: str):
    self.providers = [p for p in self.providers if p["name"] != name]
    logger.error(f"Provider '{name}' removido: {reason}")
```

---

## 🎯 Enriquecimento de Prompts

### 1. Custom Rules (config/custom_rules.json)

```json
{
  "additional_rules": [
    "Palavras 'rainha' e 'rei' no contexto de voto devem ser SUSPEITO",
    "Emoji 👑 sempre = entusiasmo, não ataque"
  ],
  "mitigate_false_positives": [
    "Gírias reginoais não são insultos",
    "Campanha de hashtag é engajamento, não coordenação"
  ],
  "custom_keywords": {
    "DANO_A_IMAGEM": ["corrupto", "ladrão", "assassino"],
    "AMEACA": ["mata", "destrói", "faz explodir"]
  }
}
```

### 2. Gold Dataset (data/classifier_gold_dataset.json)

Exemplos auditados manualmente:

```json
[
  {"text": "Vote em X! Pode acreditar", "label": "NEUTRO"},
  {"text": "X é um ladrão de merda", "label": "DANO_A_IMAGEM"},
  {"text": "Mate o deputado", "label": "AMEACA"}
]
```

Sistema automaticamente injeta os últimos 10 exemplos no prompt para calibração.

---

## ⚙️ Configuração

### Variáveis de Ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | URL da API Ollama local |
| `OLLAMA_MODEL` | `qwen2.5-coder:3b` | Modelo a usar no Ollama |
| `MISTRAL_API_KEY` | N/A | Chave de API da Mistral |
| `GROQ_API_KEY` | N/A | Chave de API da Groq |
| `OPENROUTER_API_KEY` | N/A | Chave de API da OpenRouter |
| `FINETUNED_MODEL_NAME` | N/A | Modelo fine-tuned Mistral (se houver) |
| `CONFIDENCE_THRESHOLD` | 0.5 | Threshold mínimo de confiança |

### Inicialização

```python
from core.ai_service import AIService

ai_service = AIService()

# Uso
result = await ai_service.classify_text("Texto aqui", comment_id="123")
```

---

## 📊 Resposta Padrão

```python
{
    "is_hate": True,  # Booleano
    "categoria_ia": "DANO_A_IMAGEM",  # Uma das categorias
    "confianca_ia": 0.92,  # Float 0.0-1.0
    "analise_pericial": "Imputação direta de ato ilícito (corrupção) usando jargão jurídico.",
    "name": "mistral"  # Qual provider respondeu
}
```

---

## 📈 Monitoramento e Observabilidade

### Logs Emitidos

```
🟢 [AI] OLLAMA | ID: abc123 | NEUTRO | (Triagem Local)
   └─ Resposta rápida da triagem local

🔍 [AI] MISTRAL | ID: abc123 | DANO_A_IMAGEM | (Refinado)
   └─ Resposta da análise cloud

⚠️ [AI] Provedor local 'ollama' indisponível/offline
   └─ Ollama não está rodando, abrindo disjuntor

❌ [AI] Provedor Cloud 'mistral' retornou erro de credenciais (401)
   └─ API key inválida ou expirada

🚨 [AI] Todos os provedores indisponíveis. Acionando FallbackLLM
   └─ Usando fallback final

❌ [AI] FallbackLLM falhou após colapso: ...
   └─ Falha catastrófica - nenhum recurso disponível
```

---

## 🔧 Troubleshooting

### Problema 1: Ollama Offline

**Sintoma:**
```
WARNING: Provedor local 'ollama' indisponível/offline
```

**Solução:**
1. Verificar se Ollama está rodando:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. Se não, iniciar:
   ```bash
   ollama serve
   ```

3. Verificar modelo:
   ```bash
   ollama pull qwen2.5-coder:3b
   ```

---

### Problema 2: API Key Inválida (Mistral/Groq)

**Sintoma:**
```
ERROR: Provedor Cloud 'mistral' retornou erro de credenciais (401)
```

**Solução:**
1. Verificar chave:
   ```bash
   echo $MISTRAL_API_KEY
   ```

2. Se expirada, renovar no dashboard

3. Realocar variável de ambiente

---

### Problema 3: Nenhuma Categoria Válida

**Sintoma:**
```
categoria_ia = "ERRO"
```

**Causa Provável:**
JSON parse falhou, categoria não é reconhecida.

**Solução:**
1. Verificar response do provider (logs)
2. Adicionar categoria à whitelist se legítima
3. Melhorar prompt se provider está confuso

---

### Problema 4: Confiança Baixa (<0.5)

**Sintoma:**
Todos os resultados com confiança < 0.5

**Causa Provável:**
- Prompt não está claro o bastante
- Dados de treinamento insuficientes
- Modelo não é adequado

**Solução:**
1. Adicionar exemplos ao gold_dataset.json
2. Refinar SYSTEM_PROMPT
3. Experimentar modelo diferente no Ollama

---

## 🚀 Performance e Otimizações

### Latências Típicas

| Cenário | Tempo | Notas |
|---------|-------|-------|
| Texto vazio | ~0ms | Validação imediata |
| Lixo detectado (léxico) | ~10ms | Sem IA |
| OLLAMA decisivo (confiança >=0.7) | ~2s | Custo zero |
| MISTRAL responde | ~5-10s | Cloud fallback |
| GROQ responde | ~3-8s | Mais rápido |
| FallbackLLM | ~1-2s | Local computation |

### Otimizações Possíveis

#### 1. Cache de Resultados

```python
# Não reprocessar mesmo comentário 2x
self.response_cache = {}
if text in self.response_cache:
    return self.response_cache[text]
# ... processar ...
self.response_cache[text] = result
```

#### 2. Batch Processing

```python
# Processar múltiplos comentários em paralelo
results = await asyncio.gather(
    self.classify_text(text1),
    self.classify_text(text2),
    self.classify_text(text3),
)
```

#### 3. Priorização de Provider

```python
# Se Groq é sempre rápido, tentar primeiro
self.providers.sort(key=lambda p: 0 if p["name"]=="groq" else 1)
```

---

## 📦 Dependências Externas

### Bibliotecas

| Biblioteca | Propósito |
|-----------|----------|
| `openai` | AsyncOpenAI cliente |
| `httpx` | HTTP async client |
| `json` | Parse/serialização |

### Serviços Externos

| Serviço | Criticidade | Status |
|---------|-------------|--------|
| **Ollama (local)** | ALTA | ✅ Essencial para triagem |
| **Mistral API** | ALTA | ✅ Perícia principal |
| **Groq API** | ALTA | ✅ Fallback rápido |
| **OpenRouter** | MÉDIA | ⚠️ Fallback final |
| **FallbackLLM** | CRÍTICA | ✅ Último recurso |

---

## 🔗 Integração Stanford NLP (Stanza & DSPy)

A partir da versão **v98.6 (PASA v52.4)**, o `AIService` foi integrado aos novos componentes de processamento linguístico:
*   **Stanford Stanza:** Executa a normalização e lematização morfossintática offline em CPU (`use_gpu=False`). A saída estruturada (lemmas, tags POS, dependências sintáticas) é persistida em tempo real na coluna `analise_linguistica` (JSONB) no Supabase.
*   **DSPy structured classification:** Roteamento alternativo estruturado via assinaturas tipadas (`ClassificarComentarioPASA`), ativado pela flag `USE_DSPY=true`. As chamadas síncronas do DSPy são encapsuladas em uma thread isolada para evitar deadlocks de loops de eventos asyncio.

Para detalhes completos da arquitetura, fluxo de dados e governança de DDL, consulte o documento técnico:
👉 [Stanford NLP Integration Docs](file:///c:/projetos/sentinela/docs/core/STANFORD_NLP_INTEGRATION.md)

---

## 📝 Changelog

### v98.6 (PASA v52.4)
- ✅ Integração com Stanza NLP Engine (Lemmas, POS tags e dependências UD no JSONB)
- ✅ Integração com DSPy Structured Predictor (Chain of Thought tipado)
- ✅ Omissão de `response_format` para chamadas textuais das APIs OpenAI-like (Mistral/Alibaba)
- ✅ Suporte ao GloVe local com fallback automático para TF-IDF lematizado no `DataMiner`

### v52.3 (Junho 2026)
- ✅ Cascata de 4 provedores cloud + FallbackLLM
- ✅ MCA v2.2 e PASA v16.4 implementados
- ✅ Circuit breaker com remoção automática
- ✅ Gold dataset para calibração
- ✅ Custom rules support
- ✅ Filtragem léxica robusta

---

**Documento Gerado:** Junho 2026  
**Status:** ✅ Completo
