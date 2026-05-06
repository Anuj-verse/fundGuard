from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    'edge_service_requests_total',
    'Total number of scoring requests',
    ['decision']
)

LATENCY_HISTOGRAM = Histogram(
    'edge_service_latency_seconds',
    'Latency of the scoring endpoint',
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)
