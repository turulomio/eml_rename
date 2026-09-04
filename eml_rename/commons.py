from configparser import ConfigParser
from datetime import datetime
from gettext import translation
from importlib.resources import files
from os import environ
from pathlib import Path
from sys import exit
from time import tzset, tzname

__version__ = '1.1.0'
__versiondatetime__ = datetime(2026, 4, 26, 20, 41)
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

DEFAULT_AI_MODEL = "gemini-2.5-flash"

def get_config_path() -> Path:
    """Devuelve la ruta al archivo de configuración de la aplicación."""
    return Path.home() / ".config" / "eml-rename" / "config.ini"

def get_config() -> ConfigParser:
    """Carga y devuelve el ConfigParser del archivo de configuración si existe."""
    config = ConfigParser()
    config_path = get_config_path()
    if config_path.exists():
        config.read(config_path)
    return config

def get_google_api_key():
    """Busca la API Key en el entorno o en el archivo de configuración."""
    # 1. Prioridad a la variable de entorno
    api_key = environ.get("GOOGLE_API_KEY")
    if api_key:
        return api_key

    # 2. Buscar en ~/.config/eml-rename/config.ini
    config = get_config()
    if config.has_section("auth"):
        return config.get("auth", "GOOGLE_API_KEY", fallback=None)
    return None

def get_ai_model() -> str:
    """Obtiene el modelo de IA configurado en config.ini o el valor por defecto."""
    config = get_config()
    if config.has_section("ai"):
        model = config.get("ai", "model_name", fallback=None)
        if model and model.strip():
            return model.strip()
    return DEFAULT_AI_MODEL

def save_ai_model(model_name: str) -> None:
    """Guarda el modelo de IA seleccionado en config.ini."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = get_config()
    if not config.has_section("ai"):
        config.add_section("ai")
    config.set("ai", "model_name", model_name.strip())
    with open(config_path, "w") as f:
        config.write(f)

def get_available_ai_models() -> list[str]:
    """Obtiene la lista de modelos de Google Gemini disponibles para generación de contenido."""
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

def get_system_timezone_name():
    """
        Obtiene el nombre del timezone del systema
    """
    tzset()
    return tzname[0]