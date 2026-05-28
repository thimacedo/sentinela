import os
import sys
import asyncio
import subprocess
import pandas as pd
from datetime import datetime, UTC
from typing import List, Dict, Any

# Core imports
from core.config import settings
from core.db import db_client
from core.ai_service import ai_service
from core.predictive_service import predictive_service
from core.firebase_alerter import send_alert_summary

# Specialized processing modules
from processing.text_processor import TextProcessor
from processing.data_miner import DataMiner
from processing.report_generator import ReportGenerator
from tools.target_manager import TargetManager
import json

class Orchestrator:
    def __init__(self):
        self.tp = TextProcessor()
        self.rg = ReportGenerator()
        self.tm = TargetManager(hours_threshold=48)

    async def run_scraper(self, limit=200, cooldown=300):
        print(f"🚀 [1/5] Preparando Alvos e Extração (Centralizado - Diamond) - Limite: {limit}...")
        
        from workers.processors.queue_manager import QueueManagerWorker
        qm = QueueManagerWorker()
        qm.batch_size = limit 
        await qm.execute()

        today = datetime.now(UTC).date().isoformat()
        res = db_client.client.table('fila_coleta')\
            .select('candidato_id')\
            .eq('data_agendada', today)\
            .eq('status', 'PENDENTE')\
            .order('prioridade', desc=True)\
            .limit(limit)\
            .execute()
        
        targets = [item['candidato_id'] for item in res.data]

        if not targets:
            print("✅ Fila central de hoje já processada ou vazia.")
            return

        print(f"🤖 Iniciando Ciclo de Coleta Paralela (Rocket Mode) para {len(targets)} alvos...")
        
        # Configuração de Concorrência
        concurrency_limit = int(os.getenv("CONCURRENT_SCRAPES", "2"))
        semaphore = asyncio.Semaphore(concurrency_limit)
        
        async def scrape_task(target, i):
            async with semaphore:
                print(f"🎯 [{i+1}/{len(targets)}] Iniciando raspagem paralela: @{target}...")
                from core.instagram_headless import InstagramHeadlessScraper
                scraper = InstagramHeadlessScraper()
                try:
                    await scraper.run(targets=[target])
                    print(f"✅ [{i+1}/{len(targets)}] Sucesso: @{target}")
                except Exception as e:
                    print(f"❌ [{i+1}/{len(targets)}] Erro em @{target}: {e}")

        # Dispara todas as tasks, o semáforo controlará a execução
        tasks = [scrape_task(target, i) for i, target in enumerate(targets)]
        await asyncio.gather(*tasks)
        
        print("\n🏁 Ciclo de coleta paralela finalizado. Iniciando classificação massiva...")
        # Após a coleta paralela, fazemos uma classificação massiva de tudo o que foi coletado
        await ai_service.run_batch_classification(limit=500, force_retry_failures=True)

    async def run_ia_classification(self):
        print("🧠 [2/5] Iniciando Perícia PASA v16.4...")
        # Chamando o método da instância singleton ai_service
        await ai_service.run_batch_classification(limit=200)
        print("✅ Classificação concluída.")

    async def run_repericia_cycle(self):
        print("🔍 [1.5/5] Verificando solicitações de RE-PERÍCIA...")
        targets = await db_client.fetch_targets_needing_repericia()
        
        if not targets:
            print("✅ Nenhuma re-perícia pendente.")
            return

        print(f"🕵️‍♂️ Detectados {len(targets)} alvos para re-perícia: {', '.join(targets)}")
        
        for username in targets:
            await db_client.reset_target_comments(username)
            await db_client.mark_repericia_complete(username)
            print(f"✨ Alvo @{username} pronto para re-processamento.")

    async def run_meta_ads_cycle(self):
        print("📢 [1.7/5] Rastreando META AD LIBRARY...")
        from core.meta_ad_service import meta_ad_service
        from processing.ad_processor import ad_processor
        
        try:
            with open("data/priority_queue.json", "r") as f:
                targets = json.load(f)
        except:
            targets = []

        if not targets:
            print("⚠️ Ninguém na fila de prioridade para anúncios.")
            return

        # Roda apenas para os Top 5 da fila pra não ser bloqueado rápido demais
        for target in targets[:5]:
            ads = await meta_ad_service.search_ads(target)
            if ads:
                await db_client.persist_ads_batch(ads)
        
        # Processamento de IA (PASA v16.4)
        print("⛏️ [1.8/5] Classificando Anúncios Meta...")
        await ad_processor.run_once(limit=10)
        
        print("✅ Ciclo de anúncios concluído.")

    async def fetch_and_normalize(self) -> pd.DataFrame:
        print("📥 [3/5] Coletando dados do Supabase...")
        data = await db_client.fetch_all_data()
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        
        # Normalização Diamond Edition
        rename_map = {
            'texto_bruto': 'text',
            'autor_username': 'owner_username',
            'post_id': 'post_shortcode',
            'is_hate': 'is_hate_speech',
            'categoria_ia': 'category'
        }
        for old, new in rename_map.items():
            if old in df.columns:
                df[new] = df[old]
        
        return df

    async def process_and_mine(self, df: pd.DataFrame):
        print("⛏️ [4/5] NLP & Mineração de Tendências (Modo Worker)...")
        from processing.data_miner import data_miner
        
        # O novo DataMiner agora é um worker que processa incrementalmente.
        # Aqui no Orquestrador, podemos apenas rodar um ciclo para processar o que acabou de chegar.
        count = await data_miner.run_once(limit=self.batch_size if hasattr(self, 'batch_size') else 200)
        print(f"✅ Ciclo de mineração concluído: {count} itens processados.")
        
        # Para compatibilidade com a geração de relatório legada no final da pipeline, 
        # ainda processamos o dataframe para limpeza textual.
        df_proc = self.tp.processar_dataframe(df)
        return df_proc

    async def persist_intelligence(self, df: pd.DataFrame, clusters: List[Dict], temporal: Dict):
        print("💾 [4.5/5] Persistindo Inteligência Forense...")
        
        # 1. Atualiza IDs de Cluster nos comentários (Se houver)
        if 'cluster' in df.columns:
            updates = []
            for _, row in df.iterrows():
                if pd.notna(row['cluster']):
                    updates.append({
                        "id": row['id'],
                        "cluster_id": int(row['cluster'])
                    })
            if updates:
                await db_client.batch_update_comments(updates)
                print(f"🔗 {len(updates)} comentários vinculados a clusters.")

        # 2. Métricas Diárias
        hoje = datetime.now().strftime('%Y-%m-%d')
        total = len(df)
        hate = df['is_hate_speech'].sum() if 'is_hate_speech' in df.columns else 0
        resiliencia = round(100 - ((hate / total) * 100), 2) if total > 0 else 100.0
        
        pasa = df[df['is_hate_speech'] == True]['category'].value_counts().to_dict() if 'category' in df.columns else {}
        
        await db_client.upsert_daily_metrics({
            "p_data": hoje,
            "p_total_coletado": int(total),
            "p_total_hate": int(hate),
            "p_total_neutro": int(total - hate),
            "p_resiliencia": float(resiliencia),
            "p_pasa_breakdown": pasa,
            "p_uf_breakdown": {"SP": int(hate*0.4), "RJ": int(hate*0.3), "DF": int(hate*0.3)} # Placeholder
        })

        # 3. Redes Coordenadas
        for c in clusters:
            if c['event_count'] < 3: continue
            severity = min(100, int((c['event_count'] / len(df)) * 1000)) if len(df) > 0 else 0
            await db_client.persist_coordinated_network({
                "nome": f"Rede {c['cluster_id']} - {datetime.now().strftime('%d/%m')}",
                "status": "ATIVA" if severity > 50 else "MONITORANDO",
                "eventos_count": c['event_count'],
                "severidade": severity,
                "palavras_chave": c['keywords']
            })

    async def run_predictive_cycle(self):
        print("📈 [2.5/5] Executando análise de TENDÊNCIAS PREDITIVAS...")
        try:
            status = await predictive_service.analyze_trends(days=7)
            if status.get('status') == 'insufficient_data':
                print("ℹ️ Dados insuficientes para análise preditiva confiável.")
            elif status.get('is_anomaly'):
                print(f"⚠️ ALERTA: Anomalia detectada! Tendência de {status['trend']}.")
            else:
                print(f"✅ Tendência estável ({status.get('trend')}).")
        except Exception as e:
            print(f"⚠️ Erro no ciclo preditivo: {e}")

    async def run_full_pipeline(self):
        print(f"\n🛡️ SENTINELA DEMOCRÁTICA - PIPELINE v{settings.VERSION}")
        print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🧠 Intelligence: Provider={settings.IA_PROVIDER} (Cascade={ai_service.cascade_order})")
        print("="*50 + "\n")
        
        if settings.IA_PROVIDER == "ollama":
            print(f"📡 Local AI: Verificando Ollama em {settings.OLLAMA_BASE_URL}...")
        
        await self.run_scraper()
        await self.run_repericia_cycle()
        await self.run_meta_ads_cycle()
        await self.run_ia_classification()
        await self.run_predictive_cycle()
        
        df = await self.fetch_and_normalize()
        if df.empty:
            print("🛑 Pipeline interrompida: Sem dados.")
            return

        # Export para API legacy support
        os.makedirs("api", exist_ok=True)
        df.to_csv("api/dados_latest.csv", index=False)

        df_final = await self.process_and_mine(df)
        
        # Relatório PDF
        output_path = f"data/reports/dossie_sentinela_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        os.makedirs("data/reports", exist_ok=True)
        self.rg.generate_pdf(df_final, output_path)

        # Notificação Push
        total_odio = df_final['is_hate_speech'].sum() if 'is_hate_speech' in df_final.columns else 0
        resumo = f"📊 Relatório Sentinela\nComentários: {len(df_final)}\nHostilidade: {total_odio} detectados\nVersão: {settings.VERSION}"
        send_alert_summary(resumo)
        
        print("\n" + "="*50)
        print(f"✨ PIPELINE FINALIZADA! Relatório: {output_path}\n")

if __name__ == "__main__":
    orchestrator = Orchestrator()
    asyncio.run(orchestrator.run_full_pipeline())
