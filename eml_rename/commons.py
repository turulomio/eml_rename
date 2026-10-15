"""Common utilities and configuration module for eml_rename.

Provides helper functions for configuration management, Ollama AI URL retrieval,
system signal handling, and timezone detection.
"""

from configparser import ConfigParser
from datetime import datetime
from gettext import translation
from importlib.resources import files
from os import environ
from pathlib import Path
from sys import exit
from time import tzset, tzname

__version__ = '1.3.0'
__versiondatetime__ = datetime(2026, 10, 15, 13, 30)
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

DEFAULT_AI_URL = "http://localhost:11434"

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

def get_ai_url() -> str:
    """Retrieve the Ollama AI URL with fallback precedence.

    Priority order:
    1. OLLAMA_HOST environment variable.
    2. [ai] section 'url' in ~/.config/eml-rename/config.ini.
    3. DEFAULT_AI_URL (http://localhost:11434).

    Returns:
        str: Ollama server base URL.
    """
    host = environ.get("OLLAMA_HOST")
    if host and host.strip():
        host = host.strip()
        if not host.startswith("http://") and not host.startswith("https://"):
            host = f"http://{host}"
        return host

    config = get_config()
    if config.has_section("ai"):
        url = config.get("ai", "url", fallback=None)
        if url and url.strip():
            return url.strip()
    return DEFAULT_AI_URL

def save_ai_url(url: str) -> None:
    """Persist Ollama AI server URL into config.ini.

    Creates required parent directories and the [ai] section if missing.

    Args:
        url (str): Ollama server URL to save.
    """
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = get_config()
    if not config.has_section("ai"):
        config.add_section("ai")
    config.set("ai", "url", url.strip())
    with open(config_path, "w") as f:
        config.write(f)

def get_system_timezone_name() -> str:
    """Retrieve the host operating system's timezone name.

    Calls tzset() to initialize timezone variables.

    Returns:
        str: Local timezone name or identifier (e.g. 'CET', 'Europe/Madrid').
    """
    tzset()
    return tzname[0]