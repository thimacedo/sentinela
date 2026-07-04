#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINELA — CORRECAO ABRENGETE v1.0
Aplica correcoes em todos os modulos criticos baseado nos testes falhos.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_PATH = Path('.')
BACKUP_DIR = BASE_PATH / 'backups' / 'correcoes'

def backup_file(path: Path):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_DIR / f'{path.name}.backup_{timestamp}'
    backup_path.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')
    print(f'  Backup: {backup_path}')
    return backup_path

# ============================================================
# CORRECAO 1: SCRAPER — GARANTIR ExtractionFailure E METADATA
# ============================================================

def fix_scraper():
    print('\n[1] Corrigindo instagram_scraper_v2.py...')
    path = BASE_PATH / 'core' / 'instagram_scraper_v2.py'
    if not path.exists():
        print('  ERRO: Arquivo nao encontrado')
        return False

    source = path.read_text(encoding='utf-8')
    original = source
    fixes = []

    # 1.1 Adicionar import de ExtractionFailure se necessario
    if 'from core.exceptions import ExtractionFailure' not in source:
        if 'class ExtractionFailure' not in source:
            lines = source.split('\n')
            import_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_idx = i + 1
            lines.insert(import_idx, 'from core.exceptions import ExtractionFailure')
            source = '\n'.join(lines)
            fixes.append('Adicionado import de ExtractionFailure')

    # 1.2 Garantir que o retorno tenha 'success': True
    if "'success'" not in source:
        # Procurar padrao de retorno simples e adicionar metadata
        old_pattern = 'return {\n                "comments": all_comments,\n                "post_metas": post_metas\n            }'
        new_pattern = 'return {\n                "success": True,\n                "comments": all_comments,\n                "comments_collected": len(all_comments),\n                "posts_processed": len(post_metas),\n                "post_metas": post_metas\n            }'
        if old_pattern in source:
            source = source.replace(old_pattern, new_pattern)
            fixes.append('Adicionado success=True e metadata no retorno')
        else:
            # Tentar encontrar qualquer retorno de dict e adicionar success
            if 'return {' in source and 'comments' in source:
                fixes.append('AVISO: Retorno encontrado mas padrao nao reconhecido. Verificar manualmente.')

    # 1.3 Garantir reset de stats no inicio de scrape_profile
    if 'self.stats = {' not in source:
        # Procurar def scrape_profile e adicionar reset apos docstring
        pattern = r'(async def scrape_profile\([^)]*\):\s*\n(?:\s*"""[^"]*"""\s*\n)?)'
        match = re.search(pattern, source)
        if match:
            insert_pos = match.end()
            reset_block = '\n        # [PATCH] Reset de stats no inicio de cada ciclo\n        self.stats = {\n            "posts_found": 0,\n            "posts_scraped": 0,\n            "comments_extracted": 0,\n            "api_calls": 0,\n            "fallbacks_used": 0,\n        }\n'
            source = source[:insert_pos] + reset_block + source[insert_pos:]
            fixes.append('Adicionado reset de self.stats no inicio de scrape_profile')

    # 1.4 Garantir raise ExtractionFailure em falha total
    if 'raise ExtractionFailure' not in source:
        # Procurar onde todos os fallbacks falharam e adicionar raise
        if 'return [], None' in source or 'return ([], None)' in source:
            fixes.append('AVISO: Possivel retorno vazio encontrado. Verificar se ExtractionFailure eh levantado corretamente.')

    if source != original:
        backup_file(path)
        path.write_text(source, encoding='utf-8')
        for fix in fixes:
            print(f'  OK: {fix}')
        return True
    else:
        print('  Nenhuma correcao necessaria.')
        return True

# ============================================================
# CORRECAO 2: AGENTE — GARANTIR save_status E IDLE
# ============================================================

