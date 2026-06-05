# run_long_scrape.py
import sys
import asyncio
import logging
import random

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from workers.scrapers.wk_coleta_instagram import WkColetaInstagram as InstagramWorker
from core.supabase_service import save_comments, get_next_targets_to_scrape, update_last_scraped_at, save_scrape_error
from core.worker_auditor import audit_worker_result

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

async def main():
    logger = logging.getLogger("MaestroDinamico")
    total_alerts_saved = 0

    # BUSCA DINÂMICA: Pega os 5 alvos mais quentes e esquecidos do banco
    targets = get_next_targets_to_scrape(limit=5)
    
    if not targets:
        logger.warning("⚠️ Nenhum alvo ATIVO encontrado na tabela 'candidatos'.")
        return

    logger.info("🚀 INICIANDO OPERAÇÃO DINÂMICA (MODO STEALTH + AUDITORIA)")
    logger.info(f"🎯 Alvos selecionados pelo banco: {targets}")

    for index, target_data in enumerate(targets):
        target = target_data['username'].lstrip('@')
        logger.info(f"\n{'='*50}")
        logger.info(f"📍 Iniciando extração para: @{target} ({index+1}/{len(targets)})")
        
        try:
            worker = InstagramWorker(target_profile=target, max_posts=3)
            dados = await worker.execute()
            
            if dados:
                # 1. O AUDITOR AVALIA O PROCESSO
                process_is_healthy = audit_worker_result(worker.name, dados)
                
                if not process_is_healthy:
                    logger.error("🛑 PROCESSO COMPROMETIDO POR ATALHO. Operação interrompida.")
                    break 
                
                # 2. SALVA OS ALERTAS
                logger.info(f"💾 Processo íntegro. Salvando {len(dados)} alertas...")
                # Note: save_comments is already called inside InstagramWorker._run
                # But we can track success here if needed or if worker returns data
                total_alerts_saved += len(dados)
                logger.info("✅ Sincronização concluída.")
            else:
                logger.warning(f"⚠️ @{target} não rendeu dados ou sessão bloqueada.")

        except Exception as e:
            logger.error(f"❌ Falha mecânica ao processar @{target}: {e}")
            
            # PUNIÇÃO DO ALVO / CLASSIFICAÇÃO DO ERRO
            error_msg = str(e)
            if "Perfil não encontrado" in error_msg:
                save_scrape_error(target, "PROFILE_NOT_FOUND")
                # Perfis inexistentes não devem ser tentados novamente com a mesma prioridade
                logger.warning(f"⛔ Perfil @{target} não existe. Sugerido verificar cadastro no banco.")
            elif "Timeout" in error_msg or "timeout" in error_msg.lower():
                save_scrape_error(target, "TIMEOUT")
            elif "Login" in error_msg or "Sessão" in error_msg or "Inválida" in error_msg:
                save_scrape_error(target, "LOGIN_BLOCK")
                # Se a sessão caiu, o Maestro deveria parar tudo imediatamente
                logger.error("🚨 SESSÃO DO INSTAGRAM INVALIDADA! Operação cancelada.")
                break
            else:
                save_scrape_error(target, "UNKNOWN_ERROR")

        # IMPORTANTE: Atualiza o last_scraped_at do alvo, mesmo se falhar
        # Para não ficar preso no mesmo alvo quebrado no próximo ciclo
        update_last_scraped_at(target)
        logger.info(f"⏱️ Timestamp de raspagem atualizado para @{target}.")

        # MACRO-DELAY (2 a 5 minutos)
        if index < len(targets) - 1:
            pause_secs = random.randint(120, 300)
            logger.info(f"⏳ Entrando em modo stealth por {pause_secs // 60} minutos...")
            
            for i in range(pause_secs):
                remaining = pause_secs - i
                if remaining % 30 == 0:
                    sys.stdout.write(f"\r⏳ Restam: {remaining // 60}m {remaining % 60}s   ")
                    sys.stdout.flush()
                await asyncio.sleep(1)
            sys.stdout.write("\r✅ Pausa finalizada. Próximo alvo!          \n")

    logger.info(f"\n🏁 CICLO DE COLETA CONCLUÍDO!")
    logger.info(f"📊 Total de alertas íntegros: {total_alerts_saved}")

if __name__ == "__main__":
    asyncio.run(main())
