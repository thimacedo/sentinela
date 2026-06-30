# -*- coding: utf-8 -*-
"""
core/dspy_integration.py - Integração do Framework DSPy no Sentinela (PASA v98.6)
══════════════════════════════════════════════════════════════════════════════
Orquestração declarativa de prompts, garantindo saídas estruturadas e tipadas
para classificação de hostilidade e discurso de ódio política pelo protocolo PASA.
Usa um adaptador de LM customizado para se beneficiar da resiliência do AI Service.
"""

import logging
import dspy
import json
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger("core.dspy_integration")

# ─────────────────────────────────────────────────────────────────────────────
# 1. ASSINATURA DSPY PARA O PROTOCOLO PASA v98.6 (MCA v2.3)
# ─────────────────────────────────────────────────────────────────────────────
class ClassificarComentarioPASA(dspy.Signature):
    """
    Você é um classificador especializado baseado no Método Vichi-Sentinela.
    Analise se o comentário de rede social contém hostilidade política ou discurso de ódio.
    Classifique rigorosamente de acordo com as categorias permitidas.
    Sua analise_pericial deve ser em Português Brasileiro (pt-BR) e NÃO deve usar a palavra "crime".
    """
    texto = dspy.InputField(desc="O comentário coletado das redes sociais, já decodificado.")
    contexto_forense = dspy.InputField(desc="Diretrizes do protocolo linguístico e regras de categorização.")
    
    is_hate = dspy.OutputField(desc="Valor booleano (True ou False) indicando se há hostilidade ou ataque.")
    categoria_ia = dspy.OutputField(desc="Uma das categorias: ODIO_IDENTITARIO, VIOLENCIA_GENERO, AMEACA, INSULTO_AD_HOMINEM, ATAQUE_INSTITUCIONAL, DANO_A_IMAGEM, NEUTRO.")
    confianca_ia = dspy.OutputField(desc="Float de 0.0 a 1.0 representando o grau de certeza da decisão.")
    analise_pericial = dspy.OutputField(desc="Explicação técnica curta do motivo da decisão, sem usar a palavra 'crime'.")


# ─────────────────────────────────────────────────────────────────────────────
# 2. ADAPTADOR DSPY LM CUSTOMIZADO PARA REUSAR O AI_SERVICE
# ─────────────────────────────────────────────────────────────────────────────
class SentinelaLM(dspy.LM):
    """
    Adaptador que mapeia chamadas do DSPy para a cascata de provedores do AI Service.
    Isso garante que o DSPy use o circuit breaker, a rotação de tokens, chaves e o log
    do Sentinela, aproveitando 100% da resiliência do projeto.
    """
    def __init__(self, ai_service_ref, force_local: bool = False, force_cloud: bool = False):
        super().__init__(model="sentinela-mesh")
        self.ai_service = ai_service_ref
        self.force_local = force_local
        self.force_cloud = force_cloud
        self.provider = "sentinela-mesh"

    def __call__(self, prompt: str, **kwargs) -> List[str]:
        """
        Executa a chamada síncrona/assíncrona através do loop de eventos.
        O DSPy espera receber uma lista de strings contendo a resposta da IA.
        """
        import asyncio
        
        async def _run():
            # Converte parâmetros do DSPy para o formato do nosso ai_service se necessário
            # Roda na cascata do ai_service usando _execute_provider_call direta ou classify_text
            # Para simplificar, escolhemos o provedor saudável da fila e rodamos o prompt gerado pelo DSPy
            self.ai_service._ensure_clients()
            
            allowed = self.ai_service.providers
            if self.force_cloud:
                allowed = [p for p in self.ai_service.providers if p["name"] != "ollama"]
            elif self.force_local:
                allowed = [p for p in self.ai_service.providers if p["name"] == "ollama"]
                
            if not allowed:
                allowed = self.ai_service.providers

            # Tenta executar nos provedores saudáveis
            for _ in range(len(allowed)):
                provider = allowed[self.ai_service.current_provider_idx % len(allowed)]
                self.ai_service.current_provider_idx += 1
                
                try:
                    # Executa a chamada física no provedor
                    content = await self.ai_service._execute_provider_call(
                        provider=provider,
                        system_prompt="Você é um assistente de IA estruturado. Responda estritamente ao prompt fornecido.",
                        user_content=prompt,
                        response_format="text" # O DSPy monta a estrutura no próprio prompt
                    )
                    if content:
                        return [content]
                except Exception as e:
                    self.ai_service._handle_provider_error(provider, e)
                    continue
                    
            # Fallback
            return ["{}"]

        # Executa no loop de eventos correntemente ativo
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Se o loop já está rodando (estamos em uma thread assíncrona do worker),
                # rodamos via task síncrona usando o helper loop.create_task ou run_coroutine_threadsafe
                import nest_asyncio
                nest_asyncio.apply() # Garante reentrância se necessário
            
            fut = asyncio.run_coroutine_threadsafe(_run(), loop)
            return fut.result(timeout=60.0)
        except RuntimeError:
            # Caso não haja event loop ativo na thread atual
            return asyncio.run(_run())


