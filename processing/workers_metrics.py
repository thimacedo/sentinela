"""
Worker Performance Metrics Module
Tracks latency, throughput, and health of all processing workers.
"""

import time
import json
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Any, Optional
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)


class WorkerMetric:
    """Individual metric snapshot for a worker execution."""
    
    def __init__(self, worker_name: str, batch_size: int, start_time: float, end_time: float, 
                 items_processed: int, success: bool, error_msg: Optional[str] = None):
        self.worker_name = worker_name
        self.batch_size = batch_size
        self.start_time = start_time
        self.end_time = end_time
        self.duration_ms = (end_time - start_time) * 1000
        self.items_processed = items_processed
        self.success = success
        self.error_msg = error_msg
        self.timestamp = datetime.now(UTC).isoformat()
        
        # Calculated metrics
        self.throughput = items_processed / max(self.duration_ms / 1000, 0.001)  # items/sec
        self.avg_latency_per_item = self.duration_ms / max(items_processed, 1)  # ms/item
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "worker": self.worker_name,
            "timestamp": self.timestamp,
            "duration_ms": round(self.duration_ms, 2),
            "items_processed": self.items_processed,
            "throughput_items_per_sec": round(self.throughput, 2),
            "avg_latency_ms_per_item": round(self.avg_latency_per_item, 2),
            "batch_size": self.batch_size,
            "success": self.success,
            "error": self.error_msg
        }


class WorkerMetricsCollector:
    """Central metrics collection and aggregation for all workers."""
    
    def __init__(self, retention_hours: int = 24):
        self.metrics_history: Dict[str, List[WorkerMetric]] = defaultdict(list)
        self.retention_hours = retention_hours
        self.lock = asyncio.Lock()
    
    async def record_execution(self, worker_name: str, batch_size: int, start_time: float,
                              end_time: float, items_processed: int, success: bool,
                              error_msg: Optional[str] = None) -> None:
        """Record a single worker execution."""
        async with self.lock:
            metric = WorkerMetric(
                worker_name=worker_name,
                batch_size=batch_size,
                start_time=start_time,
                end_time=end_time,
                items_processed=items_processed,
                success=success,
                error_msg=error_msg
            )
            self.metrics_history[worker_name].append(metric)
            
            # Cleanup old metrics
            await self._cleanup_old_metrics()
            
            logger.info(f"📊 [{worker_name}] {metric.items_processed} items in {metric.duration_ms:.0f}ms "
                       f"({metric.throughput:.2f} items/sec)")
    
    async def _cleanup_old_metrics(self) -> None:
        """Remove metrics older than retention period."""
        cutoff_time = datetime.now(UTC) - timedelta(hours=self.retention_hours)
        for worker_name in self.metrics_history:
            self.metrics_history[worker_name] = [
                m for m in self.metrics_history[worker_name]
                if datetime.fromisoformat(m.timestamp) > cutoff_time
            ]
    
    async def get_worker_stats(self, worker_name: str) -> Dict[str, Any]:
        """Get aggregated statistics for a specific worker."""
        async with self.lock:
            metrics = self.metrics_history.get(worker_name, [])
            
            if not metrics:
                return {
                    "worker": worker_name,
                    "status": "no_data",
                    "executions": 0,
                    "last_execution": None
                }
            
            successful = [m for m in metrics if m.success]
            failed = [m for m in metrics if not m.success]
            
            if successful:
                avg_duration = sum(m.duration_ms for m in successful) / len(successful)
                avg_throughput = sum(m.throughput for m in successful) / len(successful)
                total_items = sum(m.items_processed for m in successful)
            else:
                avg_duration = 0
                avg_throughput = 0
                total_items = 0
            
            last_metric = metrics[-1]
            
            return {
                "worker": worker_name,
                "status": "healthy" if len(successful) > len(failed) else "degraded",
                "total_executions": len(metrics),
                "successful_executions": len(successful),
                "failed_executions": len(failed),
                "success_rate": round((len(successful) / len(metrics) * 100), 1) if metrics else 0,
                "avg_duration_ms": round(avg_duration, 2),
                "avg_throughput_items_per_sec": round(avg_throughput, 2),
                "total_items_processed": total_items,
                "last_execution": {
                    "timestamp": last_metric.timestamp,
                    "duration_ms": round(last_metric.duration_ms, 2),
                    "items": last_metric.items_processed,
                    "success": last_metric.success,
                    "error": last_metric.error_msg
                },
                "recent_errors": [
                    {
                        "timestamp": m.timestamp,
                        "error": m.error_msg
                    } for m in failed[-5:]  # Last 5 failures
                ]
            }
    
    async def get_all_workers_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all workers."""
        async with self.lock:
            workers = list(self.metrics_history.keys())
        
        stats = []
        for worker in workers:
            stat = await self.get_worker_stats(worker)
            stats.append(stat)
        
        return stats
    
    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get high-level summary for dashboard."""
        all_stats = await self.get_all_workers_stats()
        
        total_workers = len(all_stats)
        healthy_workers = len([s for s in all_stats if s.get("status") == "healthy"])
        degraded_workers = len([s for s in all_stats if s.get("status") == "degraded"])
        
        total_executions = sum(s.get("total_executions", 0) for s in all_stats)
        total_successful = sum(s.get("successful_executions", 0) for s in all_stats)
        total_items = sum(s.get("total_items_processed", 0) for s in all_stats)
        
        avg_throughput = (
            sum(s.get("avg_throughput_items_per_sec", 0) for s in all_stats) / max(len(all_stats), 1)
        )
        
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_workers": total_workers,
            "healthy_workers": healthy_workers,
            "degraded_workers": degraded_workers,
            "system_health": "green" if degraded_workers == 0 else ("yellow" if degraded_workers < total_workers / 2 else "red"),
            "total_executions": total_executions,
            "total_successful": total_successful,
            "overall_success_rate": round((total_successful / total_executions * 100), 1) if total_executions > 0 else 0,
            "total_items_processed": total_items,
            "avg_system_throughput_items_per_sec": round(avg_throughput, 2),
            "workers": all_stats
        }
    
    async def export_metrics_json(self, filepath: str) -> None:
        """Export all metrics to JSON file."""
        summary = await self.get_dashboard_summary()
        async with self.lock:
            if '..' in filepath:
                raise Exception('Invalid file path')
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Métricas exportadas para {filepath}")


# Global singleton instance
metrics_collector = WorkerMetricsCollector()
