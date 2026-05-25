# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-24 | branch: main_

## Status Operacional (v64.0)

| Subsistema | Status | Observacao |
|---|---|---|
| Frontend (nextjs) | Operacional | SAAS Premium v60.2: Multitema (Light/Dark), War Room c/ Sidebar, Dossiês/Rede congelados |
| AI-SRE Advisor | Operacional | v53.1: Diagnóstico via open-mistral-nemo funcional (Gatilho automático em vazios) |
| Coleta Independente (IGWorkerV2) | Operacional | Motor V2 v64.0: Fast-Skip (Pins/Idade), Validação Biográfica via IA, Buffer Zero-Loss |
| Persistencia Supabase | OK | v63.0: Fallback de emergência para schema mismatch, Data Scrubbing (Anti-Null) |
| Classificacao IA | OK | Cascade v63.1: MCA v2.2 calibrado anti-falsos positivos, Temperatura 0.0, Confiança Local 0.85 |
| Fila de Coleta | Operacional | v59.0: Prioridade Dinâmica (Termômetro Quente/Frio), Hibernação 12h, Atomic Locking |
| Watchdog | Operacional | v61.7: Ancoragem Global, Modernizado com 'uv', Padronização de Logs IA (📊) |

## Descobertas Tecnicas (2026-05-24)
- **Validação de Identidade Biográfica (v64.0)**: O motor V2 agora captura Bio/Nome e utiliza a IA para validar se o perfil pertence ao alvo real, auto-eliminando perfis inautênticos ou paródias (ex: `@alexandre` inativado como inautêntico).
- **Ajuste Fino de Precisão Forense (v63.1)**: Refinamento do MCA v2.2 para neutralizar retórica política legítima (ex: "Lula na cadeia" = Neutro) e reduzir temperatura para 0.0, eliminando falsos positivos.
- **Normalização de Confiança Local (v62.4)**: Modelos locais (Ollama) agora possuem confiança base de 0.85, unificando a telemetria do dashboard.
- **Fast-Skip de Posts (v62.1)**: Otimização extrema no Playwright, ignorando posts fixados e velhos (>7d) diretamente no grid, economizando 40% do tempo de ciclo.
- **Ancoragem Global (v61.3)**: Implementação de auto-anchoring em todos os scripts, permitindo execução robusta de qualquer diretório do sistema operacional.
- **Frontend SAAS Multitema (v60.2)**: Nova interface premium com suporte nativo a Temas Claro/Escuro e gamificação para conversão (Créditos/Premium).
- **Termômetro de Atividade (v59.0)**: Fila de alvos agora prioriza perfis "Quentes" (alta frequência de postagem) e hiberna perfis "Frios".
- **Protocolo Zero Loss (v58.3)**: Buffer local em JSON garante que nenhuma inteligência seja perdida em crashes de rede ou banco.
- **Detecção de Bots (v56.0)**: Camada de densidade léxica identifica comportamento coordenado antes da IA, sinalizando robôs de campanha automaticamente.

## Arquitetura de Integridade

```
[Watchdog v61.7] (Guardião UV + Ancoragem)
  └── [Orchestrator v57.4] (Atomic Locking + Memory Flush + Zombie Cleanup)
        ├── [QueueManager v55.1] (Multi-tier + Fairness + Termômetro)
        └── [IGWorkerV2 v64.0] (Scraper Playwright + Identity AI Check)
              ├── [Buffer v58.3] (Zero-Loss local storage)
              └── [AIService v63.1] (Cascade Híbrido + MCA v2.2 Refinado)
```

## Fila de Coleta (Prioridade Dinâmica)

1. **Manual**: Precedência total.
2. **Prioritária**: `fila_coleta` (1=Máxima, order by prioridade ASC, created_at ASC).
3. **Justiça (Fairness 25%)**: Rotação forçada via candidatos ativos.
4. **Hibernação**: Alvos sem dados recentes (7d) ou inativos ficam fora por 12h.
