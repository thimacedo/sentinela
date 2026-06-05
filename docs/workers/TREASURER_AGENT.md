# TreasurerAgent — Auditoria Financeira e Burn Rate
_version: 88.1 | last_updated: 2026-06-04 | status: Ativo (Sob Demanda)_

## 1. Visão Geral

**TreasurerAgent** é o subagente responsável pela saúde financeira e contábil do ecossistema Sentinela. Ele monitora a integridade dos saldos de Créditos Internos (CI), a conectividade com o gateway de pagamentos (Stripe) e calcula o custo operacional de IA em tempo real (Burn Rate).

### Informações Básicas
- **ID do Agente**: `treasurer-agent`
- **Localização**: `workers/financial/treasurer_agent.py`
- **Engine**: Supabase API + Stripe API
- **Trigger**: Disparado reativamente pelo `AIProcessorWorker` ou manualmente sob demanda.
- **Status**: 🟢 Ativo

---

## 2. Responsabilidades

### Responsabilidade 1: Auditoria de Saldos (Governance)
- Verifica a tabela `profiles` em busca de saldos negativos ou inconsistentes.
- Detecta possíveis falhas no sistema de débitos de CI durante o processamento em lote.

### Responsabilidade 2: Monitoramento de Gateway (Stripe)
- Testa a conectividade com o Stripe.
- Diferencia o modo de produção (Live Key) do modo de simulação (Mock/Test Key), garantindo que o checkout esteja sempre operacional.

### Responsabilidade 3: Cálculo de Burn Rate (IA Cost)
- Analisa a tabela `fallback_logs` das últimas 24 horas.
- Atribui pesos financeiros a cada provedor (Ollama=0, Mistral/Groq/Gemini=pago).
- Calcula o custo estimado em USD do processamento de inteligência.

### Responsabilidade 4: DRE Diário (Demonstrativo de Resultados)
- Consolida o fluxo de entrada (PURCHASE) e saída (CONSUMPTION) de CI.
- Gera um sumário de rentabilidade operacional diária nos logs.

---

## 3. Fluxo de Auditoria

1. **Saldos**: `SELECT id, saldo_ci FROM profiles WHERE saldo_ci < 0`.
2. **Stripe**: `stripe.Balance.retrieve()` para validar a integridade da conexão.
3. **Burn Rate**:
   - Agrupa chamadas de IA por provedor.
   - Aplica a tabela de preços dinâmica (PASA v88.1 Pricing).
   - Reporta o valor consolidado.

---

## 4. Tabela de Preços de IA (Estimada em USD)

| Provedor | Preço por Chamada |
|----------|-------------------|
| Ollama (Local) | $0.00000 |
| Google Gemini | $0.000075 |
| Mistral | $0.00010 |
| Groq Llama 3 | $0.00010 |
| OpenRouter | $0.00050 |
| OpenAI GPT-3.5 | $0.00150 |

---

## 5. Configuração

### Variáveis de Ambiente
- `STRIPE_API_KEY`: Necessária para auditoria real do gateway.
- `SERVICE_KEY`: Necessária para auditoria de todas as tabelas no Supabase.

### Monitoramento de Logs
```bash
tail -f logs/main_runner.json | grep TreasurerAgent
```

---

## 6. Integração

O `TreasurerAgent` é disparado automaticamente após ciclos de sucesso da IA para atualizar a telemetria financeira:

```python
# workers/orchestrator/orchestrator.py
if "ai-processor" in result.worker_id and result.classifier_success:
    asyncio.create_task(TreasurerAgent().run_financial_audit())
```

---

## 7. Troubleshooting

### Problema: "Burn rate reportado como zero"
1. Verifique se existem registros na tabela `fallback_logs` nas últimas 24 horas.
2. Certifique-se de que o `AIProcessorWorker` está enviando logs de uso para o banco.

### Problema: "Anomalias de saldo detectadas"
1. O TreasurerAgent reportará o ID do perfil com saldo negativo no log `error`.
2. A correção deve ser feita manualmente ou via script de compensação.

---

**Última Revisão**: 2026-06-04
**PASA Version**: v88.1
