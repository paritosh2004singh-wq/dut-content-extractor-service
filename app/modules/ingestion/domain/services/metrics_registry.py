import time
from typing import Dict, Any

class MetricsRegistry:
    def __init__(self):
        self.counters = {
            "documents_processed_total": 0,
            "provider_failures_total": 0,
            "fallbacks_total": 0,
            "pages_processed_total": 0,
        }
        self.gauges = {
            "provider_availability": 1.0,
            "confidence_average": 0.0,
            "duplicate_rate": 0.0,
        }
        self.histograms = {
            "ocr_latency_seconds": [],
            "merge_latency_seconds": [],
            "conflict_resolution_seconds": []
        }

    def increment(self, metric: str, amount: int = 1):
        if metric in self.counters:
            self.counters[metric] += amount

    def set_gauge(self, metric: str, value: float):
        if metric in self.gauges:
            self.gauges[metric] = value

    def observe(self, metric: str, value: float):
        if metric in self.histograms:
            self.histograms[metric].append(value)

    def export_prometheus(self) -> str:
        lines = []
        for name, val in self.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {val}")
            
        for name, val in self.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {val}")
            
        for name, values in self.histograms.items():
            lines.append(f"# TYPE {name} histogram")
            avg = sum(values)/len(values) if values else 0.0
            lines.append(f"{name}_avg {avg}")
            lines.append(f"{name}_count {len(values)}")
            
        return "\n".join(lines) + "\n"

# Global instance for simplicity in this architecture
global_metrics_registry = MetricsRegistry()
