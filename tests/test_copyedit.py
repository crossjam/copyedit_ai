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


@pytest.fixture
def mock_template():
    """Mock template for testing."""
    template = MagicMock()
    template.system = SYSTEM_PROMPT
    return template


def test_system_prompt_exists():
    """Test that the system prompt is defined."""
    assert SYSTEM_PROMPT
    assert "copy editor" in SYSTEM_PROMPT.lower()
    assert "punctuation" in SYSTEM_PROMPT.lower()
    assert "grammatical" in SYSTEM_PROMPT.lower()


def test_system_prompt_includes_frontmatter_protection():
    """Test that the system prompt includes instructions to protect front matter."""
    assert SYSTEM_PROMPT
    # Check for general front matter protection instruction
    assert "front matter" in SYSTEM_PROMPT.lower()
    assert "unmodified" in SYSTEM_PROMPT.lower()
    
    # Check for YAML front matter delimiters
    assert "---" in SYSTEM_PROMPT
    assert "YAML" in SYSTEM_PROMPT or "yaml" in SYSTEM_PROMPT.lower()
    
    # Check for TOML front matter delimiters
    assert "+++" in SYSTEM_PROMPT
    assert "TOML" in SYSTEM_PROMPT or "toml" in SYSTEM_PROMPT.lower()
    
    # Check for JSON front matter delimiters
    assert "{" in SYSTEM_PROMPT and "}" in SYSTEM_PROMPT
    assert "JSON" in SYSTEM_PROMPT or "json" in SYSTEM_PROMPT.lower()


@patch("copyedit_ai.copyedit.load_template")
@patch("copyedit_ai.copyedit.llm")
def test_copyedit_with_model_name(mock_llm, mock_load_template, mock_llm_model, mock_llm_response, mock_template):
    """Test copyedit with a specific model name."""
    mock_llm.get_model.return_value = mock_llm_model
    mock_llm_model.prompt.return_value = mock_llm_response
    mock_load_template.return_value = mock_template

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


@patch("copyedit_ai.copyedit.load_template")
@patch("copyedit_ai.copyedit.llm")
def test_copyedit_without_model_name(mock_llm, mock_load_template, mock_llm_model, mock_llm_response, mock_template):
    """Test copyedit without specifying a model name."""
    mock_llm.get_model.return_value = mock_llm_model
    mock_llm_model.prompt.return_value = mock_llm_response
    mock_load_template.return_value = mock_template

    text = "Test text."

    copyedit(text, model_name=None, stream=False)

    # Should call get_model without arguments
    mock_llm.get_model.assert_called_once_with()
    mock_llm_model.prompt.assert_called_once()


@patch("copyedit_ai.copyedit.load_template")
@patch("copyedit_ai.copyedit.llm")
def test_copyedit_streaming(mock_llm, mock_load_template, mock_llm_model, mock_llm_response, mock_template):
    """Test copyedit with streaming enabled."""
    mock_llm.get_model.return_value = mock_llm_model
    mock_llm_model.prompt.return_value = mock_llm_response
    mock_load_template.return_value = mock_template

    text = "Test text."

    response = copyedit(text, stream=True)

    # Response should be the same object (streaming is handled by the response)
    assert response == mock_llm_response


@patch("copyedit_ai.copyedit.load_template")
@patch("copyedit_ai.copyedit.llm")
def test_copyedit_no_streaming(mock_llm, mock_load_template, mock_llm_model, mock_llm_response, mock_template):
    """Test copyedit with streaming disabled."""
    mock_llm.get_model.return_value = mock_llm_model
    mock_llm_model.prompt.return_value = mock_llm_response
    mock_load_template.return_value = mock_template

    text = "Test text."

    response = copyedit(text, stream=False)

    # Response should be the same object
    assert response == mock_llm_response


