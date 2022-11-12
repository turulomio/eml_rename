from .__init__ import __versiondate__, __version__
from argparse import ArgumentParser, RawTextHelpFormatter
from chardet import detect
from colorama import init as colorama_init, Fore, Style

from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from email.parser import HeaderParser
from email.utils import parsedate_to_datetime, parseaddr
from email.header import decode_header
from eml_rename.reusing.datetime_functions import dtaware2string
from gettext import translation
from glob import glob
from importlib.resources import files
from os import rename

from multiprocessing import cpu_count
from signal import signal,  SIGINT
from sys import exit
from tqdm import tqdm
from zoneinfo import ZoneInfo

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

def get_system_localzone_name():
    return datetime.now().astimezone().tzname()

## Class to work with eml file
class EmlFile():
    def __init__(self, path):
        self.path=path
        
        self.error_message=""
        
        #Guessing file chart
        with open(path, "rb") as f:
            self.detected=detect(f.read(10000))
        
        #Parse file and load used metadata            
        with open(path, "r", encoding=self.detected["encoding"]) as f:
            try:
                system_timezone=get_system_localzone_name()

                metadata=HeaderParser().parse(f)
                self.from_=parseaddr(metadata["From"])[1]
                dt_mail=parsedate_to_datetime(metadata["Date"])
                self.dt=dt_mail.astimezone(ZoneInfo(system_timezone))
                self.subject=self.parse_subject(metadata["Subject"])
            except Exception as e:
                self.error_message=e
                
    

    #Returns [(b'This is a subject', 'iso-8859-1')], codification can be None
    def parse_subject(self, subject):
        arr=decode_header(subject)
        r=""
        try:
            for stream, codification in arr:
                codification="utf-8" if codification is None else codification
                if isinstance(stream, bytes):
                    r=r+stream.decode(codification)
                elif isinstance(stream,  str):
                    r=r+stream
                    
            if r.strip()=="":
                r=_("(Without subject)")
            return r
        except:
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
    def filename_format_detected(self):
        if hasattr(self, "_filename_format_detected"):
            return self._filename_format_detected
            
        arr=self.path.split(" ")
        if len(arr)<3:
            self._filename_format_detected= False
            return self._filename_format_detected
        
        if len(arr[0])!=8:
            self._filename_format_detected=False
            return self._filename_format_detected
        if len(arr[1])!=4:
            self._filename_format_detected=False
            return self._filename_format_detected
            
        try:
            datetime.strptime( arr[0]+" "+arr[1], "%Y%m%d %H%M" )
        except:
            self._filename_format_detected=False
            return self._filename_format_detected
            
        if not arr[2].startswith("[") or not arr[2].endswith("]") or not "@" in arr[2][1:-1]:
            self._filename_format_detected=False
            return self._filename_format_detected
        self._filename_format_detected=True
        return self._filename_format_detected
        
    def will_be_renamed(self, force):
        if hasattr(self, "_will_be_renamed"):
            return self._will_be_renamed
        if self.error_message!="":
            self._will_be_renamed= False
            return self._will_be_renamed
        if force is False and self.filename_format_detected() is True:
            self._will_be_renamed=  False
            return self._will_be_renamed
        self._will_be_renamed=  True
        return self._will_be_renamed

    def report(self, force, length, save):
        if self.error_message!="":
            aclaration=_("[Error detected. Won't be renamed]") if save is False else _("[Error detected. Not Renamed]") 
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
    default_length=140
    parser=ArgumentParser(description=_('Script renames all eml files in a directory using mail metadata '), epilog=argparse_epilog(), formatter_class=RawTextHelpFormatter)
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--force', help=_("Forces subject update when 'YYYMMDD HHMM [from]' format is detected"), action="store_true", default=False)
    parser.add_argument('--length', help=_("Maximum length allowed to final name using 'YYYMMDD HHMM [from]'. Default: {0}").format(default_length), action="store", default=default_length,  type=int)
    parser.add_argument('--save', help=_("Without this parameter files won't be renamed. Script only pretend the result"), action="store_true", default=False)
    args=parser.parse_args()
    
    eml_rename(args.force, args.length, args.save)

def eml_rename(force, length, save):        
    start=datetime.now()
    
    filenames=[]
    for filename in glob( "*.eml", recursive=False):
        filenames.append(filename)

    
    futures=[]
    with ProcessPoolExecutor(max_workers=cpu_count()+1) as executor:
            with tqdm(total=len(filenames), desc=_("Processing eml files")) as progress:
                for filename in filenames:
                        future=executor.submit(EmlFile, filename)
                        future.add_done_callback(lambda p: progress.update())
                        futures.append(future)

                for future in as_completed(futures):
                    future.result()

    #Sort files by path
    futures= sorted(futures, key=lambda x: x.result().path, reverse=False)
    
    #Process files
    number_to_be_renamed=0
    for i, f in enumerate(futures):
        o=f.result()

        print(f"-- ({i+1}/{len(futures)}) ({o.detected['encoding']})-----------------------------------------")
        print(o.path)
        print(o.report(force, length, save))
        if o.will_be_renamed(force):
            number_to_be_renamed+=1
        if save is True:
            o.write(force, length)
            
    print("-----------------------------------------------------------")
    print("")
    print("")
    if save is True:
        print(white(_("{0} files were renamed.").format(number_to_be_renamed)))
    else:
        print(white(_("Process was simulated, files weren't renamed. Use --save to rename {0} files.").format(number_to_be_renamed)))
    print(white(_("It took {}").format(datetime.now()-start)))
