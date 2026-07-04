#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINELA — TESTE E CORRECAO INTEGRADO v2.0
Executa testes em todos os modulos criticos.
"""

import argparse
import ast
import json
import os
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

BASE_PATH = Path('.')
LOG_FILE = BASE_PATH / 'logs' / 'test_suite.json'
REPORT_FILE = BASE_PATH / 'logs' / 'test_report.md'

CRITICAL_FILES = {
    'scraper': 'core/instagram_scraper_v2.py',
    'queue': 'core/queue_manager.py',
    'agent': 'sentinela_autonomous_agent.py',
    'adapter': 'core/agent_scraper/worker_adapter.py',
    'worker': 'workers/scrapers/wk_coleta_instagram.py',
    'behavior': 'core/behavior_engine.py',
    'circuit': 'core/circuit_breaker.py',
    'exceptions': 'core/exceptions.py',
    'sre_health': 'workers/sre/cj_sre_health_check.py',
    'sre_backup': 'workers/sre/cj_sre_backup_sync.py',
    'dlq': 'workers/sre/wk_dead_letter_queue.py',
    'session_heal': 'workers/sre/wk_sessao_autonoma.py',
    'ntfy': 'core/ntfy.py',
}

class Colors:
    OK = '\033[92m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    INFO = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

    @classmethod
    def disable(cls):
        for attr in ['OK', 'WARN', 'FAIL', 'INFO', 'END', 'BOLD']:
            setattr(cls, attr, '')

def log(level, msg):
    color = {'OK': Colors.OK, 'WARN': Colors.WARN, 'FAIL': Colors.FAIL, 'INFO': Colors.INFO}
    prefix = color.get(level, '')
    print(f'{prefix}[{level}]{Colors.END} {msg}')

def ensure_logs_dir():
    (BASE_PATH / 'logs').mkdir(exist_ok=True)

def write_log(entry):
    ensure_logs_dir()
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False, default=str) + '\n')

def test_syntax(file_key, file_path):
    path = BASE_PATH / file_path
    errors = []
    if not path.exists():
        return False, [f'Arquivo nao encontrado: {path}']
    try:
        source = path.read_text(encoding='utf-8')
        ast.parse(source)
    except SyntaxError as e:
        return False, [f'Erro de sintaxe na linha {e.lineno}: {e.msg}']
    except Exception as e:
        return False, [f'Erro ao ler arquivo: {e}']
    return True, []

def test_scraper_patches():
    path = BASE_PATH / CRITICAL_FILES['scraper']
    errors = []
    if not path.exists():
        return False, ['instagram_scraper_v2.py nao encontrado']
    source = path.read_text(encoding='utf-8')
    checks = {
        'ExtractionFailure': 'Classe ExtractionFailure nao encontrada',
        'raise ExtractionFailure': 'Levantamento de ExtractionFailure nao encontrado',
        'success': 'Campo success nao encontrado no retorno',
        'self.stats =': 'Reset de self.stats nao encontrado',
    }
    for pattern, msg in checks.items():
        if pattern not in source:
            errors.append(msg)
    return len(errors) == 0, errors

def test_queue_patches():
    path = BASE_PATH / CRITICAL_FILES['queue']
    errors = []
    if not path.exists():
        return False, ['queue_manager.py nao encontrado']
    source = path.read_text(encoding='utf-8')
    checks = {
        'release_atomic': 'Metodo release_atomic nao encontrado',
        '_ensure_queue_populated': 'Metodo _ensure_queue_populated nao encontrado',
        'rotate_target': 'Metodo rotate_target nao encontrado',
    }
    for pattern, msg in checks.items():
        if pattern not in source:
            errors.append(msg)
    return len(errors) == 0, errors

def test_agent_patches():
    path = BASE_PATH / CRITICAL_FILES['agent']
    errors = []
    if not path.exists():
        return False, ['sentinela_autonomous_agent.py nao encontrado']
    source = path.read_text(encoding='utf-8')
    checks = {
        '_ensure_queue_populated': 'Chamada a _ensure_queue_populated nao encontrada',
        'IDLE': 'Estado IDLE nao encontrado',
        'agent.status.json': 'Persistencia de agent.status.json nao encontrada',
        'save_status': 'Metodo save_status nao encontrado',
    }
    for pattern, msg in checks.items():
        if pattern not in source:
            errors.append(msg)
    if 'ExtractionFailure' not in source:
        errors.append('Agente nao trata ExtractionFailure do scraper')
    return len(errors) == 0, errors

def test_sre_workers():
    errors = []
    sre_files = ['sre_health', 'sre_backup', 'dlq', 'session_heal']
    for key in sre_files:
        path = BASE_PATH / CRITICAL_FILES[key]
        if not path.exists():
            errors.append(f'{CRITICAL_FILES[key]} nao encontrado')
        else:
            try:
                source = path.read_text(encoding='utf-8')
                ast.parse(source)
            except SyntaxError as e:
                errors.append(f'Erro de sintaxe em {CRITICAL_FILES[key]}: {e.msg}')
    return len(errors) == 0, errors

def test_ntfy_mime():
    path = BASE_PATH / CRITICAL_FILES['ntfy']
    errors = []
    if not path.exists():
        return False, ['core/ntfy.py nao encontrado']
    source = path.read_text(encoding='utf-8')
    if 'encode' not in source and 'Header' not in source:
        errors.append('Possivel falta de encoding MIME para headers')
    return len(errors) == 0, errors

def test_dependencies():
    errors = []
    required = [('requests', 'requests'), ('playwright', 'playwright'), ('supabase', 'supabase')]
    for module, name in required:
        try:
            __import__(module)
        except ImportError:
            errors.append(f'DEPENDENCIA OBRIGATORIA FALTANDO: {name}')
    optional = [('pystray', 'pystray (para icone na bandeja)'), ('PIL', 'pillow (para icone na bandeja)')]
    for module, name in optional:
        try:
            __import__(module)
        except ImportError:
            log('WARN', f'Dependencia opcional nao encontrada: {name}')
    return len(errors) == 0, errors

def test_supabase_connection():
    errors = []
    try:
        import requests
    except ImportError:
        errors.append('Biblioteca requests nao instalada')
        return False, errors
    env_path = BASE_PATH / '.env'
    env = {}
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip(chr(39)+chr(34))
    supabase_url = env.get('SUPABASE_URL', env.get('NEXT_PUBLIC_SUPABASE_URL', ''))
    supabase_key = env.get('SUPABASE_SERVICE_KEY', env.get('SUPABASE_KEY', ''))
    if not supabase_url or not supabase_key:
        errors.append('SUPABASE_URL ou SUPABASE_KEY nao encontrados no .env')
        return False, errors
    try:
        url = f'{supabase_url}/rest/v1/fila_coleta'
        params = {'select': 'count', 'limit': '1'}
        headers = {'apikey': supabase_key, 'Authorization': f'Bearer {supabase_key}'}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code not in (200, 201):
            errors.append(f'Supabase retornou status {r.status_code}: {r.text[:100]}')
    except Exception as e:
        errors.append(f'Falha ao conectar no Supabase: {e}')
    return len(errors) == 0, errors

def test_circuit_breaker():
    path = BASE_PATH / CRITICAL_FILES['circuit']
    errors = []
    if not path.exists():
        return False, ['circuit_breaker.py nao encontrado']
    source = path.read_text(encoding='utf-8')
    required_methods = ['can_execute', 'record_success', 'record_failure']
    for method in required_methods:
        if f'def {method}' not in source:
            errors.append(f'Metodo {method}() nao encontrado no CircuitBreaker')
    return len(errors) == 0, errors

def fix_missing_imports():
    fixes = []
    scraper_path = BASE_PATH / CRITICAL_FILES['scraper']
    if scraper_path.exists():
        source = scraper_path.read_text(encoding='utf-8')
        if 'from core.exceptions import ExtractionFailure' not in source:
            if 'class ExtractionFailure' not in source:
                lines = source.split('\n')
                import_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        import_idx = i + 1
                lines.insert(import_idx, 'from core.exceptions import ExtractionFailure')
                scraper_path.write_text('\n'.join(lines), encoding='utf-8')
                fixes.append('scraper: Adicionado import de ExtractionFailure')
    return fixes

def run_all_tests():
    tests = {
        'syntax_scraper': lambda: test_syntax('scraper', CRITICAL_FILES['scraper']),
        'syntax_queue': lambda: test_syntax('queue', CRITICAL_FILES['queue']),
        'syntax_agent': lambda: test_syntax('agent', CRITICAL_FILES['agent']),
        'syntax_sre': test_sre_workers,
        'syntax_ntfy': test_ntfy_mime,
        'scraper_patches': test_scraper_patches,
        'queue_patches': test_queue_patches,
        'agent_patches': test_agent_patches,
        'circuit_breaker': test_circuit_breaker,
        'dependencies': test_dependencies,
        'supabase_connection': test_supabase_connection,
    }
    results = {}
    for name, test_fn in tests.items():
        log('INFO', f'Executando: {name}...')
        try:
            success, errors = test_fn()
            results[name] = {'success': success, 'errors': errors}
            if success:
                log('OK', f'{name}: PASSOU')
            else:
                log('FAIL', f'{name}: FALHOU - {len(errors)} erro(s)')
                for err in errors:
                    print(f'       -> {err}')
        except Exception as e:
            results[name] = {'success': False, 'errors': [str(e)]}
            log('FAIL', f'{name}: EXCECAO - {e}')
    return results

def generate_report(results):
    total = len(results)
    passed = sum(1 for r in results.values() if r['success'])
    failed = total - passed
    lines = ['# Relatorio de Testes - Sentinela', f'**Data:** {datetime.now(timezone.utc).isoformat()}', f'**Total:** {total} testes | PASSARAM {passed} | FALHARAM {failed}', '', '## Resultados por Modulo', '']
    for name, result in results.items():
        icon = 'PASSOU' if result['success'] else 'FALHOU'
        lines.append(f'### {icon} {name}')
        if result['errors']:
            lines.append('**Erros:**')
            for err in result['errors']:
                lines.append(f'- {err}')
        else:
            lines.append('**Sem erros.**')
        lines.append('')
    report = '\n'.join(lines)
    ensure_logs_dir()
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    return report

def main():
    parser = argparse.ArgumentParser(description='Sentinela - Test Suite Integrada v2.0')
    parser.add_argument('--all', action='store_true', help='Executar todos os testes')
    parser.add_argument('--test-sre', action='store_true', help='Testar workers de SRE')
    parser.add_argument('--test-scraper', action='store_true', help='Testar scraper')
    parser.add_argument('--test-queue', action='store_true', help='Testar queue manager')
    parser.add_argument('--test-agent', action='store_true', help='Testar agente autonomo')
    parser.add_argument('--test-deps', action='store_true', help='Testar dependencias')
    parser.add_argument('--fix-all', action='store_true', help='Aplicar correcoes automaticas')
    parser.add_argument('--no-color', action='store_true', help='Desabilitar cores')
    args = parser.parse_args()

    if args.no_color:
        Colors.disable()

    if not any([args.all, args.test_sre, args.test_scraper, args.test_queue, args.test_agent, args.test_deps, args.fix_all]):
        print('Uso: python sentinela_test_suite.py --all')
        print('     python sentinela_test_suite.py --fix-all')
        sys.exit(1)

    print('='*70)
    print('SENTINELA - TESTE E CORRECAO INTEGRADO v2.0')
    print('='*70)
    print()

    results = {}

    if args.all or args.test_scraper:
        log('INFO', '=== TESTES DO SCRAPER ===')
        s, e = test_syntax('scraper', CRITICAL_FILES['scraper'])
        results['syntax_scraper'] = {'success': s, 'errors': e}
        s, e = test_scraper_patches()
        results['scraper_patches'] = {'success': s, 'errors': e}

    if args.all or args.test_queue:
        log('INFO', '=== TESTES DO QUEUE MANAGER ===')
        s, e = test_syntax('queue', CRITICAL_FILES['queue'])
        results['syntax_queue'] = {'success': s, 'errors': e}
        s, e = test_queue_patches()
        results['queue_patches'] = {'success': s, 'errors': e}

    if args.all or args.test_agent:
        log('INFO', '=== TESTES DO AGENTE AUTONOMO ===')
        s, e = test_syntax('agent', CRITICAL_FILES['agent'])
        results['syntax_agent'] = {'success': s, 'errors': e}
        s, e = test_agent_patches()
        results['agent_patches'] = {'success': s, 'errors': e}

    if args.all or args.test_sre:
        log('INFO', '=== TESTES DE SRE ===')
        s, e = test_sre_workers()
        results['sre_workers'] = {'success': s, 'errors': e}
        s, e = test_ntfy_mime()
        results['ntfy_mime'] = {'success': s, 'errors': e}

    if args.all or args.test_deps:
        log('INFO', '=== TESTES DE DEPENDENCIAS ===')
        s, e = test_dependencies()
        results['dependencies'] = {'success': s, 'errors': e}
        s, e = test_supabase_connection()
        results['supabase_connection'] = {'success': s, 'errors': e}
        s, e = test_circuit_breaker()
        results['circuit_breaker'] = {'success': s, 'errors': e}

    print()
    print('='*70)
    print('RESUMO DOS TESTES')
    print('='*70)

    for name, result in results.items():
        icon = 'OK' if result['success'] else 'FALHOU'
        print(f'  {icon} {name:<40} {icon}')

    total = len(results)
    passed = sum(1 for r in results.values() if r['success'])
    print()
    print(f'Total: {total} | Passaram: {passed} | Falharam: {total - passed}')

    if args.fix_all:
        print()
        print('='*70)
        print('APLICANDO CORRECOES AUTOMATICAS')
        print('='*70)
        fixes = fix_missing_imports()
        if fixes:
            for fix in fixes:
                print(f'  OK {fix}')
        else:
            print('  Nenhuma correcao necessaria.')

    report = generate_report(results)
    print()
    print('='*70)
    print(f'Relatorio salvo em: {REPORT_FILE}')
    print('='*70)

    write_log({
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'total_tests': total,
        'passed': passed,
        'failed': total - passed,
        'results': {k: {'success': v['success']} for k, v in results.items()},
    })

    sys.exit(0 if passed == total else 1)

if __name__ == '__main__':
    main()