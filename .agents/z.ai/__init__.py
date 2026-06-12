"""
"Agente de IA Autônono para Coleta de Dados
=========================================================
Pacote lógico isolado em .agents/z.ai para o ScrapeAgent.

Componentes:
    - agent.py: Loop cognitivo OODA (Observar, Orientar, Decidir, Agir)
    - tools.py: Registro de ferramentas do agente
    - dom_healing.py: Cura autônoma de seletores DOM via IA de visão
    - cognitive_prioritizer.py: Priorização de alvos baseada em métricas
    - persona_mode.py: Simulação de comportamento humano (experimental)
    - worker_adapter.py: Adaptador para integração com wk_coleta_instagram.py

Integração com core:
    O adaptador aceita quaisquer scraper/ai_service existentes e
    NÃO exige importação hardcoded para core.agent_scraper.* para
    manter compatibilidade com o diretório atual.
"""
from .agent import ScrapeAgent

__all__ = ["ScrapeAgent"]
