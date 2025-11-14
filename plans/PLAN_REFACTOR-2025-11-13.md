# CLI Code Organization Refactoring Plan

**Date:** 2025-11-13
**Objective:** Improve code organization by extracting business logic from `__main__.py` into focused modules, reducing complexity and improving testability.

## Overview

### Current State

The `src/copyedit_ai/__main__.py` file has grown to **~350 lines** and contains:
- Main Typer app definition
- The `edit` command implementation
- `_perform_copyedit()` helper function (~100 lines) with complexity warnings (`# noqa: C901, PLR0912, PLR0915`)
- Helper functions (`_get_model_display_name()`, `_attach_llm_passthroughs()`)
- Global callback for settings
- Entry point with Click/DefaultGroup conversion

**Code Quality Issues:**
- Complexity warnings indicate `_perform_copyedit()` has too many responsibilities
- Business logic (copyediting workflow) mixed with presentation logic (CLI, spinner, output)
- Helper functions buried in large file
- Testing requires CLI runner instead of simple function calls
- File size approaching the threshold where navigation becomes cumbersome

### Goals

1. **Reduce `__main__.py` complexity** - Keep it focused on CLI command definitions only
2. **Separate concerns** - Business logic vs. presentation logic
3. **Improve testability** - Enable unit testing without CLI runner
4. **Maintain backwards compatibility** - No changes to CLI interface or behavior
5. **Keep changes minimal** - Low-effort refactoring, no major architectural changes

## Proposed Structure

### New File Organization

```
src/copyedit_ai/
├── __main__.py              # CLI command definitions only (~200 lines)
├── cli/
│   ├── __init__.py          # Empty or re-exports
│   ├── edit_handler.py      # Edit command business logic
│   └── utils.py             # CLI utility functions
├── self_subcommand.py       # Self subcommand (existing)
├── copyedit.py              # Core copyedit logic (existing)
├── settings.py              # Settings (existing)
└── user_dir.py              # User directory utilities (existing)
```

### Module Responsibilities

#### `src/copyedit_ai/__main__.py` (Reduced to ~200 lines)
**Responsibilities:**
- Typer app definition
- Command decorators and signatures
- Argument/option definitions
- Calling handlers and displaying results

**Contents:**
- `app = typer.Typer()`
- `@app.command()` decorated functions
- `@app.callback()` for global options
- `cli()` entry point
- `_attach_llm_passthroughs()` (stays here - CLI-specific)

**What moves out:**
- `_perform_copyedit()` → `cli/edit_handler.py`
- `_get_model_display_name()` → `cli/utils.py`

#### `src/copyedit_ai/cli/edit_handler.py` (New, ~120 lines)
**Responsibilities:**
- Edit command business logic
- File I/O operations
- Copyedit API calls
- Replace mode logic
- Output handling

