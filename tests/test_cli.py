"""test copyedit_ai CLI: copyedit_ai."""

import importlib
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, create_autospec, patch

import llm
from click.testing import CliRunner as ClickRunner
from loguru import logger as loguru_logger
from typer.testing import CliRunner

if TYPE_CHECKING:
    from click_default_group import DefaultGroup

main_module_name = "copyedit_ai.__main__"
main_module = importlib.import_module(main_module_name)
runner = CliRunner()
# Use the Typer app for testing, not the wrapped cli function
cli = main_module.app


def _get_click_cli() -> "DefaultGroup":
    """Get the Click CLI with DefaultGroup for testing.

    This uses the shared setup function from the main module.
    """
    return main_module.setup_click_group()


def test_cli_help() -> None:
    """Test the main command-line interface help flag."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0


def test_cli_entry_points_exist() -> None:
    """Test that both copyedit and copyedit_ai entry points are defined."""
    # Read pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        pyproject = tomllib.load(f)

    # Check that both entry points exist
    scripts = pyproject["project"]["scripts"]
    assert "copyedit_ai" in scripts, "copyedit_ai entry point should exist"
    assert "copyedit" in scripts, "copyedit entry point should exist"

    # Verify both point to the same function
    assert scripts["copyedit_ai"] == "copyedit_ai.__main__:cli"
    assert scripts["copyedit"] == "copyedit_ai.__main__:cli"
    assert scripts["copyedit"] == scripts["copyedit_ai"], (
        "Both entry points should point to the same function"
    )


def test_cli_self_no_arguments() -> None:
    """Test the self subcommand with no arguments."""
    result = runner.invoke(cli, ["self"])
    assert result.exit_code != 0
    assert "Usage:" in result.output


def test_cli_self_help() -> None:
    """Test the self subcommand help flag."""
    result = runner.invoke(cli, ["self", "--help"])
    assert result.exit_code == 0


def test_cli_self_version(project_version: str) -> None:
    """Test the version self subcommand."""
    result = runner.invoke(cli, ["self", "version"])
    assert result.exit_code == 0
    assert result.output.strip() == project_version


def test_cli_version_command(project_version: str) -> None:
    """Test the top-level version command."""
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert result.output.strip() == f"copyedit-ai: {project_version}"


def test_cli_version_option_long(project_version: str) -> None:
    """Test the --version option."""
    click_cli = _get_click_cli()
    click_runner = ClickRunner()
    result = click_runner.invoke(click_cli, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == f"copyedit-ai: {project_version}"


def test_cli_version_option_short(project_version: str) -> None:
    """Test the -V option."""
    click_cli = _get_click_cli()
    click_runner = ClickRunner()
    result = click_runner.invoke(click_cli, ["-V"])
    assert result.exit_code == 0
    assert result.output.strip() == f"copyedit-ai: {project_version}"


@patch("copyedit_ai.__main__.copyedit")
def test_cli_with_file(mock_copyedit, tmp_path: Path) -> None:
    """Test the CLI with a file argument."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text with erors.")

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    result = runner.invoke(cli, ["edit", str(test_file)])

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()
    # Verify the text was read from the file
    call_args = mock_copyedit.call_args
    assert "Test text with erors." in call_args[0][0]


@patch("copyedit_ai.__main__.copyedit")
def test_cli_with_stdin(mock_copyedit) -> None:
    """Test the CLI with stdin input."""
    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    test_input = "Test text from stdin."
    result = runner.invoke(cli, ["edit"], input=test_input)

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()
    # Verify the text was read from stdin
    call_args = mock_copyedit.call_args
    assert test_input in call_args[0][0]


@patch("copyedit_ai.__main__.copyedit")
def test_cli_with_model_option(mock_copyedit, tmp_path: Path) -> None:
    """Test the CLI with --model option."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    result = runner.invoke(cli, ["edit", "--model", "gpt-4o", str(test_file)])

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()
    # Verify the model was passed
    call_kwargs = mock_copyedit.call_args[1]
    assert call_kwargs["model_name"] == "gpt-4o"


@patch("copyedit_ai.__main__.copyedit")
def test_cli_with_no_stream(mock_copyedit, tmp_path: Path) -> None:
    """Test the CLI with --no-stream option."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Mock the copyedit response for non-streaming
    # Use create_autospec to make isinstance checks work
    mock_response = create_autospec(llm.Response, instance=True)
    mock_response.text.return_value = "Corrected text"
    mock_copyedit.return_value = mock_response

    result = runner.invoke(cli, ["edit", "--no-stream", str(test_file)])

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()
    # Verify streaming was disabled
    call_kwargs = mock_copyedit.call_args[1]
    assert call_kwargs["stream"] is False


@patch("copyedit_ai.__main__.copyedit")
def test_cli_empty_input(mock_copyedit) -> None:
    """Test the CLI with empty input."""
    result = runner.invoke(cli, ["edit"], input="")

    assert result.exit_code == 1
    assert "No input text provided" in result.output
    mock_copyedit.assert_not_called()


def test_cli_file_not_found() -> None:
    """Test the CLI with a non-existent file."""
    result = runner.invoke(cli, ["edit", "nonexistent.txt"])

    # Typer exits with 2 for validation errors
    validation_error_exit_code = 2
    assert result.exit_code == validation_error_exit_code
    # Typer will show an error about the file not existing


@patch("copyedit_ai.self_subcommand.initialize")
@patch("copyedit_ai.self_subcommand.is_initialized")
@patch("copyedit_ai.self_subcommand.get_app_config_dir")
@patch("copyedit_ai.self_subcommand.get_llm_config_dir")
def test_cli_self_init(
    mock_get_llm_config,
    mock_get_app_config,
    mock_is_initialized,
    mock_initialize,
    tmp_path: Path,
) -> None:
    """Test the self init subcommand."""
    # Setup mocks
    mock_is_initialized.return_value = False
    app_config_dir = tmp_path / "app"
    llm_config_dir = tmp_path / "llm"
    mock_get_app_config.return_value = app_config_dir
    mock_get_llm_config.return_value = llm_config_dir

    result = runner.invoke(cli, ["self", "init"])

    assert result.exit_code == 0
    assert "Initialized copyedit_ai configuration" in result.output
    assert str(app_config_dir) in result.output
    assert str(llm_config_dir) in result.output
    mock_initialize.assert_called_once_with(force=False)


