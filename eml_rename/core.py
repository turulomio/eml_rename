from .__init__ import __versiondate__, __version__
from argparse import ArgumentParser, RawTextHelpFormatter
from gettext import translation
from importlib.resources import files
from signal import signal,  SIGINT
from sys import exit

try:
    t=translation('eml_rename', files("eml_rename") / "locale")
    _=t.gettext
except:
    _=str
    
def signal_handler( signal, frame):
        print(_("You pressed 'Ctrl+C', exiting..."))
        exit(0)

## Function used in argparse_epilog
## @return String
def argparse_epilog():
    return _("Developed by Mariano Muñoz 2022-{}").format(__versiondate__.year)

def main():
    
    signal(SIGINT, signal_handler)
    parser=ArgumentParser(description=_('Script renames all eml files in a directory using mail metadata '), epilog=argparse_epilog(), formatter_class=RawTextHelpFormatter)
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--force', help=_("Forces subject update when 'YYYMMDD HHMM [from]' format is detected"), action="store_true", default=False)
    parser.add_argument('--length', help=_("Maximum length allowed to final name using 'YYYMMDD HHMM [from]'"), action="store", default=120,  type=int)
    args=parser.parse_args()
    
    eml_rename(args.force, args.length)

def eml_rename(force, length):
    print("RENAMING")
