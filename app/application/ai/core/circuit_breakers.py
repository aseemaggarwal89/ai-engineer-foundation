import pybreaker

# Ollama → fails faster (local model)
ollama_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=20,
)

# OpenAI → more tolerant
openai_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
)