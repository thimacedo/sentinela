from fastapi import FastAPI, HTTPException, Body, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Literal
from supabase import create_client, Client
import os
import sys
import hashlib
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
    metrics_collector = None

# Configuração de logs
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("sentinela-api")

load_dotenv()

# Import CORS configuration
from api.config.cors import CORS_CONFIG, validate_cors_config

# --- CONSTANTS ---
PASA_CONFIG = {
    "ODIO_IDENTITARIO": {"label": "Ódio Identitário", "color": "#ef4444", "icon": "users"},
    "VIOLENCIA_GENERO": {"label": "Violência de Gênero", "color": "#ec4899", "icon": "shield-alert"},
    "AMEACA": {"label": "Ameaça", "color": "#f97316", "icon": "alert-octagon"},
    "INSULTO_AD_HOMINEM": {"label": "Insulto Ad Hominem", "color": "#f59e0b", "icon": "swords"},
    "ATAQUE_INSTITUCIONAL": {"label": "Ataque Institucional", "color": "#8b5cf6", "icon": "landmark"},
    "DANO_A_IMAGEM": {"label": "Dano à Imagem", "color": "#06b6d4", "icon": "scale"}
}

HATE_CATEGORIES = (
    "ODIO_IDENTITARIO", 
    "VIOLENCIA_GENERO", 
    "AMEACA", 
    "INSULTO_AD_HOMINEM", 
    "ATAQUE_INSTITUCIONAL", 
    "DANO_A_IMAGEM",
    "MISOGINIA_POLITICA",
    "CAMPANHA_COORDENADA",
    "NEGATIVO"
)
RISK_COLORS = {"CRITICO": "#ef4444", "ELEVADO": "#f59e0b", "MONITORANDO": "#06b6d4", "CONTROLADO": "#10b981"}

