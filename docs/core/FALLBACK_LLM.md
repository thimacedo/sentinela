# Fallback LLM — Gerenciador de Provedores de IA de Fallback

**File**: `/workspace/core/fallback_llm.py`  
**Versão**: v1.0  
**Última Atualização**: 2026-06-04

---

## 📋 Visão Geral

O `FallbackLLM` é um wrapper genérico que rotaciona entre múltiplos provedores de IA de terceiros. É a **camada final de fallback** na cascata de AIService quando todos os provedores locais/internos falham.

### Responsabilidades Principais
- ✅ Rotacionar entre 14+ provedores de IA (Cohere, DeepSeek, Azure, OpenAI, Anthropic, Groq, Gemini, etc.)
- ✅ Gerenciar API keys dinamicamente por variáveis de ambiente
- ✅ Integrar com circuit breaker para evitar repetidas falhas
- ✅ Remover automaticamente provedores com restrição permanente
- ✅ Falhar elegantemente quando todos os provedores estão indisponíveis

---

## 🏗️ Arquitetura

### Provedores Suportados

| Provedor | Modelo Padrão | API Key | Status |
|----------|---------------|---------|--------|
| **Cohere** | command-r | `COHERE_API_KEY` | ✅ Ativo |
| **DeepSeek** | deepseek-chat | `DEEPSEEK_API_KEY` | ✅ Ativo |
| **Azure OpenAI** | gpt-35-turbo | `AZURE_OPENAI_API_KEY` | ✅ Ativo |
| **OpenRouter** | openrouter/auto | `OPENROUTER_API_KEY` | ✅ Ativo |
| **AI21 Labs** | j2-ultra | `AI21_API_KEY` | ✅ Ativo |
| **Fireworks AI** | llama-v2-7b-chat | `FIREWORKS_API_KEY` | ✅ Ativo |
| **OpenAI** | gpt-4o | `OPENAI_API_KEY` | ✅ Ativo |
| **Anthropic** | claude-3-5-sonnet | `ANTHROPIC_API_KEY` | ✅ Ativo |
| **Google Gemini** | gemini-1.5-flash | `GEMINI_API_KEY` | ✅ Ativo |
| **Groq** | llama-3.1-8b-instant | `GROQ_API_KEY` | ✅ Ativo |
| **Zhipu GLM** | glm-4-flash | `ZHIPU_API_KEY` | ✅ Ativo |
| **Cerebras** | llama3.1-8b | `CEREBRAS_API_KEY` | ✅ Ativo |
| **EdenAI** | (delegado) | `EDENAI_API_KEY` | ✅ Ativo |
| **LLaMA2** | (local) | Nenhuma | ✅ Ativo (dummy) |

### Integração com Circuit Breaker

```python
from core.circuit_breaker import ai_circuit_breaker

# No FallbackLLM.classify()
if not ai_circuit_breaker.can_execute(f"fallback_{provider['name']}"):
    # Skip este provider (em estado aberto)
    continue

# Após sucesso
ai_circuit_breaker.record_success(f"fallback_{name}")

# Após falha
ai_circuit_breaker.record_failure(f"fallback_{name}", status_code)
```

---

## 🔑 Métodos Principais

### `__init__()`

**Inicializa o FallbackLLM** com a lista de provedores configurada em `config.py`.

**Exemplo:**
```python
from core.fallback_llm import FallbackLLM

fallback_llm = FallbackLLM()
# Lê FALLBACK_PROVIDERS de core/config.py
```

---

### `classify(text, provider_name=None)`

**Classifica um texto** usando o provedor selecionado (ou rotaciona se nenhum especificado).

**Parâmetros:**
- `text` (str): Prompt de classificação
- `provider_name` (str, opcional): Nome do provedor específico. Se `None`, tenta todos em ordem de prioridade.

**Retorna:** `str` — Resposta do LLM

**Comportamento:**

1. Se `provider_name` especificado:
   - Tenta apenas esse provedor
   - Raise `ValueError` se não configurado

2. Se `provider_name=None`:
   - Itera sobre `FALLBACK_PROVIDERS` em ordem
   - Pula provedores com circuit breaker aberto
   - Tenta cada um até sucesso
   - Raise `RuntimeError` se todos falharem

**Exemplo — Usar provedor específico:**
```python
result = fallback_llm.classify(
    "Classifique este texto como positivo ou negativo",
    provider_name="openai_gpt35"
)
print(result)  # "Positivo"
```

**Exemplo — Rotação automática:**
```python
result = fallback_llm.classify(
    "Alguma entrada de IA"
)
# Tenta: openai → anthropic → groq → ... até sucesso
```

---

## 🔄 Fluxo de Rotação