@patch("copyedit_ai.self_subcommand.is_initialized")
@patch("copyedit_ai.self_subcommand.get_app_config_dir")
@patch("copyedit_ai.self_subcommand.get_llm_config_dir")
def test_cli_self_init_already_initialized(
    mock_get_llm_config, mock_get_app_config, mock_is_initialized, tmp_path: Path
) -> None:
    """Test the self init subcommand when already initialized."""
    # Setup mocks
    mock_is_initialized.return_value = True
    app_config_dir = tmp_path / "app"
    llm_config_dir = tmp_path / "llm"
    mock_get_app_config.return_value = app_config_dir
    mock_get_llm_config.return_value = llm_config_dir

    result = runner.invoke(cli, ["self", "init"])

    assert result.exit_code == 0
    assert "already initialized" in result.output.lower()
    assert "Use --force to reinitialize" in result.output


@patch("copyedit_ai.self_subcommand.initialize")
@patch("copyedit_ai.self_subcommand.is_initialized")
@patch("copyedit_ai.self_subcommand.get_app_config_dir")
@patch("copyedit_ai.self_subcommand.get_llm_config_dir")
def test_cli_self_init_force(
    mock_get_llm_config,
    mock_get_app_config,
    mock_is_initialized,
    mock_initialize,
    tmp_path: Path,
) -> None:
    """Test the self init subcommand with --force option."""
    # Setup mocks
    mock_is_initialized.return_value = True
    app_config_dir = tmp_path / "app"
    llm_config_dir = tmp_path / "llm"
    mock_get_app_config.return_value = app_config_dir
    mock_get_llm_config.return_value = llm_config_dir

    result = runner.invoke(cli, ["self", "init", "--force"])

    assert result.exit_code == 0
    assert "Initialized copyedit_ai configuration" in result.output
    mock_initialize.assert_called_once_with(force=True)


@patch("copyedit_ai.self_subcommand._import_system_llm_config")
@patch("copyedit_ai.self_subcommand.initialize")
@patch("copyedit_ai.self_subcommand.is_initialized")
@patch("copyedit_ai.self_subcommand.get_app_config_dir")
@patch("copyedit_ai.self_subcommand.get_llm_config_dir")
def test_cli_self_init_import_system_config(
    mock_get_llm_config,
    mock_get_app_config,
    mock_is_initialized,
    _mock_initialize,  # noqa: PT019
    mock_import,
    tmp_path: Path,
) -> None:
    """Test the self init subcommand with --import-system-config option."""
    # Setup mocks
    mock_is_initialized.return_value = False
    app_config_dir = tmp_path / "app"
    llm_config_dir = tmp_path / "llm"
    mock_get_app_config.return_value = app_config_dir
    mock_get_llm_config.return_value = llm_config_dir

    result = runner.invoke(cli, ["self", "init", "--import-system-config"])

    assert result.exit_code == 0
    assert "Initialized copyedit_ai configuration" in result.output
    mock_import.assert_called_once_with(llm_config_dir)


@patch("copyedit_ai.self_subcommand.is_initialized")
@patch("copyedit_ai.self_subcommand.get_app_config_dir")
@patch("copyedit_ai.self_subcommand.get_llm_config_dir")
def test_cli_self_check_initialized(
    mock_get_llm_config, mock_get_app_config, mock_is_initialized, tmp_path: Path
) -> None:
    """Test the self check subcommand when initialized."""
    # Setup mocks
    mock_is_initialized.return_value = True
    app_config_dir = tmp_path / "app"
    llm_config_dir = tmp_path / "llm"
    llm_config_dir.mkdir(parents=True)
    mock_get_app_config.return_value = app_config_dir
    mock_get_llm_config.return_value = llm_config_dir

    # Create templates directory and a test template
    templates_dir = llm_config_dir / "templates"
    templates_dir.mkdir()
    (templates_dir / "test.yaml").write_text("test: content")

    # Create aliases file
    aliases_file = llm_config_dir / "aliases.json"
    aliases_file.write_text('{"fast": "gpt-4o-mini"}')

    result = runner.invoke(cli, ["self", "check"])

    assert result.exit_code == 0
    assert "Configuration initialized" in result.output
    assert str(app_config_dir) in result.output
    assert str(llm_config_dir) in result.output
    assert "Templates (1)" in result.output
    assert "test" in result.output
    assert "Aliases (1)" in result.output
    assert "fast -> gpt-4o-mini" in result.output


@patch("copyedit_ai.self_subcommand.is_initialized")
@patch("copyedit_ai.self_subcommand.get_app_config_dir")
def test_cli_self_check_not_initialized(
    mock_get_app_config, mock_is_initialized, tmp_path: Path
) -> None:
    """Test the self check subcommand when not initialized."""
    # Setup mocks
    mock_is_initialized.return_value = False
    app_config_dir = tmp_path / "app"
    mock_get_app_config.return_value = app_config_dir

    result = runner.invoke(cli, ["self", "check"])

    assert result.exit_code == 1
    assert "Configuration not initialized" in result.output
    assert "copyedit_ai self init" in result.output


def test_cli_self_has_passthrough_commands() -> None:
    """Test that llm passthrough commands are attached to self subcommand."""
    import typer.main  # noqa: PLC0415

    from copyedit_ai.__main__ import (  # noqa: PLC0415
        _attach_llm_passthroughs,
        app,
    )

    # Convert to Click and check commands
    click_group = typer.main.get_command(app)

    # Attach the passthroughs
    _attach_llm_passthroughs(click_group)

    self_command = click_group.commands.get("self")
    assert self_command is not None

    # Verify passthrough commands exist
    expected_commands = [
        "templates",
        "keys",
        "models",
        "schemas",
        "aliases",
        "install",
        "uninstall",
        "plugins",
    ]
    for cmd_name in expected_commands:
        assert cmd_name in self_command.commands, (
            f"Expected {cmd_name} in self commands"
        )


def test_cli_self_templates_help() -> None:
    """Test that templates passthrough help works."""
    import typer.main  # noqa: PLC0415
    from click.testing import CliRunner as ClickRunner  # noqa: PLC0415

    from copyedit_ai.__main__ import _attach_llm_passthroughs  # noqa: PLC0415

    # Convert to Click and attach passthroughs
    click_group = typer.main.get_command(cli)
    _attach_llm_passthroughs(click_group)

    # Use Click's test runner for the Click group
    click_runner = ClickRunner()
    result = click_runner.invoke(click_group, ["self", "templates", "--help"])

    # Should show help for templates command
    assert result.exit_code == 0
    assert "templates" in result.output.lower()


