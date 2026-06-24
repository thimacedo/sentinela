"""
Coleta e persistência de métricas estruturadas de scraping.
Habilitação observabilidade para diagnóstico e otimização.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScrapeMetrics:
    """Métricas estruturadas de um ciclo de scrape"""
    
    # Identificação
    username: str
    worker_id: str
    cycle_number: int
    
    # Timestamps
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Durações
    total_duration_s: float = 0.0
    healing_total_duration_s: float = 0.0
    extraction_duration_s: float = 0.0
    
    # Contadores de extração
    posts_found: int = 0
    posts_processed: int = 0
    comments_collected: int = 0
    
    # Healing
    healing_attempts: int = 0
    healing_successes: int = 0
    healing_failures: int = 0
    healing_repeated_selectors: int = 0
    
    # Seletores
    selectors_used: List[str] = field(default_factory=list)
    selectors_from_cache: int = 0
    selectors_from_ai: int = 0
    
    # Validação
    selectors_validated_successfully: int = 0
    selectors_validation_failed: int = 0
    
    # Resultado
    success: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    is_control_signal: bool = False  # True se foi healer restart, etc.
    
    def end_cycle(self, success: bool, error_code: str = None, error_msg: str = None):
        """Marca o fim do ciclo de extração"""
        self.end_time = datetime.now()
        self.total_duration_s = (self.end_time - self.start_time).total_seconds()
        self.success = success
        self.error_code = error_code
        self.error_message = error_msg
    
    def to_dict(self) -> dict:
        """Converte para dicionário com timestamps serializáveis"""
        data = asdict(self)
        data["start_time"] = self.start_time.isoformat()
        data["end_time"] = self.end_time.isoformat() if self.end_time else None
        return data
    
    def to_json(self, pretty: bool = True) -> str:
        """Converte para JSON"""
        data = self.to_dict()
        indent = 2 if pretty else None
        return json.dumps(data, ensure_ascii=False, indent=indent)


class MetricsCollector:
    """
    Coleta métricas durante ciclo de scrape e persiste em disco.
    """
    
    def __init__(self, metrics_dir: Path = None):
        self.metrics_dir = metrics_dir or Path("logs/metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_metrics: Optional[ScrapeMetrics] = None
        self.logger = logger
    
    def start_cycle(
        self,
        username: str,
        worker_id: str,
        cycle_number: int,
    ) -> ScrapeMetrics:
        """Inicia coleta de métricas para novo ciclo"""
        self.current_metrics = ScrapeMetrics(
            username=username,
            worker_id=worker_id,
            cycle_number=cycle_number,
            start_time=datetime.now(),
        )
        return self.current_metrics
    
    def record_healing_attempt(
        self,
        success: bool,
        duration_s: float,
        selector: str,
    ):
        """Registra tentativa de healing"""
        if not self.current_metrics:
            return
        
        self.current_metrics.healing_attempts += 1
        self.current_metrics.healing_total_duration_s += duration_s
        
        if success:
            self.current_metrics.healing_successes += 1
        else:
            self.current_metrics.healing_failures += 1
        
        if selector not in self.current_metrics.selectors_used:
            self.current_metrics.selectors_used.append(selector)
    
    def record_repeated_selector_detected(self):
        """Registra quando IA propõe seletor repetido"""
        if self.current_metrics:
            self.current_metrics.healing_repeated_selectors += 1
    
    def record_selector_validation(self, success: bool):
        """Registra resultado de validação de seletor"""
        if not self.current_metrics:
            return
        
        if success:
            self.current_metrics.selectors_validated_successfully += 1
        else:
            self.current_metrics.selectors_validation_failed += 1
    
    def record_selector_source(self, from_cache: bool):
        """Registra origem do seletor (cache ou IA)"""
        if not self.current_metrics:
            return
        
        if from_cache:
            self.current_metrics.selectors_from_cache += 1
        else:
            self.current_metrics.selectors_from_ai += 1
    
    def record_extraction_results(
        self,
        posts_found: int,
        posts_processed: int,
        comments_collected: int,
        extraction_duration_s: float,
    ):
        """Registra resultados da extração"""
        if not self.current_metrics:
            return
        
        self.current_metrics.posts_found = posts_found
        self.current_metrics.posts_processed = posts_processed
        self.current_metrics.comments_collected = comments_collected
        self.current_metrics.extraction_duration_s = extraction_duration_s
    
    def end_cycle(
        self,
        success: bool,
        error_code: str = None,
        error_message: str = None,
    ) -> Optional[ScrapeMetrics]:
        """Finaliza coleta e persiste métricas"""
        if not self.current_metrics:
            return None
        
        self.current_metrics.end_cycle(success, error_code, error_message)
        
        # Persiste em disco
        filename = self._get_metrics_filename()
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.current_metrics.to_json())
            
            self.logger.debug(f"📊 Métricas persistidas: {filename}")
        
        except Exception as e:
            self.logger.error(f"❌ Erro ao persistir métricas: {e}")
        
        metrics = self.current_metrics
        self.current_metrics = None
        return metrics
    
    def _get_metrics_filename(self) -> Path:
        """Gera nome de arquivo para as métricas"""
        if not self.current_metrics:
            raise ValueError("Nenhum ciclo ativo")
        
        timestamp = self.current_metrics.start_time.strftime("%Y%m%d_%H%M%S")
        username = self.current_metrics.username.replace("@", "")
        worker_id = self.current_metrics.worker_id.replace(":", "_")
        
        filename = f"{timestamp}_{username}_{worker_id}_c{self.current_metrics.cycle_number}.json"
        return self.metrics_dir / filename


class MetricsAnalyzer:
    """Analisa métricas persistidas para diagnóstico e alertas"""
    
    def __init__(self, metrics_dir: Path = None):
        self.metrics_dir = metrics_dir or Path("logs/metrics")
        self.logger = logger
    
    def get_health_status(self, window_size: int = 20) -> dict:
        """
        Analisa últimas N execuções e retorna status de saúde.
        """
        metrics = self._load_recent_metrics(window_size)
        
        if len(metrics) < 5:
            return {"status": "insufficient_data", "metrics_count": len(metrics)}
        
        failures = sum(1 for m in metrics if not m.get("success"))
        failure_rate = failures / len(metrics)
        
        avg_comments = sum(m.get("comments_collected", 0) for m in metrics) / len(metrics)
        
        avg_healing_attempts = sum(
            m.get("healing_attempts", 0) for m in metrics
        ) / len(metrics)
        
        health_status = "healthy"
        if failure_rate > 0.7:
            health_status = "critical"
        elif failure_rate > 0.4:
            health_status = "degraded"
        
        return {
            "status": health_status,
            "metrics_analyzed": len(metrics),
            "failure_rate": round(failure_rate, 2),
            "avg_comments_collected": round(avg_comments, 2),
            "avg_healing_attempts": round(avg_healing_attempts, 2),
            "critical_if_failure_rate_above": 0.7,
        }
    
    def _load_recent_metrics(self, count: int = 20) -> List[dict]:
        """Carrega últimas N métricas persistidas"""
        if not self.metrics_dir.exists():
            return []
        
        files = sorted(
            self.metrics_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:count]
        
        metrics = []
        for filepath in files:
            try:
                with open(filepath) as f:
                    metrics.append(json.load(f))
            except Exception as e:
                self.logger.warning(f"Erro lendo {filepath}: {e}")
        
        return metrics