@patch("copyedit_ai.copyedit.load_template")
@patch("copyedit_ai.copyedit.llm")
def test_copyedit_with_yaml_frontmatter(mock_llm, mock_load_template, mock_llm_model, mock_llm_response, mock_template):
    """Test copyedit with YAML front matter."""
    mock_llm.get_model.return_value = mock_llm_model
    mock_llm_model.prompt.return_value = mock_llm_response
    mock_load_template.return_value = mock_template

    text = """---
title: My Document
author: Jane Doe
date: 2025-01-01
---

This is a test text with some erors."""

    copyedit(text, stream=False)

    mock_llm_model.prompt.assert_called_once()
    
    # Verify the prompt includes the full text with front matter
    call_args = mock_llm_model.prompt.call_args
    assert "Copy edit the text that follows:" in call_args[0][0]
    assert "title: My Document" in call_args[0][0]
    assert "This is a test text with some erors." in call_args[0][0]


@patch("copyedit_ai.copyedit.load_template")
@patch("copyedit_ai.copyedit.llm")
def test_copyedit_with_toml_frontmatter(mock_llm, mock_load_template, mock_llm_model, mock_llm_response, mock_template):
    """Test copyedit with TOML front matter."""
    mock_llm.get_model.return_value = mock_llm_model
    mock_llm_model.prompt.return_value = mock_llm_response
    mock_load_template.return_value = mock_template

    text = """+++
title = "My Document"
author = "Jane Doe"
date = 2025-01-01
+++

This is a test text with some erors."""

    copyedit(text, stream=False)

    mock_llm_model.prompt.assert_called_once()
    
    # Verify the prompt includes the full text with front matter
    call_args = mock_llm_model.prompt.call_args
    assert "Copy edit the text that follows:" in call_args[0][0]
    assert 'title = "My Document"' in call_args[0][0]
    assert "This is a test text with some erors." in call_args[0][0]


@patch("copyedit_ai.copyedit.load_template")
@patch("copyedit_ai.copyedit.llm")
def test_copyedit_with_json_frontmatter(mock_llm, mock_load_template, mock_llm_model, mock_llm_response, mock_template):
    """Test copyedit with JSON front matter."""
    mock_llm.get_model.return_value = mock_llm_model
    mock_llm_model.prompt.return_value = mock_llm_response
    mock_load_template.return_value = mock_template

    text = """{
  "title": "My Document",
  "author": "Jane Doe",
  "date": "2025-01-01"
}

This is a test text with some erors."""

    copyedit(text, stream=False)

    mock_llm_model.prompt.assert_called_once()
    
    # Verify the prompt includes the full text with front matter
    call_args = mock_llm_model.prompt.call_args
    assert "Copy edit the text that follows:" in call_args[0][0]
    assert '"title": "My Document"' in call_args[0][0]
    assert "This is a test text with some erors." in call_args[0][0]


@patch("copyedit_ai.copyedit.load_template")
@patch("copyedit_ai.copyedit.llm")
def test_copyedit_with_complex_yaml_frontmatter(mock_llm, mock_load_template, mock_llm_model, mock_llm_response, mock_template):
    """Test copyedit with complex YAML front matter including nested structures."""
    mock_llm.get_model.return_value = mock_llm_model
    mock_llm_model.prompt.return_value = mock_llm_response
    mock_load_template.return_value = mock_template

    text = """---
title: My Complex Document
author: Jane Doe
tags:
  - technical
  - documentation
  - markdown
metadata:
  version: 1.0
  status: draft
---

# Introduction

This is a test document with erors that need to be corrected."""

    copyedit(text, stream=False)

    mock_llm_model.prompt.assert_called_once()
    
    # Verify the prompt includes the full text with front matter
    call_args = mock_llm_model.prompt.call_args
    assert "Copy edit the text that follows:" in call_args[0][0]
    assert "title: My Complex Document" in call_args[0][0]
    assert "tags:" in call_args[0][0]
    assert "# Introduction" in call_args[0][0]
