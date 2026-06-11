import os
import sys
import socket
import subprocess
import signal
import time
import threading
import asyncio
from PIL import Image
import pystray
from pystray import MenuItem as item

# v52.8: Força invisibilidade total da janela do processo no Windows
if os.name == 'nt':
    try:
        import ctypes
        # Oculta a janela do console/gui se ela existir
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        hWnd = kernel32.GetConsoleWindow()
        if hWnd:
            user32.ShowWindow(hWnd, 0) # 0 = SW_HIDE
    except Exception:
        pass

# Garante o PYTHONPATH
WATCHDOG_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(WATCHDOG_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from watchdog import guard, run_web_server, state, AUTOPILOT_ENABLED
from watchdog.voyant import run_voyant_server
try:
    from core.autopilot.manager import autopilot
except ImportError:
    pass

ICON_PATH = os.path.join(PROJECT_ROOT, "logo_branco.png")
DASHBOARD_URL = "http://localhost:8001"

def open_dashboard(icon=None, item=None):
    try:
        import webbrowser
        webbrowser.open(DASHBOARD_URL)
    except Exception as e:
        print(f"[Tray] Falha ao abrir dashboard: {e}")

def run_audit_agent(icon=None, item=None):
    AUDIT_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "run_audit_agent.py")
    try:
        subprocess.Popen(
            ["cmd", "/k", sys.executable, AUDIT_SCRIPT, "--sample-size", "15"],
            cwd=PROJECT_ROOT,
            creationflags=0x08000000, # CREATE_NO_WINDOW (v50.1)
        )
    except Exception as e:
        print(f"[Tray] Erro ao disparar AuditAgent: {e}")

def run_revisao_online(icon=None, item=None):
    REVISAO_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "run_revisao_online.py")
    try:
        subprocess.Popen(
            ["cmd", "/k", sys.executable, REVISAO_SCRIPT],
            cwd=PROJECT_ROOT,
            creationflags=0x08000000, # CREATE_NO_WINDOW (v50.1)
        )
    except Exception as e:
        print(f"[Tray] Erro ao disparar SaRevisaoOnline: {e}")

def run_mineracao_redes(icon=None, item=None):
    MINERACAO_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "run_mineracao_redes.py")
    try:
        subprocess.Popen(
            ["cmd", "/k", sys.executable, MINERACAO_SCRIPT],
            cwd=PROJECT_ROOT,
            creationflags=0x08000000, # CREATE_NO_WINDOW (v50.1)
        )
    except Exception as e:
        print(f"[Tray] Erro ao disparar SaMineracaoRedes: {e}")

def run_auditoria_financeira(icon=None, item=None):
    FINANCEIRA_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "run_auditoria_financeira.py")
    try:
        subprocess.Popen(
            ["cmd", "/k", sys.executable, FINANCEIRA_SCRIPT],
            cwd=PROJECT_ROOT,
            creationflags=0x08000000, # CREATE_NO_WINDOW (v50.1)
        )
    except Exception as e:
        print(f"[Tray] Erro ao disparar SaAuditoriaFinanceira: {e}")

def run_dossier_agent(icon=None, item=None):
    DOSSIER_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "run_dossier_agent.py")
    if not os.path.exists(DOSSIER_SCRIPT):
        print("[Tray] DossierAgent não implementado.")
        return
    try:
        subprocess.Popen(
            ["cmd", "/k", sys.executable, DOSSIER_SCRIPT],
            cwd=PROJECT_ROOT,
            creationflags=0x08000000, # CREATE_NO_WINDOW (v50.1)
        )
    except Exception as e:
        print(f"[Tray] Erro ao disparar DossierAgent: {e}")

def run_scanner_agent(icon=None, item=None):
    SCANNER_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "run_scanner_agent.py")
    try:
        subprocess.Popen(
            ["cmd", "/k", sys.executable, SCANNER_SCRIPT, "--once"],
            cwd=PROJECT_ROOT,
            creationflags=0x08000000, # CREATE_NO_WINDOW (v50.1)
        )
    except Exception as e:
        print(f"[Tray] Erro ao disparar ScannerAgent: {e}")