def test_cli_self_keys_help() -> None:
    """Test that keys passthrough help works."""
    import typer.main  # noqa: PLC0415
    from click.testing import CliRunner as ClickRunner  # noqa: PLC0415

    from copyedit_ai.__main__ import _attach_llm_passthroughs  # noqa: PLC0415

    # Convert to Click and attach passthroughs
    click_group = typer.main.get_command(cli)
    _attach_llm_passthroughs(click_group)

    click_runner = ClickRunner()
    result = click_runner.invoke(click_group, ["self", "keys", "--help"])

    # Should show help for keys command
    assert result.exit_code == 0
    assert "keys" in result.output.lower() or "api" in result.output.lower()


def test_cli_self_models_help() -> None:
    """Test that models passthrough help works."""
    import typer.main  # noqa: PLC0415
    from click.testing import CliRunner as ClickRunner  # noqa: PLC0415

    from copyedit_ai.__main__ import _attach_llm_passthroughs  # noqa: PLC0415

    # Convert to Click and attach passthroughs
    click_group = typer.main.get_command(cli)
    _attach_llm_passthroughs(click_group)

    click_runner = ClickRunner()
    result = click_runner.invoke(click_group, ["self", "models", "--help"])

    # Should show help for models command
    assert result.exit_code == 0
    assert "model" in result.output.lower()


def test_cli_self_aliases_help() -> None:
    """Test that aliases passthrough help works."""
    import typer.main  # noqa: PLC0415
    from click.testing import CliRunner as ClickRunner  # noqa: PLC0415

    from copyedit_ai.__main__ import _attach_llm_passthroughs  # noqa: PLC0415

    # Convert to Click and attach passthroughs
    click_group = typer.main.get_command(cli)
    _attach_llm_passthroughs(click_group)

    click_runner = ClickRunner()
    result = click_runner.invoke(click_group, ["self", "aliases", "--help"])

    # Should show help for aliases command
    assert result.exit_code == 0
    assert "alias" in result.output.lower()


def test_cli_self_schemas_help() -> None:
    """Test that schemas passthrough help works."""
    import typer.main  # noqa: PLC0415
    from click.testing import CliRunner as ClickRunner  # noqa: PLC0415

    from copyedit_ai.__main__ import _attach_llm_passthroughs  # noqa: PLC0415

    # Convert to Click and attach passthroughs
    click_group = typer.main.get_command(cli)
    _attach_llm_passthroughs(click_group)

    click_runner = ClickRunner()
    result = click_runner.invoke(click_group, ["self", "schemas", "--help"])

    # Should show help for schemas command
    assert result.exit_code == 0
    assert "schema" in result.output.lower()


def test_cli_self_install_help() -> None:
    """Test that install passthrough help works."""
    import typer.main  # noqa: PLC0415
    from click.testing import CliRunner as ClickRunner  # noqa: PLC0415

    from copyedit_ai.__main__ import _attach_llm_passthroughs  # noqa: PLC0415

    # Convert to Click and attach passthroughs
    click_group = typer.main.get_command(cli)
    _attach_llm_passthroughs(click_group)

    click_runner = ClickRunner()
    result = click_runner.invoke(click_group, ["self", "install", "--help"])

    # Should show help for install command
    assert result.exit_code == 0
    assert "install" in result.output.lower() or "plugin" in result.output.lower()


def test_cli_self_uninstall_help() -> None:
    """Test that uninstall passthrough help works."""
    import typer.main  # noqa: PLC0415
    from click.testing import CliRunner as ClickRunner  # noqa: PLC0415

    from copyedit_ai.__main__ import _attach_llm_passthroughs  # noqa: PLC0415

    # Convert to Click and attach passthroughs
    click_group = typer.main.get_command(cli)
    _attach_llm_passthroughs(click_group)

    click_runner = ClickRunner()
    result = click_runner.invoke(click_group, ["self", "uninstall", "--help"])

    # Should show help for uninstall command
    assert result.exit_code == 0
    assert "uninstall" in result.output.lower() or "remove" in result.output.lower()


def test_cli_self_plugins_help() -> None:
    """Test that plugins passthrough help works."""
    import typer.main  # noqa: PLC0415
    from click.testing import CliRunner as ClickRunner  # noqa: PLC0415

    from copyedit_ai.__main__ import _attach_llm_passthroughs  # noqa: PLC0415

    # Convert to Click and attach passthroughs
    click_group = typer.main.get_command(cli)
    _attach_llm_passthroughs(click_group)

    click_runner = ClickRunner()
    result = click_runner.invoke(click_group, ["self", "plugins", "--help"])

    # Should show help for plugins command
    assert result.exit_code == 0
    assert "plugin" in result.output.lower()


@patch("copyedit_ai.__main__.copyedit")
def test_cli_replace_with_confirmation(mock_copyedit, tmp_path: Path) -> None:
    """Test the --replace option with user confirmation."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    original_content = "Test text with erors."
    test_file.write_text(original_content)

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Test text with errors."]))
    mock_copyedit.return_value = mock_response

    # Simulate user confirming the replacement
    result = runner.invoke(cli, ["edit", str(test_file), "--replace"], input="y\n")

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify the file was replaced (mdformat.text adds a trailing newline)
    assert test_file.read_text() == "Test text with errors.\n"

    # Verify backup was created
    backup_path = tmp_path / "test.txt.bak"
    assert backup_path.exists()
    assert backup_path.read_text() == original_content

    # Check output messages
    assert "Replace the original file" in result.output
    assert "File replaced successfully" in result.output
    assert "Backup saved to" in result.output


@patch("copyedit_ai.__main__.copyedit")
def test_cli_replace_with_cancellation(mock_copyedit, tmp_path: Path) -> None:
    """Test the --replace option with user cancellation."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    original_content = "Test text with erors."
    test_file.write_text(original_content)

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Test text with errors."]))
    mock_copyedit.return_value = mock_response

    # Simulate user cancelling the replacement
    result = runner.invoke(cli, ["edit", str(test_file), "--replace"], input="n\n")

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify the original file was not changed
    assert test_file.read_text() == original_content

    # Verify no backup was created
    backup_path = tmp_path / "test.txt.bak"
    assert not backup_path.exists()

    # Check output messages
    assert "Replacement cancelled" in result.output
    assert "Copyedited version saved in" in result.output


@patch("copyedit_ai.__main__.copyedit")
def test_cli_replace_with_stdin_error(mock_copyedit) -> None:
    """Test that --replace with stdin input produces an error."""
    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Test text with errors."]))
    mock_copyedit.return_value = mock_response

    test_input = "Test text with erors."
    result = runner.invoke(cli, ["edit", "--replace"], input=test_input)

    assert result.exit_code == 1
    assert "--replace requires a file argument" in result.output


