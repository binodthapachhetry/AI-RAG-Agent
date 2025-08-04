from prometheus_client import Counter, Gauge, Histogram

RETRY_ATTEMPTS = Counter("external_retry_attempts_total", "Retry attempts", ["target"])
TIMEOUTS = Counter("external_timeouts_total", "Timeouts", ["target"])
ERRORS = Counter("external_errors_total", "Errors", ["target", "kind"])
LATENCY = Histogram("external_latency_seconds", "External op latency", ["target"])
BREAKER_OPEN = Gauge("circuit_breaker_open", "Breaker open=1, closed=0", ["target"])
