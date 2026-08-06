from app.domain.exceptions.exceptions import AIProviderError, ProviderErrorCategory


def test_transient_provider_errors_are_fallback_eligible_by_default():
    error = AIProviderError(
        "provider timed out",
        category=ProviderErrorCategory.TIMEOUT,
        provider="ollama",
        model="tinyllama",
    )

    assert error.fallback_eligible is True
    assert error.category == ProviderErrorCategory.TIMEOUT
    assert error.provider == "ollama"
    assert error.model == "tinyllama"


def test_configuration_provider_errors_are_not_fallback_eligible_by_default():
    error = AIProviderError(
        "missing model",
        category=ProviderErrorCategory.CONFIGURATION,
        provider="openai",
    )

    assert error.fallback_eligible is False
