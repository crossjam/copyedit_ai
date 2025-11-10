"""Test copyedit_ai core copyediting functionality."""

from unittest.mock import MagicMock, patch

import pytest

from copyedit_ai.copyedit import SYSTEM_PROMPT, copyedit


@pytest.fixture
def mock_llm_model():
    """Mock LLM model for testing."""
    model = MagicMock()
    model.model_id = "test-model"
    return model


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    response = MagicMock()
    response.text.return_value = "Corrected text\n\n===\n\n- Fixed typo"
    response.__iter__ = MagicMock(return_value=iter(["Corrected", " text"]))
    return response


def test_system_prompt_exists():
    """Test that the system prompt is defined."""
    assert SYSTEM_PROMPT
    assert "copyeditor" in SYSTEM_PROMPT.lower()
    assert "punctuation" in SYSTEM_PROMPT.lower()
    assert "grammatical" in SYSTEM_PROMPT.lower()


@patch("copyedit_ai.copyedit.llm")
def test_copyedit_with_model_name(mock_llm, mock_llm_model, mock_llm_response):
    """Test copyedit with a specific model name."""
    mock_llm.get_model.return_value = mock_llm_model
    mock_llm_model.prompt.return_value = mock_llm_response

    text = "This is a test text with some erors."
    model_name = "gpt-4o"

    copyedit(text, model_name=model_name, stream=False)

    mock_llm.get_model.assert_called_once_with(model_name)
    mock_llm_model.prompt.assert_called_once()

    # Verify the prompt includes our text and uses the system prompt
    call_args = mock_llm_model.prompt.call_args
    assert "Copy edit the text that follows:" in call_args[0][0]
    assert text in call_args[0][0]
    assert call_args[1]["system"] == SYSTEM_PROMPT


@patch("copyedit_ai.copyedit.llm")
def test_copyedit_without_model_name(mock_llm, mock_llm_model, mock_llm_response):
    """Test copyedit without specifying a model name."""
    mock_llm.get_model.return_value = mock_llm_model
    mock_llm_model.prompt.return_value = mock_llm_response

    text = "Test text."

    copyedit(text, model_name=None, stream=False)

    # Should call get_model without arguments
    mock_llm.get_model.assert_called_once_with()
    mock_llm_model.prompt.assert_called_once()


@patch("copyedit_ai.copyedit.llm")
def test_copyedit_streaming(mock_llm, mock_llm_model, mock_llm_response):
    """Test copyedit with streaming enabled."""
    mock_llm.get_model.return_value = mock_llm_model
    mock_llm_model.prompt.return_value = mock_llm_response

    text = "Test text."

    response = copyedit(text, stream=True)

    # Response should be the same object (streaming is handled by the response)
    assert response == mock_llm_response


@patch("copyedit_ai.copyedit.llm")
def test_copyedit_no_streaming(mock_llm, mock_llm_model, mock_llm_response):
    """Test copyedit with streaming disabled."""
    mock_llm.get_model.return_value = mock_llm_model
    mock_llm_model.prompt.return_value = mock_llm_response

    text = "Test text."

    response = copyedit(text, stream=False)

    # Response should be the same object
    assert response == mock_llm_response
