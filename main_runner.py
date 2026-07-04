from __future__ import annotations
import os
import sys

# --- AUTO-ANCHORING (v61.6) ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import asyncio
import logging
import signal
from datetime import datetime

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except AttributeError:
        pass


from dotenv import load_dotenv

load_dotenv(override=True)

os.makedirs("logs", exist_ok=True)

# Configuração de Logging v50.1-final
os.makedirs("logs", exist_ok=True)
WATCHDOG_ACTIVE = os.getenv("WATCHDOG_ACTIVE") == "true"

# Root logger configuration
root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)  # modo quiet por padrão
root_logger.handlers.clear()

# Console handler (minimal)
console_handler = logging.StreamHandler(sys.stdout)
console_format = "%(message)s" if not WATCHDOG_ACTIVE else "%(message)s"
console_handler.setFormatter(logging.Formatter(console_format))
root_logger.addHandler(console_handler)

# File handler (JSON)
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
file_handler = RotatingFileHandler(
    "logs/main_runner.json",
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
json_formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s",
    timestamp=True,
)
file_handler.setFormatter(json_formatter)
root_logger.addHandler(file_handler)

# Enable INFO for principais loggers
for important_logger in ["main_runner", "orchestrator", "queue_manager", "worker.ig_v2", "worker.twitter", "worker.researcher", "instagram_scraper_v2", "core.ai_service", "worker.ai_processor", "core.autopilot"]:
    logging.getLogger(important_logger).setLevel(logging.INFO)

# Silenciar bibliotecas barulhentas
for noisy_logger in ["httpx", "httpcore", "supabase", "postgrest", "urllib3", "playwright"]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

logger = logging.getLogger("main_runner")

from workers.base.memory_store import MemoryStore
from workers.base.reward_engine import RewardEngine
from workers.orchestrator.orchestrator import SentinelaOrchestrator
from core.autopilot.manager import autopilot
from core.autopilot.cloud_listener import CloudListener, set_current_cycle
from workers.ai.wk_aplica_sugestoes import WkAplicaSugestoes

# Workers disponíveis (PASA v98.8):
from workers.scrapers.wk_coleta_instagram import WkColetaInstagram
from workers.scrapers.wk_coleta_twitter import WkColetaTwitter
from workers.processors.wk_pesquisa_alvos import WkPesquisaAlvos