app = FastAPI()
validate_cors_config()
app.add_middleware(
    CORSMiddleware, 
    **CORS_CONFIG
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
    """Dependency para obter cliente Supabase."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise HTTPException(status_code=500, detail="Database credentials missing")
    try:
        return create_client(url, key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Supabase: {str(e)}")

# --- MODELS ---
class CheckoutRequest(BaseModel):
    user_id: str
    package_slug: str
    price_id: Optional[str] = None

class DossierGenerateRequest(BaseModel):
    candidato_id: str
    user_id: str
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

class CommandRequest(BaseModel):
    command: Literal['PAUSE', 'RESUME']

@app.post("/api/v1/command")
def post_command(payload: CommandRequest, supa: Client = Depends(get_supa)):
    try:
        res = supa.table('system_commands').insert({
            "command": payload.command,
            "status": "PENDING",
            "issued_at": datetime.now(timezone.utc).isoformat()
        }).execute()
        return {"status": "success", "id": res.data[0].get('id') if res.data else None}
    except Exception as e:
        logger.error(f"Command Insert Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/webhooks/stripe")
async def stripe_webhook(request: Request, supa: Client = Depends(get_supa)):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Server webhook secret missing")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event['type'] in ['checkout.session.completed', 'checkout.session.async_payment_succeeded']:
        session = event['data']['object']
        if session.get('payment_status') != 'paid':
            return {"status": "ignored"}
        metadata = session.get('metadata', {})
        user_id = metadata.get('user_id')
        ci_amount = metadata.get('ci_amount')
        if user_id and ci_amount:
            try:
                # PASA v94.1 - Compliance com Schema v28.0 (CI Governance)
                description = f"Compra de pacote via Stripe: {metadata.get('package_type', 'N/A')}"
                res = supa.rpc('process_ci_transaction', {
                    "p_user_id": user_id,
                    "p_amount": int(ci_amount),
                    "p_type": "PURCHASE",
                    "p_description": description
                }).execute()
                
                if res.data and not res.data.get('success'):
                    logger.error(f"❌ [CI Fraud] Falha na recarga via Webhook para {user_id}: {res.data.get('message')}")
                else:
                    logger.info(f"✅ [CI] Recarga de {ci_amount} CI processada para {user_id}")
                    
            except Exception as e:
                logger.error(f"Webhook CI Error: {e}")
    return {"status": "success"}

class CIConsumeRequest(BaseModel):
    user_id: str
    amount: int
    type: str
    description: str

@app.post("/api/v1/ci/consume")
async def consume_ci(payload: CIConsumeRequest, supa: Client = Depends(get_supa)):
    """
    Endpoint centralizado para consumo de Créditos de Inteligência (CI).
    Garante o log de tentativas de fraude ou saldo insuficiente.
    """
    try:
        # Garante que o amount seja negativo para consumo
        amount = -abs(payload.amount)
        
        res = supa.rpc('process_ci_transaction', {
            "p_user_id": payload.user_id,
            "p_amount": amount,
            "p_type": payload.type,
            "p_description": payload.description
        }).execute()
        
        if res.data and not res.data.get('success'):
            msg = res.data.get('message', 'Erro desconhecido')
            if "insuficiente" in msg.lower() or "fraude" in msg.lower():
                logger.warning(f"🚨 [CI Fraud] Tentativa de consumo sem saldo! User: {payload.user_id} | Amount: {amount} | Reason: {msg}")
                raise HTTPException(status_code=402, detail=msg)
            else:
                logger.error(f"❌ [CI Error] Falha no consumo para {payload.user_id}: {msg}")
                raise HTTPException(status_code=400, detail=msg)
        
        return {"status": "success", "new_balance": res.data.get('new_balance')}
        
    except HTTPException: raise
    except Exception as e:
        logger.error(f"CI Consume Exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- UTILS ---
def calculate_risk(item: Dict[str, Any]):
    totais = item.get('comentarios_totais_count', 0) or 0
    odio = item.get('comentarios_odio_count', 0) or 0
    if totais < odio: totais = odio
    if totais == 0:
        score = min(100, 20 + (odio * 2)) if odio > 0 else 0
        nivel = 'CONTROLADO' if score == 0 else 'MONITORANDO'
        return score, nivel, RISK_COLORS[nivel]
    ratio = odio / totais
    score = min(100, int(ratio * 250) + min(35, odio * 1.5))
    if score >= 75: return score, 'CRITICO', RISK_COLORS["CRITICO"]
    if score >= 45: return score, 'ELEVADO', RISK_COLORS["ELEVADO"]
    if score >= 15: return score, 'MONITORANDO', RISK_COLORS["MONITORANDO"]
    return score, 'CONTROLADO', RISK_COLORS["CONTROLADO"]

# --- ENDPOINTS ---

@app.get("/api/v1/summary")
def summary(request: Request, supa: Client = Depends(get_supa)):
    """Retorna KPIs consolidados (MCA v2.2 Compliant)."""
    try:
        org_id = request.headers.get("X-Organization-Id")
        now_utc = datetime.now(timezone.utc)
        query_c = supa.table('candidatos').select('id', count='exact').eq('status_monitoramento', 'Ativo')
        if org_id: query_c = query_c.eq('organization_id', org_id)
        c_res = query_c.execute()
        
        last_comment_res = supa.table('comentarios').select('data_coleta').order('data_coleta', desc=True).limit(1).execute()
        last_update = last_comment_res.data[0]['data_coleta'] if last_comment_res.data else now_utc.isoformat()

        query_total = supa.table('comentarios').select('id', count='exact')
        query_hate = supa.table('comentarios').select('id', count='exact').in_('categoria_ia', HATE_CATEGORIES)
        if org_id:
            query_total = query_total.eq('organization_id', org_id)
            query_hate = query_hate.eq('organization_id', org_id)

        t_res_total = query_total.execute()
        t_res_hate = query_hate.execute()
        t_lifetime = t_res_total.count or 0
        h_lifetime = t_res_hate.count or 0
        res_val = round(((t_lifetime - h_lifetime) / t_lifetime) * 100, 1) if t_lifetime > 0 else 100.0

        return {
            "total_monitorados": c_res.count or 0,
            "total_alertas": h_lifetime,
            "total_amostra": t_lifetime,
            "resiliencia": res_val,
            "timestamp": last_update
        }
    except Exception as e:
        logger.error(f"Summary Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/targets")
def get_targets(request: Request, limit: int = 50, supa: Client = Depends(get_supa)):
    """Retorna alvos monitorados com métricas de ódio atualizadas."""
    try:
        org_id = request.headers.get("X-Organization-Id")
        query_cand = supa.table('candidatos').select('*').eq('status_monitoramento', 'Ativo').order('nota_relevancia', desc=True)
        if org_id: query_cand = query_cand.eq('organization_id', org_id)
        candidates = query_cand.execute().data or []

        active_usernames = [c.get('username') for c in candidates if c.get('username')]
        if not active_usernames: return []

        # Amostra recente para estatísticas de ódio
        h_res = supa.table('comentarios').select('candidato_id, categoria_ia')\
            .in_('categoria_ia', HATE_CATEGORIES)\
            .in_('candidato_id', active_usernames)\
            .order('data_coleta', desc=True).limit(5000).execute().data or []
            
        all_res = supa.table('comentarios').select('candidato_id')\
            .in_('candidato_id', active_usernames)\
            .order('data_coleta', desc=True).limit(5000).execute().data or []
        
        counts_odio = Counter([h['candidato_id'] for h in h_res])
        counts_totais = Counter([a['candidato_id'] for a in all_res])
        
        breakdowns = {}
        for h in h_res:
            cid, cat = h['candidato_id'], h['categoria_ia'] or 'OUTROS'
            if cid not in breakdowns: breakdowns[cid] = Counter()
            breakdowns[cid][cat] += 1
        
        enriched = []
        for item in candidates:
            un = item.get('username')
            item['comentarios_odio_count'] = counts_odio.get(un, 0)
            item['comentarios_totais_count'] = counts_totais.get(un, 0)
            score, nivel, color = calculate_risk(item)
            enriched.append({**item, "score_risco": score, "nivel_risco": nivel, "color": color, "breakdown": dict(breakdowns.get(un, {}))})
        return enriched[:limit]
    except Exception as e:
        logger.error(f"Targets Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/alerts/active")
def get_active_alerts(limit: int = 20, supa: Client = Depends(get_supa)):
    try:
        res = supa.table('comentarios').select('*, candidatos(username)')\
            .in_('categoria_ia', HATE_CATEGORIES)\
            .order('data_coleta', desc=True).limit(limit).execute()
        return res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/alerts/false-positive")
def mark_false_positive(payload: FalsePositiveRequest, supa: Client = Depends(get_supa)):
    try:
        supa.table('comentarios').update({
            "is_hate": False, 
            "processado_ia": True, 
            "categoria_ia": "FALSO_POSITIVO_MANUAL"
        }).eq('id', payload.id).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/marketing-kpis")
def get_marketing_kpis(supa: Client = Depends(get_supa)):
    try:
        total = supa.table('comentarios').select('id', count='exact').execute().count or 0
        hate = supa.table('comentarios').select('id', count='exact').in_('categoria_ia', HATE_CATEGORIES).execute().count or 0
        res_cat = supa.table('comentarios').select('categoria_ia').in_('categoria_ia', HATE_CATEGORIES).limit(5000).execute()
        categories = [c['categoria_ia'] for c in (res_cat.data or []) if c.get('categoria_ia')]
        return {
            "iceberg": {"visible_neutral": total - hate, "detected_hate": hate, "hidden_irony": int(hate * 0.3)},
            "vulnerability_map": dict(Counter(categories)),
            "roi": {"horas_poupadas": total // 300, "custo_humano_brl": (total // 300) * 150}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/resilience-ranking")
def get_resilience_ranking(limit: int = 10, supa: Client = Depends(get_supa)):
    try:
        window = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        res = supa.table('comentarios').select('candidato_id, categoria_ia').gte('data_coleta', window).limit(5000).execute()
        stats = {}
        for item in (res.data or []):
            cid = item['candidato_id']
            if cid not in stats: stats[cid] = {'total': 0, 'hate': 0}
            stats[cid]['total'] += 1
            if item.get('categoria_ia') in HATE_CATEGORIES: stats[cid]['hate'] += 1
        ranking = []
        for cid, val in stats.items():
            pct = round((val['total'] - val['hate']) / val['total'] * 100, 1)
            ranking.append({"candidato_id": cid, "total": val['total'], "alertas": val['hate'], "resiliencia_pct": pct})
        return sorted(ranking, key=lambda x: x['alertas'], reverse=True)[:limit]
    except Exception as e: return []

@app.get("/api/v1/analytics/temporal-series")
def get_temporal_series(supa: Client = Depends(get_supa)):
    try:
        window = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        res = supa.table('comentarios').select('data_coleta').in_('categoria_ia', HATE_CATEGORIES).gte('data_coleta', window).limit(2000).execute()
        hours = Counter([item['data_coleta'][:13] + ":00:00" for item in (res.data or [])])
        return sorted([{"hora": h, "alertas": v} for h, v in hours.items()], key=lambda x: x['hora'])
    except Exception as e: return []

@app.get("/api/v1/geo/uf")
def get_geo_uf(supa: Client = Depends(get_supa)):
    try:
        cands = supa.table('candidatos').select('username, estado').execute().data or []
        uf_map = {c.get('username'): (c.get('estado') or 'BR') for c in cands if c.get('username')}
        window = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        coms = supa.table('comentarios').select('candidato_id').in_('categoria_ia', HATE_CATEGORIES).gte('data_coleta', window).limit(2000).execute().data or []
        counts = Counter([uf_map.get(c['candidato_id'], 'BR') for c in coms if c.get('candidato_id')])
        return [{"uf": k, "total_hate": v, "color": RISK_COLORS["CRITICO"] if v > 20 else RISK_COLORS["MONITORANDO"]} for k, v in counts.items()]
    except Exception as e: return []

@app.get("/api/health")
def health(supa: Client = Depends(get_supa)):
    return {"status": "operational", "db": supa is not None}

@app.get("/api/v1/networks")
def get_networks(supa: Client = Depends(get_supa)):
    try:
        res = supa.table('redes_coordenadas').select('*').order('created_at', desc=True).limit(10).execute()
        return res.data or []
    except Exception as e: return []

@app.get("/api/v1/pasa/breakdown")
def pasa_breakdown(supa: Client = Depends(get_supa)):
    try:
        res = supa.table('comentarios').select('categoria_ia').in_('categoria_ia', HATE_CATEGORIES).execute()
        return dict(Counter([item.get('categoria_ia') or 'OUTROS' for item in (res.data or [])]))
    except Exception as e: return {}

@app.get("/api/v1/analytics/demographics")
def get_demographics(supa: Client = Depends(get_supa)):
    try:
        res = supa.table('comentarios').select('candidatos(username, sexo, partido, estado, ideologia)')\
            .in_('categoria_ia', HATE_CATEGORIES).order('data_coleta', desc=True).limit(5000).execute()
        from collections import defaultdict
        stats = {"sexo": defaultdict(int), "partido": defaultdict(int)}
        for item in (res.data or []):
            c = item.get('candidatos')
            if not c: continue
            if c.get('sexo'): stats['sexo'][c['sexo']] += 1
            if c.get('partido'): stats['partido'][c['partido']] += 1
        return {"sexo": [{"name": k, "value": v} for k, v in stats["sexo"].items()], 
                "partido": [{"name": k, "value": v} for k, v in stats["partido"].items()]}
    except Exception as e: return {}

# --- FINANCE & AUDIT ANALYTICS (v94.2) ---

@app.get("/api/v1/analytics/spending/providers")
def get_spending_by_provider(supa: Client = Depends(get_supa)):
    """Retorna o throughput e eficiência por provedor via View."""
    try:
        res = supa.table('view_spending_by_provider').select('*').execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Provider Spending Error: {e}")
        return []

@app.get("/api/v1/analytics/spending/targets")
def get_spending_by_target(supa: Client = Depends(get_supa)):
    """Retorna o consumo estimado por candidato via RPC."""
    try:
        res = supa.rpc('get_spending_by_target', {}).execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Target Spending Error: {e}")
        return []

@app.get("/api/v1/analytics/spending/errors")
def get_cloud_error_summary(supa: Client = Depends(get_supa)):
    """Retorna o sumário de falhas por provedor via RPC."""
    try:
        res = supa.rpc('get_cloud_error_summary', {}).execute()
        return res.data or []
    except Exception as e:
        logger.error(f"Cloud Error Summary Error: {e}")
        return []
