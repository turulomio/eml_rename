from configparser import ConfigParser
from chardet import detect
from colorama import Fore, Style
from datetime import datetime
from email import message_from_string
from email.parser import HeaderParser
from email.utils import parsedate_to_datetime, parseaddr
from email.header import decode_header
from os import rename, environ
from pathlib import Path
from pydicts import colors, casts
from zoneinfo import ZoneInfo
from .commons import get_google_api_key, get_system_localzone_name, _


## Class to work with eml file
class EmlFile():
    def __init__(self, path, length, ia=False):
        self.path=path
        self.ia=ia
        self.length=length
        self.error_message=[]

        self.google_api_key=get_google_api_key()
        self.system_timezone=get_system_localzone_name()
        self.file_encoding=self.get_file_encoding()
        self.dt=self.get_mail_datetime()
        self.from_=self.get_mail_from()
        self.body=self.get_mail_body()
        if self.ia:
            self.subject=self.get_mail_subject_with_ia()
        else:
            self.subject=self.get_mail_subject()
                
    def get_file_encoding(self):        #Guessing file chart
        with open(self.path, "rb") as f:
            detected=detect(f.read(10000)) 
            return detected["encoding"]

    def get_mail_from(self):
        #Parse file and load used metadata            
        with open(self.path, "r", encoding=self.file_encoding) as f:
            try:
                metadata=HeaderParser().parse(f)
                from_=parseaddr(metadata["From"])[1]
                return from_
            except Exception as e:
                self.error_message.append(str(e))

    def get_mail_datetime(self):       
        with open(self.path, "r", encoding=self.file_encoding) as f:
            try:
                metadata=HeaderParser().parse(f)
                dt_mail=parsedate_to_datetime(metadata["Date"])
                if self.system_timezone in ["CEST", "CET"]: #Cest wasn't recognized by ZoneInfo
                    self.system_timezone="Europe/Madrid"
                dt=dt_mail.astimezone(ZoneInfo(self.system_timezone))
                return dt
            except Exception as e:
                self.error_message.append(str(e))


    def get_mail_body(self):
        #Parse file and load used metadata            
        with open(self.path, "r", encoding=self.file_encoding) as f:
            try:
                body = ""
                f.seek(0)
                msg = message_from_string(f.read())
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = body +  payload.decode(self.file_encoding, errors='ignore')
                            break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode(self.file_encoding, errors='ignore')
                return body
            except Exception as e:
                self.error_message.append(str(e))



    def get_mail_subject(self):      
        empty_answer= _("(Without subject)")     
        with open(self.path, "r", encoding=self.file_encoding) as f:
            try:
                metadata=HeaderParser().parse(f)
                if metadata["Subject"] is None:
                    return empty_answer
                arr=decode_header(metadata["Subject"])
                r=""
                for stream, codification in arr:
                    codification="utf-8" if codification is None else codification
                    if isinstance(stream, bytes):
                        r=r+stream.decode(codification)
                    elif isinstance(stream,  str):
                        r=r+stream
                        
                if r.strip()=="":
                    r= empty_answer
                return self.remove_illegal_chars(r)
            except:
                self.error_message=_("Error parsing subject") + str(arr)
                return empty_answer

    def get_google_ia_models(self):
            try:
                from google import genai
            except ImportError:
                raise Exception(_("The 'google-genai' package is not installed. Please run 'pip install google-genai' or 'poetry install'."))

            if not self.google_api_key:
                raise Exception(_("GOOGLE_API_KEY not found. Set it in environment or in ~/.config/eml-rename/config.ini"))
            client = genai.Client(api_key=self.google_api_key)
            
            # List all available models to console
            for m in client.models.list():
                print(f"Found model: {m.name}")

    def get_mail_subject_with_ia(self):
            if casts.is_noe(self.body):
                return self.get_mail_subject()
            try:
                from google import genai
            except ImportError:
                raise Exception(_("The 'google-genai' package is not installed. Please run 'pip install google-genai' or 'poetry install'."))

            try:
                if not self.google_api_key:
                    raise Exception(_("GOOGLE_API_KEY not found. Set it in environment or in ~/.config/eml-rename/config.ini"))
                client = genai.Client(api_key=self.google_api_key)
                prompt = f"""Summarize the following email content in a single sentence, maximum 100 characters, to be used as a file name subject. The sentence must be in spanish. 

                Trata de quitar articulos y letras innecesaria. Debe dar un esquema de contenido. No detalles

                Quiero la idea fuerza de forma esquemática
                
                No pongas un punto al final.
                
                Asegúrate de que la respuesta esté codificada en UTF-8.

                Content: '{self.body}'
                """

                response = client.models.generate_content(model='gemma-3n-e4b-it', contents=prompt)
                if response and response.text:
                    return self.remove_illegal_chars(response.text)
            except Exception as e:
                self.error_message.append(f"AI Error: {str(e)}")


                
    def final_name(self):
        basename=f"{casts.dtaware2str(self.dt, '%Y%m%d %H%M')} [{self.from_}] {self.subject}"
        if len(basename)>self.length:
            basename=basename[0:self.length-4]
        return basename+".eml"


    def remove_illegal_chars(self, s):
        illegal_chars = '<>:"/\\|?*\n\t-_()[]{}¿'
        s = s.strip()
        s = s[:-1] if s[len(s)-1]=="." else s
        s = s.translate(str.maketrans('', '', illegal_chars))
        for i in range(5):
            s = s.replace("..", ".")
            s = s.replace("  ", " ")
        return s

    ##Method that detects if path has eml_rename format and returns a Boolean
    def filename_format_detected(self):  
        arr=self.path.split(" ")
        if len(arr)<3:
            return False
        
        if len(arr[0])!=8: #date
            return False
        
        if len(arr[1])!=4: #hour
            return False
            
        try:
            datetime.strptime( arr[0]+" "+arr[1], "%Y%m%d %H%M" )
        except:
            return False
            
        if not arr[2].startswith("[") or not arr[2].endswith("]") or not "@" in arr[2][1:-1]: #mail in brackets
            return False
        
        return True
        
    def will_be_renamed(self, force):
        if len(self.error_message)>0:
            return False
        if force is False and self.filename_format_detected() is True:
            return False
        return True

    def report(self, force, save):
        if len(self.error_message)>0:
            aclaration=_("[Error detected. Won't be renamed]") if save is False else _("[Error detected. Not Renamed]") 
            return  colors.red(self.error_message)+  " " + colors.blue(aclaration)
        if self.will_be_renamed(force):
            aclaration=_("[Will be renamed]") if save is False else _("[Renamed]") 
            return colors.green(self.final_name()) +  " " + colors.blue(aclaration)
        else:
            aclaration=_("[Format detected. Won't de renamed]") if save is False else _("[Format detected. Not renamed]") 
            return colors.yellow(self.final_name())+  " " + colors.blue(aclaration)
            
    def write(self, force):
        if self.will_be_renamed(force):
            rename(self.path, self.final_name())
            
