# -*- coding: utf-8 -*-
"""
deploy_frontend.py — Compila o frontend Next.js de produção, copia os arquivos
estáticos para a raiz do repositório e dispara o deploy integrado na Vercel.
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

# ── raiz do projeto ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent

# Configurar logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("deploy_frontend")

FRONTEND_DIR = ROOT / "frontend"
OUT_DIR = FRONTEND_DIR / "out"

def clean_root_static_files():
    """Remove arquivos estáticos compilados de builds anteriores na raiz para evitar sujeira."""
    log.info("Limpando arquivos estáticos antigos da raiz...")
    
    # Arquivos e diretórios Next.js típicos
    static_dirs = [ROOT / "_next", ROOT / "_not-found"]
    static_files = [
        ROOT / "index.html",
        ROOT / "dashboard.html",
        ROOT / "404.html",
        ROOT / "_not-found.html",
        ROOT / "index.txt",
        ROOT / "dashboard.txt",
        ROOT / "404.txt",
        ROOT / "file.svg",
        ROOT / "globe.svg",
        ROOT / "next.svg",
        ROOT / "vercel.svg",
        ROOT / "window.svg"
    ]
    
    for d in static_dirs:
        if d.exists() and d.is_dir():
            shutil.rmtree(d)
            log.info(f"Diretório removido: {d.name}")
            
    for f in static_files:
        if f.exists() and f.is_file():
            f.unlink()
            log.info(f"Arquivo removido: {f.name}")

def build_nextjs():
    """Executa a compilação estática do Next.js."""
    log.info("Iniciando build do Next.js na pasta frontend...")
    try:
        # Executa npm run build
        res = subprocess.run(
            ["npm", "run", "build"],
            cwd=str(FRONTEND_DIR),
            capture_output=True,
            text=True,
            shell=True,
            check=True
        )
        log.info("Next.js compilado com sucesso.")
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"Erro na compilação do Next.js:\n{e.stderr or e.stdout}")
        return False

def copy_static_to_root():
    """Copia a pasta 'out' compilada do Next.js para a raiz do projeto."""
    log.info(f"Copiando arquivos de {OUT_DIR} para a raiz {ROOT}...")
    if not OUT_DIR.exists():
        log.error("Diretório de build 'out' não encontrado no frontend!")
        return False
        
    for item in OUT_DIR.iterdir():
        dest = ROOT / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            if dest.exists():
                dest.unlink()
            shutil.copy2(item, dest)
            
    log.info("Cópia concluída.")
    return True

def restore_vercel_json():
    """Atualiza o vercel.json para apontar apenas chamadas de API, deixando a raiz para o Next.js."""
    log.info("Restaurando vercel.json...")
    vercel_config = {
        "version": 2,
        "cleanUrls": True,
        "rewrites": [
            {
                "source": "/api/(.*)",
                "destination": "/api/index.py"
            }
        ],
        "functions": {
            "api/**/*.py": {
                "maxDuration": 15,
                "includeFiles": [
                    "api/**",
                    "processing/**",
                    "core/**"
                ]
            }
        }
    }
    
    config_file = ROOT / "vercel.json"
    config_file.write_text(json.dumps(vercel_config, indent=2), encoding="utf-8")
    log.info("vercel.json restaurado com sucesso.")

def deploy_to_vercel():
    """Dispara o deploy final de produção na Vercel."""
    log.info("Disparando deploy na Vercel...")
    try:
        res = subprocess.run(
            ["npx", "vercel", "--prod", "--yes"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            shell=True,
            check=True
        )
        log.info("Deploy na Vercel concluído com sucesso!")
        # Exibe as URLs do log final
        for line in res.stdout.splitlines():
            if "Production:" in line or "Aliased:" in line or "Success!" in line:
                log.info(line)
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"Erro no deploy da Vercel:\n{e.stderr or e.stdout}")
        return False

def main():
    log.info("=" * 60)
    log.info("Iniciando Pipeline de Deploy Integrado Frontend + API")
    log.info("=" * 60)
    
    clean_root_static_files()
    
    if not build_nextjs():
        sys.exit(1)
        
    if not copy_static_to_root():
        sys.exit(1)
        
    restore_vercel_json()
    
    if not deploy_to_vercel():
        sys.exit(1)
        
    log.info("=" * 60)
    log.info("DEPLOY INTEGRADO CONCLUÍDO COM SUCESSO!")
    log.info("=" * 60)

if __name__ == "__main__":
    main()