```
FallbackLLM.classify(text)
    ↓
├─ provider_name especificado?
│  └─ Sim: Tenta só esse (ou raise ValueError)
│
└─ Não: Itera FALLBACK_PROVIDERS
   ├─ Circuit breaker aberto?
   │  └─ Sim: Skip para próximo
   │
   └─ Não: Tenta chamar API
      ├─ Sucesso? (HTTP 200)
      │  └─ Retorna resposta + record_success()
      │
      └─ Erro HTTP (401, 402, 403, 404)?
         └─ Remove provedor permanentemente
         └─ Continua para próximo
      
      └─ Erro de config (API key ausente)?
         └─ Remove provedor
         └─ Continua
      
      └─ Outro erro?
         └─ record_failure() no circuit breaker
         └─ Continua para próximo

Todos falharam? → Raise RuntimeError
```

---

## 📡 Provedores — Detalhes Técnicos

### 1. Cohere

**Endpoint:** `https://api.cohere.com/v1/chat`  
**Modelo:** `command-r`  
**API Key:** `COHERE_API_KEY`

```python
def _call_cohere(self, text: str, api_key: str) -> str:
    payload = {
        "message": text,
        "model": "command-r",
        "temperature": 0.0,
        "max_tokens": 50,
    }
```

---

### 2. DeepSeek

**Endpoint:** `https://api.deepseek.com/v1/chat/completions`  
**Modelo:** `deepseek-chat`  
**API Key:** `DEEPSEEK_API_KEY`

```python
def _call_deepseek(self, text: str, api_key: str) -> str:
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": text}],
        "max_tokens": 50,
    }
```

---

### 3. Azure OpenAI

**Endpoint:** `{AZURE_OPENAI_ENDPOINT}/openai/deployments/gpt-35-turbo/chat/completions`  
**Modelo:** `gpt-35-turbo` (configurável)  
**API Keys:** `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`

```python
def _call_azure(self, text: str, api_key: str) -> str:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    url = f"{endpoint}/openai/deployments/gpt-35-turbo/chat/completions?api-version=2023-05-15"
```

---

### 4. OpenRouter

**Endpoint:** `https://openrouter.ai/api/v1/chat/completions`  
**Modelo:** `openrouter/auto` (roteador automático)  
**API Key:** `OPENROUTER_API_KEY`

```python
def _call_openrouter(self, text: str, api_key: str) -> str:
    payload = {
        "model": "openrouter/auto",
        "messages": [{"role": "user", "content": text}],
        "max_tokens": 50,
    }
```

---

### 5. AI21 Labs

**Endpoint:** `https://api.ai21.com/studio/v1/j2-ultra/completions`  
**Modelo:** `j2-ultra`  
**API Key:** `AI21_API_KEY`

```python
def _call_ai21(self, text: str, api_key: str) -> str:
    payload = {
        "prompt": text,
        "maxTokens": 50,
        "temperature": 0.0,
    }
```

---

### 6. Fireworks AI

**Endpoint:** `https://api.fireworks.ai/inference/v1/completions`  
**Modelo:** `llama-v2-7b-chat`  
**API Key:** `FIREWORKS_API_KEY`

```python
def _call_fireworks(self, text: str, api_key: str) -> str:
    payload = {
        "model": "accounts/fireworks/models/llama-v2-7b-chat",
        "prompt": text,
        "max_tokens": 50,
        "temperature": 0.0,
    }
```

---

### 7. OpenAI GPT

**Endpoint:** `https://api.openai.com/v1/chat/completions`  
**Modelo:** `gpt-4o`  
**API Key:** `OPENAI_API_KEY`

```python
def _call_openai(self, text: str, api_key: str) -> str:
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": text}]
    }
```

---

### 8. Anthropic Claude

**Endpoint:** `https://api.anthropic.com/v1/messages`  
**Modelo:** `claude-3-5-sonnet-20240620`  
**API Key:** `ANTHROPIC_API_KEY`

```python
def _call_anthropic(self, text: str, api_key: str) -> str:
    payload = {
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": text}]
    }
```

---

### 9. Google Gemini

**Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`  
**Modelo:** `gemini-1.5-flash` (configurável)  
**API Key:** `GEMINI_API_KEY` (via query param)

```python
def _call_gemini(self, text: str, api_key: str, model: str) -> str:
    model = model or "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": text}]}]}
```

---

### 10. Groq (Llama 3.1)

**Endpoint:** `https://api.groq.com/openai/v1/chat/completions`  
**Modelo:** `llama-3.1-8b-instant` (ultra-rápido)  
**API Key:** `GROQ_API_KEY`

```python
def _call_groq(self, text: str, api_key: str, model: str) -> str:
    model = model or "llama-3.1-8b-instant"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": text}]
    }
```

---

### 11. Zhipu GLM-4

**Endpoint:** `https://open.bigmodel.cn/api/paas/v4/chat/completions`  
**Modelo:** `glm-4-flash` (configurável)  
**API Key:** `ZHIPU_API_KEY`

