# CLI Usage

Copyedit with AI provides a command-line interface built with Typer.

## Basic Syntax

```bash
copyedit_ai [OPTIONS] [COMMAND] [ARGS]...
```

## Global Options

The following options are available for all commands:

- `--help`: Show help message and exit
- `--version`: Show version and exit

## Commands

### Help

Get help for the CLI or any specific command:

```bash
copyedit_ai --help
copyedit_ai [command] --help
```

### Version

Display the version:

```bash
copyedit_ai --version
```

## Self-Subcommands

Copyedit with AI uses a self-subcommand pattern, where the main command can also act as a subcommand. This provides a clean and intuitive interface.

## Logging

The CLI uses structured logging with Loguru. You can control the log level using:

```bash
copyedit_ai --log-level DEBUG [command]
```

## Log Files

By default, logs are also written to `copyedit_ai.log` in the current directory.
## Examples

For specific usage examples, see the [Examples](examples.md) page.

## Error Handling

The CLI provides clear error messages and appropriate exit codes:

- `0`: Success
- `1`: General error
- `2`: Command line usage error

## Shell Completion

Copyedit with AI supports shell completion for bash, zsh, and fish. To enable it:

### Bash

```bash
eval "$(_COPYEDIT_AI_COMPLETE=bash_source copyedit_ai)"
```

### Zsh

```bash
eval "$(_COPYEDIT_AI_COMPLETE=zsh_source copyedit_ai)"
```

### Fish

```bash
eval "$(_COPYEDIT_AI_COMPLETE=fish_source copyedit_ai)"
```