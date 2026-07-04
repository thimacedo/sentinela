#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINELA - PATCH GRACEFUL SHUTDOWN v1.0
Adiciona signal handler para liberar locks ao encerrar o agente.
"""

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE_PATH = Path('.')
AGENT_FILE = BASE_PATH / 'sentinela_autonomous_agent.py'
BACKUP_DIR = BASE_PATH / 'backups' / 'graceful_shutdown'

# Codigo do patch como lista de linhas
PATCH_LINES = [
    '# ============================================================',
    '# [PATCH v1.0] GRACEFUL SHUTDOWN - Libera locks ao encerrar',
    '# ============================================================',
    'import signal',
    'import atexit',
    'import sys',
    '',
    '_agent_instance = None  # Referencia ao agente para shutdown',
    '',
    'def _register_agent_instance(agent):',
    '    """Registra a instancia do agente para graceful shutdown."""',
    '    global _agent_instance',
    '    _agent_instance = agent',
    '',
    'def _graceful_shutdown():',
    '    """Libera locks e salva estado ao encerrar."""',
    '    global _agent_instance',
    '    if _agent_instance is not None:',
    '        try:',
    '            if hasattr(_agent_instance, "current_target") and _agent_instance.current_target:',
    '                target = _agent_instance.current_target',
    '                if hasattr(_agent_instance, "queue_manager") and _agent_instance.queue_manager:',
    '                    import asyncio',
    '                    try:',
    '                        loop = asyncio.get_event_loop()',
    '                        if loop.is_running():',
    '                            asyncio.create_task(_agent_instance.queue_manager.release_atomic(target))',
    '                        else:',
    '                            loop.run_until_complete(_agent_instance.queue_manager.release_atomic(target))',
    '                    except:',
    '                        pass',
    '                print(f"[Shutdown] Lock liberado para @{target.username}")',
    '            if hasattr(_agent_instance, "save_status"):',
    '                _agent_instance.save_status()',
    '                print("[Shutdown] Status salvo em agent.status.json")',
    '        except Exception as e:',
    '            print(f"[Shutdown] Erro ao liberar lock: {e}")',
    '',
    'def _signal_handler(signum, frame):',
    '    """Handler para sinais de terminacao."""',
    '    sig_name = {signal.SIGINT: "SIGINT (Ctrl+C)", signal.SIGTERM: "SIGTERM (kill)"}.get(signum, f"Signal {signum}")',
    '    print(f"[Signal] Recebido {sig_name}, encerrando graciosamente...")',
    '    _graceful_shutdown()',
    '    sys.exit(0)',
    '',
    'atexit.register(_graceful_shutdown)',
    'try:',
    '    signal.signal(signal.SIGINT, _signal_handler)',
    '    signal.signal(signal.SIGTERM, _signal_handler)',
    'except (ValueError, OSError):',
    '    pass',
    '',
    '# ============================================================',
    '# FIM DO PATCH GRACEFUL SHUTDOWN',
    '# ============================================================',
]

def backup_file(path: Path):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_DIR / f'{path.name}.backup_{timestamp}'
    shutil.copy2(path, backup_path)
    print(f'Backup criado: {backup_path}')
    return backup_path

def apply_patch():
    print('=' * 70)
    print('APLICANDO PATCH: GRACEFUL SHUTDOWN')
    print('=' * 70)
    print()

    if not AGENT_FILE.exists():
        print(f'ERRO: Arquivo nao encontrado: {AGENT_FILE}')
        return False

    source = AGENT_FILE.read_text(encoding='utf-8')

    if '_graceful_shutdown' in source:
        print('Patch ja aplicado. Pulando.')
        return True

    lines = source.split(chr(10))

    last_import_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            last_import_idx = i + 1

    new_lines = lines[:last_import_idx] + [''] + PATCH_LINES + [''] + lines[last_import_idx:]
    source_patched = chr(10).join(new_lines)

    init_pattern = r'(def __init__\(self[^)]*\):\s*\n)'
    match = re.search(init_pattern, source_patched)

    if match:
        insert_pos = match.end()
        register_code = '        # [PATCH] Registrar instancia para graceful shutdown' + chr(10) + '        _register_agent_instance(self)' + chr(10)
        source_patched = source_patched[:insert_pos] + register_code + source_patched[insert_pos:]
        print('Adicionado _register_agent_instance(self) no __init__')
    else:
        print('AVISO: Nao encontrou __init__ da classe principal. Verificar manualmente.')

    backup_file(AGENT_FILE)
    AGENT_FILE.write_text(source_patched, encoding='utf-8')
    print()
    print('Patch aplicado com sucesso!')
    print('O agente agora libera locks automaticamente ao encerrar.')
    return True

def main():
    parser = argparse.ArgumentParser(description='Sentinela - Patch Graceful Shutdown')
    parser.add_argument('--dry-run', action='store_true', help='Mostrar o que seria alterado')
    args = parser.parse_args()

    if args.dry_run:
        print('Modo dry-run: codigo do patch:')
        for line in PATCH_LINES:
            print(line)
        return

    success = apply_patch()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()