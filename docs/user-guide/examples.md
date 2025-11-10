# Examples

This page provides practical examples of using Copyedit with AI.

## Basic Usage

### Getting Help

```bash
# Show main help
copyedit_ai --help

# Show help for a specific command
copyedit_ai [command] --help
```

### Check Version

```bash
copyedit_ai --version
```

## Advanced Usage

### Using with Different Log Levels

```bash
# Run with debug logging
copyedit_ai --log-level DEBUG [command]

# Run with minimal logging
copyedit_ai --log-level ERROR [command]
```

### Using with Configuration

```bash
# Set configuration via environment variables
export COPYEDIT_AI_SETTING_NAME=value
copyedit_ai [command]

# Or create a .env file
echo "COPYEDIT_AI_SETTING_NAME=value" > .env
copyedit_ai [command]
```
## Common Workflows

### Example Workflow 1

```bash
# Step 1: Initialize
copyedit_ai init

# Step 2: Process
copyedit_ai process --input file.txt

# Step 3: Output
copyedit_ai output --format json
```

### Example Workflow 2

```bash
# One-liner example
copyedit_ai process --input file.txt --output result.txt --verbose
```

## Error Handling Examples

### Common Errors

```bash
# File not found
copyedit_ai process --input nonexistent.txt
# Error: Input file 'nonexistent.txt' not found

# Invalid option
copyedit_ai --invalid-option
# Error: No such option: --invalid-option
```

### Debugging

```bash
# Run with debug logging to troubleshoot
copyedit_ai --log-level DEBUG process --input file.txt
```

## Integration Examples

### Use in Scripts

```bash
#!/bin/bash
set -e

# Check if copyedit_ai is installed
if ! command -v copyedit_ai &> /dev/null; then
    echo "copyedit_ai is not installed"
    exit 1
fi

# Run the command
copyedit_ai process --input "$1" --output "$2"
echo "Processing complete"
```

### Use with Make

```makefile
.PHONY: process
process:
	copyedit_ai process --input input.txt --output output.txt

.PHONY: clean
clean:
	rm -f output.txt copyedit_ai.log
```

## Performance Tips

- Use appropriate log levels in production
- Process files in batches when possible
- Use configuration files for repeated settings

## Next Steps

- Learn more about the [API Reference](../reference/)
- Check out the [Contributing Guide](../contributing.md)
- Visit the [GitHub repository](https://github.com/crossjam/copyedit_ai)