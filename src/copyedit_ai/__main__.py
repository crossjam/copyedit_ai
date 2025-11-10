"""copyedit_ai CLI implementation.

Copyedit text from the CLI using AI
"""

import sys

import typer
from loguru import logger

from .self_subcommand import cli as self_cli
from .settings import Settings

cli = typer.Typer()

cli.add_typer(
    self_cli,
    name="self",
    help="Manage the copyedit_ai command.",
)


@cli.callback(invoke_without_command=True, no_args_is_help=True)
def global_callback(
    ctx: typer.Context,
    debug: bool = typer.Option(
        False,
        "--debug",
        "-D",
        help="Enable debugging output.",
    ),
) -> None:
    """Copyedit text from the CLI using AI"""
    ctx.obj = Settings()
    debug = debug or ctx.obj.debug
    (logger.enable if debug else logger.disable)("copyedit_ai")
    logger.add("copyedit_ai.log")
    logger.info(f"{debug=}")


if __name__ == "__main__":
    sys.exit(cli())
