"""Main package for eml_rename.

Command-line tool and Python library to automatically rename .eml email files
using email metadata (date, sender, subject) or AI-generated summaries (Ollama).
"""

from .core import __version__, __versiondate__, __versiondatetime__, eml_rename

__all__ = ["__version__", "__versiondate__", "__versiondatetime__", "eml_rename"]
