# core/fallback_llm.py
"""Wrapper genérico para múltiplos provedores de IA de fallback.

O projeto já possui a configuração de provedores em ``core/config.py``
(como lista ``FALLBACK_PROVIDERS``). Este módulo lê essa configuração,
cria clientes simples (usando ``requests``) e disponibiliza um método
``classify`` que envia um prompt de classificação para o provedor
escolhido.

Para fins de teste rápido, caso a chamada real falhe (por falta de
bibliotecas específicas ou limites de quota), a função devolve um
resultado dummy baseado em palavras‑chave simples.
"""

import os
import logging
from typing import List, Dict, Any
import requests
from dotenv import load_dotenv

load_dotenv()

# Configura logger local
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Importa a lista de provedores configurada no projeto
try:
    from .config import FALLBACK_PROVIDERS
except Exception as e:
    logger.error(f"Não foi possível importar FALLBACK_PROVIDERS: {e}")
    FALLBACK_PROVIDERS = []


class FallbackLLM:
    """Gerencia a rotação entre provedores de IA.

    A ordem de prioridade vem de ``FALLBACK_PROVIDERS``.
    Cada provedor deve ter:
        - ``name``: identificador interno (ex.: "cohere")
        - ``api_key_env``: nome da variável de ambiente que contém a API‑key
          (pode ser ``None`` para serviços sem autenticação, como LLaMA‑2
          via Hugging Face Inference).
    """

    def __init__(self):
        self.providers_order: List[Dict[str, Any]] = [dict(provider) for provider in FALLBACK_PROVIDERS]
        if not self.providers_order:
            logger.warning("Nenhum provedor configurado em FALLBACK_PROVIDERS.")

    # ---------------------------------------------------------------------
    # Helpers de chamada HTTP genérica
    # ---------------------------------------------------------------------
    def _call_cohere(self, text: str, api_key: str) -> str:
        url = "https://api.cohere.com/v1/chat"
        payload = {
            "message": text,
            "model": "command-r",
            "temperature": 0.0,
            "max_tokens": 50,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("text", "")

    def _call_azure(self, text: str, api_key: str) -> str:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://YOUR_RESOURCE.openai.azure.com")
        url = f"{endpoint}/openai/deployments/gpt-35-turbo/chat/completions?api-version=2023-05-15"
        payload = {
            "messages": [{"role": "user", "content": text}],
            "max_tokens": 50,
        }
        headers = {"api-key": api_key, "Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    def _call_ai21(self, text: str, api_key: str) -> str:
        url = "https://api.ai21.com/studio/v1/j2-ultra/completions"
        payload = {
            "prompt": text,
            "maxTokens": 50,
            "temperature": 0.0,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("completions", [{}])[0].get("data", {}).get("text", "")

    def _call_fireworks(self, text: str, api_key: str) -> str:
        url = "https://api.fireworks.ai/inference/v1/completions"
        payload = {
            "model": "accounts/fireworks/models/llama-v2-7b-chat",
            "prompt": text,
            "max_tokens": 50,
            "temperature": 0.0,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("text", "")

    def _call_openai(self, text: str, api_key: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        payload = {"model": "gpt-4o", "messages": [{"role": "user", "content": text}]}
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _call_anthropic(self, text: str, api_key: str) -> str:
        url = "https://api.anthropic.com/v1/messages"
        payload = {"model": "claude-3-5-sonnet-20240620", "max_tokens": 1024, "messages": [{"role": "user", "content": text}]}
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    def _call_gemini(self, text: str, api_key: str, model: str) -> str:
        if not api_key:
            raise ValueError("GEMINI_API_KEY ausente.")
        model = model or "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": text}]}]}
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    def _call_groq(self, text: str, api_key: str, model: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        model = model or "llama-3.1-8b-instant" # updated groq model
        payload = {"model": model, "messages": [{"role": "user", "content": text}]}
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _call_zhipu(self, text: str, api_key: str, model: str) -> str:
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        model = model or "glm-4-flash"
        payload = {"model": model, "messages": [{"role": "user", "content": text}]}
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _call_cerebras(self, text: str, api_key: str, model: str) -> str:
        url = "https://api.cerebras.ai/v1/chat/completions"
        model = model or "llama3.1-8b"
        payload = {"model": model, "messages": [{"role": "user", "content": text}]}
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _call_edenai(self, text: str, api_key: str, provider: str) -> str:
        url = "https://api.edenai.run/v2/text/chat"
        provider = provider or "openai"
        payload = {
            "providers": provider,
            "text": text,
            "chatbot_global_action": "You are a helpful assistant.",
            "temperature": 0.0,
            "max_tokens": 1000
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data.get(provider, {}).get("generated_text", "")

    def _call_llama2(self, text: str) -> str:
        # Como fallback simples, retornamos o texto original marcado.
        return f"[LLAMA2] {text}"

    def _log_fallback_call(self, provider: str, status: str, payload: dict):
        """Salva um log de chamada na tabela fallback_logs no Supabase para auditoria financeira."""
        try:
            from core.supabase_client import get_supabase_client
            supabase = get_supabase_client()
            supabase.table('fallback_logs').insert({
                'provider': provider,
                'status': status,
                'payload': payload
            }).execute()
        except Exception as e:
            logger.warning(f"Não foi possível salvar fallback_log no Supabase: {e}")

    # ---------------------------------------------------------------------
    # API pública
    # ---------------------------------------------------------------------
    def classify(self, text: str, provider_name: str = None) -> str:
        """Classifica *text* usando o provedor selecionado.

        Se ``provider_name`` for ``None``, percorre a lista de prioridade.
        Em caso de erro, tenta o próximo provedor.
        """
        from core.circuit_breaker import ai_circuit_breaker

        if provider_name:
            provider = next((p for p in self.providers_order if p["name"] == provider_name), None)
            if not provider:
                raise ValueError(f"Provider '{provider_name}' não está configurado.")
            providers = [provider]
        else:
            providers = self.providers_order[:]

        if not providers:
            raise RuntimeError("Nenhum provider de fallback configurado.")

        available_providers = [
            provider for provider in providers
            if ai_circuit_breaker.can_execute(f"fallback_{provider['name']}")
        ]
        if not available_providers:
            raise RuntimeError("Nenhum provider de fallback disponível no momento (todos em circuito aberto ou removidos).")

        last_error = None
        for prov in available_providers:
            name = prov["name"]

            key_env = prov.get("api_key_env")
            model_name = prov.get("model")
            api_key = os.getenv(key_env) if key_env else None
            try:
                res = ""
                if name == "cohere":
                    res = self._call_cohere(text, api_key)
                elif name == "azure":
                    res = self._call_azure(text, api_key)
                elif name == "ai21":
                    res = self._call_ai21(text, api_key)
                elif name == "fireworks":
                    res = self._call_fireworks(text, api_key)
                elif name == "llama2":
                    res = self._call_llama2(text)
                elif name == "openai_gpt35":
                    res = self._call_openai(text, api_key)
                elif name == "anthropic_claude_instant":
                    res = self._call_anthropic(text, api_key)
                elif name == "zhipu_glm4":
                    res = self._call_zhipu(text, api_key, model_name)
                elif name == "cerebras_llama3":
                    res = self._call_cerebras(text, api_key, model_name)
                elif name == "eden_ai":
                    res = self._call_edenai(text, api_key, model_name)
                elif name == "cohere_command":
                    res = self._call_cohere(text, api_key)
                elif name == "fireworks_ai":
                    res = self._call_fireworks(text, api_key)
                elif name == "ai21_j2ultra":
                    res = self._call_ai21(text, api_key)
                else:
                    logger.warning(f"Implementação para provider '{name}' não encontrada; retornando dummy.")
                    res = f"[DUMMY-{name.upper()}] {text}"
                
                ai_circuit_breaker.record_success(f"fallback_{name}")
                self._log_fallback_call(name, "SUCCESS", {"model": model_name, "text_length": len(text)})
                return res

            except requests.exceptions.HTTPError as exc:
                status_code = exc.response.status_code
                logger.error(f"Erro HTTP {status_code} no provider {name}: {exc}")
                ai_circuit_breaker.record_failure(f"fallback_{name}", status_code)
                self._log_fallback_call(name, "ERROR", {"model": model_name, "error_type": "HTTPError", "status_code": status_code, "error": str(exc)})
                
                # Hard limit: remove provider from rotation
                if status_code in [400, 401, 402, 403, 404]:
                    logger.warning(f"🚨 [AI] Provider '{name}' com restrição permanente/gratuita esgotada ({status_code}). Removendo do fallback interno.")
                    if prov in self.providers_order:
                        self.providers_order.remove(prov)
                last_error = exc
                if provider_name:
                    raise exc
                continue
            except Exception as exc:
                logger.error(f"Erro ao usar provider {name}: {exc}")
                ai_circuit_breaker.record_failure(f"fallback_{name}")
                self._log_fallback_call(name, "ERROR", {"model": model_name, "error_type": "Exception", "error": str(exc)})
                
                # Config error: remove provider
                if "ausente" in str(exc).lower():
                    logger.warning(f"🚨 [AI] Provider '{name}' sem API Key configurada. Removendo do fallback interno.")
                    if prov in self.providers_order:
                        self.providers_order.remove(prov)
                last_error = exc
                if provider_name:
                    raise exc
                continue
        raise RuntimeError(f"Todas as chamadas de fallback falharam. Último erro: {last_error}")

    def upload_training_data(self, path: str) -> None:
        """Placeholder para futuro upload de datasets a um provedor."""
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Dataset não encontrado: {path}")
        logger.info(f"Dataset pronto para upload (funcionalidade ainda não implementada): {path}")
