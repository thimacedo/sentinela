# scripts/run_sa_instagram_stealth.py
import asyncio
import logging
import os
import sys
from pathlib import Path

# Garante o PYTHONPATH sem fazer import shadowing de namespace packages (ex: pasta supabase/)
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])

# Remove o diretório atual do início do path se estiver lá
if '' in sys.path:
    sys.path.remove('')
if os.getcwd() in sys.path:
    sys.path.remove(os.getcwd())
if PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)

# Adiciona o projeto no final, assim as libs do virtualenv (site-packages) têm prioridade absoluta
sys.path.append(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

from workers.ai.sa_instagram_stealth import SaInstagramStealth

import threading
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_sa_instagram_stealth")

class AppState:
    def __init__(self):
        self.should_run = True
        self.status = "Iniciando..."
        self.cycle_count = 0

state = AppState()

def create_icon_image():
    image = Image.new('RGB', (64, 64), color=(30, 30, 30))
    d = ImageDraw.Draw(image)
    d.text((10, 20), "IG", fill=(0, 255, 128))
    return image

async def agent_loop():
    logger.info("Disparando Subagente Instagram Stealth...")
    config = {
        "headless": os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true",
        "use_proxy": True
    }
    worker = SaInstagramStealth(worker_id="sa-ig-stealth-tray", config=config)
    await worker.setup()
    
    try:
        while state.should_run:
            state.status = "Executando Ciclo..."
            res = await worker.run_cycle()
            state.cycle_count += 1
            logger.info(f"Ciclo {state.cycle_count} concluído! Resultado: {res}")
            
            if getattr(res, "error", None) == "Circuit_Breaker_Open":
                state.status = "Circuit Breaker Aberto"
                await asyncio.sleep(60)
            elif not res.target:
                state.status = "Ocioso (Sem tarefas)"
                await asyncio.sleep(10)
            else:
                state.status = "Aguardando pacing..."
                await asyncio.sleep(5)
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        state.status = "Erro!"
    finally:
        state.status = "Encerrando..."
        await worker.teardown()

def start_asyncio_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(agent_loop())
    loop.close()

def on_quit(icon, item):
    state.should_run = False
    icon.stop()
    sys.exit(0)

def build_menu():
    return pystray.Menu(
        item(lambda text: f"Status: {state.status}", lambda i: None, enabled=False),
        item(lambda text: f"Ciclos Executados: {state.cycle_count}", lambda i: None, enabled=False),
        pystray.Menu.SEPARATOR,
        item('Sair', on_quit)
    )

if __name__ == "__main__":
    # Inicia o agente em background
    t = threading.Thread(target=start_asyncio_thread, daemon=True)
    t.start()
    
    # Inicia o Tray Icon
    icon = pystray.Icon("sa_instagram_stealth", create_icon_image(), "Instagram Stealth Agent", build_menu())
    icon.run()
