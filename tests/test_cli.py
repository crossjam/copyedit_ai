"""test copyedit_ai CLI: copyedit_ai."""

import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch

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
    mock_response = MagicMock()
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


@patch("copyedit_ai.self_subcommand.llm.user_dir")
def test_cli_self_install_template(mock_user_dir, tmp_path: Path) -> None:
    """Test the self install-template subcommand."""
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


@patch("copyedit_ai.self_subcommand.llm.user_dir")
def test_cli_self_install_template_custom_name(mock_user_dir, tmp_path: Path) -> None:
    """Test the self install-template subcommand with custom name."""
    # Create a temporary llm user directory
    mock_user_dir.return_value = str(tmp_path)
    templates_dir = tmp_path / "templates"

    result = runner.invoke(cli, ["self", "install-template", "my-template"])

    assert result.exit_code == 0
    assert "Installed template 'my-template'" in result.output

    # Verify the template file was created
    template_path = templates_dir / "my-template.yaml"
    assert template_path.exists()


@patch("copyedit_ai.self_subcommand.llm.user_dir")
def test_cli_self_install_template_already_exists(
    mock_user_dir, tmp_path: Path
) -> None:
    """Test the self install-template subcommand when template already exists."""
    # Create a temporary llm user directory
    mock_user_dir.return_value = str(tmp_path)
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir(parents=True)
    template_path = templates_dir / "copyedit.yaml"
    template_path.write_text("existing: content")

    result = runner.invoke(cli, ["self", "install-template"])

    assert result.exit_code == 1
    assert "already exists" in result.output


@patch("copyedit_ai.self_subcommand.llm.user_dir")
def test_cli_self_install_template_force(mock_user_dir, tmp_path: Path) -> None:
    """Test the self install-template subcommand with --force option."""
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


@patch("copyedit_ai.self_subcommand.llm.set_alias")
def test_cli_self_install_alias(mock_set_alias) -> None:
    """Test the self install-alias subcommand."""
    result = runner.invoke(cli, ["self", "install-alias", "fast", "gpt-4o-mini"])

    assert result.exit_code == 0
    assert "Installed alias 'fast' -> 'gpt-4o-mini'" in result.output
    mock_set_alias.assert_called_once_with("fast", "gpt-4o-mini")


@patch("copyedit_ai.self_subcommand.llm.set_alias")
def test_cli_self_install_alias_error(mock_set_alias) -> None:
    """Test the self install-alias subcommand with error."""
    mock_set_alias.side_effect = Exception("Test error")

    result = runner.invoke(cli, ["self", "install-alias", "fast", "gpt-4o-mini"])

    assert result.exit_code == 1
    assert "Error:" in result.output
