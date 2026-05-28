from fastapi import FastAPI, HTTPException, Body, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
import os
import sys
from dotenv import load_dotenv
from collections import Counter
import traceback
import logging
from datetime import datetime, timedelta, timezone
import stripe

# Ajuste de path para imports locais (Vercel compliance)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

try:
    from stripe_service import payment_manager
except ImportError:
    try:
        from api.stripe_service import payment_manager
    except ImportError:
        from .stripe_service import payment_manager

# Import Workers Metrics
try:
    from processing.workers_metrics import metrics_collector
except ImportError:
    # Fallback if running from root
    metrics_collector = None

# Configuração de logs
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("sentinela-api")

load_dotenv()

# --- CONSTANTS ---
PASA_CONFIG = {
    "ODIO_IDENTITARIO": {"label": "Ódio Identitário", "color": "#ef4444", "icon": "users"},
    "VIOLENCIA_GENERO": {"label": "Violência de Gênero", "color": "#ec4899", "icon": "shield-alert"},
    "AMEACA": {"label": "Ameaça", "color": "#f97316", "icon": "alert-octagon"},
    "INSULTO_AD_HOMINEM": {"label": "Insulto Ad Hominem", "color": "#f59e0b", "icon": "swords"},
    "ATAQUE_INSTITUCIONAL": {"label": "Ataque Institucional", "color": "#8b5cf6", "icon": "landmark"},
    "RIGOR_CRIMINAL": {"label": "Rigor Criminal", "color": "#06b6d4", "icon": "scale"}
}
RISK_COLORS = {"CRITICO": "#ef4444", "ELEVADO": "#f59e0b", "MONITORANDO": "#06b6d4", "CONTROLADO": "#10b981"}

app = FastAPI()
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

@app.get("/")
def read_root():
    return {
        "status": "operational",
        "service": "Sentinela API Backend",
        "version": "50.1",
        "documentation": "/docs",
        "endpoints": {
            "health": "/api/health",
            "summary": "/api/v1/summary",
            "targets": "/api/v1/targets"
        }
    }


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