def run_coleta_instagram(icon=None, item=None):
    SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "run_coleta_instagram.py")
    try:
        subprocess.Popen(
            ["cmd", "/k", sys.executable, SCRIPT],
            cwd=PROJECT_ROOT,
            creationflags=0x08000000, # CREATE_NO_WINDOW (v50.1)
        )
    except Exception as e:
        print(f"[Tray] Erro ao disparar WkColetaInstagram: {e}")

def run_pesquisa_alvos(icon=None, item=None):
    SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "run_pesquisa_alvos.py")
    try:
        subprocess.Popen(
            ["cmd", "/k", sys.executable, SCRIPT],
            cwd=PROJECT_ROOT,
            creationflags=0x08000000, # CREATE_NO_WINDOW (v50.1)
        )
    except Exception as e:
        print(f"[Tray] Erro ao disparar WkPesquisaAlvos: {e}")

def run_classifica_comentarios(icon=None, item=None):
    SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "run_classifica_comentarios.py")
    try:
        subprocess.Popen(
            ["cmd", "/k", sys.executable, SCRIPT],
            cwd=PROJECT_ROOT,
            creationflags=0x08000000, # CREATE_NO_WINDOW (v50.1)
        )
    except Exception as e:
        print(f"[Tray] Erro ao disparar WkClassificaComentarios: {e}")

def run_analisa_tendencias(icon=None, item=None):
    SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "run_analisa_tendencias.py")
    try:
        subprocess.Popen(
            ["cmd", "/k", sys.executable, SCRIPT],
            cwd=PROJECT_ROOT,
            creationflags=0x08000000, # CREATE_NO_WINDOW (v50.1)
        )
    except Exception as e:
        print(f"[Tray] Erro ao disparar WkAnalisaTendencias: {e}")

def run_aplica_sugestoes(icon=None, item=None):
    SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "run_aplica_sugestoes.py")
    try:
        subprocess.Popen(
            ["cmd", "/k", sys.executable, SCRIPT],
            cwd=PROJECT_ROOT,
            creationflags=0x08000000, # CREATE_NO_WINDOW (v50.1)
        )
    except Exception as e:
        print(f"[Tray] Erro ao disparar WkAplicaSugestoes: {e}")

def run_gera_alertas(icon=None, item=None):
    SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "run_gera_alertas.py")
    try:
        subprocess.Popen(
            ["cmd", "/k", sys.executable, SCRIPT],
            cwd=PROJECT_ROOT,
            creationflags=0x08000000, # CREATE_NO_WINDOW (v50.1)
        )
    except Exception as e:
        print(f"[Tray] Erro ao disparar WkGeraAlertas: {e}")

def run_consulta_banco(icon=None, item=None):
    SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "run_consulta_banco.py")
    try:
        subprocess.Popen(
            ["cmd", "/k", sys.executable, SCRIPT],
            cwd=PROJECT_ROOT,
            creationflags=0x08000000, # CREATE_NO_WINDOW (v50.1)
        )
    except Exception as e:
        print(f"[Tray] Erro ao disparar SaConsultaBanco: {e}")

def run_diagnostica_sistemas(icon=None, item=None):
    SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "run_diagnostica_sistemas.py")
    try:
        subprocess.Popen(
            ["cmd", "/k", sys.executable, SCRIPT],
            cwd=PROJECT_ROOT,
            creationflags=0x08000000, # CREATE_NO_WINDOW (v50.1)
        )
    except Exception as e:
        print(f"[Tray] Erro ao disparar SaDiagnosticaSistemas: {e}")

def run_doc_fetcher(icon=None, item=None):
    SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "run_doc_fetcher.py")
    try:
        subprocess.Popen(
            ["cmd", "/k", sys.executable, SCRIPT],
            cwd=PROJECT_ROOT,
            creationflags=0x08000000, # CREATE_NO_WINDOW (v50.1)
        )
    except Exception as e:
        print(f"[Tray] Erro ao disparar DocFetcher: {e}")

