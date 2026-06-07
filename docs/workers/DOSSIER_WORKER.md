# WkGeraDossies — Geração de Dossiês em PDF
_version: 90.8 | last_updated: 2026-06-07 | status: Ativo em Produção_

## 1. Visão Geral

**WkGeraDossies** é o worker especializado em **geração automatizada de dossiês em PDF** a partir de dados estruturados. Refatorado de script standalone para `BaseWorker` com ciclo de vida gerenciado.

### Informações Básicas
- **ID do Worker**: Dinâmico (e.g., `dossier-worker-01`)
- **Localização**: `workers/processors/wk_gera_dossies.py`
- **Classe**: `WkGeraDossies` (herda de `BaseWorker`)
- **Status**: 🟢 Ativo em produção

---

## 2. Responsabilidades

| Responsabilidade | Descrição |
|---|---|
| **Monitoramento de Fila** | Busca dossiês com status="Pendente" |
| **Detecção de Schema** | Identifica automaticamente nomes de colunas da tabela `dossies` |
| **Geração de PDF** | Converte dossiê via ReportGenerator |
| **Atualização de Status** | Marca como "Concluído" ou "Falhou" |
| **Registro de Erro** | Armazena mensagens de falha para debug |

---

## 3. Estados do Dossiê

| Estado | Significado |
|--------|-------------|
| **Pendente** | Aguardando processamento |
| **Processando** | Em geração de PDF |
| **Concluído** | PDF gerado com sucesso (`arquivo_path` preenchido) |
| **Falhou** | Erro durante geração (`error_log` preenchido) |

---

## 4. Execução

### Via Bandeja do Watchdog
```bash
python scripts/run_gera_dossies.py
```

### Via CLI
```bash
# O worker não é registrado por padrão no main_runner.py
# Dispara sob demanda via bandeja ou CLI
```

---

## 5. Monitoramento

```bash
tail -f logs/main_runner.json | grep "worker.dossier"
```

---

## 6. Troubleshooting

### "Conexão Supabase Falhou"
Verificar variáveis de ambiente:
```bash
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

### "ReportGenerator não encontrado"
O módulo `processing.report_generator` deve estar disponível. Verificar se existe:
```bash
ls processing/report_generator.py
```

### "Schema não detectado"
WkGeraDossies detecta automaticamente variações de schema (`status`/`situacao`, `arquivo_path`/`report_path`). Se a tabela `dossies` não existe, o worker retorna `error="no_tasks_available"`.

---

## 7. Dependências

- `workers/base/worker_base.py` — Classe base
- `workers/base/cycle_result.py` — Estrutura de resultado
- `processing.report_generator` — Geração de PDFs

---

## 8. Changelog

### v90.8 (2026-06-07)
- [x] Corrigido path: `workers/processors/wk_gera_dossies.py`
- [x] Classe renomeada: `WkGeraDossies`
- [x] Migrado para BaseWorker moderno (PASA v88.0)

---

**Última Revisão**: 2026-06-07
**PASA Version**: v88.0 → v90.8
