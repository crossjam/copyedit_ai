# Installation

Copyedit with AI requires Python 3.11 or later.

## Install from PyPI

The easiest way to install copyedit_ai is from PyPI:

```bash
pip install copyedit_ai
```

## Install from Source

You can also install from source:

```bash
git clone https://github.com/crossjam/copyedit_ai.git
cd copyedit_ai
pip install -e .
```

## Development Installation

For development, we recommend using `uv`:

```bash
git clone https://github.com/crossjam/copyedit_ai.git
cd copyedit_ai
uv sync
```

This will install all dependencies including development tools.

## Verify Installation

After installation, verify that copyedit_ai is working:

```bash
copyedit_ai --version
```

You should see the version number displayed.

## Next Steps

Now that you have copyedit_ai installed, check out the [Quick Start](quickstart.md) guide to learn how to use it.