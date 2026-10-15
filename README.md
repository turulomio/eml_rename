# eml_rename project

[![Tests](https://github.com/turulomio/eml_rename/actions/workflows/tests.yml/badge.svg)](https://github.com/turulomio/eml_rename/actions/workflows/tests.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/eml-rename)](https://pypi.org/project/eml-rename/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/eml_rename)](https://pypi.org/project/eml_rename/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Script that renames `.eml` email files in a directory or by specific path using email metadata (Date, From, Subject).

## Idea

I needed this tool to classify and order my email files at work.
I took this idea from an article by Armand Niculescu (August 20, 2014) at https://www.media-division.com/using-python-to-batch-rename-email-files/ , so thanks and I hope you like this code.

## Installation

```bash
pip install eml_rename 
```

## Features

<img src="https://raw.githubusercontent.com/turulomio/eml_rename/master/doc/command.gif?raw=true" width="100%"></img>

- **Automatic Metadata Renaming**: Extracts date, time, sender, and subject to generate filenames in the format: `YYYYMMDD HHMM [From] Subject.eml`.
- **Target Single File, Directory, or Current Working Directory**: By default processes all `*.eml` files in the current working directory, or you can pass an optional path to a specific file or directory.
- **Directory Preservation**: Renamed files stay in their original folder, even when targeting files in subdirectories or absolute paths.
- **Safe Simulation by Default**: Previews changes without renaming unless `--save` is specified.
- **Protects Manual Edits**: If a file already has the `YYYYMMDD HHMM [From]` format, the script won't overwrite manual edits to the subject unless `--force` is used.
- **Ollama AI Subject Summarization (`--ai MODEL`)**: Summarizes email content into concise subjects using local Ollama models (e.g., `llama3`, `mistral`, etc.).
- **Configurable Ollama Server (`--ai_url`)**: Connect to your Ollama instance (defaults to `http://localhost:11434`).
- **Concurrent Processing**: Uses multi-threading to process large archives fast.

## Usage & Examples

### 1. Simulation (Default)
Run in the current directory to preview changes without modifying files:
```bash
eml_rename
```

### 2. Rename All Emails in Current Directory
Use `--save` to apply the renames:
```bash
eml_rename --save
```

### 3. Rename a Specific File or Directory
Pass a path to a single `.eml` file or a directory:
```bash
# Specific file
eml_rename path/to/email.eml --save

# Specific directory
eml_rename /path/to/archive/ --save
```

### 4. Force Overwriting Already Renamed Files
```bash
eml_rename --force --save
```

### 5. Custom Maximum Length
Set a custom length for generated filenames (default is 140 characters):
```bash
eml_rename --length 160 --save
```

### 6. AI-Powered Subject Summarization (Ollama)
Use Ollama AI to summarize the email content into a concise subject by specifying the model:
```bash
eml_rename --ai llama3 --save
```

---

## AI Configuration (Optional)

To use the AI subject generation feature, an [Ollama](https://ollama.com/) instance is required. By default, `eml_rename` connects to `http://localhost:11434`.

### 1. Custom Ollama URL

#### Option A: Command-Line Argument
```bash
eml_rename --ai llama3 --ai_url http://192.168.1.50:11434 --save
```

#### Option B: Environment Variable
```bash
export OLLAMA_HOST='http://192.168.1.50:11434'
```

#### Option C: Configuration File
Create or edit `~/.config/eml-rename/config.ini`:
```ini
[ai]
url = http://192.168.1.50:11434
```

---

## Command-Line Options

<img src="https://raw.githubusercontent.com/turulomio/eml_rename/master/doc/help.gif?raw=true" width="100%"></img>

| Option | Description |
|---|---|
| `path` | Optional path(s) to `.eml` file(s) or directory. Defaults to current directory. |
| `--save` | Actually rename files (default is simulation mode). |
| `--force` | Force subject update even if `YYYYMMDD HHMM [From]` format is already detected. |
| `--length LENGTH` | Maximum filename length (default: 140). |
| `--ai MODEL` | Use Ollama AI with specified model to summarize email content as subject (default: None / no AI). |
| `--ai_url URL`, `--ai-url URL` | Ollama server URL (default: `http://localhost:11434`). |
| `--version` | Show program's version number and exit. |
| `-h`, `--help` | Show help message and exit. |