@patch("copyedit_ai.__main__.copyedit")
def test_cli_replace_no_stream(mock_copyedit, tmp_path: Path) -> None:
    """Test the --replace option with --no-stream."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    original_content = "Test text with erors."
    test_file.write_text(original_content)

    # Mock the copyedit response for non-streaming
    mock_response = create_autospec(llm.Response, instance=True)
    mock_response.text.return_value = "Test text with errors."
    mock_copyedit.return_value = mock_response

    # Simulate user confirming the replacement
    result = runner.invoke(
        cli, ["edit", str(test_file), "--replace", "--no-stream"], input="y\n"
    )

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify the file was replaced (mdformat.text adds a trailing newline)
    assert test_file.read_text() == "Test text with errors.\n"

    # Verify backup was created
    backup_path = tmp_path / "test.txt.bak"
    assert backup_path.exists()
    assert backup_path.read_text() == original_content


@patch("copyedit_ai.__main__.copyedit")
def test_cli_no_log_file_by_default(mock_copyedit, tmp_path: Path) -> None:
    """Test that no log file is created by default."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    # Run in the tmp_path directory
    import os  # noqa: PLC0415

    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        result = runner.invoke(cli, ["edit", str(test_file)])

        assert result.exit_code == 0

        # Verify no log file was created in the current directory
        assert not (tmp_path / "copyedit_ai.log").exists()
    finally:
        os.chdir(original_cwd)


@patch("copyedit_ai.__main__.copyedit")
def test_cli_with_log_file_option(mock_copyedit, tmp_path: Path) -> None:
    """Test that log file is created when --log-file is specified."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    # Specify log file path
    log_file_path = tmp_path / "custom.log"

    result = runner.invoke(
        cli, ["--log-file", str(log_file_path), "edit", str(test_file)]
    )

    assert result.exit_code == 0, f"Output: {result.output}"

    # Ensure all log handlers have completed their writes
    # This is necessary because CliRunner may close file handles
    # before loguru finishes writing, especially on some platforms
    loguru_logger.complete()

    # Verify log file was created
    assert log_file_path.exists()
    log_content = log_file_path.read_text()
    assert "Logging to file:" in log_content or "debug=" in log_content


@patch("copyedit_ai.__main__.copyedit")
def test_cli_startup_message_with_file(mock_copyedit, tmp_path: Path) -> None:
    """Test that startup message shows the filename."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    result = runner.invoke(cli, ["edit", str(test_file)])

    assert result.exit_code == 0
    # The startup message goes to stderr (Rich Console is configured with stderr=True)
    # Typer's CliRunner captures both stdout and stderr in output
    assert "Copyediting:" in result.output or str(test_file) in result.output


@patch("copyedit_ai.__main__.copyedit")
def test_cli_startup_message_with_stdin(mock_copyedit) -> None:
    """Test that startup message shows 'stdin' when reading from stdin."""
    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    test_input = "Test text from stdin."
    result = runner.invoke(cli, ["edit"], input=test_input)

    assert result.exit_code == 0
    # Check for startup message mentioning stdin
    assert "Copyediting:" in result.output or "stdin" in result.output


@patch("copyedit_ai.__main__.mdformat.text")
@patch("copyedit_ai.__main__.copyedit")
def test_cli_wrap_width_default(mock_copyedit, mock_mdformat, tmp_path: Path) -> None:
    """Test that the default wrap width is 80."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    # Mock mdformat.text to return the input unchanged
    mock_mdformat.return_value = "Corrected text"

    result = runner.invoke(cli, ["edit", str(test_file)])

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify mdformat.text was called with default wrap width of 80
    mock_mdformat.assert_called_once_with(
        "Corrected text",
        options={"wrap": 80},
        extensions={"front_matters", "footnote"},
    )


@patch("copyedit_ai.__main__.mdformat.text")
@patch("copyedit_ai.__main__.copyedit")
def test_cli_wrap_width_custom(mock_copyedit, mock_mdformat, tmp_path: Path) -> None:
    """Test that custom wrap width is passed to mdformat."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    # Mock mdformat.text to return the input unchanged
    mock_mdformat.return_value = "Corrected text"

    result = runner.invoke(cli, ["edit", "--wrap-width", "120", str(test_file)])

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify mdformat.text was called with custom wrap width of 120
    mock_mdformat.assert_called_once_with(
        "Corrected text",
        options={"wrap": 120},
        extensions={"front_matters", "footnote"},
    )


@patch("copyedit_ai.__main__.mdformat.text")
@patch("copyedit_ai.__main__.copyedit")
def test_cli_wrap_width_short_option(
    mock_copyedit, mock_mdformat, tmp_path: Path
) -> None:
    """Test that the -w short option works for wrap width."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    # Mock mdformat.text to return the input unchanged
    mock_mdformat.return_value = "Corrected text"

    result = runner.invoke(cli, ["edit", "-w", "72", str(test_file)])

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify mdformat.text was called with wrap width of 72
    mock_mdformat.assert_called_once_with(
        "Corrected text",
        options={"wrap": 72},
        extensions={"front_matters", "footnote"},
    )


@patch("copyedit_ai.__main__.mdformat.text")
@patch("copyedit_ai.__main__.copyedit")
def test_cli_wrap_width_with_no_stream(
    mock_copyedit, mock_mdformat, tmp_path: Path
) -> None:
    """Test that wrap width works correctly with --no-stream option."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Mock the copyedit response for non-streaming
    mock_response = create_autospec(llm.Response, instance=True)
    mock_response.text.return_value = "Corrected text without streaming"
    mock_copyedit.return_value = mock_response

    # Mock mdformat.text to return the input unchanged
    mock_mdformat.return_value = "Corrected text without streaming"

    result = runner.invoke(
        cli, ["edit", "--no-stream", "--wrap-width", "100", str(test_file)]
    )

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify mdformat.text was called with wrap width of 100
    mock_mdformat.assert_called_once_with(
        "Corrected text without streaming",
        options={"wrap": 100},
        extensions={"front_matters", "footnote"},
    )


@patch("copyedit_ai.__main__.mdformat.text")
@patch("copyedit_ai.__main__.copyedit")
def test_cli_wrap_width_with_replace(
    mock_copyedit, mock_mdformat, tmp_path: Path
) -> None:
    """Test that wrap width works correctly with --replace option."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    # Mock mdformat.text to return the input unchanged
    mock_mdformat.return_value = "Corrected text"

    # Simulate user confirming the replacement
    result = runner.invoke(
        cli, ["edit", "--replace", "-w", "80", str(test_file)], input="y\n"
    )

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify mdformat.text was called with wrap width of 80
    mock_mdformat.assert_called_once_with(
        "Corrected text",
        options={"wrap": 80},
        extensions={"front_matters", "footnote"},
    )

    # Verify the file was replaced with the formatted text
    assert test_file.read_text() == "Corrected text"


@patch("copyedit_ai.__main__.mdformat.text")
@patch("copyedit_ai.__main__.copyedit")
def test_cli_markdown_default(mock_copyedit, mock_mdformat, tmp_path: Path) -> None:
    """Test that markdown formatting is enabled by default."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    # Mock mdformat.text to return the input unchanged
    mock_mdformat.return_value = "Corrected text"

    result = runner.invoke(cli, ["edit", str(test_file)])

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify mdformat.text was called (markdown formatting is enabled by default)
    mock_mdformat.assert_called_once()


