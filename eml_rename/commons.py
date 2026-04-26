from configparser import ConfigParser
from datetime import datetime
from gettext import translation
from importlib.resources import files
from os import environ
from pathlib import Path

from sys import exit

__version__ = '1.0.1'
__versiondatetime__ = datetime(2026, 1, 11, 21, 57)
__versiondate__ = __versiondatetime__.date()

try:
    t = translation('eml_rename', files("eml_rename") / "locale")
    _ = t.gettext
except:
    _ = str
    
def signal_handler( signal, frame):
        print(_("You pressed 'Ctrl+C', exiting..."))
        exit(0)

## Function used in argparse_epilog
## @return String
def argparse_epilog():
    return _("Developed by Mariano Muñoz 2022-{}").format(__versiondate__.year)

def get_google_api_key():
    """Busca la API Key en el entorno o en el archivo de configuración."""
    # 1. Prioridad a la variable de entorno
    api_key = environ.get("GOOGLE_API_KEY")
    if api_key:
        return api_key

    # 2. Buscar en ~/.config/eml-rename/config.ini
    config_path = Path.home() / ".config" / "eml-rename" / "config.ini"
    if config_path.exists():
        config = ConfigParser()
        config.read(config_path)
        return config.get("auth", "GOOGLE_API_KEY", fallback=None)
    return None

def get_system_localzone_name():
    tz= datetime.now().astimezone().tzname()
    if tz in ["CEST", "CET"]: #Cest wasn't recognized by ZoneInfo
        return "UTC"
    return tz
