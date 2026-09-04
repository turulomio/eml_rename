"""Paquete principal de eml_rename.

Herramienta de línea de comandos y biblioteca Python para el renombrado automático
y estructurado de archivos de correo electrónico (.eml) a partir de sus metadatos
(fecha, remitente, asunto) o resúmenes generados mediante IA (Google Gemini).
"""

from .core import __version__, __versiondate__, __versiondatetime__, eml_rename

__all__ = ["__version__", "__versiondate__", "__versiondatetime__", "eml_rename"]
