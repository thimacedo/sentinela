# Script de Inicialização Padronizada - Sentinela Watchdog
cls
Set-Location "C:\Projetos\sentinela"
Write-Host "🚀 Iniciando SENTINELA DEMOCRÁTICA - WATCHDOG..." -ForegroundColor Cyan
uv run python watchdog/__init__.py --force
