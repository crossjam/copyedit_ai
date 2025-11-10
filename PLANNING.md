Our goal is to create a modern Python package that implements a CLI
tool to copyedit plain text files or markdown files. The copyediting
is implemented by prompting AI APIs.

## copyedit_ai planning description

In @scripts/copyedit.sh is a bash script that was created with this
prompt to Claude.

> Use the Python llm cli package from Simon Willison to  create a bash
> script that reads from standard input or a file and then prompts a
> model to copyedit the text from stdin. The prompt should be
> something like  
> 
> "Review this text for punctuation, grammatical, spelling, and
> logical errors. Try hard to keep the style and tone but make
> corrections as needed. Summarize any corrections you made at the
> bottom the text in bullet point format". 

Our goal is convert the bash script in copyedit.sh into Python plugged
into the framework of this repository.

The current repository implements providesa set of opinionated
preferences for implementing a CLI in Python. It was created from a
Python cookiecutter template at:
https://github.com/JnyJny/python-package-cookiecutter

The template includes the following features

* Zero Configuration CI/CD - Complete GitHub Actions workflows for testing, building, and publishing to PyPI
* CLI Ready - Typer CLI with help and autocompletion
* Fast Dependencies - uv for lightning-fast package management
* Quality Tools - Pre-configured ruff, ty, pytest, and coverage reporting
* Documentation - MkDocs with auto-deployment to GitHub Pages
* Flexible - Optional Pydantic settings, multiple build backends, cross-platform testing

Our first step is to generate a plan for appropriately converting
copyedit.sh into Python code. Analyze the code in this repository, the
code in the script, and any documentation you need for the llm
module. That documentation is at https://llm.datasette.io/.

