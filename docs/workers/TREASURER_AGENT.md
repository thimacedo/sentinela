# SaAuditoriaFinanceira — Auditoria Financeira e Burn Rate
_version: 90.8 | last_updated: 2026-06-07 | status: Ativo (Sob Demanda)_

## 1. Visão Geral

**SaAuditoriaFinanceira** é o subagente responsável pela saúde financeira e contábil do ecossistema Sentinela. Ele monitora a integridade dos saldos de Créditos Internos (CI), a conectividade com o gateway de pagamentos (Stripe) e calcula o custo operacional de IA em tempo real (Burn Rate).

### Informações Básicas
- **ID do Subagente**: `sa-auditoria-financeira`
- **Localização**: `workers/financial/sa_auditoria_financeira.py`
- **Classe**: `SaAuditoriaFinanceira`
- **Engine**: Supabase API + Stripe API
- **Trigger**: Disparado reativamente pelo `WkClassificaComentarios` via EventBus, ou sob demanda via bandeja do watchdog
- **Status**: 🟢 Ativo sob demanda

---

## 2. Responsabilidades

### 1. Auditoria de Saldos (Governance)
- Verifica a tabela `profiles` em busca de saldos negativos ou inconsistentes
- Detecta possíveis falhas no sistema de débitos de CI durante o processamento em lote

### 2. Monitoramento de Gateway (Stripe)
- Testa a conectividade com o Stripe
- Diferencia o modo de produção (Live Key) do modo de simulação (Mock/Test Key)
- Protegido por `STRIPE_ALLOW_MOCK_PAYMENTS` para validação local

### 3. Cálculo de Burn Rate (IA Cost)
- Analisa a tabela `fallback_logs` das últimas 24 horas
- Atribui pesos financeiros a cada provedor (Ollama=0, Sabia-4/Mistral/Groq=pago)
- Calcula o custo estimado em USD do processamento de inteligência

### 4. DRE Diário (Demonstrativo de Resultados)
- Consolida o fluxo de entrada (PURCHASE) e saída (CONSUMPTION) de CI
- Gera um sumário de rentabilidade operacional diária nos logs

---

## 3. Fluxo de Auditoria

1. **Saldos**: `SELECT id, saldo_ci FROM profiles WHERE saldo_ci < 0`
2. **Stripe**: `stripe.Balance.retrieve()` para validar a integridade da conexão
3. **Burn Rate**:
   - Agrupa chamadas de IA por provedor
   - Aplica a tabela de preços dinâmica
   - Reporta o valor consolidado em USD

---

## 4. Tabela de Preços de IA (USD)

| Provedor | Preço/1M tokens (aprox.) |
|----------|-------------------------|
| Ollama (Local) | $0.00 |
| Sabia-4 (Maritaca) | $0.10 |
| Mistral | $0.10 |
| Groq Llama 3 | $0.10 |
| OpenRouter | $0.50 |

---

## 5. Execução

### Sob Demanda (Bandeja do Watchdog)
```bash
python scripts/run_auditoria_financeira.py
```
Menu: `SUBAGENTES (SA)` → `Executar SaAuditoriaFinanceira`

### Via Código
```python
from workers.financial.sa_auditoria_financeira import SaAuditoriaFinanceira

sa = SaAuditoriaFinanceira()
result = await sa.run_financial_audit()
print(result)
```

---

## 6. Monitoramento

```bash
tail -f logs/main_runner.json | grep SaAuditoriaFinanceira
```

---

## 7. Troubleshooting

### "Burn rate reportado como zero"
1. Verificar se existem registros na tabela `fallback_logs` nas últimas 24h
2. Verificar se o `WkClassificaComentarios` está enviando logs de uso para o banco

### "Anomalias de saldo detectadas"
- SaAuditoriaFinanceira reportará o ID do perfil com saldo negativo
- Correção deve ser feita manualmente ou via script de compensação

---

## 8. Changelog

### v90.8 (2026-06-07)
- [x] Corrigido path: `workers/financial/sa_auditoria_financeira.py`
- [x] Classe renomeada: `SaAuditoriaFinanceira`
- [x] Cascade de IA atualizada com Sabia-4

---

**Última Revisão**: 2026-06-07
**PASA Version**: v88.1 → v90.8