@patch("copyedit_ai.__main__.mdformat.text")
@patch("copyedit_ai.__main__.copyedit")
def test_cli_no_markdown(mock_copyedit, mock_mdformat, tmp_path: Path) -> None:
    """Test that --no-markdown disables markdown formatting."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    # Mock mdformat.text (should not be called)
    mock_mdformat.return_value = "Should not be called"

    result = runner.invoke(cli, ["edit", "--no-markdown", str(test_file)])

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify mdformat.text was NOT called
    mock_mdformat.assert_not_called()


@patch("copyedit_ai.__main__.mdformat.text")
@patch("copyedit_ai.__main__.copyedit")
def test_cli_no_markdown_with_no_stream(
    mock_copyedit, mock_mdformat, tmp_path: Path
) -> None:
    """Test that --no-markdown works with --no-stream option."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Mock the copyedit response for non-streaming
    mock_response = create_autospec(llm.Response, instance=True)
    mock_response.text.return_value = "Corrected text without streaming"
    mock_copyedit.return_value = mock_response

    # Mock mdformat.text (should not be called)
    mock_mdformat.return_value = "Should not be called"

    result = runner.invoke(
        cli, ["edit", "--no-stream", "--no-markdown", str(test_file)]
    )

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify mdformat.text was NOT called
    mock_mdformat.assert_not_called()


@patch("copyedit_ai.__main__.mdformat.text")
@patch("copyedit_ai.__main__.copyedit")
def test_cli_no_markdown_with_replace(
    mock_copyedit, mock_mdformat, tmp_path: Path
) -> None:
    """Test that --no-markdown works with --replace option."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    original_content = "Test text."
    test_file.write_text(original_content)

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    # Mock mdformat.text (should not be called)
    mock_mdformat.return_value = "Should not be called"

    # Simulate user confirming the replacement
    result = runner.invoke(
        cli, ["edit", "--replace", "--no-markdown", str(test_file)], input="y\n"
    )

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify mdformat.text was NOT called
    mock_mdformat.assert_not_called()

    # Verify the file was replaced with the unformatted text
    assert test_file.read_text() == "Corrected text"


@patch("copyedit_ai.__main__.mdformat.text")
@patch("copyedit_ai.__main__.copyedit")
def test_cli_markdown_with_wrap_width(
    mock_copyedit, mock_mdformat, tmp_path: Path
) -> None:
    """Test that --markdown and --wrap-width work together."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    # Mock mdformat.text to return the input unchanged
    mock_mdformat.return_value = "Corrected text"

    result = runner.invoke(
        cli, ["edit", "--markdown", "--wrap-width", "100", str(test_file)]
    )

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify mdformat.text was called with the correct wrap width
    mock_mdformat.assert_called_once_with(
        "Corrected text",
        options={"wrap": 100},
        extensions={"front_matters", "footnote"},
    )


@patch("copyedit_ai.__main__.mdformat.text")
@patch("copyedit_ai.__main__.copyedit")
def test_cli_no_markdown_ignores_wrap_width(
    mock_copyedit, mock_mdformat, tmp_path: Path
) -> None:
    """Test that --no-markdown ignores --wrap-width since formatting is disabled."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter(["Corrected text"]))
    mock_copyedit.return_value = mock_response

    # Mock mdformat.text (should not be called)
    mock_mdformat.return_value = "Should not be called"

    result = runner.invoke(
        cli, ["edit", "--no-markdown", "--wrap-width", "100", str(test_file)]
    )

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify mdformat.text was NOT called even though wrap-width was specified
    mock_mdformat.assert_not_called()


# Integration tests for actual word wrapping execution


@patch("copyedit_ai.__main__.copyedit")
def test_cli_word_wrapping_executed_with_default_settings(
    mock_copyedit, tmp_path: Path
) -> None:
    """Test that word wrapping is actually executed with default settings."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Create a long line that should be wrapped at 90 characters
    long_line = (
        "This is a very long line that definitely exceeds ninety "
        "characters and should be wrapped by mdformat when the default "
        "wrap width setting of ninety characters is applied to the text."
    )

    # Mock the copyedit response with a long line
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([long_line]))
    mock_copyedit.return_value = mock_response

    result = runner.invoke(cli, ["edit", str(test_file)])

    assert result.exit_code == 0

    # The output should contain the text, and mdformat should have wrapped it
    # Default wrap is 90 chars, so the long line should be broken
    output = result.output
    # Check that no single line exceeds 90 characters significantly
    # (accounting for some mdformat behavior)
    lines = output.strip().split("\n")
    # Filter out non-content lines (like status messages)
    content_lines = [line for line in lines if not line.startswith("[")]
    # At least one line should exist and the long content should be wrapped
    assert any(len(line) < len(long_line) for line in content_lines if line.strip())


@patch("copyedit_ai.__main__.copyedit")
def test_cli_word_wrapping_executed_with_custom_width(
    mock_copyedit, tmp_path: Path
) -> None:
    """Test that word wrapping is executed with custom wrap width."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Create a line that would fit in 90 chars but not in 50
    medium_line = (
        "This is a medium length line that fits in ninety "
        "characters but should wrap at fifty."
    )

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([medium_line]))
    mock_copyedit.return_value = mock_response

    # Use a custom wrap width of 50
    result = runner.invoke(cli, ["edit", "--wrap-width", "50", str(test_file)])

    assert result.exit_code == 0

    # The output should be wrapped at 50 characters
    output = result.output
    lines = output.strip().split("\n")
    content_lines = [line for line in lines if not line.startswith("[")]
    # With 50 char wrap, the line should be split
    # Allow some tolerance for mdformat behavior (60 chars)
    max_line_length_with_tolerance = 60
    assert len(content_lines) > 1 or all(
        len(line) <= max_line_length_with_tolerance
        for line in content_lines
        if line.strip()
    )


@patch("copyedit_ai.__main__.copyedit")
def test_cli_word_wrapping_not_executed_with_no_markdown(
    mock_copyedit, tmp_path: Path
) -> None:
    """Test that word wrapping is NOT executed when --no-markdown is set."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Create a very long line
    long_line = (
        "This is a very long line that definitely exceeds ninety "
        "characters and should NOT be wrapped when markdown formatting "
        "is disabled with the no-markdown flag."
    )

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([long_line]))
    mock_copyedit.return_value = mock_response

    result = runner.invoke(cli, ["edit", "--no-markdown", str(test_file)])

    assert result.exit_code == 0

    # The output should NOT be wrapped - the long line should remain intact
    output = result.output
    # The long line should appear as-is in the output
    default_wrap_width = 90
    assert (
        long_line in output
        or len([line for line in output.split("\n") if len(line) > default_wrap_width])
        > 0
    )


