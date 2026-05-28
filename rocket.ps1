# SENTINELA ROCKET LAUNCHER (v1.0)
# Uso: ./rocket.ps1 "Instrução para os Agentes"

param (
    [Parameter(Mandatory=$true)]
    [string]$Instruction
)

$SyncFile = "AGENTS_SYNC.md"
$Timestamp = Get-Date -Format "dd/MM/yyyy HH:mm:ss"

# 1. Injeta a instrução no Canal de Sincronia
$NewCommand = @"

---
## 🚀 NOVA MISSÃO UNIFICADA ($Timestamp)
**Solicitação do Usuário:** $Instruction
**Status:** AGUARDANDO AGENTES...
"@

Add-Content -Path $SyncFile -Value $NewCommand

Write-Host "🚀 Missão injetada em $SyncFile" -ForegroundColor Cyan

# 2. Aciona o Orquestrador (Gemini CLI)
# Nota: Como eu já estou rodando aqui, você verá minha resposta neste terminal.

# 3. Aciona o Executor (Antigravity CLI) via comando externo ou lembrete
Write-Host "🛰️ Agente Antigravity notificado via canal de sincronia." -ForegroundColor Yellow
Write-Host "⚡ Iniciando processamento paralelo..." -ForegroundColor Green

# Se você quiser que o script abra um novo terminal para o Antigravity automaticamente:
# Start-Process powershell -ArgumentList "-NoExit", "-Command", "antigravity --sync-file AGENTS_SYNC.md"
