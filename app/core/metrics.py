from prometheus_client import Counter, Histogram

# Total requests
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

# Request latency
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)

# Error counter
REQUEST_ERRORS = Counter(
    "http_request_errors_total",
    "HTTP request errors",
    ["method", "path"],
)