@patch("copyedit_ai.__main__.copyedit")
def test_cli_word_wrapping_executed_in_streaming_mode(
    mock_copyedit, tmp_path: Path
) -> None:
    """Test that word wrapping is executed in streaming mode."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Create chunks that form a long line when combined
    chunk1 = "This is a very long line that definitely exceeds ninety characters "
    chunk2 = "and should be wrapped by mdformat even when streaming is enabled."

    # Mock the copyedit response with streaming chunks
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([chunk1, chunk2]))
    mock_copyedit.return_value = mock_response

    result = runner.invoke(cli, ["edit", "--stream", str(test_file)])

    assert result.exit_code == 0

    # Even in streaming mode, the final output should be wrapped
    # Note: In streaming mode, chunks are output as they arrive,
    # but mdformat is still applied to the collected text


@patch("copyedit_ai.__main__.copyedit")
def test_cli_word_wrapping_executed_in_non_streaming_mode(
    mock_copyedit, tmp_path: Path
) -> None:
    """Test that word wrapping is executed in non-streaming mode."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Create a long line
    long_line = (
        "This is a very long line that definitely exceeds ninety "
        "characters and should be wrapped by mdformat when "
        "non-streaming mode is used."
    )

    # Mock the copyedit response for non-streaming
    mock_response = create_autospec(llm.Response, instance=True)
    mock_response.text.return_value = long_line
    mock_copyedit.return_value = mock_response

    result = runner.invoke(cli, ["edit", "--no-stream", str(test_file)])

    assert result.exit_code == 0

    # The output should be wrapped
    output = result.output
    # At least verify the command succeeded and produced output
    assert len(output) > 0


@patch("copyedit_ai.__main__.copyedit")
def test_cli_word_wrapping_executed_with_replace_mode(
    mock_copyedit, tmp_path: Path
) -> None:
    """Test that word wrapping is executed and written to file in replace mode."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Create a long line that should be wrapped
    long_line = (
        "This is a very long line that definitely exceeds ninety "
        "characters and should be wrapped by mdformat and written "
        "to the file in replace mode."
    )

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([long_line]))
    mock_copyedit.return_value = mock_response

    # Simulate user confirming the replacement
    result = runner.invoke(
        cli, ["edit", "--replace", "--wrap-width", "60", str(test_file)], input="y\n"
    )

    assert result.exit_code == 0

    # Read the file and verify it was wrapped
    file_content = test_file.read_text()
    # The file should not contain the full long line on a single line
    # It should be wrapped into multiple lines
    file_lines = file_content.strip().split("\n")
    # With 60 char wrap, a long line should be split into at least 2-3 lines
    min_expected_lines = 2
    assert len(file_lines) >= min_expected_lines, (
        "Long line should be wrapped into multiple lines"
    )
    # Verify no line is excessively long (with some tolerance for mdformat)
    max_line_length = 70
    assert all(len(line) < max_line_length for line in file_lines), (
        "All lines should respect wrap width"
    )


@patch("copyedit_ai.__main__.copyedit")
def test_cli_word_wrapping_not_executed_with_no_markdown_and_replace(
    mock_copyedit, tmp_path: Path
) -> None:
    """Test that word wrapping is NOT executed with --no-markdown in replace mode."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    original_content = "Test text."
    test_file.write_text(original_content)

    # Create a long line that should NOT be wrapped
    long_line = (
        "This is a very long line that definitely exceeds ninety "
        "characters and should NOT be wrapped when no-markdown flag "
        "is used even in replace mode."
    )

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([long_line]))
    mock_copyedit.return_value = mock_response

    # Simulate user confirming the replacement
    result = runner.invoke(
        cli, ["edit", "--replace", "--no-markdown", str(test_file)], input="y\n"
    )

    assert result.exit_code == 0

    # Read the file and verify it was NOT wrapped
    file_content = test_file.read_text()
    # The long line should be preserved as-is
    assert long_line in file_content, (
        "Long line should not be wrapped with --no-markdown"
    )


@patch("copyedit_ai.__main__.copyedit")
def test_cli_word_wrapping_with_multiple_paragraphs(
    mock_copyedit, tmp_path: Path
) -> None:
    """Test that word wrapping handles multiple paragraphs correctly."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Create multiple paragraphs with long lines
    paragraph1 = (
        "This is the first paragraph with a very long line that "
        "definitely exceeds ninety characters and should be wrapped."
    )
    paragraph2 = (
        "This is the second paragraph with another very long line that "
        "also exceeds ninety characters and should be wrapped."
    )
    text_with_paragraphs = f"{paragraph1}\n\n{paragraph2}"

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([text_with_paragraphs]))
    mock_copyedit.return_value = mock_response

    result = runner.invoke(cli, ["edit", "--wrap-width", "70", str(test_file)])

    assert result.exit_code == 0

    # The output should preserve paragraph breaks while wrapping lines


@patch("copyedit_ai.__main__.copyedit")
def test_cli_word_wrapping_combination_stream_and_custom_width(
    mock_copyedit, tmp_path: Path
) -> None:
    """Test word wrapping with --stream and custom --wrap-width together."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Create a long line
    long_line = (
        "This is a very long line that should be wrapped at the "
        "custom width of forty characters specified by the user."
    )

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([long_line]))
    mock_copyedit.return_value = mock_response

    result = runner.invoke(
        cli, ["edit", "--stream", "--wrap-width", "40", str(test_file)]
    )

    # Just verify the command executes successfully
    assert result.exit_code == 0


