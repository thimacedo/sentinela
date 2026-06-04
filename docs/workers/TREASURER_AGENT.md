# TreasurerAgent - Documentação de Auditoria Financeira e Fechamento

**Versão:** PASA v88.1  
**Arquivo Fonte:** [treasurer_agent.py](file:///c:/projetos/sentinela/workers/financial/treasurer_agent.py)  
**Status:** ✅ Operacional (Subagente reativo / sob demanda)  
**Última Atualização:** Junho 2026

---

## 🎯 Visão Geral

O **TreasurerAgent** é o subagente financeiro responsável por garantir a integridade das transações do ecossistema de créditos de informação (CI) no Sentinela. Suas responsabilidades principais incluem:

- **Auditoria de Saldos**: Rastrear perfis com saldos inconsistentes ou negativos para evitar exploits no uso de créditos.
- **Verificação de Gateway**: Testar e garantir que a integração com o gateway de pagamentos (Stripe) está operacional.
- **Fechamento Diário (DRE)**: Calcular e consolidar o fluxo de compras de créditos (Inflow) contra o consumo de recursos (Outflow) nas últimas 24 horas.

Sua execução é disparada de forma assíncrona em background na conclusão de processamentos de IA ou via requisições explícitas do dashboard administrativo.

---

## 🔄 Fluxo de Processamento

```
┌────────────────────────────────────────────────────────┐
│ 1. INICIALIZAÇÃO                                       │
│   • Prepara variáveis de controle e status             │
└────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────┐
│ 2. AUDITORIA DE SALDOS (profiles)                      │
│   • Executa consulta por perfis com saldo_ci < 0       │
│   • Registra anomalias como erro para ação corretiva   │
└────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────┐
│ 3. CONECTIVIDADE GATEWAY (Stripe)                      │
│   • Testa conectividade real contra API do Stripe      │
│   • Fallback automático para modo Mock/Beta se key ok  │
└────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────┐
│ 4. FECHAMENTO DIÁRIO DRE (Uma vez por dia)             │
│   • Agrega transações PURCHASE (+) e CONSUMPTION (-)   │
│   • Loga receita líquida consolidada das últimas 24h   │
└────────────────────────────────────────────────────────┘
```

---

## 🧬 Métodos Principais

### `run_financial_audit()`
Executa o pipeline completo de auditoria financeira.
- **Retorno**: Um dicionário contendo estatísticas da auditoria (sucesso do ciclo, anomalias encontradas, conectividade Stripe).

### `audit_balances()`
Busca no Supabase e identifica perfis que consumiram créditos além de seus limites.

### `check_stripe_connectivity()`
Realiza uma chamada leve para listar o saldo da conta e verificar se a API Key do Stripe está válida.

### `generate_daily_financial_report()`
Agrega transações do dia anterior por tipo para compor o fluxo de caixa consolidado.
