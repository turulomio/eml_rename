from .__init__ import __versiondate__, __version__
from argparse import ArgumentParser, RawTextHelpFormatter
from colorama import init as colorama_init, Fore, Style
from datetime import datetime
from email.parser import Parser
from email.utils import parsedate_to_datetime, parseaddr
from email.header import decode_header
from eml_rename.reusing.datetime_functions import dtaware2string
from gettext import translation
from glob import glob
from importlib.resources import files
from os import rename
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

   
def red(s):
    return Style.BRIGHT + Fore.RED + str(s) + Style.RESET_ALL
def green(s):
    return Style.BRIGHT + Fore.GREEN + str(s) + Style.RESET_ALL
def yellow(s):
    return Style.BRIGHT + Fore.YELLOW + str(s) + Style.RESET_ALL
def blue(s):
    return Style.BRIGHT + Fore.BLUE + str(s) + Style.RESET_ALL
def white(s):
    return Style.BRIGHT + Fore.WHITE + str(s) + Style.RESET_ALL

## Class to work with eml file
class EmlFile():
    def __init__(self, path):
        self.path=path
        
        self.error_message=""
        
        #Parse file and load used metadata            
        with open(path, "r") as f:
            try:
                metadata=Parser().parse(f, True)
                self.from_=parseaddr(metadata["From"])[1]
                self.dt=parsedate_to_datetime(metadata["Date"])
                self.subject=self.parse_subject(metadata["Subject"])
            except Exception as e:
                self.error_message=e
                

    #Returns [(b'This is a subject', 'iso-8859-1')], codification can be None
    def parse_subject(self, subject):
        arr=decode_header(subject)
        if len(arr)==1:
            first=arr[0]
            codification="utf-8" if first[1] is None else first[1]
            if isinstance(first[0], bytes):
                return first[0].decode(codification)
            elif isinstance(first[0], str):
                return first[0]
        self.error_message=_("Error parsing subject") + str(arr)
        return subject
                
    def final_name(self, length):
        r= f"{dtaware2string(self.dt,  '%Y%m%d %H%M')} [{self.from_}] {self.subject}"[:length-4] +".eml"
        sub=""
        r=r.replace("<", sub)
        r=r.replace(">", sub)
        r=r.replace(":", sub)
        r=r.replace('"', sub)
        r=r.replace("/", sub)
        r=r.replace("\\", sub)
        r=r.replace("|", sub)
        r=r.replace("?", sub)
        r=r.replace("*", sub)
        r=r.replace("\n", sub)
        r=r.replace("\t", sub)
        return r



    ##Method that detects if path has eml_rename format and returns a Boolean
    def format_detected(self):
        if hasattr(self, "_format_detected"):
            return self._format_detected
            
        arr=self.path.split(" ")
        if len(arr)<3:
            self._format_detected= False
            return self._format_detected
        
        if len(arr[0])!=8:
            self._format_detected=False
            return self._format_detected
        if len(arr[1])!=4:
            self._format_detected=False
            return self._format_detected
            
        try:
            datetime.strptime( arr[0]+" "+arr[1], "%Y%m%d %H%M" )
        except:
            self._format_detected=False
            return self._format_detected
            
        if not arr[2].startswith("[") or not arr[2].endswith("]") or not "@" in arr[2][1:-1]:
            self._format_detected=False
            return self._format_detected
        self._format_detected=True
        return self._format_detected
        
    def will_be_renamed(self, force):
        if hasattr(self, "_will_be_renamed"):
            return self._will_be_renamed
        if self.error_message!="":
            self._will_be_renamed= False
            return self._will_be_renamed
        if force is False and self.format_detected() is True:
            self._will_be_renamed=  False
            return self._will_be_renamed
        self._will_be_renamed=  True
        return self._will_be_renamed

    def report(self, force, length, save):
        if self.error_message!="":
            aclaration=_("[Won't be renamed]") if save is False else _("[Not Renamed]") 
            return  red(self.error_message)+  " " + blue(aclaration)
        if self.will_be_renamed(force):
            aclaration=_("[Will be renamed]") if save is False else _("[Renamed]") 
            return green(self.final_name(length)) +  " " + blue(aclaration)
        else:
            aclaration=_("[Format detected. Won't de renamed]") if save is False else _("[Format detected. Not renamed]") 
            return yellow(self.final_name(length))+  " " + blue(aclaration)
            
    def write(self, force, length):
        if self.will_be_renamed(force):
            rename(self.path, self.final_name(length))


def main():
    colorama_init()
    signal(SIGINT, signal_handler)
    parser=ArgumentParser(description=_('Script renames all eml files in a directory using mail metadata '), epilog=argparse_epilog(), formatter_class=RawTextHelpFormatter)
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--force', help=_("Forces subject update when 'YYYMMDD HHMM [from]' format is detected"), action="store_true", default=False)
    parser.add_argument('--length', help=_("Maximum length allowed to final name using 'YYYMMDD HHMM [from]'"), action="store", default=120,  type=int)
    parser.add_argument('--save', help=_("Without this parameter files won't be renamed. Script only pretend the result"), action="store_true", default=False)
    args=parser.parse_args()
    
    eml_rename(args.force, args.length, args.save)

def eml_rename(force, length, save):
    #Load in list al files
    emls=[]
    for filename in glob( "*.eml", recursive=False):
        emls.append(EmlFile(filename))
        
    #Sort files by path
    emls= sorted(emls, key=lambda x: x.path, reverse=False)
    
    #Process files
    for i, o in enumerate(emls):

        print(f"-- ({i+1}/{len(emls)}) -----------------------------------------")
        print(o.path)
        print(o.report(force, length, save))
        if save is True:
            o.write(force, length)
            
    print("")
    print("")
    if save is True:
        print(white(_("Files have been renamed")))
    else:
        print(white(_("Process has been simulated, files haven't been renamed.")))
