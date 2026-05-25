# Especificação Técnica: Sentinela Autopilot (v70.0)

O módulo **Autopilot** é a camada de inteligência operacional projetada para gerenciar o ciclo de vida completo do sistema sem intervenção humana, aplicando conceitos de SRE (Site Reliability Engineering) e Engenharia de Prompt Dinâmica.

## 1. Arquitetura de Camadas (PASA L3)

1.  **L1 - Workers (Execução):** Raspagem, normalização e classificação.
2.  **L2 - Watchdog (Guardião):** Monitoramento de processos e reinício básico.
3.  **L3 - Autopilot (Comando):** Diagnóstico semântico de falhas, auto-patching e gestão de custos.

## 2. Componentes do Autopilot

### A. Health Engine (Monitoramento Semântico)
Diferente de um monitor de processo comum, o Health Engine analisa a *qualidade* da saída:
*   **Detecção de Vazios:** Se a taxa de `extracted=0` for superior a 20% em 1 hora, o Autopilot assume que houve mudança no DOM ou bloqueio de IP.
*   **Análise de Sentimento do Log:** Identifica mensagens de erro que indicam fadiga de sessão ou mudanças de política do alvo.

### B. Intervention Engine (Auto-Patching)
Utiliza IA para corrigir o próprio código:
*   **Hot-Fixes:** Se um scraper falha por `SelectorNotFoundError`, o Autopilot captura o HTML da página, envia para o Gemini para identificar o novo seletor e aplica um `replace` direto no código fonte.
*   **Session Resurrection:** Gerencia o pool de sessões, testando e descartando cookies expirados automaticamente.

### C. Resource Optimizer (Gestão de Tokens e Custos)
*   **Controle de Quota:** Alterna entre modelos (Gemini Pro -> Flash -> Llama Local) baseando-se no saldo restante e na complexidade do texto.
*   **Adaptive Jitter:** Ajusta os tempos de espera baseando-se na latência de resposta do alvo para maximizar a furtividade.

## 3. Fluxo de Decisão (Loop OODA)

1.  **Observar:** Coleta métricas de extração, erros de banco e logs de IA.
2.  **Orientar:** Compara o estado atual com a "Baseline de Operação Saudável".
3.  **Decidir:** Escolhe entre: *Restart*, *Hibernação*, *Troca de Sessão* ou *Correção de Código*.
4.  **Agir:** Executa a intervenção via Shell/Replace e valida o resultado.

## 4. Estrutura de Arquivos Proposta

```
core/autopilot/
├── __init__.py
├── manager.py          # Orquestrador central
├── diagnostician.py    # IA que analisa logs e HTML
├── patcher.py          # Aplica correções no código-fonte
└── policies/
    ├── recovery.json   # Regras de reinício
    └── strategy.json   # Regras de troca de modelos de IA
```

## 5. Implementação de Referência (Pseudo-código)

```python
class Autopilot:
    async def pulse(self):
        metrics = await self.health_check()
        if metrics.failure_rate > 0.5:
            analysis = await self.diagnostician.analyze_last_errors()
            if analysis.type == "DOM_CHANGE":
                await self.patcher.fix_selector(analysis.target_html)
                await self.restart_system()
            elif analysis.type == "IP_BLOCK":
                await self.activate_proxy_rotation()
```

---
**Status:** Design concluído. Pronto para prototipagem do `manager.py`.
