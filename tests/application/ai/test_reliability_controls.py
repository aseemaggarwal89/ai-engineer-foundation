import pytest

from app.application.ai.core.bullet_parser import BulletParser
from app.application.ai.prompts.summary_prompt import SummaryPrompt
from app.application.ai.validator.request.ai_guardrails import AIGuardrails
from app.application.ai.validator.request.ai_safety import AISafetyFilter
from app.application.ai.validator.response.hallucination_guard import HallucinationGuard
from app.application.ai.validator.response.response_scorer import AIResponseScorer
from app.application.ai.validator.response.response_validator import AIResponseValidator
from app.core.config import AISettings
from app.domain.exceptions.exceptions import (
    BadRequestError,
    PromptTooLargeError,
    RequestValidationError,
    ResponseValidationError,
)


def make_ai_settings(**overrides) -> AISettings:
    defaults = {
        "model_name": "tinyllama",
        "max_prompt_length": 20,
        "hard_prompt_limit": 100,
    }
    return AISettings(**{**defaults, **overrides})


@pytest.mark.parametrize(
    "text",
    [
        "my PASSWORD is hidden",
        "credit card number",
        "cvv code",
        "ssn value",
    ],
)
def test_safety_filter_blocks_configured_terms_case_insensitively(text):
    with pytest.raises(RequestValidationError, match="Sensitive data detected"):
        AISafetyFilter().check(text)


def test_safety_filter_is_keyword_based_and_can_block_educational_text():
    with pytest.raises(RequestValidationError):
        AISafetyFilter().check("Explain password hashing")


@pytest.mark.parametrize(
    "text",
    [
        "4111 1111 1111 1111",
        "123-45-6789",
        "sk-test-secret-looking-value",
    ],
)
def test_safety_filter_does_not_detect_sensitive_looking_values_without_keywords(text):
    assert AISafetyFilter().check(text) is None


@pytest.mark.parametrize("text", ["", "   "])
def test_guardrails_reject_empty_or_whitespace_only_prompt(text):
    guardrails = AIGuardrails(make_ai_settings())

    with pytest.raises((BadRequestError, RequestValidationError)):
        guardrails.validate_prompt(text)


def test_guardrails_reject_prompt_above_hard_character_limit():
    guardrails = AIGuardrails(make_ai_settings(hard_prompt_limit=5))

    with pytest.raises(PromptTooLargeError):
        guardrails.validate_prompt("abcdef")


def test_guardrails_soft_limit_truncates_by_character_count():
    guardrails = AIGuardrails(make_ai_settings(max_prompt_length=5))

    assert guardrails.validate_prompt("abcdef") == "abcde"


def test_guardrails_reject_binary_like_control_characters():
    guardrails = AIGuardrails(make_ai_settings())

    with pytest.raises(RequestValidationError, match="Binary input detected"):
        guardrails.validate_prompt("abc" + "\x00" * 20)


def test_guardrails_normalize_whitespace_and_preserve_unicode_text():
    guardrails = AIGuardrails(make_ai_settings(max_prompt_length=100))

    assert guardrails.validate_prompt("  hello\n\nworld  café  ") == "hello world café"


def test_summary_prompt_is_versioned_and_deterministic():
    prompt = SummaryPrompt()

    first = prompt.build("Some text")
    second = prompt.build("Some text")

    assert prompt.VERSION == "v1"
    assert first == second
    assert "EXACTLY 5 short bullet points" in first
    assert "Text:\nSome text" in first


def test_bullet_parser_preserves_order_and_parses_simple_bullet_lines():
    parser = BulletParser()

    assert parser.parse("- One\n• Two\nThree") == ["One", "Two", "Three"]


def test_response_validator_rejects_invalid_raw_output():
    validator = AIResponseValidator()

    with pytest.raises(ResponseValidationError):
        validator.validate("")

    with pytest.raises(ResponseValidationError):
        validator.validate("short")

    with pytest.raises(ResponseValidationError):
        validator.validate("I am an AI language model and cannot help")


def test_response_validator_clamps_bullets_to_five():
    validator = AIResponseValidator()

    bullets = validator.validate_bullets(
        ["one", "two", "three", "four", "five", "six"]
    )

    assert bullets == ["one", "two", "three", "four", "five"]


def test_output_length_guard_rejects_overly_long_bullet():
    guard = HallucinationGuard()

    with pytest.raises(ResponseValidationError):
        guard.check_bullets(["x" * (guard.MAX_BULLET_LENGTH + 1)])


def test_response_scorer_measures_structural_shape():
    scorer = AIResponseScorer()

    assert scorer.score_bullets([]) == 0.0
    assert scorer.score_bullets(["short"]) == 0.5
    assert scorer.score_bullets(
        ["long enough bullet text" * 4 for _ in range(5)]
    ) == pytest.approx(0.9)