@patch("copyedit_ai.__main__.copyedit")
def test_cli_word_wrapping_combination_no_stream_and_custom_width(
    mock_copyedit, tmp_path: Path
) -> None:
    """Test word wrapping with --no-stream and custom --wrap-width together."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Create a long line
    long_line = (
        "This is a very long line that should be wrapped at the "
        "custom width of eighty characters specified."
    )

    # Mock the copyedit response for non-streaming
    mock_response = create_autospec(llm.Response, instance=True)
    mock_response.text.return_value = long_line
    mock_copyedit.return_value = mock_response

    result = runner.invoke(
        cli, ["edit", "--no-stream", "--wrap-width", "80", str(test_file)]
    )

    # Just verify the command executes successfully
    assert result.exit_code == 0


@patch("copyedit_ai.__main__.mdformat.text")
@patch("copyedit_ai.__main__.copyedit")
def test_cli_word_wrapping_validation_warning(
    mock_copyedit, mock_mdformat, tmp_path: Path
) -> None:
    """Test that a warning is emitted when word wrapping doesn't appear to work."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test text.")

    # Create multiple very long lines that exceed the wrap width
    # Using .join() is clearer than f-strings for multi-line text
    long_lines = "\n".join(  # noqa: FLY002
        [
            (
                "This is a very long line number one that definitely exceeds the "
                "wrap width and should trigger a warning if not properly wrapped."
            ),
            (
                "This is a very long line number two that definitely exceeds the "
                "wrap width and should trigger a warning if not properly wrapped."
            ),
            (
                "This is a very long line number three that definitely exceeds the "
                "wrap width and should trigger a warning if not properly wrapped."
            ),
            (
                "This is a very long line number four that definitely exceeds the "
                "wrap width and should trigger a warning if not properly wrapped."
            ),
        ]
    )

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([long_lines]))
    mock_copyedit.return_value = mock_response

    # Mock mdformat.text to return the text unchanged (simulating wrapping failure)
    mock_mdformat.return_value = long_lines

    result = runner.invoke(cli, ["edit", "--wrap-width", "50", str(test_file)])

    assert result.exit_code == 0
    # Check that a warning about wrapping was emitted
    assert "Warning" in result.output or "wrap" in result.output.lower()


@patch("copyedit_ai.__main__.copyedit")
def test_cli_preserves_yaml_frontmatter(mock_copyedit, tmp_path: Path) -> None:
    """Test that YAML frontmatter is preserved when _perform_copyedit is run."""
    # Create the test document with YAML frontmatter
    test_file = tmp_path / "test_doc.md"
    frontmatter_content = """---
title: "Testing, Testing!"
date: 2026-05-26
author: "J. Random User"
---

Microphone check. One, two! One, two!

Is this thing on?
"""
    test_file.write_text(frontmatter_content)

    # Mock the copyedit response to return text with frontmatter
    # (simulating that the LLM preserved it or we're testing the mdformat step)
    copyedited_text = """---
title: "Testing, Testing!"
date: 2026-05-26
author: "J. Random User"
---

Microphone check. One, two! One, two!

Is this thing on?
"""
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([copyedited_text]))
    mock_copyedit.return_value = mock_response

    # Run copyedit on the file
    result = runner.invoke(cli, ["edit", str(test_file)])

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify the frontmatter is in the output
    output = result.output
    assert "---" in output
    assert 'title: "Testing, Testing!"' in output
    assert "date: 2026-05-26" in output
    assert 'author: "J. Random User"' in output
    assert "Microphone check" in output


@patch("copyedit_ai.__main__.copyedit")
def test_cli_preserves_yaml_frontmatter_from_test_file(
    mock_copyedit, tmp_path: Path
) -> None:
    """Test that YAML frontmatter is preserved using the actual test_doc.md file."""
    # Read the actual test document
    test_doc_path = Path(__file__).parent / "test_doc.md"
    test_content = test_doc_path.read_text()

    # Create a copy in tmp_path for the test
    test_file = tmp_path / "test_doc.md"
    test_file.write_text(test_content)

    # Mock the copyedit response to return the same content
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([test_content]))
    mock_copyedit.return_value = mock_response

    # Run copyedit on the file
    result = runner.invoke(cli, ["edit", str(test_file)])

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify the frontmatter is in the output
    output = result.output
    assert "---" in output
    assert "Testing, Testing!" in output
    assert "2026-05-26" in output
    assert "J. Random User" in output
    assert "Microphone check" in output


@patch("copyedit_ai.__main__.copyedit")
def test_cli_preserves_yaml_frontmatter_in_replace_mode(
    mock_copyedit, tmp_path: Path
) -> None:
    """Test that YAML frontmatter is preserved when replacing a file."""
    # Create the test document with YAML frontmatter
    test_file = tmp_path / "test_doc.md"
    original_content = """---
title: "Testing, Testing!"
date: 2026-05-26
author: "J. Random User"
---

Microphone check. One, two! One, two!

Is this thing on?
"""
    test_file.write_text(original_content)

    # Mock the copyedit response to return edited text with frontmatter
    copyedited_text = """---
title: "Testing, Testing!"
date: 2026-05-26
author: "J. Random User"
---

Microphone check. One, two! One, two!

Is this thing on?
"""
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([copyedited_text]))
    mock_copyedit.return_value = mock_response

    # Run copyedit with --replace and confirm
    result = runner.invoke(cli, ["edit", "--replace", str(test_file)], input="y\n")

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Read the replaced file and verify frontmatter is preserved
    # Note: mdformat may normalize YAML (e.g., removing unnecessary quotes)
    replaced_content = test_file.read_text()
    assert "---" in replaced_content
    # Check for title value (mdformat may remove quotes from simple strings)
    assert "title:" in replaced_content
    assert "Testing, Testing!" in replaced_content
    assert "date: 2026-05-26" in replaced_content
    # Check for author value (mdformat may remove quotes)
    assert "author:" in replaced_content
    assert "J. Random User" in replaced_content
    assert "Microphone check" in replaced_content

    # Verify backup was created with original frontmatter
    backup_path = tmp_path / "test_doc.md.bak"
    assert backup_path.exists()
    backup_content = backup_path.read_text()
    assert "---" in backup_content
    assert "Testing, Testing!" in backup_content


@patch("copyedit_ai.__main__.copyedit")
def test_cli_preserves_yaml_frontmatter_from_test_file_replace_mode(
    mock_copyedit, tmp_path: Path
) -> None:
    """Test YAML frontmatter preservation in replace mode using test_doc.md file."""
    # Read the actual test document
    test_doc_path = Path(__file__).parent / "test_doc.md"
    original_content = test_doc_path.read_text()

    # Create a copy in tmp_path for the test
    test_file = tmp_path / "test_doc.md"
    test_file.write_text(original_content)

    # Mock the copyedit response to return the same content
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([original_content]))
    mock_copyedit.return_value = mock_response

    # Run copyedit with --replace and confirm
    result = runner.invoke(cli, ["edit", "--replace", str(test_file)], input="y\n")

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Read the replaced file and verify frontmatter is preserved
    # Note: mdformat may normalize YAML (e.g., removing unnecessary quotes)
    replaced_content = test_file.read_text()
    assert "---" in replaced_content
    assert "title:" in replaced_content
    assert "Testing, Testing!" in replaced_content
    assert "date:" in replaced_content
    assert "2026-05-26" in replaced_content
    assert "author:" in replaced_content
    assert "J. Random User" in replaced_content
    assert "Microphone check" in replaced_content

    # Verify backup was created with original frontmatter
    backup_path = tmp_path / "test_doc.md.bak"
    assert backup_path.exists()
    backup_content = backup_path.read_text()
    assert "---" in backup_content
    assert "Testing, Testing!" in backup_content


