# LLM Subcommand Passthrough Plan

**Date:** 2025-11-12
**Objective:** Enable `copyedit_ai self` to pass through certain subcommands to the `llm` package, providing seamless access to llm's native functionality within copyedit_ai's isolated configuration context.

## Overview

### Current State
- `copyedit_ai` uses Typer for CLI, which compiles to Click
- `llm` package uses Click for CLI with command groups for templates, keys, models, schemas, and aliases
- `copyedit_ai` has implemented isolated LLM configuration using XDG-compliant directories
- Current `self` subcommand provides: `init`, `check`, `install-template`, and `install-alias`

### Goal
Extend the `self` subcommand to pass through llm's native command groups, allowing users to manage their isolated llm configuration using familiar llm commands through copyedit_ai.

## Strategy

### Core Approach: Direct Command Group Attachment

We'll leverage Click's command composition capabilities to attach llm's command groups directly to copyedit_ai's `self` subcommand. This approach provides:

1. **Native functionality** - All llm features work exactly as documented
2. **Automatic isolation** - Commands run within copyedit_ai's isolated config (via `LLM_USER_PATH`)
3. **No duplication** - We reuse llm's existing, well-tested command implementations
4. **Easy extensibility** - Adding new passthrough commands is a one-liner
5. **Seamless UX** - Help text, options, and behavior match llm exactly

### Technical Implementation

Since both `copyedit_ai` (via Typer) and `llm` use Click, we can programmatically attach llm's command groups to our CLI:

```python
from llm.cli import cli as llm_cli

# Get the Click group objects from llm
templates_group = llm_cli.commands['templates']
keys_group = llm_cli.commands['keys']
models_group = llm_cli.commands['models']
schemas_group = llm_cli.commands['schemas']
aliases_group = llm_cli.commands['aliases']

# Attach them to our self subcommand
self_click_group.add_command(templates_group)
self_click_group.add_command(keys_group)
self_click_group.add_command(models_group)
self_click_group.add_command(schemas_group)
self_click_group.add_command(aliases_group)
```

### Why This Works

1. **Both are Click** - Typer compiles to Click, so we're working with compatible objects
2. **llm exposes commands** - The `llm.cli.cli.commands` dict contains all command groups
3. **Isolated context** - `LLM_USER_PATH` environment variable (set by our Settings) is inherited
4. **Command groups are reusable** - Click command groups can be attached to multiple parent groups

## Detailed Implementation Plan

### 1. Modify CLI Entry Point (`src/copyedit_ai/__main__.py`)

Currently, the entry point converts the Typer app to Click and sets up DefaultGroup. We need to access the `self` subcommand after this conversion to attach llm's commands.

**Current structure:**
```python
def cli() -> None:
    """CLI entry point with default command support."""
    click_group = typer.main.get_command(app)
    click_group.__class__ = DefaultGroup
    default_group = cast(DefaultGroup, click_group)
    default_group.default_cmd_name = "edit"
    default_group.default_if_no_args = True
    default_group()
```

**New approach:**
```python
def cli() -> None:
    """CLI entry point with default command support."""
    click_group = typer.main.get_command(app)
    click_group.__class__ = DefaultGroup
    default_group = cast(DefaultGroup, click_group)
    default_group.default_cmd_name = "edit"
    default_group.default_if_no_args = True

    # Attach llm passthrough commands to 'self' subcommand
    _attach_llm_passthroughs(default_group)

    default_group()
```

### 2. Create Passthrough Attachment Function

Add a new function to handle the attachment of llm commands:

```python
def _attach_llm_passthroughs(main_group: DefaultGroup) -> None:
    """Attach llm's command groups to the 'self' subcommand.

    This allows users to access llm's native commands within copyedit_ai's
    isolated configuration context.

    Args:
        main_group: The main Click group (converted from Typer app)
    """
    from llm.cli import cli as llm_cli

    # Get the 'self' subcommand (it's also a Click group)
    self_command = main_group.commands.get('self')
    if not self_command:
        logger.warning("Could not find 'self' subcommand for llm passthrough")
        return

    # List of llm commands to pass through
    passthrough_commands = [
        'templates',  # Manage prompt templates
        'keys',       # Manage API keys
        'models',     # List and configure models
        'schemas',    # Manage stored schemas
        'aliases',    # Manage model aliases
    ]

    # Attach each command group
    for cmd_name in passthrough_commands:
        llm_command = llm_cli.commands.get(cmd_name)
        if llm_command:
            self_command.add_command(llm_command, name=cmd_name)
            logger.debug(f"Attached llm command: {cmd_name}")
        else:
            logger.warning(f"Could not find llm command: {cmd_name}")
```

