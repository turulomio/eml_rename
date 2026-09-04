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
- **Gemini AI Subject Summarization (`--ai`)**: Summarizes email content into concise subjects using Google Gemini models, optimized for low token consumption.
- **Model Selection & Persistence**: List available models (`--ai_models`) and save your preferred model in configuration (`--ai_model MODEL`).
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

### 6. AI-Powered Subject Summarization
Use Gemini AI to summarize the email content into a concise subject:
```bash
eml_rename --ai --save
```

---

## AI Configuration (Optional)

To use the AI subject generation feature (`--ai`), a Google Gemini API Key is required.

### 1. Set API Key

#### Option A: Environment Variable
```bash
export GOOGLE_API_KEY='your_api_key_here'
```

#### Option B: Configuration File
Create a file in `~/.config/eml-rename/config.ini`:
```ini
[auth]
GOOGLE_API_KEY = your_api_key_here

[ai]
model_name = gemini-2.5-flash
delay = 2
```

### 2. Manage AI Models

- **List available models**:
  ```bash
  eml_rename --ai_models
  ```
- **Change and save your preferred model**:
  ```bash
  eml_rename --ai_model gemini-2.5-flash
  ```
  *(This automatically saves the model to your `config.ini` so you don't need to specify it every time).*

- **Automatic Fallback**:
  If a configured model becomes unavailable or deprecated, `eml_rename` warns you and falls back automatically to `gemini-2.5-flash`.

---

## Command-Line Options

<img src="https://raw.githubusercontent.com/turulomio/eml_rename/master/doc/help.gif?raw=true" width="100%"></img>

| Option | Description |
|---|---|
| `path` | Optional path(s) to `.eml` file(s) or directory. Defaults to current directory. |
| `--save` | Actually rename files (default is simulation mode). |
| `--force` | Force subject update even if `YYYYMMDD HHMM [From]` format is already detected. |
| `--length LENGTH` | Maximum filename length (default: 140). |
| `--ai` | Use Google Gemini AI to summarize email content as subject. |
| `--ai_delay AI_DELAY` | Delay in seconds between AI requests (default: 2). |
| `--ai_models`, `--ai-models` | List available Gemini models for content generation and exit. |
| `--ai_model MODEL`, `--ai-model MODEL` | Specify Gemini model to use and persist it in configuration. |
| `--version` | Show program's version number and exit. |
| `-h`, `--help` | Show help message and exit. |
