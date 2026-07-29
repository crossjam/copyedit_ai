"""Core copyediting functionality using LLM."""

from collections.abc import Iterator
from typing import Any

import llm
from loguru import logger

SYSTEM_PROMPT = """You are copyeditor that suggests and makes edits on text.

You review the text you receive for punctuation, grammatical,
spelling, and logical errors. Try hard to keep the style and tone but
make corrections as needed. Summarize any corrections you made at the
bottom of the text in bullet point format.

Don't make any commentary at the beginning of your output. Just output
the corrected code to start off. Use a string of '=' characters to
separate corrected text from your comments.

Always, always, always output the document to start. Even if you don't
make any changes. Do not ignore this instruction.

If the text looks like markdown, ignore fenced quotes or leading text with
> . Don't edit the quoted text.

Do not modify emojis.
"""

JSON_SYSTEM_PROMPT = """You are copyeditor that suggests and makes edits on text.

You review the text you receive for punctuation, grammatical, spelling, and logical
errors. Try hard to keep the style and tone but make corrections as needed.

Return the complete corrected document in the `copyedited_text` field. Return a
concise list of corrections and other changes in the `changes` field. Always return
the complete document, even if you do not make any changes. Do not include
commentary outside the requested structured response.

If the text looks like markdown, ignore fenced quotes or leading text with
> . Don't edit the quoted text.

Do not modify emojis.
"""


def copyedit(
    text: str,
    model_name: str | None = None,
    *,
    stream: bool = True,
    schema: dict[str, Any] | None = None,
) -> llm.Response | Iterator[str]:
    """Copyedit text using an LLM.

    Args:
        text: The text to copyedit
        model_name: Optional model name to use (defaults to llm's default model)
        stream: Whether to stream the response (default: True)
        schema: Optional JSON schema for structured output

    Returns:
        LLM response object if not streaming, iterator of text chunks if streaming

    """
    logger.info(f"Copyediting text with model={model_name}, stream={stream}")

    # Get the model
    model = llm.get_model(model_name) if model_name else llm.get_model()

    logger.debug(f"Using model: {model.model_id}")

    # Prepare the prompt
    prompt_text = f"Copy edit the text that follows:\n\n{text}"

    # Execute the prompt
    prompt_kwargs: dict[str, Any] = {
        "system": JSON_SYSTEM_PROMPT if schema else SYSTEM_PROMPT,
        "stream": stream,
    }
    if schema is not None:
        prompt_kwargs["schema"] = schema

    response = model.prompt(prompt_text, **prompt_kwargs)

    if stream:
        return response
    return response
