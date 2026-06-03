import os
import sys
import subprocess
import logging
from typing import List

# Try to import psutil for robust process handling. If unavailable, fallback to PowerShell.
try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("watchdog")

def _list_python_processes() -> List:
    """Return a list of Python processes with their PID, command line and create time.
    Falls back to a PowerShell query when psutil is not present.
    """
    processes = []
    if psutil:
        for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
            try:
                if proc.info["name"] and proc.info["name"].lower() in ("python.exe", "python"):
                    processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    else:
        # PowerShell returns JSON; we parse it safely.
        cmd = (
            "powershell -Command "
            "\"Get-CimInstance Win32_Process -Filter 'Name=\'python.exe\'' "
            "| Select-Object ProcessId, CommandLine, CreationDate "
            "| ConvertTo-Json\""
        )
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0 and result.stdout.strip():
            try:
                import json
                data = json.loads(result.stdout)
                # PowerShell may return a dict for a single object.
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    pid = int(item.get("ProcessId", 0))
                    cmdline = item.get("CommandLine", "")
                    # Convert CreationDate (e.g., 20260603090000.000000+000) to timestamp.
                    creation = item.get("CreationDate")
                    try:
                        # Simple heuristic: ignore timezone, take first 14 chars as YYYYMMDDhhmmss
                        ts = int(creation[:14])
                        # Convert to epoch seconds (approximate)
                        import datetime
                        dt = datetime.datetime.strptime(str(ts), "%Y%m%d%H%M%S")
                        create_time = dt.timestamp()
                    except Exception:
                        create_time = 0
                    # Build a mock object with needed attributes.
                    mock = type("Proc", (), {})()
                    mock.pid = pid
                    mock.info = {"pid": pid, "cmdline": [cmdline], "create_time": create_time}
                    processes.append(mock)
            except Exception as e:
                logger.warning(f"Failed to parse PowerShell process list: {e}")
    return processes


def _is_main_runner(proc) -> bool:
    """Return True if the process command line references ``main_runner.py``.
    Handles both list and string representations.
    """
    cmd = proc.info.get("cmdline")
    if not cmd:
        return False
    # ``cmd`` may be a list (psutil) or a single string (fallback).
    if isinstance(cmd, list):
        return any("main_runner.py" in part for part in cmd)
    return "main_runner.py" in cmd


def _choose_process_to_keep(processes: List) -> object:
    """Select the process that should remain alive.
    Preference order:
    1. The current process (the watchdog itself).
    2. The most recently started ``main_runner`` instance.
    """
    current_pid = os.getpid()
    # If the watchdog itself is a ``main_runner`` (unlikely), keep it.
    for proc in processes:
        if proc.pid == current_pid:
            return proc
    # Otherwise, keep the newest instance based on ``create_time``.
    if psutil:
        return max(processes, key=lambda p: p.info.get("create_time", 0))
    # Fallback: keep the first one (no reliable timestamp).
    return processes[0]


def _terminate(proc) -> None:
    """Terminate a process safely, logging the outcome."""
    try:
        if psutil:
            psutil.Process(proc.pid).terminate()
        else:
            subprocess.run(f"taskkill /PID {proc.pid} /F", shell=True, capture_output=True)
        logger.info(f"Killed duplicate process PID {proc.pid}")
    except Exception as exc:  # pragma: no cover
        logger.error(f"Failed to kill PID {proc.pid}: {exc}")


def main() -> None:
    """Watchdog entry point.
    Detects duplicate ``main_runner.py`` processes and terminates all but one.
    """
    all_python = _list_python_processes()
    runners = [p for p in all_python if _is_main_runner(p)]
    if not runners:
        logger.info("Nenhum processo main_runner.py encontrado.")
        return
    if len(runners) == 1:
        logger.info("Apenas um processo main_runner.py ativo – nada a fazer.")
        return
    logger.info(f"Encontrados {len(runners)} processos main_runner.py – iniciando limpeza.")
    keeper = _choose_process_to_keep(runners)
    logger.info(f"Mantendo processo PID {keeper.pid} ativo.")
    for proc in runners:
        if proc.pid != keeper.pid:
            _terminate(proc)

if __name__ == "__main__":
    main()