def toggle_autopilot_action(icon=None, item=None):
    try:
        from core.autopilot.manager import autopilot
        if autopilot:
            autopilot.is_active = not autopilot.is_active
            state.add_log("info", f"[Watchdog] 🤖 Autopilot L3 alterado para: {'ATIVADO' if autopilot.is_active else 'DESATIVADO'}")
            if icon:
                icon.menu = build_menu()
    except Exception as e:
        print(f"[Tray] Erro ao alternar autopilot: {e}")

def build_menu():
    try:
        from core.autopilot.manager import autopilot
    except ImportError:
        autopilot = None

    def get_autopilot_status():
        if AUTOPILOT_ENABLED and autopilot and autopilot.is_active:
            return "Ativo (L3)"
        return "Inativo"

    return pystray.Menu(
        item(lambda text: f"Status: {state.status}", lambda i: None, enabled=False),
        item(lambda text: f"Restarts: {state.restarts}", lambda i: None, enabled=False),
        item(lambda text: f"Erros de Código: {state.code_errors}", lambda i: None, enabled=False),
        item(lambda text: f"Alertas: {state.alerts}", lambda i: None, enabled=False),
        item(lambda text: f"Falhas Rápidas: {state.fast_crashes}", lambda i: None, enabled=False),
        item(lambda text: f"🤖 Autopilot: {get_autopilot_status()}", toggle_autopilot_action),
        pystray.Menu.SEPARATOR,
        item('Abrir Dashboard', open_dashboard),
        item('Iniciar Servidor', start_server_action),
        item('Parar Servidor', stop_server_action),
        item('Reiniciar Servidor', restart_server_action),
        pystray.Menu.SEPARATOR,
        item('--- SUBAGENTES (SA) ---', lambda i: None, enabled=False),
        item('▶ Auditoria IA (SaAuditaClassificacoes)', run_audit_agent),
        item('▶ Revisão Online (SaRevisaoOnline)', run_revisao_online),
        item('▶ Mineração de Redes (SaMineracaoRedes)', run_mineracao_redes),
        item('▶ Auditoria Financeira (SaAuditoriaFinanceira)', run_auditoria_financeira),
        item('▶ Consulta Banco (SaConsultaBanco)', run_consulta_banco),
        item('▶ Diagnóstico Sistemas (SaDiagnosticaSistemas)', run_diagnostica_sistemas),
        item('▶ Sincronizar Docs (DocFetcher)', run_doc_fetcher),
        pystray.Menu.SEPARATOR,
        item('--- WORKERS (WK) ---', lambda i: None, enabled=False),
        item('▶ Coleta Instagram (WkColetaInstagram)', run_coleta_instagram),
        item('▶ Curador de Alvos (WkPesquisaAlvos)', run_pesquisa_alvos),
        item('▶ Classificador (WkClassificaComentarios)', run_classifica_comentarios),
        item('▶ Scanner de Candidatos (WkEscaneiaCandidatos)', run_scanner_agent),
        item('▶ Gerador de Dossiês (WkGeraDossies)', run_dossier_agent),
        item('▶ Analisador Tendências (WkAnalisaTendencias)', run_analisa_tendencias),
        item('▶ Aplicador Sugestões (WkAplicaSugestoes)', run_aplica_sugestoes),
        item('▶ Monitor Alertas (WkGeraAlertas)', run_gera_alertas),
        pystray.Menu.SEPARATOR,
        item('Sair', quit_tray),
    )

def start_server_action(icon=None, item=None):
    state.should_run = True
    state.add_log("info", "[Watchdog] Inicialização disparada via menu da bandeja.")
    if icon:
        try:
            icon.menu = build_menu()
        except Exception:
            pass

def stop_server_action(icon=None, item=None):
    state.should_run = False
    if state.process and state.process.poll() is None:
        state.add_log("warn", "[Watchdog] Parada disparada via menu da bandeja. Finalizando...")
        state.process.terminate()
    if icon:
        try:
            icon.menu = build_menu()
        except Exception:
            pass