def build_orchestrator() -> SentinelaOrchestrator:
    store = MemoryStore()
    engine = RewardEngine(store)
    orch = SentinelaOrchestrator(engine)

    # 🚀 ROCKET MODE: Escalonamento de Scrapers
    num_scrapers = int(os.getenv("NUM_SCRAPER_WORKERS", "1"))
    logger.info(f"[main_runner] Configurando {num_scrapers} Scraper Workers...")
    
    for i in range(num_scrapers):
        worker_id = f"ig-v2-{i+1:02d}"
        orch.register(WkColetaInstagram(
            worker_id=worker_id,
            config={
                "max_posts": int(os.getenv("MAX_POSTS_PER_PROFILE", "3")),
                "max_comments_per_post": int(os.getenv("MAX_COMMENTS_PER_POST", "50")),
                "headless": os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
            },
        ))

    # 🚀 API TWITTER SCRAPER
    orch.register(WkColetaTwitter(worker_id="twitter-01", config={}))

    # 🧠 AI PROCESSOR: Worker dedicado para classificação PASA
    # Este worker consome o backlog deixado pelos scrapers
    try:
        from workers.processors.wk_classifica_comentarios import WkClassificaComentarios
        
        num_ai_workers = int(os.getenv("NUM_AI_WORKERS", "2"))
        logger.info(f"[main_runner] Configurando {num_ai_workers} AI Processors...")
        
        for i in range(num_ai_workers):
            orch.register(WkClassificaComentarios(worker_id=f"ai-processor-{i+1:02d}", config={}))
            
        logger.info("[main_runner] WkClassificaComentarios registrados com sucesso.")
    except ImportError as e:
        logger.warning(f"[main_runner] Erro ao registrar WkClassificaComentarios: {e}")

    # 🔍 REVISÃO CLOUD: Fila secundária para reclassificação de SUSPEITOS
    try:
        from workers.ai.sa_revisao_online import SaRevisaoOnline
        orch.register(SaRevisaoOnline(worker_id="sa-revisao-online-01", config={"batch_size": 20}))
        logger.info("[main_runner] SaRevisaoOnline registrado com sucesso.")
    except ImportError as e:
        logger.warning(f"[main_runner] Erro ao registrar SaRevisaoOnline: {e}")

    # ⚡ FAST DROP LOCAL: Pré-triagem léxica sem Java e sem LLM
    try:
        from workers.ai.sa_fast_drop import SaFastDrop
        orch.register(SaFastDrop(worker_id="sa-fast-drop-01", config={}))
        logger.info("[main_runner] SaFastDrop registrado com sucesso.")
    except ImportError as e:
        logger.warning(f"[main_runner] SaFastDrop indisponível (será criado): {e}")

    # Motor de Curadoria e Inteligência de Alvos (v84.9)
    researcher_mode = os.getenv("RESEARCHER_MODE", "disabled").strip().lower()
    if researcher_mode != "disabled":
        orch.register(WkPesquisaAlvos(
            worker_id="researcher-01",
            config={
                "headless": True,
                "mode": researcher_mode,
            }
        ))
        logger.info(f"[main_runner] Researcher registrado em modo: {researcher_mode}")
    else:
        logger.info("[main_runner] Researcher desabilitado (RESEARCHER_MODE=disabled).")

    # 🛡️ SRE & RESILIÊNCIA: DLQ Manager e SessionHealer (v100.0)
    try:
        from workers.sre.wk_dead_letter_queue import WkDeadLetterQueue
        from workers.sre.wk_sessao_autonoma import WkSessaoAutonoma
        
        orch.register(WkDeadLetterQueue(worker_id="sre-dlq-01", config={}))
        orch.register(WkSessaoAutonoma(worker_id="sre-sessao-01", config={}))
        logger.info("[main_runner] Workers de SRE (WkDeadLetterQueue e WkSessaoAutonoma) registrados com sucesso.")
    except Exception as e_sre:
        logger.warning(f"[main_runner] Falha ao registrar workers de SRE: {e_sre}")

    logger.info(f"[main_runner] Workers registrados: {orch.worker_ids}")
    return orch


# Evento global de desligamento (PASA v85.0)
shutdown_event = asyncio.Event()

def setup_signal_handlers(
    orch: SentinelaOrchestrator,
    loop: asyncio.AbstractEventLoop,
) -> None:
    def _shutdown(sig_name: str) -> None:
        logger.info(f"[main_runner] {sig_name} detectado — sinalizando pouso de emergência (Graceful Shutdown)...")
        shutdown_event.set()
        orch.stop_all()

    if sys.platform.startswith("win"):
        # No Windows, loop.add_signal_handler não é implementado. Usamos o signal clássico.
        def handle_win_signal(signum, frame):
            sig_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
            loop.call_soon_threadsafe(lambda: _shutdown(sig_name))
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, handle_win_signal)
            except Exception:
                pass
    else:
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda s=sig.name: _shutdown(s))
            except NotImplementedError:
                pass


