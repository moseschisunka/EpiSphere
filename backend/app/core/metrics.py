"""Small in-process request metrics registry for pilot observability."""

from collections import defaultdict
from threading import Lock


class RequestMetrics:
    def __init__(self):
        self._lock = Lock()
        self._counts = defaultdict(int)
        self._latency_sum = defaultdict(float)

    def observe(self, method: str, path: str, status_code: int, elapsed_seconds: float) -> None:
        key = (method, path, str(status_code))
        with self._lock:
            self._counts[key] += 1
            self._latency_sum[key] += elapsed_seconds

    def render_prometheus(self) -> str:
        lines = [
            "# HELP episphere_http_requests_total Total HTTP requests handled by the process.",
            "# TYPE episphere_http_requests_total counter",
            "# HELP episphere_http_request_duration_seconds_sum Sum of HTTP request durations.",
            "# TYPE episphere_http_request_duration_seconds_sum counter",
        ]
        with self._lock:
            for (method, path, status), count in sorted(self._counts.items()):
                labels = f'method="{method}",path="{path}",status="{status}"'
                lines.append(f"episphere_http_requests_total{{{labels}}} {count}")
                lines.append(f"episphere_http_request_duration_seconds_sum{{{labels}}} {self._latency_sum[(method, path, status)]:.6f}")
        return "\n".join(lines) + "\n"


request_metrics = RequestMetrics()
