from datetime import datetime
from gettext import translation
from importlib.resources import files

__version__ = '0.3.9999'
__versiondatetime__=datetime(2026, 1, 11, 0, 0)
__versiondate__=__versiondatetime__.date()


try:
    t=translation('eml_rename', files("eml_rename") / "locale")
    _=t.gettext
except:
    _=str