```python
def _call_zhipu(self, text: str, api_key: str, model: str) -> str:
    model = model or "glm-4-flash"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": text}]
    }
```

---

### 12. Cerebras

**Endpoint:** `https://api.cerebras.ai/v1/chat/completions`  
**Modelo:** `llama3.1-8b` (configurável)  
**API Key:** `CEREBRAS_API_KEY`

```python
def _call_cerebras(self, text: str, api_key: str, model: str) -> str:
    model = model or "llama3.1-8b"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": text}]
    }
```

---

### 13. EdenAI (Meta-Provedor)

**Endpoint:** `https://api.edenai.run/v2/text/chat`  
**Modelo/Provider:** Configurável (padrão: `openai`)  
**API Key:** `EDENAI_API_KEY`

```python
def _call_edenai(self, text: str, api_key: str, provider: str) -> str:
    provider = provider or "openai"
    payload = {
        "providers": provider,  # "openai", "anthropic", "cohere", etc.
        "text": text,
        "chatbot_global_action": "You are a helpful assistant.",
        "temperature": 0.0,
        "max_tokens": 1000
    }
```

---

### 14. LLaMA2 (Local Dummy)

**Tipo:** Dummy/Fallback local  
**Sem API Key**

```python
def _call_llama2(self, text: str) -> str:
    return f"[LLAMA2] {text}"
```

---

## ⚙️ Configuração

### Em `config.py`

Define a lista de provedores e sua ordem de prioridade:

```python
FALLBACK_PROVIDERS = [
    {
        "name": "openai_gpt35",
        "api_key_env": "OPENAI_API_KEY",
        "model": None,  # Usa padrão (gpt-4o)
    },
    {
        "name": "anthropic_claude_instant",
        "api_key_env": "ANTHROPIC_API_KEY",
        "model": None,
    },
    {
        "name": "groq_llama3",
        "api_key_env": "GROQ_API_KEY",
        "model": "llama-3.1-8b-instant",
    },
    {
        "name": "openrouter",
        "api_key_env": "OPENROUTER_API_KEY",
        "model": "openrouter/auto",
    },
    {
        "name": "llama2",
        "api_key_env": None,  # Sem autenticação
        "model": None,
    },
]
```

### Variáveis de Ambiente Necessárias

```bash
# Cohere
COHERE_API_KEY=sk-...

# DeepSeek
DEEPSEEK_API_KEY=sk-...

# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://YOUR_RESOURCE.openai.azure.com

# OpenRouter
OPENROUTER_API_KEY=sk-or-...

# AI21
AI21_API_KEY=...

# Fireworks
FIREWORKS_API_KEY=...

# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Google Gemini
GEMINI_API_KEY=...

# Groq
GROQ_API_KEY=gsk_...

# Zhipu
ZHIPU_API_KEY=...

# Cerebras
CEREBRAS_API_KEY=...

# EdenAI
EDENAI_API_KEY=...
```

---

## 🔐 Gerenciamento Dinâmico de Provedores

### Remoção Permanente

O FallbackLLM remove provedores automaticamente em dois cenários:

#### 1. Erro Permanente (401, 402, 403, 404)

```python
if status_code in [401, 402, 403, 404]:
    logger.warning(f"🚨 [AI] Provider '{name}' com restrição permanente/gratuita esgotada ({status_code}). Removendo do fallback.")
    self.providers_order.remove(prov)
```

**Causas típicas:**
- **401**: API key inválida ou expirada
- **402**: Quota gratuita esgotada
- **403**: Acesso proibido/account suspenso
- **404**: Modelo ou endpoint não encontrado

#### 2. Configuração Ausente

```python
if "ausente" in str(exc).lower():
    logger.warning(f"🚨 [AI] Provider '{name}' sem API Key configurada. Removendo do fallback.")
    self.providers_order.remove(prov)
```

**Exemplo:**
```
GEMINI_API_KEY ausente. → Remover "google_gemini"
```

---

## 🚨 Tratamento de Erros

### Cascata de Erros

```
Provedor 1: ✗ (HTTP 429 — rate limit)
  → record_failure() no circuit breaker
  → Tenta próximo

Provedor 2: ✗ (API key ausente)
  → Remove do FALLBACK_PROVIDERS
  → Tenta próximo

Provedor 3: ✓ (sucesso)
  → Retorna resposta
  → record_success() no circuit breaker

Todos esgotados: ✗
  → RuntimeError: "Todas as chamadas de fallback falharam."
```

---

## 📚 Integração com AIService

Na cascata de AIService, o FallbackLLM é chamado como **último resort**:

