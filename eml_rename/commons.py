"""Common utilities and configuration module for eml_rename.

Provides helper functions for configuration management, API key retrieval,
Google Gemini AI models discovery, system signal handling, and timezone detection.
"""

from configparser import ConfigParser
from datetime import datetime
from gettext import translation
from importlib.resources import files
from os import environ
from pathlib import Path
from sys import exit
from time import tzset, tzname

__version__ = '1.2.0'
__versiondatetime__ = datetime(2026, 9, 4, 11, 30)
__versiondate__ = __versiondatetime__.date()

try:
    t = translation('eml_rename', files("eml_rename") / "locale")
    _ = t.gettext
except:
    _ = str
    
def signal_handler(signal, frame):
    """Signal handler for SIGINT (Ctrl+C).

    Interrupts execution cleanly and prints an informative message.

    Args:
        signal: Signal number received.
        frame: Current stack frame object.
    """
    print(_("You pressed 'Ctrl+C', exiting..."))
    exit(0)

def argparse_epilog() -> str:
    """Generate epilog text for the CLI argument parser.

    Returns:
        str: Formatted authorship message with current version year.
    """
    return _("Developed by Mariano Muñoz 2022-{}").format(__versiondate__.year)

DEFAULT_AI_MODEL = "gemini-2.5-flash"

def get_config_path() -> Path:
    """Get the path to the application's configuration file.

    Returns:
        Path: Path to ~/.config/eml-rename/config.ini.
    """
    return Path.home() / ".config" / "eml-rename" / "config.ini"

def get_config() -> ConfigParser:
    """Load and return the ConfigParser instance from the config file if it exists.

    Returns:
        ConfigParser: Parsed configuration object or empty instance if file does not exist.
    """
    config = ConfigParser()
    config_path = get_config_path()
    if config_path.exists():
        config.read(config_path)
    return config

def get_google_api_key() -> str | None:
    """Retrieve Google API Key with fallback precedence.

    Priority order:
    1. GOOGLE_API_KEY environment variable.
    2. [auth] section in ~/.config/eml-rename/config.ini.

    Returns:
        str | None: The API key if found, or None otherwise.
    """
    # 1. Environment variable priority
    api_key = environ.get("GOOGLE_API_KEY")
    if api_key:
        return api_key

    # 2. Look up ~/.config/eml-rename/config.ini
    config = get_config()
    if config.has_section("auth"):
        return config.get("auth", "GOOGLE_API_KEY", fallback=None)
    return None

def get_ai_model() -> str:
    """Get the configured AI model name from config.ini or return the default.

    Returns:
        str: Configured AI model name (defaults to DEFAULT_AI_MODEL).
    """
    config = get_config()
    if config.has_section("ai"):
        model = config.get("ai", "model_name", fallback=None)
        if model and model.strip():
            return model.strip()
    return DEFAULT_AI_MODEL

def save_ai_model(model_name: str) -> None:
    """Persist selected AI model name into config.ini.

    Creates required parent directories and the [ai] section if missing.

    Args:
        model_name (str): Model name to save.
    """
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = get_config()
    if not config.has_section("ai"):
        config.add_section("ai")
    config.set("ai", "model_name", model_name.strip())
    with open(config_path, "w") as f:
        config.write(f)

def get_available_ai_models() -> list[str]:
    """Retrieve the list of Google Gemini models available for content generation.

    Requires a configured API key and the 'google-genai' package.
    Filters models that support the 'generateContent' action.

    Returns:
        list[str]: Clean model identifiers (without 'models/' prefix).

    Raises:
        Exception: If GOOGLE_API_KEY is not defined or google-genai is not installed.
    """
    api_key = get_google_api_key()
    if not api_key:
        raise Exception(_("GOOGLE_API_KEY not found. Set it in environment or in ~/.config/eml-rename/config.ini"))
    try:
        from google import genai
    except ImportError:
        raise Exception(_("The 'google-genai' package is not installed. Please run 'pip install google-genai' or 'poetry install'."))

    client = genai.Client(api_key=api_key)
    models = []
    for m in client.models.list():
        name = m.name.removeprefix("models/")
        supported_actions = getattr(m, "supported_actions", None) or []
        if not supported_actions or "generateContent" in supported_actions:
            models.append(name)
    return models

def get_system_timezone_name() -> str:
    """Retrieve the host operating system's timezone name.

    Calls tzset() to initialize timezone variables.

    Returns:
        str: Local timezone name or identifier (e.g. 'CET', 'Europe/Madrid').
    """
    tzset()
    return tzname[0]