def restart_server_action(icon=None, item=None):
    if state.process and state.process.poll() is None:
        state.add_log("warn", "[Watchdog] Reinício disparado via menu da bandeja...")
        state.process.terminate()
    else:
        state.should_run = True
        state.add_log("info", "[Watchdog] Inicialização disparada via menu da bandeja (reinício)...")
    if icon:
        try:
            icon.menu = build_menu()
        except Exception:
            pass

def quit_tray(icon, item_clicked):
    state.should_run = False
    if state.process and state.process.poll() is None:
        state.process.terminate()
        try:
            state.process.wait(timeout=5)
        except Exception:
            pass
    
    # Executa a limpeza de duplicados de main_runner
    try:
        from watchdog_duplicate_killer import main as kill_duplicate_main
        kill_duplicate_main()
    except Exception:
        pass
        
    icon.stop()

def kill_process_on_port(port: int):
    try:
        creationflags = 0x08000000  # CREATE_NO_WINDOW
        output = subprocess.check_output("netstat -ano", shell=True, creationflags=creationflags).decode('utf-8', errors='ignore')
        for line in output.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = int(parts[-1])
                if pid != os.getpid():
                    print(f"[SHIELD] Detectada instância antiga do Watchdog (PID {pid}) na porta {port}. Encerrando...")
                    try:
                        os.kill(pid, signal.SIGTERM)
                        time.sleep(2)
                    except Exception as ex:
                        print(f"[SHIELD] Falha ao encerrar PID {pid}: {ex}")
    except Exception as e:
        print(f"[SHIELD] Falha ao checar conexões da porta {port}: {e}")

def setup_tray():
    # Carrega imagem do logo
    if os.path.exists(ICON_PATH):
        image = Image.open(ICON_PATH)
    else:
        image = Image.new('RGB', (64, 64), color='white')

    try:
        icon = pystray.Icon("sentinela_watchdog", image, "Sentinela Watchdog", build_menu())
        print("[Watchdog] Iniciando bandeja gráfica...")
        icon.run()
    except Exception as e:
        print(f"[Watchdog] Falha ao iniciar bandeja gráfica (rodando em ambiente Headless/Sem Desktop?): {e}")
        print("[Watchdog] Executando em modo CLI de Fallback resiliente...")
        
        # Mantém o processo principal vivo já que a bandeja falhou
        while True:
            time.sleep(1)