### 3. Update Self Subcommand Structure

The `self` subcommand in `src/copyedit_ai/self_subcommand.py` is currently a Typer app. We need to ensure it's accessible as a Click group after conversion.

**Current:**
```python
self_app = typer.Typer(
    name="self",
    help="Manage copyedit_ai itself (configuration, installation, etc.)",
)
```

**After conversion in __main__.py:**
```python
# When main app is converted to Click, self_app becomes a Click Group
# We can access it via: main_group.commands['self']
```

No changes needed in `self_subcommand.py` - the conversion happens automatically.

### 4. Handle Isolated Configuration Context

Our `Settings` class already sets `LLM_USER_PATH` when `use_isolated_llm_config=True` (which is the default). This means:

- All llm commands will automatically use the isolated config
- Users don't need to do anything special
- Commands like `llm templates list` → `copyedit_ai self templates list` will work identically

**Verification in Settings:**
```python
@model_validator(mode="after")
def setup_llm_config(self) -> "Settings":
    """Set up LLM configuration path if isolated config is enabled."""
    if self.use_isolated_llm_config:
        from .user_dir import set_llm_user_path
        set_llm_user_path()
    return self
```

This runs on startup, so `LLM_USER_PATH` is set before any commands execute.

### 5. Configuration for Extensibility

Create a simple configuration to make it easy to add/remove passthrough commands:

```python
# Could be in a config file or directly in the code
PASSTHROUGH_COMMANDS = [
    {
        'name': 'templates',
        'description': 'Manage prompt templates (llm passthrough)',
    },
    {
        'name': 'keys',
        'description': 'Manage API keys (llm passthrough)',
    },
    {
        'name': 'models',
        'description': 'List and configure models (llm passthrough)',
    },
    {
        'name': 'schemas',
        'description': 'Manage stored schemas (llm passthrough)',
    },
    {
        'name': 'aliases',
        'description': 'Manage model aliases (llm passthrough)',
    },
]
```

## User Experience Examples

### Before (current state):

```bash
# User has to manage templates manually or use install-template
$ copyedit_ai self install-template
Template 'copyedit' installed successfully

# Can't easily list or edit templates without directly calling llm
$ llm templates list  # Uses system llm, not isolated config
```

### After (with passthrough):

```bash
# List templates in isolated config
$ copyedit_ai self templates list
copyedit
custom-prompt
technical-writing

# Show a specific template
$ copyedit_ai self templates show copyedit
[template content...]

# Edit a template (opens in $EDITOR)
$ copyedit_ai self templates edit copyedit

# Get path to templates directory
$ copyedit_ai self templates path
/home/user/.config/dev.pirateninja.copyedit_ai/llm_config/templates

# List available models
$ copyedit_ai self models list
OpenAI Chat: gpt-4o (aliases: 4o)
OpenAI Chat: gpt-4o-mini (aliases: 4o-mini)
...

# Set default model
$ copyedit_ai self models default gpt-4o-mini

# Manage API keys
$ copyedit_ai self keys set openai
Enter value: [input hidden]
Key 'openai' set successfully

$ copyedit_ai self keys list
openai
anthropic

# Manage aliases (same as install-alias but more discoverable)
$ copyedit_ai self aliases set fast gpt-4o-mini
$ copyedit_ai self aliases list
fast: gpt-4o-mini

# Manage schemas
$ copyedit_ai self schemas list
person
article
metadata

$ copyedit_ai self schemas show person
[schema content...]
```

### Help Integration

The passthrough commands will appear in `copyedit_ai self --help`:

```bash
$ copyedit_ai self --help
Usage: copyedit_ai self [OPTIONS] COMMAND [ARGS]...

  Manage copyedit_ai itself (configuration, installation, etc.)

Commands:
  init            Initialize copyedit_ai configuration directory
  check           Check copyedit_ai configuration status
  install-template Install copyedit template
  install-alias   Install model alias
  templates       Manage stored prompt templates
  keys            Manage API keys for different models
  models          Manage available models
  schemas         Manage stored schemas
  aliases         Manage model aliases
```

