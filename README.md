# copyedit_ai - Copyedit with AI

> Copyedit text from the CLI using AI

<!-- project description -->

## Features

<!-- project features -->

### Core Functionality
- Copyedit text using AI models via the command line
- Support for multiple LLM providers through the `llm` library
- Stream responses as they're generated or get complete responses
- Read from files or stdin

### LLM Configuration Management

Manage your isolated LLM configuration directly through copyedit:

- `copyedit self install` - Install LLM plugins from PyPI
- `copyedit self uninstall` - Uninstall LLM plugins
- `copyedit self plugins` - List and manage installed plugins
- `copyedit self keys` - Manage API keys for different model providers
- `copyedit self templates` - Manage prompt templates
- `copyedit self models` - List and configure available models
- `copyedit self aliases` - Create shortcuts for frequently used models
- `copyedit self schemas` - Manage stored schemas

All commands operate within copyedit's isolated configuration directory, preventing conflicts with system-wide llm installations.

#### Example: Adding Claude Support

```bash
# Install Anthropic plugin
copyedit self install llm-anthropic

# Set up API key
copyedit self keys set anthropic
# Enter your API key when prompted

# Create an alias for convenience
copyedit self aliases set sonnet claude-sonnet-4.5

# Use Claude to copyedit
copyedit --model sonnet article.txt
```

#### Example: Using Local Models with Ollama

```bash
# Install Ollama plugin
copyedit self install llm-ollama

# List available Ollama models
copyedit self models list

# Use a local model
copyedit --model llama3.2 draft.txt
``` 

## Installation

TBD: publishing a package to PyPI. 

### uvx
```console
uvx --from git+https://github.com/crossjam/copyedit_ai copyedit --help
```

### uv

```console
uv tool install git+https://github.com/crossjam/copyedit_ai
```

## Usage

The CLI can be invoked using either `copyedit` or `copyedit_ai`:

```console
copyedit --help
# or
copyedit_ai --help
```

The author prefers `copyedit`

## Development

This project and it's virtual environment is managed using [uv][uv] and
is configured to support automatic activation of virtual environments
using [direnv][direnv]. Development activites such as linting and testing
are automated via [Poe The Poet][poe], run `poe` after cloning
this repo.

### Clone
```console
git clone https://github.com/crossjam/copyedit_ai
cd copyedit_ai
```

### Create a Virtual Environment
```console
uv venv
```
### Install Dependencies
```console
uv sync
```
### Run `poe`
```console
poe --help
```

### Release Management

This project uses automated release management with GitHub Actions:

#### Version Bumping
- `poe publish_patch` - Bump patch version, commit, tag, and push
- `poe publish_minor` - Bump minor version, commit, tag, and push  
- `poe publish_major` - Bump major version, commit, tag, and push

#### Release Notes
- `poe changelog` - Generate changelog since last tag
- `poe release-notes` - Generate release notes file

#### Automatic Releases
When you push a version tag (e.g., `v1.0.0`), the unified GitHub Actions workflow will:
1. **Test** - Run tests across all supported Python versions and OS combinations
2. **Publish** - Build and publish to PyPI (only if tests pass)
3. **GitHub Release** - Create GitHub release with auto-generated notes and artifacts (only if PyPI publish succeeds)

This ensures a complete release pipeline where each step depends on the previous step's success.

#### MkDocs Documentation
- `poe docs-serve` - Serve documentation locally
- `poe docs-build` - Build documentation
- `poe docs-deploy` - Deploy to GitHub Pages

The template includes MkDocs with material theme and automatic deployment to GitHub Pages.

<hr>

[![gh:JnyJny/python-package-cookiecutter][python-package-cookiecutter-badge]][python-package-cookiecutter]

<!-- End Links -->

[python-package-cookiecutter-badge]: https://img.shields.io/badge/Made_With_Cookiecutter-python--package--cookiecutter-green?style=for-the-badge
[python-package-cookiecutter]: https://github.com/JnyJny/python-package-cookiecutter
[poe]: https://poethepoet.natn.io
[uv]: https://docs.astral.sh/uv/
[direnv]: https://direnv.net
