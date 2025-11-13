# Type Checking Fixes Plan

## Issues Found

Running `poe ty` revealed 3 type checking errors in the codebase:

### 1. possibly-missing-attribute: `response.text()` (src/copyedit_ai/__main__.py:65)

**Error:**
```
Attribute `text` may be missing on object of type `Response | Iterator[str]`
```

**Root Cause:**
- The `copyedit()` function returns `llm.Response | Iterator[str]`
- In non-streaming mode, we call `response.text()`, but the type checker doesn't know that in this branch, `response` is definitely a `Response` and not an `Iterator[str]`
- The type narrowing isn't working because both branches return the same type annotation

**Solution Options:**

**Option A: Type Narrowing with isinstance check (Recommended)**
```python
if stream:
    # Stream output
    for chunk in response:
        typer.echo(chunk, nl=False)
    typer.echo()  # Final newline
else:
    # Output complete response
    if isinstance(response, llm.Response):
        typer.echo(response.text())
    # Or use assert isinstance(response, llm.Response) for type checker
```

**Option B: Change copyedit() return type annotation**
```python
# Use Overload to specify different return types
from typing import overload

@overload
def copyedit(text: str, model_name: str | None = None, *, stream: Literal[True]) -> Iterator[str]: ...

@overload
def copyedit(text: str, model_name: str | None = None, *, stream: Literal[False]) -> llm.Response: ...

def copyedit(text: str, model_name: str | None = None, *, stream: bool = True) -> llm.Response | Iterator[str]:
    ...
```

**Option C: Type ignore comment (Quick fix, not ideal)**
```python
typer.echo(response.text())  # type: ignore[union-attr]
```

**Recommendation:** Use Option A with an assertion for type narrowing. It's the cleanest and helps the type checker understand the code flow.

---

### 2 & 3. unresolved-attribute: `default_cmd_name` and `default_if_no_args` (src/copyedit_ai/__main__.py:131-132)

**Error:**
```
Unresolved attribute `default_cmd_name` on type `Command`.
Unresolved attribute `default_if_no_args` on type `Command`.
```

**Root Cause:**
- We dynamically change the class from `Command` to `DefaultGroup` at runtime
- The type checker sees `click_group` as type `Command` (from typer.main.get_command)
- `Command` doesn't have `default_cmd_name` or `default_if_no_args` attributes
- These attributes exist on `DefaultGroup` but type checker doesn't know about the runtime class change

**Solution Options:**

**Option A: Type cast after class change (Recommended)**
```python
from typing import cast, Any
from click_default_group import DefaultGroup

def cli() -> None:
    """CLI entry point with default command support."""
    click_group = typer.main.get_command(app)
    # Replace the group class with DefaultGroup
    click_group.__class__ = DefaultGroup

    # Cast to DefaultGroup for type checker
    default_group = cast(DefaultGroup, click_group)
    default_group.default_cmd_name = "edit"
    default_group.default_if_no_args = True
    default_group()
```

**Option B: Use Any type (Less type-safe)**
```python
def cli() -> None:
    """CLI entry point with default command support."""
    click_group: Any = typer.main.get_command(app)
    click_group.__class__ = DefaultGroup
    click_group.default_cmd_name = "edit"
    click_group.default_if_no_args = True
    click_group()
```

**Option C: Type ignore comments (Quick fix)**
```python
click_group.default_cmd_name = "edit"  # type: ignore[attr-defined]
click_group.default_if_no_args = True  # type: ignore[attr-defined]
```

**Recommendation:** Use Option A with proper type casting. This maintains type safety while acknowledging the dynamic class change.

---

## Implementation Plan

### Step 1: Fix response.text() type issue
1. Update `_perform_copyedit()` in `src/copyedit_ai/__main__.py`
2. Add type assertion before calling `response.text()`
3. This helps the type checker understand the branch logic

**Code change:**
```python
# In _perform_copyedit function
if stream:
    # Stream output
    for chunk in response:
        typer.echo(chunk, nl=False)
    typer.echo()  # Final newline
else:
    # Output complete response
    assert isinstance(response, llm.Response)
    typer.echo(response.text())
```

### Step 2: Fix DefaultGroup attribute issues
1. Update `cli()` function in `src/copyedit_ai/__main__.py`
2. Add proper type casting after class reassignment
3. Import necessary types

**Code change:**
```python
from typing import cast
from click_default_group import DefaultGroup

def cli() -> None:
    """CLI entry point with default command support."""
    click_group = typer.main.get_command(app)
    # Replace the group class with DefaultGroup
    click_group.__class__ = DefaultGroup

    # Cast to tell type checker about the new type
    default_group = cast(DefaultGroup, click_group)
    default_group.default_cmd_name = "edit"
    default_group.default_if_no_args = True
    default_group()
```

### Step 3: Verify fixes
1. Run `poe ty` to ensure all type errors are resolved
2. Run `pytest` to ensure functionality hasn't changed
3. Run `poe ruff-check` to ensure code quality

### Step 4: Update tests if needed
- No test changes expected as this is only type annotation fixes
- Tests should continue to pass

---

## Alternative: Use type: ignore

If the above solutions prove too complex or cause runtime issues, we can use targeted type ignore comments:

```python
# In _perform_copyedit
typer.echo(response.text())  # type: ignore[union-attr]

# In cli function
click_group.default_cmd_name = "edit"  # type: ignore[attr-defined]
click_group.default_if_no_args = True  # type: ignore[attr-defined]
```

This is a pragmatic approach when:
- The code is correct at runtime
- Adding proper types is overly complex
- The type checker limitations are known

However, the proper fix (Steps 1-2) is preferred as it improves type safety.

---

## Priority

1. **High Priority**: Fix issue #1 (response.text()) - This is a real type safety issue
2. **Medium Priority**: Fix issues #2-3 (DefaultGroup) - These are known safe but type checker doesn't understand

## Testing Strategy

After implementing fixes:
1. ✅ Type check passes: `poe ty`
2. ✅ All tests pass: `pytest -v`
3. ✅ Linter passes: `poe ruff-check`
4. ✅ Manual smoke test: `copyedit_ai self check`

---

**Status**: Ready for implementation
**Estimated Time**: 15-20 minutes
**Risk**: Low - Changes are type annotation only
