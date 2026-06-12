# ============================================================
# setup_heartbeat_task.ps1
# Registra o Sentinela Heartbeat Monitor no Windows Task Scheduler
# Executa a cada 15 minutos, inclusive no boot e sem login do usuário
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File scripts\setup_heartbeat_task.ps1
# ============================================================

$ErrorActionPreference = "Stop"

# ── Detecta caminhos ──────────────────────────────────────────
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir
$PythonExe   = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
$MonitorScript = Join-Path $ScriptDir "heartbeat_monitor.py"
$TaskName    = "SentinelaHeartbeat"

# Verifica se pythonw existe (usa python.exe como fallback)
if (-Not (Test-Path $PythonExe)) {
    $PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
}
if (-Not (Test-Path $PythonExe)) {
    Write-Host "❌ Erro: ambiente virtual não encontrado em .venv\Scripts\" -ForegroundColor Red
    Write-Host "   Execute: python -m venv .venv && .venv\Scripts\pip install -r requirements-workers.txt"
    exit 1
}
if (-Not (Test-Path $MonitorScript)) {
    Write-Host "❌ Erro: heartbeat_monitor.py não encontrado em scripts\" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Configurando Task Scheduler..."
Write-Host "   Python  : $PythonExe"
Write-Host "   Script  : $MonitorScript"
Write-Host "   Raiz    : $ProjectRoot"

# ── Remove tarefa anterior (idempotente) ──────────────────────
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "   Tarefa anterior removida."
}

# ── Cria a tarefa ─────────────────────────────────────────────
$action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$MonitorScript`"" `
    -WorkingDirectory $ProjectRoot

# Trigger 1: Repetição a cada 15 minutos, indefinidamente
$triggerRepeat = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 15) `
    -Once -At (Get-Date)
$triggerRepeat.RepetitionPattern.StopAtDurationEnd = $false

# Trigger 2: No boot do sistema (garante que roda mesmo após reinicialização)
$triggerBoot = New-ScheduledTaskTrigger -AtStartup

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

# Roda com privilégios elevados mas sem precisar de login ativo
$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

$task = Register-ScheduledTask `
    -TaskName $TaskName `
    -TaskPath "\Sentinela\" `
    -Action $action `
    -Trigger @($triggerRepeat, $triggerBoot) `
    -Settings $settings `
    -Principal $principal `
    -Description "Sentinela Heartbeat Monitor — detecta paradas de coleta e reinicia o sistema automaticamente (v98.2)"

if ($task) {
    Write-Host ""
    Write-Host "✅ Tarefa '$TaskName' registrada com sucesso!" -ForegroundColor Green
    Write-Host "   Execução: a cada 15 minutos + no boot do sistema"
    Write-Host "   Log     : $ProjectRoot\logs\heartbeat.log"
    Write-Host ""
    Write-Host "Para testar imediatamente:"
    Write-Host "   Start-ScheduledTask -TaskPath '\Sentinela\' -TaskName '$TaskName'"
    Write-Host ""
    Write-Host "Para remover:"
    Write-Host "   Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
} else {
    Write-Host "❌ Falha ao registrar a tarefa." -ForegroundColor Red
    exit 1
}
