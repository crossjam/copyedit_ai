"""copyedit_ai CLI implementation.

Copyedit text from the CLI using AI
"""

import shutil
import sys
import tempfile
from pathlib import Path
from typing import cast

import llm
import typer
import typer.main
from click_default_group import DefaultGroup
from loguru import logger
from rich.console import Console
from rich.status import Status

from .copyedit import copyedit
from .self_subcommand import cli as self_cli
from .settings import Settings

console = Console(stderr=True)

app = typer.Typer()

# Register subcommands
app.add_typer(
    self_cli,
    name="self",
    help="Manage the copyedit_ai command.",
)


def _perform_copyedit(  # noqa: C901, PLR0912, PLR0915
    settings: Settings,
    file_path: Path | None,
    model: str | None,
    stream: bool,
    replace: bool,
) -> None:
    """Perform copyediting operation.

    Helper function to handle the actual copyediting logic.
    """
    # Use default model from settings if not provided
    model_name = model or settings.default_model

    # Read input text
    source_name = str(file_path) if file_path else "stdin"
    if file_path:
        logger.info(f"Reading from file: {file_path}")
        text = file_path.read_text()
    else:
        logger.info("Reading from stdin")
        text = sys.stdin.read()

    if not text.strip():
        logger.error("No input text provided")
        typer.echo("Error: No input text provided", err=True)
        raise typer.Exit(1)

    # Show startup message
    console.print(f"[bold blue]Copyediting:[/bold blue] {source_name}")

    # Perform copyediting with spinner
    try:
        status = Status(
            "[bold green]Generating copyedited version...",
            console=console,
            spinner="dots",
        )
        status.start()

        try:
            response = copyedit(text, model_name=model_name, stream=stream)
        finally:
            # For replace mode, we'll stop the spinner later
            # For non-replace streaming, we'll stop when first chunk arrives
            # For non-replace non-streaming, we'll stop it now
            if not replace and not stream:
                status.stop()

        # Collect the output
        output_text = ""
        if stream:
            # Stream output and collect it
            chunks = []
            first_chunk = True
            for chunk in response:
                # Stop spinner on first chunk for non-replace mode
                if first_chunk and not replace:
                    status.stop()
                    first_chunk = False

                chunks.append(chunk)
                if not replace:
                    # Only print to stdout if not replacing
                    typer.echo(chunk, nl=False)

            output_text = "".join(chunks)
            if not replace:
                typer.echo()  # Final newline
            else:
                # Stop spinner after collecting all chunks in replace mode
                status.stop()
        else:
            # Output complete response
            # Type assertion: in non-streaming mode, response is always Response
            assert isinstance(response, llm.Response)  # noqa: S101
            output_text = response.text()
            if not replace:
                typer.echo(output_text)
            else:
                # Stop spinner after getting response in replace mode
                status.stop()

        # Handle replace mode
        if replace:
            if not file_path:
                logger.error("Cannot use --replace with stdin input")
                typer.echo(
                    "Error: --replace requires a file argument, not stdin",
                    err=True,
                )
                raise typer.Exit(1)  # noqa: TRY301

            # Write to secure temporary file
            temp_fd, temp_path_str = tempfile.mkstemp(
                suffix=file_path.suffix,
                prefix=f"{file_path.stem}_copyedit_",
                text=True,
            )
            import os  # noqa: PLC0415

            os.close(temp_fd)  # Close fd, we'll use Path.open() instead
            temp_path = Path(temp_path_str)
            try:
                with temp_path.open("w") as temp_file:
                    temp_file.write(output_text)

                logger.info(f"Wrote copyedited content to temporary file: {temp_path}")

                # Prompt user for confirmation
                typer.echo(f"\nCopyedited content written to: {temp_path}")
                typer.echo(f"Original file: {file_path}")
                confirm = typer.confirm(
                    "\nReplace the original file with the copyedited version?",
                    default=False,
                )

                if confirm:
                    # Create backup of original file
                    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                    shutil.copy2(file_path, backup_path)
                    logger.info(f"Created backup: {backup_path}")

                    # Replace original with temp file
                    shutil.copy2(temp_path, file_path)
                    logger.info(f"Replaced {file_path} with copyedited version")

                    typer.secho(
                        f"✓ File replaced successfully. Backup saved to: {backup_path}",
                        fg=typer.colors.GREEN,
                    )
                else:
                    typer.echo(
                        f"Replacement cancelled. "
                        f"Copyedited version saved in: {temp_path}"
                    )
                    logger.info("User cancelled replacement")
            except Exception as e:
                logger.exception("Error during file replacement")
                typer.echo(f"Error: {e}", err=True)
                raise typer.Exit(1) from e

    except Exception as e:
        logger.exception("Error during copyediting")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@app.callback()
