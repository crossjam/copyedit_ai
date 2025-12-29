# GitHub Copilot Instructions for copyedit_ai

## Project Overview

copyedit_ai is a Python CLI tool that provides AI-powered copyediting through the command line. The project uses the `llm` library to support multiple LLM providers and offers both streaming and complete response modes.

## Technology Stack

- **Language:** Python 3.11+
- **Package Manager:** uv (UV package manager)
- **Testing:** pytest with coverage reporting
- **Linting:** ruff (format and check)
- **Type Checking:** ty
- **Task Runner:** Poe the Poet (poe)
- **CLI Framework:** Typer
- **Documentation:** MkDocs with Material theme
- **Dependencies:** llm, loguru, typer, pydantic_settings, rich, platformdirs, mdformat

## Setup and Development

### Environment Setup
- ALWAYS use `uv` for package management, never use pip directly
- Run `uv sync` to set up the environment from pyproject.toml + uv.lock
- All Python commands should be prefixed with `uv run`
- Never activate virtualenv manually - let uv handle it

### Running Commands
```bash
# Install dependencies
uv sync

# Run tests
uv run pytest -q -x

# Run with coverage
uv run pytest --cov=./src/copyedit_ai --cov-report=html

# Type checking
uv run ty src/copyedit_ai

# Linting and formatting
uv run ruff check src tests
uv run ruff format src tests
```

### Task Runner
- Use `poe` (Poe the Poet) for common development tasks
- Run `poe` to list all available tasks
- Common tasks:
  - `poe test` - Run test suite
  - `poe ruff` - Run ruff check and format
  - `poe ty` - Run type checking
  - `poe qc` - Run all quality checks (test, ruff, ty)
  - `poe check` - Run ruff and ty
  - `poe docs-serve` - Serve documentation locally

## Code Style and Quality

### Linting (Ruff)
- Ruff is configured with `fix = true` to auto-fix issues
- Follow ALL ruff rules with specific exceptions in pyproject.toml
- Ignored rules:
  - COM812 (missing-trailing-comma)
  - D203, D211, D212, D213 (docstring formatting conflicts)
  - FBT001, FBT003 (boolean type hints)
  - D400, D415 (missing trailing periods)
  - BLE001 (blank-except)
- Test files have additional exemptions (S101, S603, ANN001, ANN201)
- `__main__.py` exempts B008 (function-call-in-default-argument) for Typer defaults

### Type Checking
- Use ty for type checking on all source code
- Run `uv run ty src/copyedit_ai` before committing

### Imports
- Use isort ordering (configured in ruff)
- Imports are automatically sorted and formatted

### Code Comments
- Match the style of existing comments in the file
- Only add comments when necessary to explain complex logic
- Prefer self-documenting code over excessive comments

## Testing

### Test Framework
- Use pytest for all tests
- Test files in `tests/` directory
- Run tests with `uv run pytest -q -x` (quiet mode, stop on first failure)

### Coverage
- Maintain high test coverage
- Generate coverage reports with `uv run pytest --cov=./src/copyedit_ai --cov-report=html`
- Use `poe coverage` to generate and open coverage reports

### Test Requirements
- Write tests for all new features and bug fixes
- Tests should be clear, focused, and independent
- Follow existing test patterns in the repository
- Tests can use assertions (S101 exempted for test files)

## Security

### Best Practices
- Never hardcode secrets, API keys, or credentials
- Use environment variables or secure configuration for sensitive data
- The project uses platformdirs for isolated configuration storage
- LLM configuration is stored in an isolated directory (not system-wide)

### Dependencies
- All dependencies are managed through pyproject.toml
- Use `uv add <package>` to add new dependencies
- Keep dependencies up to date using dependabot (configured)

## Project Structure

```
copyedit_ai/
├── .github/           # GitHub configuration and workflows
│   ├── workflows/     # CI/CD workflows (release.yaml, docs.yml)
│   ├── ISSUE_TEMPLATE/  # Issue templates
│   └── PULL_REQUEST_TEMPLATE.md
├── src/copyedit_ai/   # Main source code
│   ├── __init__.py
│   ├── __main__.py    # CLI entry point
│   ├── copyedit.py    # Core copyedit functionality
│   ├── settings.py    # Configuration settings
│   ├── self_subcommand.py  # Self-management commands
│   └── user_dir.py    # User directory management
├── tests/             # Test files
├── docs/              # Documentation source
├── pyproject.toml     # Project configuration
├── uv.lock           # Locked dependencies
├── AGENTS.md         # AI agent instructions
├── README.md         # Project readme
├── CONTRIBUTING.md   # Contribution guidelines
└── CHANGELOG.md      # Change log
```

