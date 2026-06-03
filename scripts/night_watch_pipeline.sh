#!/bin/bash
# SENTINELA | Operação Night Watch Pipeline
# Consolidado de manutenção e processamento noturno

set -e

# Configura o PYTHONPATH para garantir que os módulos locais sejam encontrados
export PYTHONPATH=$PYTHONPATH:.

echo "--------------------------------------------------"
echo "🚀 [Night Watch] Iniciando Pipeline de Rotina..."
echo "🕒 Horário: $(date)"
echo "--------------------------------------------------"

echo "Fase 1: Limpeza de Processos Fantasmas..."
python tools/cleanup_ghosts.py

echo "Fase 2: Processamento de Backlog de Inteligência..."
python tools/process_backlog.py

echo "Fase 3: Scanner documental..."
python scripts/run_scanner_agent.py --once

echo "--------------------------------------------------"
echo "✅ [Night Watch] Pipeline concluído com sucesso!"
echo "🕒 Fim: $(date)"
echo "--------------------------------------------------"