**Contents:**
- `perform_copyedit()` - Main handler (no underscore prefix, it's public now)
- Helper functions for replace mode
- File reading/writing logic
- Error handling

**Key difference from current `_perform_copyedit()`:**
- Returns data instead of printing directly (where possible)
- Takes `console` and `settings` as parameters
- UI concerns (spinner, printing) stay in `__main__.py` or passed as callbacks

#### `src/copyedit_ai/cli/utils.py` (New, ~50 lines)
**Responsibilities:**
- CLI utility functions
- Model name display logic
- Other shared CLI helpers

**Contents:**
- `get_model_display_name()` (public function)
- Future: Other CLI utilities as needed

## Detailed Migration Plan

### Phase 1: Create New Modules

#### Step 1.1: Create `cli/` package
```python
# src/copyedit_ai/cli/__init__.py
"""CLI-specific utilities and handlers."""

from .edit_handler import perform_copyedit
from .utils import get_model_display_name

__all__ = ["perform_copyedit", "get_model_display_name"]
```

#### Step 1.2: Create `cli/utils.py`
Move `_get_model_display_name()` from `__main__.py`:

```python
# src/copyedit_ai/cli/utils.py
"""CLI utility functions."""

import llm
from loguru import logger


def get_model_display_name(model_name: str) -> str:
    """Get a short display name for a model (alias if available, otherwise model_id).

    Args:
        model_name: The model name or alias to lookup

    Returns:
        The shortest alias for the model, or the model_id if no alias exists
    """
    try:
        models_with_aliases = llm.get_models_with_aliases()
        for model_with_alias in models_with_aliases:
            if model_with_alias.matches(model_name):
                # Return first alias if available
                # (aliases are usually sorted shortest first)
                if model_with_alias.aliases:
                    return model_with_alias.aliases[0]
                # Fall back to model_id
                return model_with_alias.model.model_id
    except Exception:  # noqa: S110
        # If anything goes wrong, just return the original name
        pass

    # Default: return the model_name as-is
    return model_name
```

#### Step 1.3: Create `cli/edit_handler.py`
Move `_perform_copyedit()` from `__main__.py`:

```python
# src/copyedit_ai/cli/edit_handler.py
"""Handler for the edit command business logic."""

import shutil
import sys
import tempfile
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console
from rich.status import Status

from ..copyedit import copyedit
from ..settings import Settings
from .utils import get_model_display_name


def perform_copyedit(  # noqa: C901, PLR0912, PLR0915
    settings: Settings,
    file_path: Path | None,
    model: str | None,
    stream: bool,
    replace: bool,
    console: Console,
) -> None:
    """Perform copyediting operation.

    Handles the complete copyedit workflow including:
    - Reading input from file or stdin
    - Making API calls with spinner UI
    - Outputting results
    - Replace mode with confirmation

    Args:
        settings: Application settings
        file_path: Path to file to edit, or None for stdin
        model: Model name/alias to use, or None for default
        stream: Whether to stream the response
        replace: Whether to replace the original file
        console: Rich console for output (on stderr)
    """
    # [Rest of the current _perform_copyedit() implementation]
    # ... (all the existing logic)
```

**Key changes in the function:**
1. Remove underscore prefix (it's now a public API)
2. Add `console: Console` parameter (passed from command)
3. Keep all existing logic - this is a simple move, not a rewrite

### Phase 2: Update `__main__.py`

#### Step 2.1: Update imports
```python
from .cli import perform_copyedit, get_model_display_name
```

#### Step 2.2: Update `edit` command
```python
@app.command(name="edit")
def edit_command(
    file_path: Path | None = typer.Argument(None, help="File to copyedit (or stdin)"),
    model: str | None = typer.Option(None, "-m", "--model", help="Model to use"),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Stream output"),
    replace: bool = typer.Option(
        False,
        "-r",
        "--replace",
        help="Replace file in-place with confirmation",
    ),
    ctx: typer.Context = typer.Option(None),
) -> None:
    """Copyedit text from a file or stdin."""
    settings = ctx.obj

    # Call the handler
    perform_copyedit(
        settings=settings,
        file_path=file_path,
        model=model,
        stream=stream,
        replace=replace,
        console=console,  # console is module-level in __main__.py
    )
```

#### Step 2.3: Remove old functions
Delete the old `_perform_copyedit()` and `_get_model_display_name()` implementations.

### Phase 3: Update Tests

Tests in `tests/test_cli.py` should continue to work without changes because we're not changing the CLI interface. However, we can now add unit tests for the handlers.

#### Step 3.1: Create `tests/test_edit_handler.py`
```python
"""Test edit_handler business logic."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from copyedit_ai.cli.edit_handler import perform_copyedit
from copyedit_ai.settings import Settings


def test_perform_copyedit_with_file(tmp_path: Path):
    """Test copyedit with a file input."""
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content.")

    # Mock settings and console
    settings = Settings()
    console = Console()

    # Mock the copyedit function
    with patch("copyedit_ai.cli.edit_handler.copyedit") as mock_copyedit:
        mock_response = MagicMock()
        mock_response.__iter__ = MagicMock(return_value=iter(["Corrected content."]))
        mock_copyedit.return_value = mock_response

        # Call handler
        perform_copyedit(
            settings=settings,
            file_path=test_file,
            model=None,
            stream=True,
            replace=False,
            console=console,
        )

        # Verify copyedit was called
        mock_copyedit.assert_called_once()


# Additional unit tests for specific scenarios
# - Test stdin input
# - Test replace mode
# - Test error handling
# - Test model resolution
```

#### Step 3.2: Create `tests/test_cli_utils.py`
```python
"""Test CLI utility functions."""

from unittest.mock import MagicMock, patch

from copyedit_ai.cli.utils import get_model_display_name


def test_get_model_display_name_with_alias():
    """Test getting display name for model with alias."""
    with patch("copyedit_ai.cli.utils.llm.get_models_with_aliases") as mock_get:
        # Mock model with alias
        mock_model = MagicMock()
        mock_model.model_id = "gpt-4o-mini"

        mock_with_alias = MagicMock()
        mock_with_alias.matches.return_value = True
        mock_with_alias.aliases = ["4o-mini"]
        mock_with_alias.model = mock_model

        mock_get.return_value = [mock_with_alias]

        result = get_model_display_name("gpt-4o-mini")
        assert result == "4o-mini"


def test_get_model_display_name_fallback():
    """Test fallback when model not found."""
    with patch("copyedit_ai.cli.utils.llm.get_models_with_aliases") as mock_get:
        mock_get.return_value = []

        result = get_model_display_name("unknown-model")
        assert result == "unknown-model"
```

### Phase 4: Documentation Updates

#### Update docstrings
- Add comprehensive module-level docstrings to new files
- Update `__main__.py` docstring to reflect its new focused role
- Add type hints where missing

#### Update inline comments
- Remove complexity suppression comments from `__main__.py`
- Add comments explaining the handler pattern in `edit_handler.py`

## Benefits of This Refactoring

### Immediate Benefits

1. **Reduced Complexity**
   - `__main__.py` drops from ~350 to ~200 lines
   - No more complexity warnings
   - Each file has a single, clear responsibility

2. **Better Testability**
   - Can test `perform_copyedit()` without CLI runner
   - Easier to mock dependencies
   - Faster test execution for business logic

3. **Improved Maintainability**
   - Logic is easier to find
   - Changes to edit workflow don't require touching CLI definition
   - Helper functions have a clear home

4. **Better Code Navigation**
   - Developers can find specific functionality faster
   - IDE tools work better with smaller, focused files
   - Clearer module boundaries

### Future Benefits

1. **Easier to Add Commands**
   - Pattern established for new commands: create handler in `cli/`
   - `__main__.py` stays clean as more commands are added

2. **Reusability**
   - Business logic can be reused outside CLI context
   - Could build a web API or library interface

3. **Testing Pyramid**
   - Fast unit tests for handlers
   - Integration tests for CLI
   - Better test coverage with less effort

## Migration Checklist

### Code Changes
- [ ] Create `src/copyedit_ai/cli/__init__.py`
- [ ] Create `src/copyedit_ai/cli/utils.py` with `get_model_display_name()`
- [ ] Create `src/copyedit_ai/cli/edit_handler.py` with `perform_copyedit()`
- [ ] Update `src/copyedit_ai/__main__.py` imports
- [ ] Update `edit_command()` to call handler
- [ ] Remove old `_perform_copyedit()` from `__main__.py`
- [ ] Remove old `_get_model_display_name()` from `__main__.py`
- [ ] Update type hints and docstrings

### Testing
- [ ] Run existing test suite - all should pass
- [ ] Create `tests/test_edit_handler.py` with unit tests
- [ ] Create `tests/test_cli_utils.py` with unit tests
- [ ] Verify no regressions in CLI behavior
- [ ] Test edge cases (stdin, replace mode, errors)

### Code Quality
- [ ] Run `ruff check` - should pass with no complexity warnings
- [ ] Run `ruff format` - apply formatting
- [ ] Run type checker - should pass
- [ ] Verify no circular import issues
- [ ] Check that all tests pass

### Documentation
- [ ] Add module docstrings to new files
- [ ] Update function docstrings with examples
- [ ] Add inline comments for complex logic
- [ ] Update any developer documentation if it exists

## Alternative Approaches Considered

### Alternative 1: Extract to Multiple Handler Files
Create separate handlers for each major function:
- `cli/edit_handler.py`
- `cli/replace_handler.py`
- `cli/output_handler.py`

**Decision:** Rejected for now. Too granular for the current complexity level. Keep it simple with one handler for edit workflow.

### Alternative 2: Create a Full CLI Package
Move all CLI code including `__main__.py` into `cli/`:
```
cli/
├── __init__.py
├── app.py          # Main Typer app
├── commands/
│   ├── edit.py
│   └── self.py
└── utils.py
```

**Decision:** Rejected. Too much change for a "low-effort" refactoring. This is better as a future enhancement if the CLI grows significantly.

### Alternative 3: Keep Everything in __main__.py but Reorganize
Just reorder functions and add comments to group related code.

**Decision:** Rejected. Doesn't address the core issues of testability and separation of concerns. Only a cosmetic improvement.

## Risks and Mitigation

### Risk 1: Breaking Changes
**Risk:** Refactoring might accidentally change behavior.
**Mitigation:**
- Existing test suite must pass 100%
- Manual testing of all CLI commands
- No changes to function logic, only location

### Risk 2: Import Cycles
**Risk:** New module structure could create circular imports.
**Mitigation:**
- Careful dependency management
- `cli/` package imports from parent package, not vice versa
- Test imports explicitly

### Risk 3: Lost Context
**Risk:** Moving code loses git history/blame.
**Mitigation:**
- Use git commit message with "Moved from..." notation
- Consider using git's rename detection
- Document in this plan where code came from

### Risk 4: Increased Complexity
**Risk:** More files means more navigation overhead.
**Mitigation:**
- Clear naming and organization
- Good module docstrings
- Only create files that add clear value

## Success Criteria

### Must Have
- ✅ All existing tests pass without modification
- ✅ No complexity warnings in `__main__.py`
- ✅ `__main__.py` reduced to ~200 lines or less
- ✅ All linter checks pass
- ✅ No type errors
- ✅ CLI behavior unchanged (backwards compatible)

### Should Have
- ✅ At least 5 new unit tests for handlers
- ✅ Clear module docstrings on all new files
- ✅ No circular import issues
- ✅ Improved code organization visible in file structure

### Nice to Have
- ✅ Test coverage increase
- ✅ Faster test execution (unit tests vs CLI tests)
- ✅ Developer documentation on new structure

## Timeline Estimate

**Total Effort:** 2-3 hours

- **Phase 1** (Create new modules): 30 minutes
- **Phase 2** (Update `__main__.py`): 30 minutes
- **Phase 3** (Update/add tests): 60 minutes
- **Phase 4** (Documentation): 30 minutes
- **Buffer** (debugging, polish): 30 minutes

## Future Enhancements

After this refactoring is complete, consider:

1. **Extract Replace Logic**: Move replace-specific logic to its own module if `edit_handler.py` grows
2. **Add More Handler Tests**: Increase coverage of edge cases
3. **Create Handler Base Class**: If more commands added, create abstract base for handlers
4. **CLI Package Restructure**: Full `cli/` package if 4+ commands are added
5. **Type-safe Handler Protocol**: Define Protocol for handlers if needed

## Conclusion

This refactoring provides immediate benefits with minimal risk:
- Reduces `__main__.py` complexity by ~150 lines
- Improves testability and maintainability
- Establishes pattern for future commands
- No breaking changes to CLI interface
- Low effort (2-3 hours)

The changes are conservative and focused on the current pain points while setting up a better structure for future growth.

---

**Status:** Planning Complete - Ready for Implementation