### Key Files
- `pyproject.toml`: Central configuration for dependencies, tools, and tasks
- `AGENTS.md`: Quick reference for AI coding agents (similar purpose to this file)
- `uv.lock`: Locked dependency versions (DO commit this file)
- `.gitignore`: Comprehensive ignore list including build artifacts, caches, and virtual environments

## CLI Commands

### Main Commands
- `copyedit_ai` or `copyedit` - Main CLI entry point
- Both commands invoke the same CLI defined in `__main__.py:cli`

### Self-Management Subcommands
The `self` subcommand group manages LLM configuration:
- `copyedit_ai self install` - Install LLM plugins
- `copyedit_ai self uninstall` - Uninstall plugins
- `copyedit_ai self plugins` - List/manage plugins
- `copyedit_ai self keys` - Manage API keys
- `copyedit_ai self templates` - Manage prompt templates
- `copyedit_ai self models` - List/configure models
- `copyedit_ai self aliases` - Create model shortcuts
- `copyedit_ai self schemas` - Manage stored schemas

## Build and Release

### Versioning
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Version is defined in pyproject.toml
- Use poe tasks for version bumps:
  - `poe publish_patch` - Bump patch version
  - `poe publish_minor` - Bump minor version
  - `poe publish_major` - Bump major version

### Release Process
1. Version bump tasks automatically:
   - Update version in pyproject.toml
   - Commit changes
   - Create git tag (e.g., v1.0.0)
   - Push changes and tags
2. GitHub Actions workflow (.github/workflows/release.yaml) triggers on tag push:
   - Runs tests across all supported Python versions
   - Publishes to PyPI (if tests pass)
   - Creates GitHub release with auto-generated notes

### Documentation
- Built with MkDocs and Material theme
- `poe docs-serve` - Serve locally for development
- `poe docs-build` - Build documentation
- `poe docs-deploy` - Deploy to GitHub Pages
- Automatic deployment configured in .github/workflows/docs.yml

## Dependencies and Plugins

### Core Dependencies
- `llm`: LLM library for AI model integration
- `typer`: CLI framework
- `loguru`: Logging
- `pydantic_settings`: Configuration management
- `rich`: Rich text formatting in terminal
- `platformdirs`: Cross-platform directory detection
- `mdformat`: Markdown formatting (with footnote and front-matter support)

### Development Dependencies
- `poethepoet`: Task runner
- `pytest`: Testing framework
- `pytest-cov`: Coverage reporting
- `ruff`: Linter and formatter
- `ty`: Type checker
- `toml-cli`: TOML manipulation

### Documentation Dependencies
- `mkdocs`: Documentation generator
- `mkdocstrings[python]`: API documentation
- `mkdocs-material`: Material theme
- Additional MkDocs plugins for navigation and features

## Best Practices

### When Adding Features
1. Update tests first or alongside implementation
2. Run `poe qc` before committing to ensure all quality checks pass
3. Update documentation if adding user-facing features
4. Follow existing patterns in the codebase
5. Keep changes focused and minimal

### When Fixing Bugs
1. Write a failing test that reproduces the bug
2. Fix the bug
3. Verify the test now passes
4. Run full test suite to ensure no regressions

### Before Committing
1. Run `poe qc` (tests, ruff, ty)
2. Ensure all tests pass
3. Verify type checking passes
4. Check that formatting is correct
5. Review changes for unintended modifications

## Working with uv

- **Adding packages:** `uv add <package-name>`
- **Adding dev packages:** `uv add --dev <package-name>`
- **Removing packages:** `uv remove <package-name>`
- **Updating packages:** `uv sync` updates from pyproject.toml
- **Running commands:** `uv run <command>` executes in the managed environment
- **Version bumping:** `uv version --bump patch|minor|major`

## Common Pitfalls to Avoid

1. **Don't use pip directly** - Always use `uv` for package management
2. **Don't activate virtualenv manually** - Let `uv run` handle it
3. **Don't skip quality checks** - Always run `poe qc` before committing
4. **Don't ignore type errors** - Fix all ty issues before committing
5. **Don't commit without tests** - New features and bug fixes need tests
6. **Don't hardcode paths** - Use platformdirs for cross-platform compatibility
7. **Don't ignore ruff warnings** - Fix or explicitly exempt with good reason
8. **Don't commit build artifacts** - They're in .gitignore for a reason
9. **Don't modify uv.lock manually** - Let uv manage it through sync/add/remove
10. **Don't skip documentation** - Update docs for user-facing changes
