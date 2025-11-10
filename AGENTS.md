# AGENTS.md

> A concise brief for AI coding agents working on this repository.  
> This project is a **Python package** managed with **uv** and tested with **pytest**.

---

## 🧭 Quick Start

```bash
# set up environment from pyproject + uv.lock
uv sync

# run the test suite (quiet, stop on first failure)
uv run pytest -q -x

# run type checks & lint (if dev deps are present)
uv run ty src/copyedit_ai
uv run ruff check .
uv run ruff format .

# run the package (replace with your module/CLI)
uv run python -m copyedit_ai --help
