# LLM Configuration Isolation Plan

## Overview

Implement an isolated LLM configuration for copyedit_ai to prevent conflicts with explicitly installed system-wide llm installations. This ensures that copyedit_ai's templates, aliases, and other llm configurations remain separate from the user's global llm setup.

## Goals

1. Provide XDG-conformant configuration storage
2. Isolate copyedit_ai's llm configuration from system llm
3. Make configuration initialization explicit and user-controlled
4. Provide visibility into configuration state

## Architecture

### Directory Structure

```
~/.config/dev.pirateninja.copyedit_ai/
├── llm_config/
│   ├── templates/          # copyedit_ai templates
│   ├── logs.db            # llm conversation logs
│   ├── aliases.json       # model aliases
│   └── keys.json          # API keys (if stored separately)
└── config.json            # copyedit_ai app config (future use)
```

### XDG Base Directory Specification

- **Primary location**: `$XDG_CONFIG_HOME/dev.pirateninja.copyedit_ai/`
- **Fallback** (when `XDG_CONFIG_HOME` unset): `~/.config/dev.pirateninja.copyedit_ai/`
- **Application identifier**: `dev.pirateninja.copyedit_ai` (reverse domain notation)

### Environment Variable Integration

The llm package respects the `LLM_USER_PATH` environment variable to override its default user directory. We'll set this programmatically before making llm API calls.

## Implementation Tasks

### 1. Create User Directory Module

**File**: `src/copyedit_ai/user_dir.py`

**Responsibilities**:
- Determine XDG config home directory
- Construct application-specific path
- Provide functions to get/initialize directories
- Check initialization status

**Key Functions**:
```python
def get_xdg_config_home() -> Path:
    """Get XDG_CONFIG_HOME or fallback to ~/.config"""

def get_app_config_dir() -> Path:
    """Get dev.pirateninja.copyedit_ai config directory"""

def get_llm_config_dir() -> Path:
    """Get llm_config subdirectory"""

def is_initialized() -> bool:
    """Check if directory structure exists"""

def initialize() -> None:
    """Create directory structure"""

def set_llm_user_path() -> None:
    """Set LLM_USER_PATH environment variable to our config dir"""
```

### 2. Update Settings Module

**File**: `src/copyedit_ai/settings.py`

**Changes**:
- Add `use_isolated_llm_config` setting (default: True)
- Add `llm_config_path` setting (optional override)
- On initialization, call `set_llm_user_path()` if `use_isolated_llm_config` is True

**New Settings**:
```python
use_isolated_llm_config: bool = True
llm_config_path: Path | None = None  # Override path if needed
```

### 3. Update Existing LLM Integration Points

**Files to modify**:
- `src/copyedit_ai/copyedit.py` - Ensure env var set before llm calls
- `src/copyedit_ai/self_subcommand.py` - Ensure env var set before llm calls

**Pattern**:
```python
from .user_dir import set_llm_user_path

def some_function():
    set_llm_user_path()  # Ensure isolated config is active
    # ... proceed with llm calls
```

### 4. Add `self init` Subcommand

**File**: `src/copyedit_ai/self_subcommand.py`

**Command**: `copyedit_ai self init`

**Features**:
- Create XDG directory structure
- Initialize llm_config subdirectory
- Optionally copy templates/aliases from system llm (with `--import` flag)
- Show success message with directory path
- Handle already-initialized case gracefully

**Options**:
- `--import-system-config`: Import aliases and templates from system llm
- `--force`: Reinitialize even if already exists

**Example Usage**:
```bash
# Basic initialization
copyedit_ai self init

# Initialize and import system llm config
copyedit_ai self init --import-system-config

# Force reinitialize
copyedit_ai self init --force
```

**Output Example**:
```
✓ Initialized copyedit_ai configuration
  Location: /home/user/.config/dev.pirateninja.copyedit_ai
  LLM config: /home/user/.config/dev.pirateninja.copyedit_ai/llm_config

Configuration is ready. You can now:
  - Install templates: copyedit_ai self install-template
  - Create aliases: copyedit_ai self install-alias <alias> <model>
```

### 5. Add `self check` Subcommand

**File**: `src/copyedit_ai/self_subcommand.py`

**Command**: `copyedit_ai self check`

**Features**:
- Check if directory structure exists
- Report initialization status
- Show directory paths
- List installed templates and aliases
- Show whether isolated config is enabled in settings

