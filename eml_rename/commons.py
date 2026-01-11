from configparser import ConfigParser
from chardet import detect
from colorama import Fore, Style
from datetime import datetime
from email.parser import HeaderParser
from email.utils import parsedate_to_datetime, parseaddr
from email.header import decode_header
from gettext import translation
from importlib.resources import files
from os import rename, environ
from pathlib import Path
from pydicts import colors, casts

from sys import exit
from zoneinfo import ZoneInfo

__version__ = '0.3.9999'
__versiondatetime__ = datetime(2026, 1, 11, 0, 0)
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
    return datetime.now().astimezone().tzname()
