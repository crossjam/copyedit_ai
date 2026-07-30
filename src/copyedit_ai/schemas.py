"""Schemas used for structured copyedit output."""

import json
from importlib.resources import files
from typing import Any


def get_copyedit_schema() -> dict[str, Any]:
    """Load the JSON schema used by the ``edit --json`` option."""
    schema_path = files("copyedit_ai").joinpath("copyedit_schema.json")
    return json.loads(schema_path.read_text(encoding="utf-8"))
