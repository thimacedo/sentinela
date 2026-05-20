from fastapi import FastAPI
from app.api.audit_routes import router as audit_router
from app.api.monitor_routes import router as monitor_router
from app.api.session_routes import router as session_router
from app.scheduler.queue_processor import QueueProcessor

app = FastAPI(title="Sentinela Democrática", version="20.0")

app.include_router(audit_router)
app.include_router(monitor_router)
app.include_router(session_router)

@app.on_event("startup")
def startup_event():
    """PASA v20: Inicia o motor de autonomia na inicialização do servidor."""
    processor = QueueProcessor(poll_interval=30)
    processor.start_async()

@app.get("/")
def read_root():
    return {"status": "online", "pasa_version": "20", "mode": "autonomous"}