def main_callback(
    ctx: typer.Context,
    debug: bool = typer.Option(
        False,
        "--debug",
        "-D",
        help="Enable debugging output.",
    ),
    log_file: Path | None = typer.Option(
        None,
        "--log-file",
        help="Path to log file. If not specified, logging to file is disabled.",
    ),
) -> None:
    """Copyedit text from the CLI using AI"""
    ctx.obj = Settings()
    debug = debug or ctx.obj.debug

    # Only add file logging if explicitly requested
    log_path = log_file or ctx.obj.log_file

    # Enable logging if debug mode or file logging is requested
    if debug or log_path:
        logger.enable("copyedit_ai")
        if log_path:
            logger.add(str(log_path))
            logger.info(f"Logging to file: {log_path}")
        logger.info(f"{debug=}")
    else:
        logger.disable("copyedit_ai")


@app.command(name="edit")
def edit_command(
    ctx: typer.Context,
    file_path: Path | None = typer.Argument(
        None,
        help="File to copyedit. If not provided, reads from stdin.",
        exists=True,
        readable=True,
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="LLM model to use for copyediting.",
    ),
    stream: bool = typer.Option(
        True,
        "--stream/--no-stream",
        help="Stream the response as it's generated.",
    ),
    replace: bool = typer.Option(
        False,
        "--replace",
        "-r",
        help="Replace the original file after confirmation. Creates a .bak backup.",
    ),
) -> None:
    """Copyedit text using AI.

    Reads text from a file or stdin and copyedits it using an LLM.
    The copyedited text and a summary of changes are output to stdout.

    Examples:
        copyedit_ai < draft.txt
        copyedit_ai draft.txt
        cat draft.txt | copyedit_ai -m claude-opus
        copyedit_ai draft.txt --replace

    """
    settings: Settings = ctx.obj
    _perform_copyedit(settings, file_path, model, stream, replace)


def _attach_llm_passthroughs(main_group: DefaultGroup) -> None:
    """Attach llm's command groups to the 'self' subcommand.

    This allows users to access llm's native commands within copyedit_ai's
    isolated configuration context.

    Args:
        main_group: The main Click group (converted from Typer app)

    """
    try:
        from llm.cli import cli as llm_cli  # noqa: PLC0415
    except ImportError:
        logger.warning("Could not import llm.cli for passthrough commands")
        return

    # Get the 'self' subcommand (it's also a Click group)
    self_command = main_group.commands.get("self")
    if not self_command:
        logger.warning("Could not find 'self' subcommand for llm passthrough")
        return

    # List of llm commands to pass through
    passthrough_commands = [
        "templates",  # Manage prompt templates
        "keys",  # Manage API keys
        "models",  # List and configure models
        "schemas",  # Manage stored schemas
        "aliases",  # Manage model aliases
    ]

    # Attach each command group
    for cmd_name in passthrough_commands:
        # Don't override existing commands
        if cmd_name in self_command.commands:
            logger.debug(f"Skipping llm command {cmd_name} - already exists")
            continue

        llm_command = llm_cli.commands.get(cmd_name)
        if llm_command:
            self_command.add_command(llm_command, name=cmd_name)
            logger.debug(f"Attached llm command: {cmd_name}")
        else:
            logger.warning(f"Could not find llm command: {cmd_name}")


def cli() -> None:
    """CLI entry point with default command support."""
    click_group = typer.main.get_command(app)
    # Replace the group class with DefaultGroup
    click_group.__class__ = DefaultGroup

    # Cast to tell type checker about the new type
    default_group = cast("DefaultGroup", click_group)
    default_group.default_cmd_name = "edit"
    default_group.default_if_no_args = True

    # Attach llm passthrough commands to 'self' subcommand
    _attach_llm_passthroughs(default_group)

    default_group()


if __name__ == "__main__":
    sys.exit(cli())
