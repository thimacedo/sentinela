"""
ScrapeAgent — Agente de IA Autônomo para Coleta de Dados
=========================================================
Diretório de isolamento lógico conforme GEMINI.md e AGENTS_SYNC.md.

Componentes:
    - agent.py: Loop cognitivo OODA (Observar, Orientar, Decidir, Agir)
    - tools.py: Registro de ferramentas do agente
    - dom_healing.py: Cura autônoma de seletores DOM via IA de visão
    - cognitive_prioritizer.py: Priorização de alvos baseada em métricas
    - persona_mode.py: Simulação de comportamento humano (experimental)
    - worker_adapter.py: Adaptador para integração com wk_coleta_instagram.py

Padrão seguido: core/autopilot/sre_agent.py (loop OODA com filtros determinísticos)
"""
from core.agent_scraper.agent import ScrapeAgent

__all__ = ["ScrapeAgent"]
