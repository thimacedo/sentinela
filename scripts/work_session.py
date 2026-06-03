
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import os, sys, time, subprocess
from datetime import datetime

# Ensure the project root is in the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

log_path = os.path.join(project_root, "logs", "worker.log")

def log_msg(msg):
    """Logs a message to both the console and the worker.log file with a timestamp."""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}\n"

    # Print to console
    print(line, end="")
    
    # Append to log file
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print(f"Error writing to log file {log_path}: {e}", file=sys.stderr)

def run_command_and_log(command: str, script_name: str):
    """
    Executes a command and streams its stdout and stderr to both the console and the log file.
    """
    log_msg(f"--- Iniciando {script_name} ---")
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = project_root
        env["PYTHONUNBUFFERED"] = "1"
        env["DEBUG"] = "pw:api,pw:browser"
        # Força o Python do subprocesso a usar UTF-8
        env["PYTHONIOENCODING"] = "utf-8"
        
        proc = subprocess.Popen( 
            command, 
            shell=True, 
            env=env,
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            bufsize=1, # Line buffered
            universal_newlines=False # Read bytes to handle encoding manually
        )

        # Usamos um loop de leitura de bytes para evitar erros de decodificação fatal
        while True:
            line_bytes = proc.stdout.readline()
            if not line_bytes and proc.poll() is not None:
                break
            
            if line_bytes:
                # Tenta decodificar como utf-8, cai para cp1252 se falhar (comum no Windows)
                try:
                    output_line = line_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    output_line = line_bytes.decode('cp1252', errors='replace')
                
                print(output_line, end="")
                try:
                    os.makedirs(os.path.dirname(log_path), exist_ok=True)
                    with open(log_path, "a", encoding="utf-8", errors='replace') as f:
                        f.write(output_line)
                except Exception as e:
                    print(f"Error writing to log file {log_path}: {e}", file=sys.stderr)
        
        proc.wait()
        if proc.returncode != 0:
            log_msg(f"!!! {script_name} finalizado com erro (código {proc.returncode}) !!!")
        else:
            log_msg(f"--- {script_name} concluído com sucesso ---")

    except FileNotFoundError:
        log_msg(f"!!! Erro: Comando '{command}' não encontrado. Verifique o caminho e as permissões. !!!")
    except Exception as e:
        log_msg(f"!!! Erro inesperado ao executar '{command}': {e} !!!")

def run_routine():
    """Executa a sequência de tarefas da rotina diária."""
    scripts_to_run = [
        ("Limpeza", "python tools/cleanup_ghosts.py"),
        ("Raspagem", "python main_runner.py"),
        ("IA / Classificação", "python tools/process_backlog.py"),
        ("Scanner Documental", "python scripts/run_scanner_agent.py --once")
    ]
    
    for name, cmd in scripts_to_run:
        run_command_and_log(cmd, name)

if __name__ == "__main__":
    log_msg("🛡️ MODO WORK SESSION ATIVADO. Pressione Ctrl+C para parar.")
    try:
        while True:
            run_routine()
            sleep_duration = 1800  # 30 minutos
            log_msg(f"⏳ Ciclo concluído. Dormindo por {sleep_duration // 60} minutos...")
            time.sleep(sleep_duration)
    except KeyboardInterrupt:
        log_msg("🛑 Work Session encerrada manualmente. Bom descanso!")
        sys.exit(0)
    except Exception as e:
        log_msg(f"!!! Erro inesperado no loop principal: {e}. Reiniciando em 60 segundos. !!!")
        time.sleep(60)