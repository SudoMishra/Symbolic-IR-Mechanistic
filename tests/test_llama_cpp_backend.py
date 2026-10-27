from __future__ import annotations

from unittest.mock import MagicMock

from symbolic_ir.inference.llama_cpp import LlamaCppBackend
from symbolic_ir.schema import GenerationRequest


def test_prefill_raises_when_handler_missing() -> None:
    backend = object.__new__(LlamaCppBackend)
    backend._model_name = "mock_model"
    backend._revision = "mock_rev"
    backend._assistant_prefill = "<think>\n</think>\n"
    backend._llm = MagicMock()
    backend._llm.chat_handler = None
    backend._llm._chat_handlers = {}
    backend._llm.chat_format = "invalid_format"

    request = GenerationRequest(
        example_id="test_001",
        prompt="What is the capital of France?",
        max_output_tokens=50,
        temperature=0.0,
    )

    try:
        backend.generate(request)
        raise AssertionError("Expected RuntimeError when handler is missing")
    except RuntimeError as exc:
        assert "No chat template handler available" in str(exc)


def test_prefill_raises_when_formatter_throws() -> None:
    backend = object.__new__(LlamaCppBackend)
    backend._model_name = "mock_model"
    backend._revision = "mock_rev"
    backend._assistant_prefill = "<think>\n</think>\n"
    backend._llm = MagicMock()

    def broken_formatter(*args, **kwargs):
        raise ValueError("Jinja syntax error")

    mock_closure = (MagicMock(),)
    mock_closure[0].cell_contents = broken_formatter

    mock_handler = MagicMock()
    mock_handler.__closure__ = mock_closure
    backend._llm.chat_handler = mock_handler

    request = GenerationRequest(
        example_id="test_001",
        prompt="What is the capital of France?",
        max_output_tokens=50,
        temperature=0.0,
    )

    try:
        backend.generate(request)
        raise AssertionError("Expected RuntimeError when formatter throws")
    except RuntimeError as exc:
        assert "Failed to render canonical chat template" in str(exc)
