# run_deep_scrape.py
import asyncio
import logging
import random
import sys
import os
from datetime import datetime
from core.supabase_service import get_next_targets_to_scrape, update_last_scraped_at, save_scrape_error
from workers.scrapers.instagram_worker import InstagramWorker
from workers.analytics.report_worker import ReportWorker

# Configuração de Log de Elite
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("deep_scrape_operation.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MaestroDeep")

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

async def run_operation():
    logger.info("🚀 INICIANDO OPERAÇÃO SENTINELA: COBERTURA TOTAL (DEEP SCRAPE)")
    logger.info("⚠️ ESTA RODADA SÓ PARA QUANDO AS PENDÊNCIAS FOREM MITIGADAS OU POR INTERVENÇÃO.")
    
    iteration = 0
    total_sucessos = 0
    total_falhas = 0
    
    max_posts = 3
    max_comments = 50

    while True:
        iteration += 1
        logger.info(f"\n{'='*60}\n🔄 CICLO DE OPERAÇÃO #{iteration}\n{'='*60}")
        
        # 1. Busca os próximos alvos (Prioriza PENDENTES e ALTO VALOR)
        targets = get_next_targets_to_scrape(limit=3)
        
        if not targets:
            logger.info("🏁 TODOS OS ALVOS FORAM PROCESSADOS! Iniciando calibração final...")
            await ReportWorker().execute()
            logger.info("✅ Operação concluída com sucesso. Base 100% coberta.")
            break

        for target in targets:
            username = target['username']
            priority = target.get('prioridade_coleta', 1)
            
            logger.info(f"📍 Alvo Atual: @{username} (Prioridade: {priority})")
            
            from core.instagram_scraper_v2 import InstagramScraperV2
            from core.ai_service import ai_service
            
            scraper = InstagramScraperV2(headless=False)
            
            try:
                # Executa a Raspagem
                result = await scraper.scrape_profile(username, candidato_id=username, max_posts=max_posts)
                
                if result:
                    logger.info(f"✅ SUCESSO: {len(result)} itens extraídos de @{username}")
                    update_last_scraped_at(username)
                    total_sucessos += 1
                else:
                    logger.warning(f"⚠️ VAZIO: Nenhum dado novo em @{username}. Verificando bloqueios...")
                    # Se retornar vazio mas sem erro, pode ser perfil sem posts ou bloqueio silencioso
                
            except Exception as e:
                total_falhas += 1
                error_msg = str(e)
                logger.error(f"❌ FALHA em @{username}: {error_msg}")
                
                # Classifica Erro para o Banco
                error_type = "UNKNOWN"
                if "Timeout" in error_msg: error_type = "TIMEOUT"
                elif "login" in error_msg.lower(): error_type = "LOGIN_BLOCK"
                elif "not found" in error_msg.lower(): error_type = "PROFILE_NOT_FOUND"
                
                save_scrape_error(username, error_type)
                
                if error_type == "LOGIN_BLOCK":
                    logger.critical("🚨 BLOQUEIO DE CONTA DETECTADO! Entrando em hibernação profunda...")
                    await asyncio.sleep(1800) # 30 min de cooldown
                    continue

            # Intervalo Stealth Dinâmico (Recompensa/Punição de Tempo)
            # Alvos de prioridade alta têm pausa menor; alvos comuns têm pausa maior.
            wait_time = random.randint(120, 300) if priority < 4 else random.randint(60, 120)
            logger.info(f"⏳ Modo Stealth: Aguardando {wait_time}s antes do próximo alvo...")
            await asyncio.sleep(wait_time)

        # 2. A cada 3 alvos, roda o ReportWorker para recalibrar o sistema
        if iteration % 2 == 0:
            logger.info("⚖️ Calibrando Sistema de Recompensas em tempo real...")
            await ReportWorker().execute()
            logger.info(f"📊 Status Atual: {total_sucessos} Sucessos | {total_falhas} Falhas")

if __name__ == "__main__":
    try:
        asyncio.run(run_operation())
    except KeyboardInterrupt:
        logger.info("🛑 Operação interrompida pelo usuário.")
    except Exception as e:
        logger.critical(f"💥 ERRO FATAL NO MAESTRO: {e}")