def check_and_prompt_envs():
    """Valida se todas as credenciais essenciais estão presentes no .env. Se não, solicita interativamente."""
    required_envs = {
        "SUPABASE_URL": "URL do projeto Supabase (https://supabase.com/dashboard)",
        "SUPABASE_KEY": "Chave (anon/service_role) do Supabase",
    }
    
    missing_envs = {}
    for key, help_text in required_envs.items():
        val = os.getenv(key)
        # Verifica se está vazio ou se possui os placeholders padrão do .env.example
        if not val or "your_" in val.lower():
            missing_envs[key] = help_text

    if missing_envs:
        print("\n" + "="*60)
        print("🚨 SENTINELA SETUP: CREDENCIAIS AUSENTES 🚨")
        print("="*60)
        print("Parece que você está rodando o Sentinela sem todas as chaves de API necessárias.")
        
        if not sys.stdin.isatty():
            print("Execução em modo headless detectada. Abortando. Configure as chaves no arquivo .env.")
            sys.exit(1)
            
        print("Por favor, preencha as chaves abaixo para salvar automaticamente no seu arquivo .env:")
        
        with open(".env", "a", encoding="utf-8") as f:
            for key, help_text in missing_envs.items():
                print(f"\n👉 [{key}]")
                print(f"Obtenha em: {help_text}")
                value = input(f"Cole o valor para {key} (ou Enter para ignorar temporariamente): ").strip()
                if value:
                    f.write(f"\n{key}={value}")
                    os.environ[key] = value
                    
        # Recarrega para garantir que as libs as vejam
        load_dotenv(override=True)
        print("\n✅ Credenciais salvas no arquivo .env!")
        print("="*60 + "\n")


async def main() -> None:
    # 0. Verificação das variáveis de ambiente antes de qualquer boot complexo
    check_and_prompt_envs()

    logger.info("[main_runner] Sentinela iniciando...")
    
    # v90.7: Log de emergência para diagnosticar crash de boot
    with open("boot_debug.log", "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}] Boot iniciado (PID {os.getpid()})\n")
        f.flush()

    try:
        # 🧹 Faxina de processos órfãos de navegadores no boot
        try:
            from core.process_cleaner import cleanup_orphans
            cleanup_orphans()
        except Exception as e:
            logger.warning(f"[main_runner] Falha ao executar cleanup_orphans no boot: {e}")

        orch = build_orchestrator()
        # Injeta o evento de shutdown no orquestrador
        orch.shutdown_event = shutdown_event

        loop = asyncio.get_running_loop()
        setup_signal_handlers(orch, loop)

        # 🤖 ATIVAÇÃO DO AUTOPILOT L3 (PASA v70.0)
        asyncio.create_task(autopilot.pulse())

        # 🛡️ CONTROLE REMOTO E HEARTBEAT (PASA v80.0)
        cloud_listener = CloudListener(source="local")
        asyncio.create_task(cloud_listener.start())
        logger.info("[main_runner] 🛡️ CloudListener ativado (heartbeat + controle remoto).")

        # 💡 LOOP DE FEEDBACK DO AI ADVISOR (PASA v80.0)
        suggestion_consumer = WkAplicaSugestoes(orchestrator=orch)
        asyncio.create_task(suggestion_consumer.start())
        logger.info("[main_runner] 💡 WkAplicaSugestoes ativado (aplicação automática de sugestões).")

        if not orch.worker_ids:
            logger.warning(
                "[main_runner] Nenhum worker ativo. "
                "Mantendo processo vivo para evitar restart loop do Watchdog."
            )
            while True:
                await asyncio.sleep(300)

        await orch.run_all()
    except Exception as e:
        logger.critical(f"💥 [FATAL] Erro não tratado no main_runner: {e}", exc_info=True)
        raise e

    logger.info("[main_runner] Encerrado.")


from core.guard_locker import GuardLocker

def main_with_lock():
    locker = GuardLocker("main_runner", PROJECT_ROOT)
    if not locker.acquire(kill_existing=True):
        print("🚨 [main_runner] Falha ao adquirir lock de instância única. Abortando.")
        sys.exit(1)
        
    try:
        asyncio.run(main())
    finally:
        locker.release()

if __name__ == "__main__":
    main_with_lock()
# hot-reload trigger: 2026-06-04 v3
