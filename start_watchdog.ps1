# Script de Inicialização Padronizada - Sentinela Watchdog (v84.16)
cls
Set-Location "C:\Projetos\sentinela"
Write-Host "[INICIO] Iniciando SENTINELA DEMOCRATICA - WATCHDOG..." -ForegroundColor Cyan
uv run python watchdog/__init__.py --force