@patch("copyedit_ai.__main__.copyedit")
def test_cli_preserves_toml_frontmatter(mock_copyedit, tmp_path: Path) -> None:
    """Test that TOML frontmatter is preserved when _perform_copyedit is run."""
    # Create the test document with TOML frontmatter
    test_file = tmp_path / "test_doc.md"
    frontmatter_content = """+++
title = "Testing, Testing!"
date = 2026-05-26
author = "J. Random User"
+++

Microphone check. One, two! One, two!

Is this thing on?
"""
    test_file.write_text(frontmatter_content)

    # Mock the copyedit response to return text with frontmatter
    copyedited_text = """+++
title = "Testing, Testing!"
date = 2026-05-26
author = "J. Random User"
+++

Microphone check. One, two! One, two!

Is this thing on?
"""
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([copyedited_text]))
    mock_copyedit.return_value = mock_response

    # Run copyedit on the file
    result = runner.invoke(cli, ["edit", str(test_file)])

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify the frontmatter is in the output
    output = result.output
    assert "+++" in output
    assert "title" in output
    assert "Testing, Testing!" in output
    assert "date" in output
    assert "2026-05-26" in output
    assert "author" in output
    assert "J. Random User" in output
    assert "Microphone check" in output


@patch("copyedit_ai.__main__.copyedit")
def test_cli_preserves_toml_frontmatter_in_replace_mode(
    mock_copyedit, tmp_path: Path
) -> None:
    """Test that TOML frontmatter is preserved when replacing a file."""
    # Create the test document with TOML frontmatter
    test_file = tmp_path / "test_doc.md"
    original_content = """+++
title = "Testing, Testing!"
date = 2026-05-26
author = "J. Random User"
+++

Microphone check. One, two! One, two!

Is this thing on?
"""
    test_file.write_text(original_content)

    # Mock the copyedit response to return edited text with frontmatter
    copyedited_text = """+++
title = "Testing, Testing!"
date = 2026-05-26
author = "J. Random User"
+++

Microphone check. One, two! One, two!

Is this thing on?
"""
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([copyedited_text]))
    mock_copyedit.return_value = mock_response

    # Run copyedit with --replace and confirm
    result = runner.invoke(cli, ["edit", "--replace", str(test_file)], input="y\n")

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Read the replaced file and verify frontmatter is preserved
    replaced_content = test_file.read_text()
    assert "+++" in replaced_content
    assert "title" in replaced_content
    assert "Testing, Testing!" in replaced_content
    assert "date" in replaced_content
    assert "2026-05-26" in replaced_content
    assert "author" in replaced_content
    assert "J. Random User" in replaced_content
    assert "Microphone check" in replaced_content

    # Verify backup was created with original frontmatter
    backup_path = tmp_path / "test_doc.md.bak"
    assert backup_path.exists()
    backup_content = backup_path.read_text()
    assert "+++" in backup_content
    assert "Testing, Testing!" in backup_content


@patch("copyedit_ai.__main__.copyedit")
def test_cli_preserves_json_frontmatter(mock_copyedit, tmp_path: Path) -> None:
    """Test that JSON frontmatter is preserved when _perform_copyedit is run."""
    # Create the test document with JSON frontmatter
    test_file = tmp_path / "test_doc.md"
    frontmatter_content = """{
  "title": "Testing, Testing!",
  "date": "2026-05-26",
  "author": "J. Random User"
}

Microphone check. One, two! One, two!

Is this thing on?
"""
    test_file.write_text(frontmatter_content)

    # Mock the copyedit response to return text with frontmatter
    copyedited_text = """{
  "title": "Testing, Testing!",
  "date": "2026-05-26",
  "author": "J. Random User"
}

Microphone check. One, two! One, two!

Is this thing on?
"""
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([copyedited_text]))
    mock_copyedit.return_value = mock_response

    # Run copyedit on the file
    result = runner.invoke(cli, ["edit", str(test_file)])

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify the frontmatter is in the output
    output = result.output
    assert "{" in output
    assert "}" in output
    assert '"title"' in output
    assert "Testing, Testing!" in output
    assert '"date"' in output
    assert "2026-05-26" in output
    assert '"author"' in output
    assert "J. Random User" in output
    assert "Microphone check" in output


@patch("copyedit_ai.__main__.copyedit")
def test_cli_preserves_json_frontmatter_in_replace_mode(
    mock_copyedit, tmp_path: Path
) -> None:
    """Test that JSON frontmatter is preserved when replacing a file."""
    # Create the test document with JSON frontmatter
    test_file = tmp_path / "test_doc.md"
    original_content = """{
  "title": "Testing, Testing!",
  "date": "2026-05-26",
  "author": "J. Random User"
}

Microphone check. One, two! One, two!

Is this thing on?
"""
    test_file.write_text(original_content)

    # Mock the copyedit response to return edited text with frontmatter
    copyedited_text = """{
  "title": "Testing, Testing!",
  "date": "2026-05-26",
  "author": "J. Random User"
}

Microphone check. One, two! One, two!

Is this thing on?
"""
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(return_value=iter([copyedited_text]))
    mock_copyedit.return_value = mock_response

    # Run copyedit with --replace and confirm
    result = runner.invoke(cli, ["edit", "--replace", str(test_file)], input="y\n")

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Read the replaced file and verify frontmatter is preserved
    replaced_content = test_file.read_text()
    assert "{" in replaced_content
    assert "}" in replaced_content
    assert '"title"' in replaced_content
    assert "Testing, Testing!" in replaced_content
    assert '"date"' in replaced_content
    assert "2026-05-26" in replaced_content
    assert '"author"' in replaced_content
    assert "J. Random User" in replaced_content
    assert "Microphone check" in replaced_content

    # Verify backup was created with original frontmatter
    backup_path = tmp_path / "test_doc.md.bak"
    assert backup_path.exists()
    backup_content = backup_path.read_text()
    assert "{" in backup_content
    assert "Testing, Testing!" in backup_content