# ─────────────────────────────────────────────────────────────────────────────
# 3. ENGINE DE CLASSIFICAÇÃO BASEADA EM DSPY
# ─────────────────────────────────────────────────────────────────────────────
class DSpyClassifierEngine:
    def __init__(self, ai_service_ref):
        self.ai_service = ai_service_ref
        
    def _get_contexto(self, is_local: bool) -> str:
        """Obtém o contexto forense configurado no ai_service."""
        if is_local:
            return (
                "Diretrizes básicas de triagem local:\n"
                "- Categorias permitidas: NEUTRO (críticas comuns, elogios), LIXO (emojis ou sem nexo), "
                "SUSPEITO (qualquer sinal de ofensa grave, ameaça, ataque identitário ou desinformação a ser analisado na nuvem).\n"
                "- Atente para obfuscação léxica."
            )
        else:
            return self.ai_service._get_system_prompt(is_local=False)

    async def classificar(self, text: str, force_local: bool = False, force_cloud: bool = False) -> Dict[str, Any]:
        """
        Classifica um comentário usando a pipeline estruturada do DSPy.
        """
        # 1. Configura a LM temporária no DSPy com base nos filtros de execução
        lm_adaptada = SentinelaLM(self.ai_service, force_local=force_local, force_cloud=force_cloud)
        
        # 2. Inicializa o preditor do DSPy (usando ChainOfThought para maior acurácia pericial)
        with dspy.context(lm=lm_adaptada):
            contexto = self._get_contexto(is_local=force_local)
            predictor = dspy.ChainOfThought(ClassificarComentarioPASA)
            
            try:
                # Executa o preditor
                pred = predictor(texto=text, contexto_forense=contexto)
                
                # Valida e converte a resposta
                is_hate = str(pred.is_hate).strip().lower() in {"true", "yes", "1"}
                conf = 0.5
                try:
                    # Tenta extrair float da confiança
                    match = re.search(r"\d+\.\d+|\d+", str(pred.confianca_ia))
                    if match:
                        conf = float(match.group(0))
                        if conf > 1.0: conf = conf / 100.0 # Se veio em formato porcentagem
                except:
                    pass
                
                categoria = str(pred.categoria_ia).strip().upper()
                # Garante categoria permitida
                allowed = {"ODIO_IDENTITARIO", "VIOLENCIA_GENERO", "AMEACA", "INSULTO_AD_HOMINEM", "ATAQUE_INSTITUCIONAL", "DANO_A_IMAGEM", "NEUTRO", "LIXO", "SUSPEITO"}
                if categoria not in allowed:
                    categoria = "SUSPEITO" if force_local else "NEUTRO"
                
                analise = str(pred.analise_pericial).strip() or "Sem análise DSPy."
                # Remove referências de "crime" na análise pericial conforme regras
                analise = re.sub(r"\bcrime(s)?\b", "ato ilícito", analise, flags=re.IGNORECASE)

                return {
                    "is_hate": is_hate,
                    "categoria_ia": categoria,
                    "confianca_ia": conf,
                    "analise_pericial": analise,
                    "success": True
                }
            except Exception as e:
                logger.error(f"[DSPy:Engine] Falha ao processar predição DSPy: {e}")
                # Fallback resiliente
                return {
                    "is_hate": False,
                    "categoria_ia": "SUSPEITO" if force_local else "NEUTRO",
                    "confianca_ia": 0.5,
                    "analise_pericial": f"Erro predição DSPy: {e}",
                    "success": False
                }