Each passthrough command retains its original help:

```bash
$ copyedit_ai self templates --help
Usage: copyedit_ai self templates [OPTIONS] COMMAND [ARGS]...

  Manage stored prompt templates

Commands:
  list    List available prompt templates
  show    Show the specified prompt template
  edit    Edit template using $EDITOR
  path    Output path to templates directory
  loaders Show template loaders from plugins
```

## Testing Strategy

### 1. Unit Tests

Add tests in `tests/test_cli.py` to verify passthrough commands are attached:

```python
def test_self_has_llm_passthrough_commands():
    """Verify that llm passthrough commands are attached to self subcommand."""
    from copyedit_ai.__main__ import app
    import typer.main

    # Convert to Click and check commands
    click_group = typer.main.get_command(app)
    self_command = click_group.commands.get('self')

    # Verify passthrough commands exist
    assert 'templates' in self_command.commands
    assert 'keys' in self_command.commands
    assert 'models' in self_command.commands
    assert 'schemas' in self_command.commands
    assert 'aliases' in self_command.commands

def test_self_templates_list(tmp_path: Path):
    """Test that templates list command works in isolated config."""
    with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(tmp_path)}):
        # Initialize config
        result = runner.invoke(cli, ["self", "init"])
        assert result.exit_code == 0

        # List templates (should work even if empty)
        result = runner.invoke(cli, ["self", "templates", "list"])
        assert result.exit_code == 0

def test_self_models_list():
    """Test that models list command works."""
    result = runner.invoke(cli, ["self", "models", "list"])
    assert result.exit_code == 0
    # Should show at least some models
    assert "gpt" in result.output.lower() or "claude" in result.output.lower()

def test_self_aliases_passthrough(tmp_path: Path):
    """Test that aliases command works and uses isolated config."""
    with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(tmp_path)}):
        # Initialize config
        result = runner.invoke(cli, ["self", "init"])
        assert result.exit_code == 0

        # Set an alias
        result = runner.invoke(cli, ["self", "aliases", "set", "test", "gpt-4o"])
        assert result.exit_code == 0

        # List aliases
        result = runner.invoke(cli, ["self", "aliases", "list"])
        assert result.exit_code == 0
        assert "test" in result.output
```

### 2. Integration Tests

Test the full flow of using passthrough commands:

```python
def test_full_passthrough_workflow(tmp_path: Path):
    """Test a complete workflow using passthrough commands."""
    with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(tmp_path)}):
        # Initialize
        result = runner.invoke(cli, ["self", "init"])
        assert result.exit_code == 0

        # Create a template
        templates_dir = tmp_path / "dev.pirateninja.copyedit_ai" / "llm_config" / "templates"
        test_template = templates_dir / "test.yaml"
        test_template.write_text("system: Test template")

        # List templates
        result = runner.invoke(cli, ["self", "templates", "list"])
        assert result.exit_code == 0
        assert "test" in result.output

        # Show template
        result = runner.invoke(cli, ["self", "templates", "show", "test"])
        assert result.exit_code == 0
        assert "Test template" in result.output

        # Get templates path
        result = runner.invoke(cli, ["self", "templates", "path"])
        assert result.exit_code == 0
        assert str(templates_dir) in result.output
```

### 3. Manual Testing Checklist

- [ ] `copyedit_ai self --help` shows all passthrough commands
- [ ] `copyedit_ai self templates --help` shows llm's templates help
- [ ] `copyedit_ai self templates list` works
- [ ] `copyedit_ai self templates show <name>` works
- [ ] `copyedit_ai self templates path` returns isolated config path
- [ ] `copyedit_ai self models list` shows available models
- [ ] `copyedit_ai self models default` shows/sets default model
- [ ] `copyedit_ai self keys list` works
- [ ] `copyedit_ai self keys path` returns isolated config path
- [ ] `copyedit_ai self aliases list` works
- [ ] `copyedit_ai self aliases set` creates alias in isolated config
- [ ] `copyedit_ai self schemas list` works
- [ ] All commands respect isolated configuration
- [ ] Commands work after `copyedit_ai self init`
- [ ] Appropriate error if used before `self init` (if applicable)

## Edge Cases and Considerations

### 1. Initialization Requirement

Some llm commands create files (templates, keys, aliases). These should work automatically after `self init` since the directories exist.