def is_watchdog_running():
    """Tenta conectar na porta 8009 para ver se o watchdog já está ouvindo."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", 8009))
        s.close()
        return True
    except Exception:
        return False

def acquire_boot_lock(lock_path):
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
    except Exception:
        return None

    if sys.platform.startswith("win"):
        try:
            import msvcrt
            msvcrt.locking(fd, msvcrt.LK_NBRLCK, 1)
            return fd
        except Exception:
            try:
                os.close(fd)
            except Exception:
                pass
            return None
    else:
        try:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except Exception:
            try:
                os.close(fd)
            except Exception:
                pass
            return None

def release_boot_lock(fd):
    if fd is not None:
        try:
            if sys.platform.startswith("win"):
                import msvcrt
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        except Exception:
            pass

if __name__ == "__main__":
    BOOT_LOCK_PATH = os.path.join(PROJECT_ROOT, "runtime_state", "watchdog_boot.lock")

    # 1. Verifica se já está rodando
    if is_watchdog_running():
        print("[Watchdog] Já existe uma instância do Watchdog rodando. Encerrando...")
        sys.exit(0)

    # 2. Auto-desacoplamento no Windows para ocultar o terminal (apenas se --background for passado)
    if sys.platform.startswith("win") and "--background" in sys.argv and "--detached" not in sys.argv:
        # Tenta obter o boot lock para garantir que nenhuma outra inicialização ocorra ao mesmo tempo
        boot_fd = acquire_boot_lock(BOOT_LOCK_PATH)
        if boot_fd is None:
            print("[Watchdog] Já existe uma instância do Watchdog inicializando ou rodando. Encerrando...")
            sys.exit(0)

        det_flags = 0x08000000 | 0x00000008 | 0x00000200  # CREATE_NO_WINDOW | DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        
        log_path = os.path.join(PROJECT_ROOT, "runtime_state", "watchdog_bg.log")
        log_file = open(log_path, "a")

        # Dispara o processo em background
        subprocess.Popen(
            [sys.executable, "-u", __file__, "--detached", "--background"],
            creationflags=det_flags,
            cwd=PROJECT_ROOT,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            close_fds=True
        )

        # Espera o processo filho iniciar e dar bind na porta 8009
        started = False
        for _ in range(50):  # tenta por 5 segundos
            time.sleep(0.1)
            if is_watchdog_running():
                started = True
                break

        # Libera o boot lock e finaliza o pai
        release_boot_lock(boot_fd)
        
        if started:
            print("[Watchdog] Watchdog em background iniciado com sucesso.")
        else:
            print("[Watchdog] Erro: O Watchdog em background falhou ao iniciar no tempo limite.")
            sys.exit(1)
        sys.exit(0)

    # 3. Processo principal (seja detached em background ou interativo em foreground)
    # Tenta obter o socket lock de instância única definitivo
    kill_process_on_port(8009)
    _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _lock_socket.bind(("127.0.0.1", 8009))
        _lock_socket.listen(5)  # Habilita escuta para permitir testes de conexão (connect)
    except OSError:
        print("[Watchdog] Já existe uma instância do Watchdog rodando na porta 8009. Encerrando...")
        sys.exit(0)

    # 4. Execução do Watchdog
    os.chdir(PROJECT_ROOT)
    kill_process_on_port(8001)

    # Inicia servidores e Autopilot em threads daemon
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # 🤖 INICIALIZAÇÃO DO AUTOPILOT L3 (PASA v70.0)
    if AUTOPILOT_ENABLED:
        def run_autopilot():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            state.add_log("info", "[Watchdog] 🤖 Autopilot L3 Ativado.")
            try:
                loop.run_until_complete(autopilot.pulse())
            except Exception as e:
                state.add_log("error", f"[Watchdog] 🤖 Autopilot falhou: {e}")

        threading.Thread(target=run_autopilot, daemon=True).start()

    # 🤖 INICIALIZAÇÃO DO DATASETTE EXPLORADOR SQL (PASA v50.1 - Porta 8002)
    db_file = os.path.join(PROJECT_ROOT, "data", "sentinela_data.db")
    if not os.path.exists(db_file):
        try:
            from scripts.export_to_sqlite import export_to_sqlite
            export_to_sqlite()
        except Exception as e_init:
            print(f"[Watchdog] Erro na exportação inicial para Datasette: {e_init}")

    def run_datasette_server():
        try:
            kill_process_on_port(8002)
            # v90.9: Prioriza Python do venv, que tem datasette instalado
            project_root_ds = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            venv_python = os.path.join(project_root_ds, ".venv", "Scripts", "python.exe")
            if os.path.exists(venv_python):
                python_exe = venv_python
            else:
                python_exe = sys.executable
            creationflags = 0x08000000 if os.name == 'nt' else 0
            subprocess.Popen(
                [python_exe, "-m", "datasette", "serve", "-i", db_file, "--port", "8002", "--host", "0.0.0.0"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )
            print("[START] Explorador SQL (Datasette) disponível em: http://localhost:8002")
        except Exception as e_ds:
            print(f"[WARN] Falha ao iniciar Datasette: {e_ds}")

    threading.Thread(target=run_datasette_server, daemon=True).start()
    threading.Thread(target=run_voyant_server, args=(PROJECT_ROOT,), daemon=True).start()

    print("[START] Dashboard disponível em: http://localhost:8001")
    print("[SHIELD] SENTINELA DEMOCRÁTICA - WATCHDOG v50.0")

    # Inicia o monitoramento (guard) em thread de background
    threading.Thread(target=guard, daemon=True).start()

    # Roda a interface da bandeja na thread principal
    setup_tray()