**Options**:
- `--verbose`: Show detailed information about each component

**Example Output (Initialized)**:
```
✓ Configuration initialized
  Config directory: /home/user/.config/dev.pirateninja.copyedit_ai
  LLM config: /home/user/.config/dev.pirateninja.copyedit_ai/llm_config
  Isolated config: Enabled

Templates (2):
  - copyedit
  - my-template

Aliases (1):
  - fast -> gpt-4o-mini

To initialize, run: copyedit_ai self init
```

**Example Output (Not Initialized)**:
```
⚠ Configuration not initialized
  Expected location: /home/user/.config/dev.pirateninja.copyedit_ai

Run 'copyedit_ai self init' to set up configuration.
```

### 6. Update `install-template` Subcommand

**File**: `src/copyedit_ai/self_subcommand.py`

**Changes**:
- Check if configuration is initialized before proceeding
- Call `set_llm_user_path()` before using llm API
- Provide helpful error if not initialized

**Error Message**:
```
Error: Configuration not initialized.
Run 'copyedit_ai self init' first.
```

### 7. Update `install-alias` Subcommand

**File**: `src/copyedit_ai/self_subcommand.py`

**Changes**:
- Check if configuration is initialized before proceeding
- Call `set_llm_user_path()` before using llm API
- Provide helpful error if not initialized

### 8. Update Main CLI Module

**File**: `src/copyedit_ai/__main__.py`

**Changes**:
- In `main_callback()`, call `set_llm_user_path()` if settings indicate isolated config
- This ensures all llm calls throughout the application use the isolated config

### 9. Add Tests

**New test file**: `tests/test_user_dir.py`

**Test coverage**:
- XDG directory path resolution
- Fallback to `~/.config` when `XDG_CONFIG_HOME` unset
- Directory initialization
- Status checking
- Environment variable setting

**Updates to**: `tests/test_cli.py`

**New tests**:
- `test_cli_self_init`
- `test_cli_self_init_already_initialized`
- `test_cli_self_init_force`
- `test_cli_self_init_import_system_config`
- `test_cli_self_check_initialized`
- `test_cli_self_check_not_initialized`
- `test_cli_self_install_template_not_initialized`
- `test_cli_self_install_alias_not_initialized`

### 10. Update Documentation

**Files to update**:
- `docs/getting-started/configuration.md` - Add section on isolated config
- `docs/user-guide/cli.md` - Document new `init` and `check` commands
- `README.md` - Add note about isolated configuration

**Documentation content**:
- Explain why isolated config is beneficial
- Show initialization workflow
- Explain how to disable isolated config if needed
- Document migration from system llm

## Migration Strategy

### For Existing Users

1. **Opt-in approach**: Require explicit `copyedit_ai self init` call
2. **Backward compatibility**: If not initialized, warn but still work (fall back to system llm)
3. **Gradual migration**: Users can run `copyedit_ai self init --import-system-config` to migrate

### For New Users

1. **First-run detection**: On first use, suggest running `copyedit_ai self init`
2. **Installation docs**: Update getting-started guide to include initialization step

## Environment Variable Behavior

### LLM_USER_PATH Priority

1. **Explicit user override**: If user sets `LLM_USER_PATH` env var, respect it
2. **copyedit_ai override**: If `use_isolated_llm_config=True`, set programmatically
3. **System default**: Fall back to llm's default `~/.config/io.datasette.llm`

### Implementation

```python
def set_llm_user_path() -> None:
    """Set LLM_USER_PATH to isolated config directory.

    Only sets if not already set by user, respecting explicit overrides.
    """
    if os.environ.get("LLM_USER_PATH"):
        # User has explicitly set this, don't override
        logger.debug("LLM_USER_PATH already set, using user override")
        return

    llm_config = get_llm_config_dir()
    os.environ["LLM_USER_PATH"] = str(llm_config)
    logger.debug(f"Set LLM_USER_PATH={llm_config}")
```

## Configuration Options

### Disabling Isolated Config

Users can disable isolated config via:

**Option 1: Environment variable**
```bash
export COPYEDIT_AI_USE_ISOLATED_LLM_CONFIG=false
copyedit_ai "your text"
```

**Option 2: Config file** (`.env-copyedit_ai`)
```
COPYEDIT_AI_USE_ISOLATED_LLM_CONFIG=false
```

