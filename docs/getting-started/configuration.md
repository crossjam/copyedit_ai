# Configuration

Copyedit with AI uses Pydantic Settings for configuration management, which allows you to configure the application using environment variables, configuration files, or both.

## Environment Variables

You can configure copyedit_ai using environment variables:

```bash
export COPYEDIT_AI_SETTING_NAME=value
copyedit_ai [command]
```

## Configuration File

You can also use a configuration file. Create a `.env` file in your project directory:

```bash
# .env
COPYEDIT_AI_SETTING_NAME=value
```

## Available Settings

The following settings are available:

### Logging Settings

- `COPYEDIT_AI_LOG_LEVEL`: Set the logging level (default: INFO)
- `COPYEDIT_AI_LOG_FILE`: Path to log file (default: copyedit_ai.log)
### Application Settings

Add your application-specific settings here.

## Priority Order

Settings are loaded in the following priority order (highest to lowest):

1. Environment variables
2. Configuration file (`.env`)
3. Default values

## Example

```bash
# Set log level to DEBUG
export COPYEDIT_AI_LOG_LEVEL=DEBUG

# Run the CLI
copyedit_ai [command]
```

## Installing Model Providers

copyedit_ai supports multiple LLM providers through llm's plugin ecosystem. Plugins are installed in your Python environment and configured within copyedit_ai's isolated configuration.

### Available Plugins

Popular llm plugins include:
- `llm-anthropic` - Claude models (Claude Sonnet, Opus, Haiku)
- `llm-ollama` - Local models via Ollama
- `llm-gemini` - Google Gemini models
- `llm-mistral` - Mistral AI models
- `llm-openrouter` - Access to multiple providers via OpenRouter

See the [llm plugins directory](https://llm.datasette.io/en/stable/plugins/directory.html) for a complete list.

### Installation

Install a plugin using the `install` command:

```bash
copyedit_ai self install llm-anthropic
```

This will:
1. Download the plugin from PyPI
2. Install it in copyedit_ai's Python environment
3. Make new models available to copyedit_ai

### Configuration

After installing a plugin, you typically need to:

1. **Set up API keys** (for cloud providers):
   ```bash
   copyedit_ai self keys set anthropic
   ```

2. **List available models**:
   ```bash
   copyedit_ai self models list
   ```

3. **Create aliases** for convenience:
   ```bash
   copyedit_ai self aliases set sonnet claude-sonnet-4.5
   ```

4. **Use the new model**:
   ```bash
   copyedit_ai --model sonnet document.txt
   ```

### Managing Plugins

List installed plugins:
```bash
copyedit_ai self plugins list
```

Uninstall a plugin:
```bash
copyedit_ai self uninstall llm-anthropic
```

Upgrade a plugin:
```bash
copyedit_ai self install --upgrade llm-anthropic
```
