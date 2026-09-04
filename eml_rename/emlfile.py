import codecs
from chardet import detect
from datetime import datetime
from email import message_from_string
from email.parser import HeaderParser
from email.utils import parsedate_to_datetime, parseaddr
from email.header import decode_header
from os import rename
from pathlib import Path
from pydicts import colors, casts
from zoneinfo import ZoneInfo
from .commons import get_google_api_key, get_system_timezone_name, _


## Class to work with eml file
class EmlFile():
    def __init__(self, path, length, ia=False, force=False, ia_delay=2):
        self.path=path
        self.ia_requested=ia # Store if AI was requested
        self.length=length
        self.error_message=[]
        self.force = force # Store the force parameter
        self.ia_delay = ia_delay # Store AI delay

        self.google_api_key=get_google_api_key()
        self.system_timezone=get_system_timezone_name()
        self.file_encoding=self.get_file_encoding()
        self.dt=self.get_mail_datetime()
        self.from_=self.get_mail_from()
        self.body=self.get_mail_body()
        
        # Determine if AI should be used for subject generation
        # AI should only be used if it was requested AND the file is not already in the target format (or force is True)
        if self.ia_requested and not (not self.force and self.filename_format_detected()):
            self.subject=self.get_mail_subject_with_ia()
        else:
            self.subject=self.get_mail_subject()
                
    def get_file_encoding(self):        #Guessing file chart
        try:
            with open(self.path, "rb") as f:
                detected=detect(f.read(10000)) 
                encoding = detected.get("encoding")
                if not encoding or encoding.lower().replace("-", "") == "utf7":
                    return "utf-8"
                codecs.lookup(encoding)
                return encoding
        except LookupError:
            return "utf-8"
        except Exception as e:
            self.error_message.append(str(e))
            return "utf-8"

    def get_mail_from(self):
        #Parse file and load used metadata            
        try:
            with open(self.path, "r", encoding=self.file_encoding, errors="replace") as f:
                metadata=HeaderParser().parse(f)
                from_=parseaddr(metadata["From"])[1]
                return from_
        except Exception as e:
            self.error_message.append(str(e))

    def get_mail_datetime(self):       
        try:
            with open(self.path, "r", encoding=self.file_encoding, errors="replace") as f:
                metadata=HeaderParser().parse(f)
                dt_mail=parsedate_to_datetime(metadata["Date"])
                dt=casts.dtaware_changes_tz(dt_mail, self.system_timezone)
                return dt
        except Exception as e:
            self.error_message.append(str(e))


    def get_mail_body(self):
        #Parse file and load used metadata            
        try:
            with open(self.path, "r", encoding=self.file_encoding, errors="replace") as f:
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
        try:
            with open(self.path, "r", encoding=self.file_encoding, errors="replace") as f:
                metadata=HeaderParser().parse(f)
                if metadata["Subject"] is None:
                    return empty_answer
                arr=decode_header(metadata["Subject"])
                r=""
                for stream, codification in arr:
                    codification="utf-8" if codification is None else codification
                    if isinstance(stream, bytes):
                        try:
                            r=r+stream.decode(codification, errors="replace")
                        except LookupError:
                            r=r+stream.decode("utf-8", errors="replace")
                    elif isinstance(stream,  str):
                        r=r+stream
                        
                if r.strip()=="":
                    r= empty_answer
                return self.remove_illegal_chars(r)
        except Exception as e:
            self.error_message.append(f"{_('Error parsing subject')}: {str(e)}")
            return empty_answer

    def _get_prefix_from_filename(self, filename):
        """
        Extracts the 'YYYYMMDD HHMM [From]' part from a filename if it matches the pattern.
        Returns the prefix string or None.
        """
        file_stem = Path(filename).stem # Get filename without extension
        arr = file_stem.split(" ", 3) # Split at most 3 times to get date, time, from, and rest
        if len(arr) < 3:
            return None # Not enough parts
        
        date_part = arr[0]
        time_part = arr[1]
        from_part = arr[2]

        if len(date_part) != 8 or len(time_part) != 4:
            return None
        
        try:
            datetime.strptime(date_part + " " + time_part, "%Y%m%d %H%M")
        except ValueError:
            return None
            
        if not from_part.startswith("[") or not from_part.endswith("]") or "@" not in from_part[1:-1]:
            return None
        
        return f"{date_part} {time_part} {from_part}"

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
                from google.genai import types
            except ImportError:
                raise Exception(_("The 'google-genai' package is not installed. Please run 'pip install google-genai' or 'poetry install'."))

            try:
                if not self.google_api_key:
                    raise Exception(_("GOOGLE_API_KEY not found. Set it in environment or in ~/.config/eml-rename/config.ini"))
                client = genai.Client(api_key=self.google_api_key)

                # Limita la entrada a los primeros 3.000 caracteres para reducir el consumo de tokens
                # en correos con hilos extensos, firmas largas o volcados de texto.
                body_sample = self.body[:3000] if len(self.body) > 3000 else self.body

                config = types.GenerateContentConfig(
                    # max_output_tokens: Limita la respuesta a un máximo de 50 tokens (~150-200 caracteres),
                    # evitando explicaciones sobrantes o texto redundante.
                    max_output_tokens=50,
                    # temperature: Valor bajo (0.1) para priorizar respuestas deterministas, concisas y directas.
                    temperature=0.1,
                    # thinking_budget=0: Desactiva los tokens de razonamiento interno de Gemini 2.5 Flash,
                    # ahorrando cientos de tokens de 'thinking' innecesarios para un resumen simple.
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    # disable=True: Desactiva el Automatic Function Calling (AFC) para eliminar la sobrecarga
                    # del SDK y suprimir avisos de consola al no utilizar herramientas/funciones.
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                    # system_instruction: Define el rol del modelo y las reglas de formato esperadas
                    # para que la respuesta sea directamente utilizable como nombre de archivo.
                    system_instruction=(
                        "Resume el correo en una sola frase breve (máximo 80 caracteres) "
                        "en español para usar como asunto de archivo. "
                        "Esquemático, conciso, sin artículos innecesarios, sin punto final ni formato markdown."
                    ),
                )

                response = client.models.generate_content(
                    # Modelo estándar recomendado por Google para tareas rápidas y de bajo coste con soporte multimodal/texto.
                    model='gemini-2.5-flash',
                    contents=f"Correo:\n{body_sample}",
                    config=config,
                )
                if response and response.text:
                    return self.remove_illegal_chars(response.text)
            except Exception as e:
                self.error_message.append(f"AI Error: {str(e)}")
                return self.get_mail_subject() # Fallback to non-AI subject if AI fails

                
    def final_name(self):
        basename=f"{casts.dtaware2str(self.dt, '%Y%m%d %H%M')} [{self.from_}] {self.subject}"
        if len(basename)>self.length:
            basename=basename[0:self.length-4]
        return basename+".eml"


    def remove_illegal_chars(self, s):
        illegal_chars = '<>:"/\\|?*\n\t-_()[]{}¿'
        s = s.strip()
        s = s[:-1] if s.endswith(".") else s
        s = s.translate(str.maketrans('', '', illegal_chars))
        for i in range(5):
            s = s.replace("..", ".")
            s = s.replace("  ", " ")
        return s

    ##Method that detects if path has eml_rename format and returns a Boolean
    def filename_format_detected(self):
        """
        Checks if the current file's name matches the 'YYYYMMDD HHMM [From]' pattern.
        """
        return self._get_prefix_from_filename(self.path) is not None
        
    def will_be_renamed(self, force):
        """
        Determines if the file should be renamed based on force flag, errors,
        and whether the current filename matches the target format.
        """
        if len(self.error_message)>0:
            return False
        
        # If force is True, always rename (unless errors)
        if force:
            return True

        # If the current filename is EXACTLY the same as the final name, no rename needed.
        if Path(self.path).name == self.final_name():
            return False
        
        # If force is False and the current filename is NOT the final name,
        # we need to decide if it should be renamed.
        # It should NOT be renamed if:
        # 1. The current filename matches the expected prefix format (YYYYMMDD HHMM [From])
        # 2. AND the prefix of the current filename is IDENTICAL to the prefix of the generated final name.
        # This protects manually edited subjects.
        
        current_prefix = self._get_prefix_from_filename(self.path)
        generated_prefix = self._get_prefix_from_filename(self.final_name())

        if current_prefix is not None and current_prefix == generated_prefix:
            # The current file already has the expected date, time, and from format,
            # and that prefix is the same as what we would generate.
            # This means only the subject part is different, likely due to manual editing.
            # So, we should not rename it.
            return False
            
        # In all other cases, a rename is necessary.
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
            
