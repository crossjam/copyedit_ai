"""test copyedit_ai CLI: copyedit_ai."""

import importlib
from pathlib import Path
from unittest.mock import MagicMock, create_autospec, patch

import llm
import yaml
from typer.testing import CliRunner

main_module_name = "copyedit_ai.__main__"
main_module = importlib.import_module(main_module_name)
runner = CliRunner()
# Use the Typer app for testing, not the wrapped cli function
cli = main_module.app


def test_cli_help() -> None:
    """Test the main command-line interface help flag."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0


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


@patch("copyedit_ai.self_subcommand.is_initialized")
@patch("copyedit_ai.self_subcommand.set_llm_user_path")
@patch("copyedit_ai.self_subcommand.llm.user_dir")
def test_cli_self_install_template(
    mock_user_dir,
    _mock_set_llm_user_path,  # noqa: PT019
    mock_is_initialized,
    tmp_path: Path,
) -> None:
    """Test the self install-template subcommand."""
    # Mock initialization check
    mock_is_initialized.return_value = True

    # Create a temporary llm user directory
    mock_user_dir.return_value = str(tmp_path)
    templates_dir = tmp_path / "templates"

    result = runner.invoke(cli, ["self", "install-template"])

    assert result.exit_code == 0
    assert "Installed template 'copyedit'" in result.output

    # Verify the template file was created
    template_path = templates_dir / "copyedit.yaml"
    assert template_path.exists()

    # Verify the template content
    with template_path.open() as f:
        template_data = yaml.safe_load(f)

    assert "system" in template_data
    assert "copyeditor" in template_data["system"]
    assert "prompt" in template_data
    assert "$input" in template_data["prompt"]


@patch("copyedit_ai.self_subcommand.is_initialized")
@patch("copyedit_ai.self_subcommand.set_llm_user_path")
@patch("copyedit_ai.self_subcommand.llm.user_dir")
def test_cli_self_install_template_custom_name(
    mock_user_dir,
    _mock_set_llm_user_path,  # noqa: PT019
    mock_is_initialized,
    tmp_path: Path,
) -> None:
    """Test the self install-template subcommand with custom name."""
    # Mock initialization check
    mock_is_initialized.return_value = True

    # Create a temporary llm user directory
    mock_user_dir.return_value = str(tmp_path)
    templates_dir = tmp_path / "templates"

    result = runner.invoke(cli, ["self", "install-template", "my-template"])

    assert result.exit_code == 0
    assert "Installed template 'my-template'" in result.output

    # Verify the template file was created
    template_path = templates_dir / "my-template.yaml"
    assert template_path.exists()


@patch("copyedit_ai.self_subcommand.is_initialized")
@patch("copyedit_ai.self_subcommand.set_llm_user_path")
@patch("copyedit_ai.self_subcommand.llm.user_dir")
def test_cli_self_install_template_already_exists(
    mock_user_dir,
    _mock_set_llm_user_path,  # noqa: PT019
    mock_is_initialized,
    tmp_path: Path,
) -> None:
    """Test the self install-template subcommand when template already exists."""
    # Mock initialization check
    mock_is_initialized.return_value = True

    # Create a temporary llm user directory
    mock_user_dir.return_value = str(tmp_path)
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir(parents=True)
    template_path = templates_dir / "copyedit.yaml"
    template_path.write_text("existing: content")

    result = runner.invoke(cli, ["self", "install-template"])

    assert result.exit_code == 1
    assert "already exists" in result.output


@patch("copyedit_ai.self_subcommand.is_initialized")
@patch("copyedit_ai.self_subcommand.set_llm_user_path")
@patch("copyedit_ai.self_subcommand.llm.user_dir")
def test_cli_self_install_template_force(
    mock_user_dir,
    _mock_set_llm_user_path,  # noqa: PT019
    mock_is_initialized,
    tmp_path: Path,
) -> None:
    """Test the self install-template subcommand with --force option."""
    # Mock initialization check
    mock_is_initialized.return_value = True

    # Create a temporary llm user directory
    mock_user_dir.return_value = str(tmp_path)
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir(parents=True)
    template_path = templates_dir / "copyedit.yaml"
    template_path.write_text("existing: content")

    result = runner.invoke(cli, ["self", "install-template", "--force"])

    assert result.exit_code == 0
    assert "Installed template 'copyedit'" in result.output

    # Verify the template was overwritten
    with template_path.open() as f:
        template_data = yaml.safe_load(f)

    assert "system" in template_data
    assert "existing" not in template_data


@patch("copyedit_ai.self_subcommand.is_initialized")
def test_cli_self_install_template_not_initialized(mock_is_initialized) -> None:
    """Test the self install-template subcommand when not initialized."""
    # Mock initialization check to return False
    mock_is_initialized.return_value = False

    result = runner.invoke(cli, ["self", "install-template"])

    assert result.exit_code == 1
    assert "Configuration not initialized" in result.output
    assert "copyedit_ai self init" in result.output


@patch("copyedit_ai.self_subcommand.is_initialized")
@patch("copyedit_ai.self_subcommand.set_llm_user_path")
@patch("copyedit_ai.self_subcommand.llm.set_alias")
def test_cli_self_install_alias(
    mock_set_alias,
    _mock_set_llm_user_path,  # noqa: PT019
    mock_is_initialized,
) -> None:
    """Test the self install-alias subcommand."""
    # Mock initialization check
    mock_is_initialized.return_value = True

    result = runner.invoke(cli, ["self", "install-alias", "fast", "gpt-4o-mini"])

    assert result.exit_code == 0
    assert "Installed alias 'fast' -> 'gpt-4o-mini'" in result.output
    mock_set_alias.assert_called_once_with("fast", "gpt-4o-mini")


@patch("copyedit_ai.self_subcommand.is_initialized")
@patch("copyedit_ai.self_subcommand.set_llm_user_path")
@patch("copyedit_ai.self_subcommand.llm.set_alias")
def test_cli_self_install_alias_error(
    mock_set_alias,
    _mock_set_llm_user_path,  # noqa: PT019
    mock_is_initialized,
) -> None:
    """Test the self install-alias subcommand with error."""
    # Mock initialization check
    mock_is_initialized.return_value = True

    mock_set_alias.side_effect = Exception("Test error")

    result = runner.invoke(cli, ["self", "install-alias", "fast", "gpt-4o-mini"])

    assert result.exit_code == 1
    assert "Error:" in result.output


@patch("copyedit_ai.self_subcommand.is_initialized")
def test_cli_self_install_alias_not_initialized(mock_is_initialized) -> None:
    """Test the self install-alias subcommand when not initialized."""
    # Mock initialization check to return False
    mock_is_initialized.return_value = False

    result = runner.invoke(cli, ["self", "install-alias", "fast", "gpt-4o-mini"])

    assert result.exit_code == 1
    assert "Configuration not initialized" in result.output
    assert "copyedit_ai self init" in result.output


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
    expected_commands = ["templates", "keys", "models", "schemas", "aliases"]
    for cmd_name in expected_commands:
        assert (
            cmd_name in self_command.commands
        ), f"Expected {cmd_name} in self commands"


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


@patch("copyedit_ai.__main__.copyedit")
def test_cli_replace_with_confirmation(mock_copyedit, tmp_path: Path) -> None:
    """Test the --replace option with user confirmation."""
    # Create a temporary test file
    test_file = tmp_path / "test.txt"
    original_content = "Test text with erors."
    test_file.write_text(original_content)

    # Mock the copyedit response
    mock_response = MagicMock()
    mock_response.__iter__ = MagicMock(
        return_value=iter(["Test text with errors."])
    )
    mock_copyedit.return_value = mock_response

    # Simulate user confirming the replacement
    result = runner.invoke(cli, ["edit", str(test_file), "--replace"], input="y\n")

    assert result.exit_code == 0
    mock_copyedit.assert_called_once()

    # Verify the file was replaced
    assert test_file.read_text() == "Test text with errors."

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
    mock_response.__iter__ = MagicMock(
        return_value=iter(["Test text with errors."])
    )
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
    mock_response.__iter__ = MagicMock(
        return_value=iter(["Test text with errors."])
    )
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

    # Verify the file was replaced
    assert test_file.read_text() == "Test text with errors."

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

    # Verify log file was created
    assert log_file_path.exists()
    log_content = log_file_path.read_text()
    assert "Logging to file:" in log_content or "debug=" in log_content
