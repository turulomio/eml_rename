from chardet import detect
from colorama import init as Fore, Style
from datetime import datetime
from email.parser import HeaderParser
from email.utils import parsedate_to_datetime, parseaddr
from email.header import decode_header
from gettext import translation
from importlib.resources import files
from os import rename
from pydicts import colors

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


## Returns if a datetime is aware
def is_aware(dt):
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return False
    return True

## Returns if a datetime is naive
def is_naive(dt):
    return not is_aware(dt)

## Returns a formated string of a dtaware string formatting with a zone name
## @param dt datetime aware object
## @return String
def dtaware2string(dt, format):
    if is_naive(dt)==True:
        print("A dtaware is needed for {}".format(dt))
    else:
        return dtnaive2string(dt, format)

## Returns a formated string of a dtaware string formatting with a zone name
## @param dt datetime aware object
## @param format String in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y%m%d %H%M", "%Y%m%d%H%M"]
## @return String
def dtnaive2string(dt, format):
    allowed=["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y%m%d %H%M", "%Y%m%d%H%M", "JsUtcIso"]
    if dt==None:
        return "None"
    elif format in allowed:
        if format=="%Y-%m-%d":
            return dt.strftime("%Y-%m-%d")
        elif format=="%Y-%m-%d %H:%M:%S": 
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif format=="%Y%m%d %H%M": 
            return dt.strftime("%Y%m%d %H%M")
        elif format=="%Y%m%d%H%M":
            return dt.strftime("%Y%m%d%H%M")
        elif format=="JsUtcIso":
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        print("I can't convert this format '{}'. I only support this {}".format(format, allowed))


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
                metadata=HeaderParser().parse(f)
                self.from_=parseaddr(metadata["From"])[1]
                dt_mail=parsedate_to_datetime(metadata["Date"])
                system_timezone=get_system_localzone_name()
                if system_timezone in ["CEST", "CET"]: #Cest wasn't recognized by ZoneInfo
                    system_timezone="Europe/Madrid"
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
            return  red(self.error_message)+  " " + colors.blue(aclaration)
        if self.will_be_renamed(force):
            aclaration=_("[Will be renamed]") if save is False else _("[Renamed]") 
            return colors.green(self.final_name(length)) +  " " + colors.blue(aclaration)
        else:
            aclaration=_("[Format detected. Won't de renamed]") if save is False else _("[Format detected. Not renamed]") 
            return yellow(self.final_name(length))+  " " + colors.blue(aclaration)
            
    def write(self, force, length):
        if self.will_be_renamed(force):
            rename(self.path, self.final_name(length))
            