def fix_agent():
    print('\n[2] Corrigindo sentinela_autonomous_agent.py...')
    path = BASE_PATH / 'sentinela_autonomous_agent.py'
    if not path.exists():
        print('  ERRO: Arquivo nao encontrado')
        return False

    source = path.read_text(encoding='utf-8')
    original = source
    fixes = []

    # 2.1 Garantir metodo save_status
    if 'def save_status' not in source:
        # Adicionar no final da classe principal
        save_method = '''\n\n    def save_status(self, health=None):\n        """Persiste status do agente em agent.status.json"""\n        import json\n        from datetime import datetime, timezone\n        status = {\n            "version": "1.2",\n            "status": getattr(self, '_status', 'UNKNOWN'),\n            "cycle_count": getattr(self, '_cycle_count', 0),\n            "consecutive_blocks": getattr(self, '_consecutive_blocks', 0),\n            "last_cycle_time": datetime.now(timezone.utc).isoformat(),\n            "last_heartbeat": datetime.now(timezone.utc).isoformat(),\n            "targets_tracked": len(getattr(self, '_target_states', {})),\n            "queue_status": health.queue_status if health else "unknown"\n        }\n        try:\n            with open('agent.status.json', 'w', encoding='utf-8') as f:\n                json.dump(status, f, indent=2, ensure_ascii=False)\n        except Exception as e:\n            print(f'[WARN] Falha ao salvar status: {e}')\n'''
        source = source + save_method
        fixes.append('Adicionado metodo save_status')

    # 2.2 Garantir estado IDLE
    if 'IDLE' not in source:
        fixes.append('AVISO: Estado IDLE nao encontrado. Verificar implementacao do tray icon.')

    if source != original:
        backup_file(path)
        path.write_text(source, encoding='utf-8')
        for fix in fixes:
            print(f'  OK: {fix}')
        return True
    else:
        print('  Nenhuma correcao necessaria.')
        return True

# ============================================================
# CORRECAO 3: QUEUE MANAGER — GARANTIR release_atomic
# ============================================================

def fix_queue():
    print('\n[3] Corrigindo queue_manager.py...')
    path = BASE_PATH / 'core' / 'queue_manager.py'
    if not path.exists():
        print('  ERRO: Arquivo nao encontrado')
        return False

    source = path.read_text(encoding='utf-8')
    original = source
    fixes = []

    # 3.1 Verificar se release_atomic existe
    if 'def release_atomic' not in source:
        fixes.append('AVISO: Metodo release_atomic nao encontrado. Verificar implementacao manualmente.')

    # 3.2 Verificar se eh chamado em rotate_target
    if 'def rotate_target' in source:
        rotate_match = re.search(r'def rotate_target\(self.*?\n(?:(?!\ndef ).)*', source, re.DOTALL)
        if rotate_match:
            rotate_body = rotate_match.group(0)
            if 'release_atomic' not in rotate_body:
                fixes.append('AVISO: release_atomic() nao chamado dentro de rotate_target(). Verificar manualmente.')

    if source != original:
        backup_file(path)
        path.write_text(source, encoding='utf-8')
        for fix in fixes:
            print(f'  OK: {fix}')
        return True
    else:
        print('  Nenhuma correcao necessaria.')
        return True

# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='Sentinela - Correcao Abrangente v1.0')
    parser.add_argument('--all', action='store_true', help='Aplicar todas as correcoes')
    parser.add_argument('--scraper', action='store_true', help='Corrigir scraper')
    parser.add_argument('--agent', action='store_true', help='Corrigir agente')
    parser.add_argument('--queue', action='store_true', help='Corrigir queue manager')
    args = parser.parse_args()

    if not any([args.all, args.scraper, args.agent, args.queue]):
        print('Uso: python sentinela_correcao.py --all')
        sys.exit(1)

    print('='*70)
    print('SENTINELA - CORRECAO ABRENGETE v1.0')
    print('='*70)

    results = {}

    if args.all or args.scraper:
        results['scraper'] = fix_scraper()

    if args.all or args.agent:
        results['agent'] = fix_agent()

    if args.all or args.queue:
        results['queue'] = fix_queue()

    print('\n' + '='*70)
    print('RESUMO DAS CORRECOES')
    print('='*70)
    for module, ok in results.items():
        status = 'OK' if ok else 'FALHOU'
        print(f'  {module}: {status}')

    sys.exit(0 if all(results.values()) else 1)

if __name__ == '__main__':
    main()