**Decision:** Don't require initialization check for passthrough commands. Let llm handle errors naturally. Users will see helpful messages like "Could not write to path" if directories don't exist.

### 2. Conflicts with Existing Subcommands

We currently have:
- `install-template` - Creates the copyedit template
- `install-alias` - Creates model aliases

And we're adding:
- `templates` - Full template management
- `aliases` - Full alias management

**Decision:** Keep both. `install-template` and `install-alias` are high-level, opinionated commands. The passthrough commands provide full access to llm's functionality. They serve different purposes:
- `install-template`: Quick setup of copyedit template (one command)
- `templates`: Full template management (list, show, edit, create custom ones)

### 3. Version Compatibility

If llm changes its CLI structure, our passthrough might break.

**Decision:**
- Document the llm version we tested against
- Add a unit test that verifies llm.cli.cli.commands contains expected commands
- Gracefully handle missing commands (log warning, don't crash)

### 4. Help Text Confusion

Users might wonder why some commands say "llm" in their help text.

**Decision:** This is acceptable. The commands ARE from llm, and it's good for users to know they can reference llm documentation. We could optionally modify help text, but that adds complexity.

### 5. Command Name Collisions

Future llm versions might add commands that collide with our existing commands.

**Decision:** Our commands take precedence (we don't override them). Only attach llm commands that don't already exist in `self`. Add a check:

```python
if cmd_name not in self_command.commands:
    self_command.add_command(llm_command, name=cmd_name)
else:
    logger.debug(f"Skipping llm command {cmd_name} - already exists")
```

## Alternative Approaches Considered

### Alternative 1: Subprocess Calls

**Approach:** Shell out to `llm` command with proper environment:

```python
@self_app.command()
def templates(ctx: typer.Context):
    """Manage templates (llm passthrough)"""
    args = sys.argv[sys.argv.index('templates'):]
    subprocess.run(['llm'] + args, env=os.environ)
```

**Pros:**
- Complete isolation from llm internals
- Guaranteed version compatibility

**Cons:**
- Requires llm to be on PATH (might not be if only in venv)
- Extra process overhead
- Harder to test
- Arguments need careful parsing
- Help text integration is clunky

**Decision:** Rejected. Direct command attachment is more elegant.

### Alternative 2: Reimplementation

**Approach:** Reimplement llm's commands using llm's Python API:

```python
@self_app.command()
def templates_list():
    """List templates"""
    import llm
    # Use llm.get_templates() or similar
```

**Pros:**
- Full control over behavior
- Can customize for copyedit_ai

**Cons:**
- Massive duplication of code
- Need to track llm updates
- More maintenance burden
- Would miss new llm features

**Decision:** Rejected. Goes against DRY principle.

### Alternative 3: Dynamic Command Generation

**Approach:** Programmatically generate Typer commands that invoke Click commands:

```python
def make_passthrough(llm_command):
    @self_app.command(name=llm_command.name)
    def wrapper(ctx: typer.Context):
        # Invoke llm_command with context
        pass
    return wrapper

for cmd_name in ['templates', 'keys', ...]:
    make_passthrough(llm_cli.commands[cmd_name])
```

**Pros:**
- More explicit control
- Could add middleware

**Cons:**
- More complex than direct attachment
- Context conversion between Typer and Click
- Harder to maintain

**Decision:** Rejected. Direct attachment is simpler and works.

## Documentation Updates

### README.md

Add section under "Features":

```markdown
### LLM Configuration Management

Manage your isolated LLM configuration directly through copyedit_ai:

- `copyedit_ai self templates` - Manage prompt templates
- `copyedit_ai self keys` - Manage API keys
- `copyedit_ai self models` - List and configure models
- `copyedit_ai self aliases` - Manage model aliases
- `copyedit_ai self schemas` - Manage stored schemas

All commands operate within copyedit_ai's isolated configuration,
preventing conflicts with system-wide llm installations.
```

### docs/configuration.md

Add detailed section:

```markdown
## LLM Command Passthrough

copyedit_ai provides direct access to llm's management commands through
the `self` subcommand. These commands operate within your isolated
copyedit_ai configuration directory.

### Available Commands

#### Templates
\`\`\`bash
copyedit_ai self templates list          # List templates
copyedit_ai self templates show <name>   # View template
copyedit_ai self templates edit <name>   # Edit in $EDITOR
copyedit_ai self templates path          # Show templates directory
\`\`\`

#### Models
\`\`\`bash
copyedit_ai self models list             # List available models
copyedit_ai self models default          # Show default model
copyedit_ai self models default <model>  # Set default model
\`\`\`

#### Keys
\`\`\`bash
copyedit_ai self keys list               # List stored keys
copyedit_ai self keys set <name>         # Set an API key
copyedit_ai self keys get <name>         # Retrieve a key
copyedit_ai self keys path               # Show keys file path
\`\`\`

... etc ...
```

## Implementation Checklist

### Phase 1: Core Implementation
- [ ] Add `_attach_llm_passthroughs()` function in `src/copyedit_ai/__main__.py`
- [ ] Import `llm.cli` and access command groups
- [ ] Implement command attachment logic with error handling
- [ ] Add configuration list for passthrough commands
- [ ] Add collision detection (don't override existing commands)
- [ ] Update `cli()` function to call `_attach_llm_passthroughs()`
- [ ] Add debug/warning logging for attachment process

### Phase 2: Testing
- [ ] Add unit test for command attachment verification
- [ ] Add test for each passthrough command (basic invocation)
- [ ] Add integration test for templates workflow
- [ ] Add integration test for aliases workflow
- [ ] Add integration test for models workflow
- [ ] Add test for isolated config usage (verify LLM_USER_PATH)
- [ ] Add test for error handling (missing llm commands)
- [ ] Add test for collision handling (existing command names)
- [ ] Run full test suite and ensure all pass

### Phase 3: Documentation
- [ ] Update README.md with passthrough features
- [ ] Add/update docs/configuration.md with detailed examples
- [ ] Add docstring to `_attach_llm_passthroughs()` function
- [ ] Update CHANGELOG.md with new feature
- [ ] Add inline comments for maintainability

### Phase 4: Quality Assurance
- [ ] Run `poe ruff-check` and fix any issues
- [ ] Run `poe ruff` to format code
- [ ] Run `poe ty` and fix any type issues
- [ ] Manual testing of all passthrough commands
- [ ] Test help text (`--help`) for all commands
- [ ] Test in fresh environment (new user directory)
- [ ] Test with COPYEDIT_AI_USE_ISOLATED_LLM_CONFIG=false

### Phase 5: Future Extensibility
- [ ] Document how to add new passthrough commands
- [ ] Consider adding configuration file for passthrough list
- [ ] Add note about llm version compatibility
- [ ] Consider adding `llm --version` passthrough for debugging

## Success Criteria

1. **Functionality**: All five command groups (templates, keys, models, schemas, aliases) are accessible via `copyedit_ai self`
2. **Isolation**: All passthrough commands use copyedit_ai's isolated configuration
3. **Discoverability**: Commands appear in `copyedit_ai self --help`
4. **Documentation**: Each command's help text is accessible via `--help`
5. **Testing**: Comprehensive test coverage (unit + integration)
6. **Code Quality**: All linter and type checks pass
7. **User Experience**: Commands work exactly as llm's native commands
8. **Extensibility**: Adding new passthrough commands is straightforward
9. **Maintainability**: Code is well-documented and easy to understand
10. **Robustness**: Graceful handling of missing/incompatible llm versions

## Rollout Plan

### Version: 0.2.0 (Minor version bump - new feature)

1. **Development**: Implement as per checklist above
2. **Testing**: Complete all test phases
3. **Documentation**: Update all docs before merge
4. **Release**: Create release notes highlighting new capabilities
5. **Announcement**: Update README and documentation site
6. **User Communication**: Mention in release that users can now manage llm through copyedit_ai

## Future Enhancements

### Potential additions for future versions:

1. **Custom command wrapping**: Add middleware to inject copyedit_ai-specific behavior
2. **Selective passthrough**: Allow users to disable certain passthroughs via config
3. **Command aliasing**: Allow shorter names (e.g., `tpl` for `templates`)
4. **Enhanced help**: Modify help text to clarify isolated config usage
5. **Plugin discovery**: Auto-discover and pass through plugin commands from llm
6. **Version checking**: Warn if llm version is incompatible
7. **Additional commands**: Pass through `logs`, `embed`, `similar`, etc. based on user feedback

---

**End of Plan**

This plan provides a comprehensive roadmap for implementing llm command passthrough while maintaining code quality, testability, and user experience. The approach is extensible and maintainable for future enhancements.
