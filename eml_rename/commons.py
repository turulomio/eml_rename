"""Módulo de utilidades comunes y configuración para eml_rename.

Proporciona funciones para la gestión de configuración, acceso a claves de API,
consulta de modelos de IA de Google Gemini, manejo de señales del sistema y utilidades de zona horaria.
"""

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
    
def signal_handler(signal, frame):
    """Manejador de señal SIGINT (Ctrl+C).

    Interrumpe la ejecución de forma limpia mostrando un mensaje informativo.

    Args:
        signal: Número de la señal recibida.
        frame: Objeto de marco de pila de ejecución actual.
    """
    print(_("You pressed 'Ctrl+C', exiting..."))
    exit(0)

def argparse_epilog() -> str:
    """Genera el texto de cierre (epilog) para el parser de argumentos de la CLI.

    Returns:
        str: Mensaje con los datos de autoría y el año actual de la versión.
    """
    return _("Developed by Mariano Muñoz 2022-{}").format(__versiondate__.year)

DEFAULT_AI_MODEL = "gemini-2.5-flash"

def get_config_path() -> Path:
    """Devuelve la ruta al archivo de configuración de la aplicación.

    Returns:
        Path: Ruta a ~/.config/eml-rename/config.ini.
    """
    return Path.home() / ".config" / "eml-rename" / "config.ini"

def get_config() -> ConfigParser:
    """Carga y devuelve el objeto ConfigParser del archivo de configuración si existe.

    Returns:
        ConfigParser: Instancia con la configuración leída o vacía si el archivo no existe.
    """
    config = ConfigParser()
    config_path = get_config_path()
    if config_path.exists():
        config.read(config_path)
    return config

def get_google_api_key() -> str | None:
    """Busca y recupera la API Key de Google.

    Tiene en cuenta el siguiente orden de prioridad:
    1. Variable de entorno GOOGLE_API_KEY.
    2. Sección [auth] en el archivo ~/.config/eml-rename/config.ini.

    Returns:
        str | None: La clave de la API si fue encontrada, o None en caso contrario.
    """
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
    """Obtiene el modelo de IA configurado en config.ini o el valor predeterminado.

    Returns:
        str: Nombre del modelo de IA a utilizar (por defecto DEFAULT_AI_MODEL).
    """
    config = get_config()
    if config.has_section("ai"):
        model = config.get("ai", "model_name", fallback=None)
        if model and model.strip():
            return model.strip()
    return DEFAULT_AI_MODEL

def save_ai_model(model_name: str) -> None:
    """Guarda el modelo de IA seleccionado en el archivo de configuración config.ini.

    Crea los directorios necesarios y la sección [ai] si no existen previamente.

    Args:
        model_name (str): Nombre del modelo que se desea persistir.
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
    """Obtiene la lista de modelos de Google Gemini disponibles para generación de contenido.

    Requiere que la API Key esté configurada y que el paquete google-genai esté instalado.
    Filtra los modelos que admitan la acción 'generateContent'.

    Returns:
        list[str]: Lista con los nombres limpios de los modelos (sin prefijo 'models/').

    Raises:
        Exception: Si GOOGLE_API_KEY no está definida o si google-genai no está instalado.
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
    """Obtiene el nombre de la zona horaria del sistema operativo.

    Ejecuta tzset() para inicializar y sincronizar las variables de zona horaria.

    Returns:
        str: Nombre o identificador de la zona horaria local (ej. 'CET', 'Europe/Madrid').
    """
    tzset()
    return tzname[0]