import os
import sys
import asyncio
import logging

# Set up logging to console
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("debug_boot")

async def test_boot():
    logger.info("Starting debug boot...")
    try:
        from core.guard_locker import GuardLocker
        from main_runner import build_orchestrator, PROJECT_ROOT
        
        logger.info("Initializing GuardLocker...")
        locker = GuardLocker("main_runner_debug", PROJECT_ROOT)
        if not locker.acquire(kill_existing=True):
            logger.error("Failed to acquire lock")
            return
            
        logger.info("Building orchestrator...")
        orch = build_orchestrator()
        logger.info(f"Orchestrator built with workers: {orch.worker_ids}")
        
        logger.info("Testing Supabase connection via core.db...")
        from core.db import db_client
        res = db_client.client.table('candidatos').select('id').limit(1).execute()
        logger.info("Supabase connection OK")
        
        logger.info("Testing AIService initialization...")
        from core.ai_service import ai_service
        logger.info(f"AIService initialized with {len(ai_service.providers)} providers")
        
        logger.info("Boot test successful")
        locker.release()
    except Exception as e:
        logger.exception(f"FATAL ERROR DURING BOOT: {e}")

if __name__ == "__main__":
    asyncio.run(test_boot())
