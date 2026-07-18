import pytest

from app.application.ai.core.chat_pipeline import ChatPipeline
from app.application.ai.validator.response.response_scorer import AIResponseScorer
from app.application.ai.validator.response.response_validator import AIResponseValidator
from app.domain.exceptions.exceptions import ModelRefusalError, ResponseValidationError


def build_pipeline() -> ChatPipeline:
    return ChatPipeline(
        validator=AIResponseValidator(),
        scorer=AIResponseScorer(),
    )


def test_chat_pipeline_normalizes_and_scores_response():
    pipeline = build_pipeline()

    response, score = pipeline.run(
        "\n  FastAPI routes should stay thin.\n\n"
        "  Use cases should hold business workflow.  \n"
    )

    assert response == (
        "FastAPI routes should stay thin.\n"
        "Use cases should hold business workflow."
    )
    assert score == 1.0


def test_chat_pipeline_rejects_empty_response():
    pipeline = build_pipeline()

    with pytest.raises(ResponseValidationError):
        pipeline.run("   \n  ")


def test_chat_pipeline_rejects_common_refusal_response():
    pipeline = build_pipeline()

    with pytest.raises(ModelRefusalError):
        pipeline.run("I cannot help with that request.")