**Option 3: Explicit LLM_USER_PATH**
```bash
export LLM_USER_PATH=/custom/path
copyedit_ai "your text"
```

## Edge Cases and Error Handling

### 1. Permission Errors
- **Issue**: Cannot create config directory
- **Handling**: Clear error message, suggest checking permissions

### 2. Disk Space
- **Issue**: Insufficient disk space for config
- **Handling**: Catch and report IOError with context

### 3. Concurrent Initialization
- **Issue**: Multiple processes init simultaneously
- **Handling**: Use atomic directory creation, handle race conditions gracefully

### 4. Partial Initialization
- **Issue**: Init fails partway through
- **Handling**: Clean up partial state, or mark as incomplete

### 5. XDG_CONFIG_HOME Points to Invalid Location
- **Issue**: Environment variable points to non-writable location
- **Handling**: Detect and fall back to `~/.config`

## Testing Strategy

### Unit Tests
- Test directory path resolution with various env var combinations
- Test initialization logic
- Test status checking
- Mock file system operations

### Integration Tests
- Test full initialization workflow
- Test template/alias installation with isolated config
- Test copyedit operations with isolated config
- Test import from system llm

### Manual Testing Checklist
- [ ] Init on clean system
- [ ] Init when already initialized
- [ ] Init with --force
- [ ] Init with --import-system-config
- [ ] Check before init
- [ ] Check after init
- [ ] Install template in isolated config
- [ ] Install alias in isolated config
- [ ] Run copyedit with isolated config
- [ ] Disable isolated config and verify fallback
- [ ] Test with XDG_CONFIG_HOME set to custom location
- [ ] Test with LLM_USER_PATH set explicitly

## Success Criteria

1. ✅ Configuration stored in XDG-compliant location
2. ✅ No conflicts with system llm installation
3. ✅ Users can initialize and check config via CLI
4. ✅ All llm operations use isolated config when enabled
5. ✅ Clear error messages when config not initialized
6. ✅ Comprehensive test coverage (>90%)
7. ✅ Documentation updated with new workflow
8. ✅ Backward compatible with existing installations

## Future Enhancements

### Phase 2 (Optional)
- `copyedit_ai self export` - Export config for backup/sharing
- `copyedit_ai self import` - Import config from file
- `copyedit_ai self reset` - Reset config to defaults
- GUI configuration tool
- Config sync across machines

## Implementation Order

1. **Phase 1**: Core infrastructure
   - Create `user_dir.py` module
   - Update settings module
   - Add `set_llm_user_path()` calls to existing code

2. **Phase 2**: CLI commands
   - Implement `self init` subcommand
   - Implement `self check` subcommand
   - Update `install-template` and `install-alias` to check initialization

3. **Phase 3**: Testing
   - Write unit tests for user_dir module
   - Update CLI tests
   - Manual testing

4. **Phase 4**: Documentation
   - Update user guide
   - Update getting started docs
   - Update README

## Questions to Resolve

1. **Default behavior**: Should isolated config be enabled by default? ✅ Yes
2. **Auto-initialization**: Should we auto-init on first use? ❌ No, require explicit init
3. **Migration**: Should we auto-migrate from system llm? ❌ No, offer --import flag
4. **Logging**: Should we log LLM API calls to isolated db? ✅ Yes, llm handles this
5. **API keys**: Should API keys be isolated or shared? 🤔 Shared (system llm keys) - users set once

## Security Considerations

1. **File permissions**: Ensure config directory is user-readable only (0700)
2. **API keys**: If stored, ensure keys.json is 0600
3. **Path traversal**: Validate any user-provided paths
4. **Environment injection**: Sanitize environment variables

## Performance Considerations

1. **Startup time**: `set_llm_user_path()` should be fast (no I/O)
2. **Directory checks**: Cache initialization status to avoid repeated checks
3. **Environment variable**: Setting once per process is sufficient

## Rollout Plan

### Version 0.2.0
- Implement isolated config infrastructure
- Add init/check commands
- Update existing commands
- Mark as breaking change in changelog

### Communication
- Blog post explaining benefits
- Update PyPI description
- Migration guide in docs
- Announcement in release notes

---

**Document Status**: Draft
**Author**: Claude Code
**Date**: 2025-11-11
**Version**: 1.0
