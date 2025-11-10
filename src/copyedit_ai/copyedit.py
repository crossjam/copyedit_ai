"""Core copyediting functionality using LLM."""

from collections.abc import Iterator

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


def copyedit(
    text: str,
    model_name: str | None = None,
    *,
    stream: bool = True,
) -> llm.Response | Iterator[str]:
    """Copyedit text using an LLM.

    Args:
        text: The text to copyedit
        model_name: Optional model name to use (defaults to llm's default model)
        stream: Whether to stream the response (default: True)

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
    response = model.prompt(prompt_text, system=SYSTEM_PROMPT)

    if stream:
        return response
    return response