```
AIService.classify(text)
    ↓
1. Ollama local? → Sucesso: Retorna
                  → Falha: próximo
↓
2. Mistral? → Sucesso: Retorna
            → Falha: próximo
↓
3. Groq? → Sucesso: Retorna
         → Falha: próximo
↓
4. OpenRouter? → Sucesso: Retorna
               → Falha: próximo
↓
5. FallbackLLM (todos os provedores)
    ↓
    → Sucesso: Retorna
    → Falha: RuntimeError
```

---

## 📊 Exemplo de Uso Completo

```python
from core.fallback_llm import FallbackLLM

# Inicializar
fallback = FallbackLLM()

# Caso 1: Usar provedor específico
try:
    result = fallback.classify(
        "Este é um texto para classificar",
        provider_name="openai_gpt35"
    )
    print(f"OpenAI resultado: {result}")
except ValueError as e:
    print(f"Provedor não configurado: {e}")

# Caso 2: Rotação automática
try:
    result = fallback.classify(
        "Classifique como positivo ou negativo: 'Ótimo produto!'"
    )
    print(f"Resultado (qualquer provedor): {result}")
except RuntimeError as e:
    print(f"Todos os provedores falharam: {e}")

# Caso 3: Usar em AIService
from core.ai_service import AIService

ai_service = AIService(db_client)
# AIService já integra FallbackLLM internamente
response = ai_service.classify("algum texto")
```

---

## 🐛 Troubleshooting

### ❌ "Nenhum provider de fallback configurado"

**Causa:** `FALLBACK_PROVIDERS` vazio ou não importado de `config.py`

**Solução:**
```python
# Em config.py, adicione:
FALLBACK_PROVIDERS = [
    {"name": "openai_gpt35", "api_key_env": "OPENAI_API_KEY"},
    {"name": "llama2", "api_key_env": None},
]
```

---

### ❌ "RuntimeError: Nenhum provider de fallback disponível"

**Causa:** Todos têm circuit breaker aberto (falhas repetidas)

**Solução:**
1. Checar saúde dos provedores:
```python
from core.circuit_breaker import ai_circuit_breaker
print(ai_circuit_breaker.get_status())  # Ver status de cada fallback_*
```

2. Resetar circuit breaker:
```python
ai_circuit_breaker.reset_provider("fallback_openai_gpt35")
```

3. Aguardar timeout de repouso (padrão: 60s)

---

### ❌ "Provider 'xyz' removido permanentemente"

**Causa:** Erro 401/402/403/404 ou API key ausente

**Solução:**
1. Verificar API key:
```bash
echo $OPENAI_API_KEY  # Ou qualquer provider
```

2. Verificar quota online (site do provedor)

3. Re-adicionar manualmente em `config.py` se corrigido

---

### ⚠️ "Timeout (15 segundos) excedido"

**Causa:** Rede lenta ou provedor sobrecarregado

**Solução:**
1. Aumentar timeout em método específico (linhas 63, 76, etc.):
```python
resp = requests.post(url, ..., timeout=30)  # Antes: 15
```

2. Usar provedor mais rápido (ex: Groq é ultra-fast)

---

## 📈 Performance e Escalabilidade

| Provedor | Latência Típica | Custo | Confiabilidade |
|----------|-----------------|-------|---|
| **Groq** | 100-500ms | 🟢 Barato | 🟢 Alta |
| **OpenRouter** | 200-800ms | 🟡 Médio | 🟢 Alta |
| **OpenAI** | 300-1000ms | 🔴 Caro | 🟢 Alta |
| **Anthropic Claude** | 400-1500ms | 🔴 Caro | 🟢 Muito Alta |
| **Gemini** | 300-1200ms | 🟡 Médio | 🟢 Alta |
| **DeepSeek** | 500-2000ms | 🟢 Barato | 🟡 Média |
| **Cohere** | 400-1200ms | 🟡 Médio | 🟡 Média |
| **EdenAI** | 500-2000ms | 🟡 Médio | 🟡 Média |

**Recomendação:** Priorizar Groq → OpenRouter → Claude para melhor balance

---

## 🔗 Referências

- **Arquivo Principal**: `/workspace/core/fallback_llm.py` (318 linhas)
- **Config**: `/workspace/core/config.py` (FALLBACK_PROVIDERS)
- **Circuit Breaker**: `/workspace/core/circuit_breaker.py`
- **AIService**: `/workspace/core/ai_service.py` (integração)

---

## ✅ Checklist de Setup

- [ ] `FALLBACK_PROVIDERS` configurado em `config.py`
- [ ] Todas as API keys definidas em `.env`
- [ ] Circuit breaker funcionando (ver `circuit_breaker.py`)
- [ ] Provedor rápido (Groq) com quota ativa
- [ ] Testado fallback manual: `fallback.classify("test", provider_name="openai_gpt35")`
- [ ] Testado rotação automática: `fallback.classify("test")`
- [ ] Logs verificados para mensagens de remoção de provedor

