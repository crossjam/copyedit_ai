"""Exercise real LLM response APIs with a provider that never uses the network."""

import json
from unittest.mock import patch

import llm
import pytest

from copyedit_ai.__main__ import _get_structured_output
from copyedit_ai.copyedit import copyedit
from copyedit_ai.schemas import get_copyedit_schema


class OfflineModel(llm.Model):
    """Provide deterministic text and structured responses through LLM's API."""

    model_id = "offline-copyedit"
    can_stream = True
    supports_schema = True

    def execute(self, prompt, stream, response, conversation=None):
        """Return text chunks or schema-conforming JSON without a provider call."""
        assert "Text with erors." in prompt.prompt
        if prompt.schema is not None:
            assert prompt.schema == get_copyedit_schema()
            yield json.dumps(
                {"copyedited_text": "Text with errors.", "changes": ["Fixed typo"]}
            )
        else:
            yield "Text with "
            yield "errors."


@pytest.mark.parametrize("stream", [True, False])
def test_real_llm_response_text(stream):
    """Consume real streaming and non-streaming responses from an offline model."""
    with (
        patch("copyedit_ai.copyedit.llm.get_model", return_value=OfflineModel()),
        patch(
            "copyedit_ai.copyedit.load_template",
            return_value=llm.Template(name="copyedit", system="Copyedit the text."),
        ),
    ):
        response = copyedit("Text with erors.", stream=stream)
        assert isinstance(response, llm.Response)
        if stream:
            assert list(response) == ["Text with ", "errors."]
        assert response.text() == "Text with errors."


@pytest.mark.parametrize("provider_metadata", [None, {"id": "raw-provider-envelope"}])
def test_real_llm_response_json(provider_metadata):
    """Validate schema forwarding and JSON parsing using an actual LLM response."""
    with (
        patch("copyedit_ai.copyedit.llm.get_model", return_value=OfflineModel()),
        patch(
            "copyedit_ai.copyedit.load_template",
            return_value=llm.Template(name="copyedit", system="Copyedit the text."),
        ),
    ):
        response = copyedit(
            "Text with erors.", stream=False, schema=get_copyedit_schema()
        )
        assert isinstance(response, llm.Response)
        response.response_json = provider_metadata
        output_data = {
            "copyedited_text": "Text with errors.",
            "changes": ["Fixed typo"],
        }
        assert _get_structured_output(response) == (output_data, "Text with errors.")
