from prometheus_client import Counter, Histogram

# TOTAL AI CALLS
ai_requests_total = Counter(
    "ai_requests_total",
    "Total number of AI inference requests",
    ["model"]
)

# AI FAILURES
ai_errors_total = Counter(
    "ai_errors_total",
    "Total number of AI inference errors",
    ["model"]
)

# LATENCY
ai_latency_seconds = Histogram(
    "ai_latency_seconds",
    "Latency of AI model calls",
    ["model"]
)

# TOKEN USAGE
ai_tokens_used_total = Counter(
    "ai_tokens_used_total",
    "Total tokens consumed",
    ["model", "type"]  # prompt / completion
)