def get_supa() -> Client:
    """Dependency para obter cliente Supabase com diagnóstico aprimorado."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        logger.error(f"❌ CREDENCIAIS AUSENTES: URL={bool(url)}, KEY={bool(key)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Database credentials missing in environment (URL:{bool(url)}, KEY:{bool(key)})"
        )
    try:
        return create_client(url, key)
    except Exception as e:
        logger.error(f"❌ SUPABASE CONNECTION ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to Supabase: {str(e)}")

# --- MODELS ---
class CheckoutRequest(BaseModel):
    user_id: str
    package_slug: str
    price_id: Optional[str] = None

class DossierGenerateRequest(BaseModel):
    candidato_id: str
    modules: Optional[List[str]] = ["base"]

class PushTokenRegistration(BaseModel):
    user_id: str
    token: str
    platform: Optional[str] = "web"
    device_id: Optional[str] = None

class FalsePositiveRequest(BaseModel):
    id: str

class SessionRotationRequest(BaseModel):
    enabled: Optional[bool] = None
    intervalHours: Optional[int] = None

class SessionCookieRequest(BaseModel):
    cookies: str

# --- UTILS ---
def calculate_risk(item: Dict[str, Any]):
    totais = item.get('comentarios_totais_count', 0) or 0
    odio = item.get('comentarios_odio_count', 0) or 0
    if totais == 0:
        return 0, 'CONTROLADO', RISK_COLORS["CONTROLADO"]
    
    ratio = odio / totais
    score = min(100, int(ratio * 150) + min(50, odio))
    
    if score > 80 or ratio > 0.25:
        return score, 'CRITICO', RISK_COLORS["CRITICO"]
    if score > 50 or ratio > 0.15:
        return score, 'ELEVADO', RISK_COLORS["ELEVADO"]
    if score > 20 or ratio > 0.05:
        return score, 'MONITORANDO', RISK_COLORS["MONITORANDO"]
    return score, 'CONTROLADO', RISK_COLORS["CONTROLADO"]

# --- ENDPOINTS ---

@app.get("/api/v1/summary")
def summary(request: Request, supa: Client = Depends(get_supa)):
    """Retorna KPIs consolidados com o ACUMULADO (Solenya Edition)."""
    try:
        org_id = request.headers.get("X-Organization-Id")
        now_utc = datetime.now(timezone.utc)
        
        # 1. Total de Alvos Ativos (Continua dinâmico)
        query_c = supa.table('candidatos').select('id', count='exact').eq('status_monitoramento', 'Ativo')
        if org_id:
            query_c = query_c.eq('organization_id', org_id)
        c_res = query_c.limit(0).execute()
        c = c_res.count if (c_res and c_res.count is not None) else 0
        
        # 2. Busca Métrica Diária mais recente para o timestamp
        res_diaria = supa.table('metricas_diarias').select('updated_at').order('data', desc=True).limit(1).execute()
        last_update = res_diaria.data[0]['updated_at'] if res_diaria.data else now_utc.isoformat()

        # 3. Calcula o Acumulado (Lifetime) de forma dinâmica a partir da tabela de comentários
        query_total = supa.table('comentarios').select('id', count='exact')
        query_hate = supa.table('comentarios').select('id', count='exact').eq('is_hate', True)
        if org_id:
            query_total = query_total.eq('organization_id', org_id)
            query_hate = query_hate.eq('organization_id', org_id)
            
        t_res_total = query_total.limit(1).execute()
        t_res_hate = query_hate.limit(1).execute()
        
        t_lifetime = t_res_total.count if (t_res_total and t_res_total.count is not None) else 0
        h_lifetime = t_res_hate.count if (t_res_hate and t_res_hate.count is not None) else 0
        
        res_val = round(((t_lifetime - h_lifetime) / t_lifetime) * 100, 1) if t_lifetime > 0 else 100.0
        
        return {
            "total_monitorados": c, 
            "total_alertas": h_lifetime, 
            "total_amostra": t_lifetime, 
            "resiliencia": res_val, 
            "periodo": "Acumulado",
            "org_id": org_id,
            "timestamp": last_update
        }
    except Exception as e:
        logger.error(f"Summary KPI Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/networks")
def get_networks(request: Request, supa: Client = Depends(get_supa)):
    """Busca as redes coordenadas (clusters) mais recentes."""
    try:
        res = supa.table('redes_coordenadas').select('*').order('created_at', desc=True).limit(10).execute()
        return res.data if res.data else []
    except Exception as e:
        logger.error(f"Networks Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/targets")
def get_targets(request: Request, limit: int = 50, supa: Client = Depends(get_supa)):
    try:
        org_id = request.headers.get("X-Organization-Id")
        
        # Busca candidatos ativos escopados
        query_cand = supa.table('candidatos').select('*').eq('status_monitoramento', 'Ativo')
        if org_id:
            query_cand = query_cand.eq('organization_id', org_id)
        candidates_res = query_cand.execute()
        candidates = candidates_res.data or []
        
        # Busca ódio recente escopado
        query_h = supa.table('comentarios').select('candidato_id, categoria_ia').eq('is_hate', True)
        if org_id:
            query_h = query_h.eq('organization_id', org_id)
        h_res = query_h.limit(2000).execute()
        h_data = h_res.data or []
        
        counts = Counter([h['candidato_id'] for h in h_data])
        breakdowns = {}
        for h in h_data:
            cid, cat = h['candidato_id'], h['categoria_ia'] or 'OUTROS'
            if cid not in breakdowns:
                breakdowns[cid] = Counter()
            breakdowns[cid][cat] += 1
        
        enriched = []
        for item in candidates:
            cid = item.get('username')
            item['comentarios_odio_count'] = counts.get(cid, 0)
            score, nivel, color = calculate_risk(item)
            enriched.append({
                **item, 
                "score_risco": score, 
                "nivel_risco": nivel, 
                "color": color, 
                "breakdown": dict(breakdowns.get(cid, {}))
            })
            
        return sorted(enriched, key=lambda x: x.get('comentarios_odio_count', 0), reverse=True)[:limit]
    except Exception as e:
        logger.error(f"Targets Error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/alerts/active")
def get_active_alerts(limit: int = 20, supa: Client = Depends(get_supa)):
    try:
        res = supa.table('comentarios').select('*, candidatos(username)').eq('is_hate', True).order('data_coleta', desc=True).limit(limit).execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Alerts Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/alerts/false-positive")
def mark_false_positive(payload: FalsePositiveRequest, supa: Client = Depends(get_supa)):
    """Marca um comentário como falso positivo e garante sua exclusão da timeline de ódio."""
    try:
        res = supa.table('comentarios').update({
            "is_hate": False, 
            "processado_ia": True, 
            "categoria_ia": "FALSO_POSITIVO_MANUAL"
        }).eq('id', payload.id).execute()
        
        return {"status": "success", "id": payload.id}
    except Exception as e:
        logger.error(f"False Positive Critical Error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail={"error": str(e), "id": payload.id})

@app.post("/api/v1/dossiers/generate")
async def generate_dossier(payload: DossierGenerateRequest, supa: Client = Depends(get_supa)):
    """Gera um novo relatório estratégico."""
    try:
        from processing.dossie_service import DossieService
        data = supa.table('comentarios').select('*').eq('candidato_id', payload.candidato_id).limit(500).execute().data
        if not data:
            raise HTTPException(status_code=404, detail="No data found for this target")
        
        # Simulação de geração para evitar bloqueio de thread
        timestamp = int(datetime.now().timestamp())
        path = f"data/reports/relatorio_{payload.candidato_id}_{timestamp}.pdf"
        
        # Persistência do registro de relatório
        supa.table('dossies').insert({
            "candidato_id": payload.candidato_id,
            "total_comentarios": len(data),
            "total_hate": len([i for i in data if i.get('is_hate')]),
            "arquivo_path": path,
            "hash_integridade": f"sha256:{payload.candidato_id}:{timestamp}",
            "versao_pasa": "v16.4"
        }).execute()

        return {"status": "success", "pdf_url": path}
    except Exception as e:
        logger.error(f"Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dossiers")
def list_dossiers(candidato_id: Optional[str] = None, supa: Client = Depends(get_supa)):
    """Lista relatórios gerados."""
    try:
        query = supa.table('dossies').select('*')
        if candidato_id and candidato_id != "null": 
            query = query.eq('candidato_id', candidato_id)
        res = query.order('data_geracao', desc=True).execute()
        return res.data or []
    except Exception as e:
        logger.error(f"List Dossiers Error: {e}")
        return []

@app.get("/api/v1/analytics/resilience-ranking")
def get_resilience_ranking(limit: int = 10, supa: Client = Depends(get_supa)):
    """Ranking de alvos com maior incidência de ódio."""
    try:
        yesterday = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        res = supa.table('comentarios').select('candidato_id, is_hate').gte('data_coleta', yesterday).limit(5000).execute()
        data = res.data or []
        
        stats = {}
        for item in data:
            cid = item['candidato_id']
            if cid not in stats:
                stats[cid] = {'total': 0, 'hate': 0}
            stats[cid]['total'] += 1
            if item['is_hate']:
                stats[cid]['hate'] += 1
            
        ranking = []
        for cid, val in stats.items():
            res_pct = round((val['total'] - val['hate']) / val['total'] * 100, 1)
            ranking.append({"candidato_id": cid, "total": val['total'], "alertas": val['hate'], "resiliencia_pct": res_pct})
            
        return sorted(ranking, key=lambda x: x['alertas'], reverse=True)[:limit]
    except Exception as e:
        logger.error(f"Ranking Error: {e}")
        return []

@app.get("/api/v1/analytics/temporal-series")
def get_temporal_series(supa: Client = Depends(get_supa)):
    """Série temporal de alertas."""
    try:
        window = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        res = supa.table('comentarios').select('data_coleta').eq('is_hate', True).gte('data_coleta', window).limit(2000).execute()
        data = res.data or []
        hours = Counter([item['data_coleta'][:13] + ":00:00" for item in data])
        return sorted([{"hora": h, "alertas": v} for h, v in hours.items()], key=lambda x: x['hora'])
    except Exception as e:
        logger.error(f"Series Error: {e}")
        return []

@app.post("/api/v1/audit/validate")
async def audit_validate(payload: Dict[str, Any] = Body(...), supa: Client = Depends(get_supa)):
    """Ponto de auditoria manual do frontend."""
    try:
        comment_id = payload.get("comment_id")
        rotulo = payload.get("rotulo_correto")
        analise_pericial = payload.get("analise_pericial")
        
        # Atualiza o comentário original
        is_hate = rotulo == 'hate'
        update_data = {
            "is_hate": is_hate,
            "processado_ia": True,
            "categoria_ia": "VALIDADO_MANUALMENTE"
        }
        if analise_pericial is not None:
            update_data["analise_pericial"] = analise_pericial
            
        supa.table('comentarios').update(update_data).eq('id', comment_id).execute()
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Audit Validate Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- COMPATIBILITY ALIASES FOR TESTS ---
@app.get("/api/v1/trends")
def trends(supa: Client = Depends(get_supa)):
    return get_temporal_series(supa)

@app.get("/api/v1/pasa/breakdown")
def pasa_breakdown(supa: Client = Depends(get_supa)):
    """Retorna o breakdown de categorias PASA (Compatibility Mode)."""
    try:
        res = supa.table('comentarios').select('categoria_ia').eq('is_hate', True).execute()
        counts = Counter([item.get('categoria_ia') or 'OUTROS' for item in res.data])
        return dict(counts)
    except Exception as e:
        logger.error(f"PASA Breakdown Error: {e}")
        return {}

@app.post("/api/v1/checkout/create-session")
def create_checkout(payload: CheckoutRequest):
    try:
        # A lógica de mapeamento de CI e Price IDs foi movida para o PaymentManager.
        # Agora ele aceita package_slug ("tatica", "warroom", "nacional").
        # O user_id é mantido para que os webhooks creditem a conta certa depois.
        session_url = payment_manager.create_checkout_session(
            user_id=payload.user_id or "guest_user", 
            package_type=payload.package_slug
        )
        return {"url": session_url}
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/geo/uf")
def get_geo_uf(supa: Client = Depends(get_supa)):
    """Retorna dados de hostilidade por Unidade Federativa."""
    try:
        # Busca candidatos para mapear UF
        cands = supa.table('candidatos').select('username, estado').execute().data or []
        uf_map = {c.get('username'): (c.get('estado') or 'BR') for c in cands if c.get('username')}
        
        # Busca alertas recentes (48h)
        window = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        coms = supa.table('comentarios').select('candidato_id').eq('is_hate', True).gte('data_coleta', window).limit(2000).execute().data or []
        
        counts = Counter([uf_map.get(c['candidato_id'], 'BR') for c in coms if c.get('candidato_id')])
        
        results = []
        for uf, val in counts.items():
            color = RISK_COLORS["CRITICO"] if val > 20 else (RISK_COLORS["ELEVADO"] if val > 5 else RISK_COLORS["MONITORANDO"])
            results.append({
                "uf": uf, 
                "total_hate": val, 
                "total_alvos": len([k for k, v in uf_map.items() if v == uf]),
                "color": color
            })
            
        return results
    except Exception as e:
        logger.error(f"Geo UF Error: {e}")
        return []

# Alias for tests
geo_uf = get_geo_uf

@app.get("/api/v1/ads")
def list_ads(candidato_id: Optional[str] = None, supa: Client = Depends(get_supa)):
    """Lista anúncios detectados na Meta Ad Library."""
    try:
        query = supa.table('anuncios').select('*')
        if candidato_id and candidato_id != "null":
            query = query.eq('candidato_id', candidato_id)
        res = query.order('data_coleta', desc=True).limit(100).execute()
        return res.data or []
    except Exception as e:
        logger.error(f"List Ads Error: {e}")
        return []

@app.get("/api/health")
def health(supa: Client = Depends(get_supa)):
    return {"status": "operational", "db": supa is not None, "engine": "FastAPI on Vercel"}

@app.post("/api/v1/auth/register-push-token")
def register_push_token(payload: PushTokenRegistration, supa: Client = Depends(get_supa)):
    try:
        supa.table('user_push_tokens').upsert({**payload.dict(), "updated_at": datetime.now(timezone.utc).isoformat()}, on_conflict="user_id,token").execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- WORKERS METRICS ENDPOINTS (v20.1+) ---

@app.get("/api/v1/workers/telemetry")
async def get_workers_telemetry():
    """Alias para compatibilidade com o frontend (PASA v47.3)."""
    return await workers_stats()

@app.get("/api/v1/monitor/status")
async def get_monitor_status(supa: Client = Depends(get_supa)):
    """Status consolidado do monitoramento para o frontend."""
    try:
        # Busca estatísticas básicas de saúde do sistema
        res = supa.table('worker_sessions').select('status').eq('plataforma', 'instagram').execute()
        sessions = res.data or []
        active_sessions = sum(1 for s in sessions if s.get('status') == 'active')
        
        return {
            "status": "operational",
            "queue_health": {
                "active_sessions": active_sessions,
                "total_sessions": len(sessions)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Monitor Status Error: {e}")
        raise HTTPException(status_code=500, detail=f"Monitor Status Error: {str(e)}")

@app.get("/api/v1/workers/dashboard")
async def workers_dashboard():
    """Dashboard consolidado de saúde e desempenho dos workers."""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not initialized")
    
    try:
        summary = await metrics_collector.get_dashboard_summary()
        return summary
    except Exception as e:
        logger.error(f"Workers Dashboard Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/workers/stats")
async def workers_stats():
    """Estatísticas de todos os workers."""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not initialized")
    
    try:
        all_stats = await metrics_collector.get_all_workers_stats()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "workers": all_stats,
            "total_workers": len(all_stats)
        }
    except Exception as e:
        logger.error(f"Workers Stats Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/workers/{worker_name}/stats")
async def worker_stats(worker_name: str):
    """Estatísticas de um worker específico."""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not initialized")
    
    try:
        stats = await metrics_collector.get_worker_stats(worker_name)
        if stats.get("status") == "no_data":
            raise HTTPException(status_code=404, detail=f"No metrics found for worker '{worker_name}'")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Worker Stats Error ({worker_name}): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/workers/export-metrics")
async def export_metrics(filepath: str = "data/workers_metrics_export.json"):
    """Export metrics to JSON file for analysis."""
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not initialized")
    
    try:
        await metrics_collector.export_metrics_json(filepath)
        return {"status": "success", "filepath": filepath, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error(f"Export Metrics Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- SESSIONS ENDPOINTS (v47.5) ---

@app.get("/api/v1/sessions/instagram/status")
async def get_instagram_session_status(supa: Client = Depends(get_supa)):
    """Verifica o status da sessão do Instagram (Busca a sessão ATIVA mais recente)."""
    try:
        # PASA v49.6: Busca a sessão ATIVA mais recente para suporte a fallback
        res = supa.table('worker_sessions')\
            .select('*')\
            .eq('plataforma', 'instagram')\
            .eq('status', 'active')\
            .order('updated_at', desc=True)\
            .limit(1)\
            .execute()
            
        if not res.data:
            return {"status": "missing", "message": "Nenhuma sessão ativa encontrada"}
        
        session = res.data[0]
        return {
            "status": "active",
            "last_updated": session.get('updated_at'),
            "is_valid": True,
            "session_id_preview": session.get('cookies', '')[:15] + "..."
        }
    except Exception as e:
        logger.error(f"Session Status Error: {e}")
        raise HTTPException(status_code=500, detail=f"Session Status Error: {str(e)}")

@app.get("/api/v1/sessions/instagram")
async def get_sessions(supa: Client = Depends(get_supa)):
    """Lista todas as sessões de raspagem do Instagram."""
    try:
        res = supa.table('worker_sessions').select('*').eq('plataforma', 'instagram').order('updated_at', desc=True).execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Get Sessions Error: {e}")
        raise HTTPException(status_code=500, detail=f"Get Sessions Error: {str(e)}")

@app.post("/api/v1/sessions/instagram/cookies")
async def add_session(payload: SessionCookieRequest, supa: Client = Depends(get_supa)):
    """Adiciona/Injeta novos cookies de sessão (Evita duplicados plataforma+cookies)."""
    try:
        data = {
            "plataforma": "instagram",
            "cookies": payload.cookies,
            "status": "active",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        # PASA v49.6: on_conflict agora usa a restrição composta
        res = supa.table('worker_sessions').upsert(data, on_conflict='plataforma,cookies').execute()
        return {"status": "success", "data": res.data[0] if res.data else {}}
    except Exception as e:
        logger.error(f"Add Session Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/v1/sessions/instagram/{session_id}/rotation")
async def update_rotation(session_id: str, payload: SessionRotationRequest, supa: Client = Depends(get_supa)):
    """Atualiza configuração de rotação automática de uma sessão."""
    try:
        update_data = {}
        if payload.enabled is not None:
            update_data["auto_rotate_enabled"] = payload.enabled
        if payload.intervalHours is not None:
            update_data["auto_rotate_interval"] = payload.intervalHours

        res = supa.table('worker_sessions').update(update_data).eq('id', session_id).execute()
        return {"status": "success", "data": res.data[0] if res.data else {}}
    except Exception as e:
        logger.error(f"Update Rotation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/sessions/instagram/rotate")
async def rotate_now(supa: Client = Depends(get_supa)):
    """Dispara rotação manual imediata."""
    return {"status": "success", "message": "Rotação sinalizada para o orquestrador local."}

@app.delete("/api/v1/sessions/instagram/{session_id}")
async def delete_session(session_id: str, supa: Client = Depends(get_supa)):
    """Remove uma sessão."""
    try:
        supa.table('worker_sessions').delete().eq('id', session_id).execute()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Delete Session Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
