"""Módulo de procesamiento y representación de archivos de correo electrónico (.eml).

Define la clase EmlFile, encargada de analizar las cabeceras MIME, extraer y normalizar
la fecha a la zona horaria del sistema, detectar codificaciones, sanitizar textos,
generar resúmenes con IA de Google Gemini y efectuar el renombrado de ficheros.
"""

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
from .commons import get_google_api_key, get_system_timezone_name, get_ai_model, get_available_ai_models, _


class EmlFile:
    """Representa y gestiona un archivo de correo electrónico individual (.eml).

    Extrae metadatos esenciales (fecha, remitente, asunto y cuerpo), determina la codificación,
    soporta generación de asunto mediante IA (Google Gemini) y calcula el nuevo nombre estandarizado
    con formato 'YYYYMMDD HHMM [remitente] asunto.eml'.
    """

    def __init__(self, path, length, ia=False, force=False, ia_delay=2, ai_model=None):
        """Inicializa una instancia de EmlFile y analiza sus metadatos.

        Args:
            path (str | Path): Ruta al archivo .eml a procesar.
            length (int): Longitud máxima permitida para el nombre final de archivo.
            ia (bool, optional): Indica si debe resumirse el cuerpo con IA. Por defecto False.
            force (bool, optional): Fuerza el renombrado aunque el archivo ya tenga prefijo estándar. Por defecto False.
            ia_delay (int, optional): Segundos de pausa entre llamadas consecutivas a la IA. Por defecto 2.
            ai_model (str, optional): Nombre del modelo Gemini a utilizar. Si es None, toma el de la configuración.
        """
        self.path=path
        self.ia_requested=ia # Store if AI was requested
        self.length=length
        self.error_message=[]
        self.force = force # Store the force parameter
        self.ia_delay = ia_delay # Store AI delay
        self.ai_model = ai_model or get_ai_model()

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
                
    def get_file_encoding(self) -> str:
        """Detecta la codificación de caracteres del archivo .eml mediante chardet.

        Lee una muestra inicial de hasta 10.000 bytes. Devuelve 'utf-8' como fallback
        si no se puede determinar la codificación o si se detecta 'utf-7'.

        Returns:
            str: Nombre de la codificación detectada o 'utf-8' ante excepciones o formatos no reconocidos.
        """
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
        """Extrae la dirección de correo electrónico del remitente a partir de la cabecera 'From'.

        Returns:
            str | None: Dirección de email del remitente (ej. 'usuario@ejemplo.com') o None en caso de error.
        """
        try:
            with open(self.path, "r", encoding=self.file_encoding, errors="replace") as f:
                metadata=HeaderParser().parse(f)
                from_=parseaddr(metadata["From"])[1]
                return from_
        except Exception as e:
            self.error_message.append(str(e))

    def get_mail_datetime(self):
        """Extrae la fecha del correo y la convierte a la zona horaria del sistema.

        Lee la cabecera 'Date' MIME, la interpreta y transforma el objeto datetime
        al huso horario local configurado en el sistema operativo.

        Returns:
            datetime | None: Objeto datetime con zona horaria convertida o None si falla el análisis.
        """
        try:
            with open(self.path, "r", encoding=self.file_encoding, errors="replace") as f:
                metadata=HeaderParser().parse(f)
                dt_mail=parsedate_to_datetime(metadata["Date"])
                dt=casts.dtaware_changes_tz(dt_mail, self.system_timezone)
                return dt
        except Exception as e:
            self.error_message.append(str(e))

    def get_mail_body(self):
        """Extrae el contenido de texto plano del cuerpo del mensaje de correo.

        Si el correo es de tipo multiparte (multipart), recorre sus partes hasta encontrar
        la primera de tipo 'text/plain'. Si no es multiparte, decodifica directamente el contenido.

        Returns:
            str: Texto plano decodificado del cuerpo del mensaje, o cadena vacía si no se encuentra.
        """
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
        """Extrae, decodifica y sanitiza el asunto (Subject) de las cabeceras del correo.

        Maneja la decodificación de cabeceras RFC 2047 en múltiples fragmentos y codificaciones.
        Si el correo no tiene asunto o queda vacío tras la limpieza, devuelve '(Without subject)'.

        Returns:
            str: Asunto decodificado y saneado para uso seguro como nombre de archivo.
        """
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
        """Extrae el prefijo con formato 'YYYYMMDD HHMM [remitente]' del nombre de archivo si coincide con el patrón.

        Args:
            filename (str | Path): Nombre o ruta del archivo a verificar.

        Returns:
            str | None: La cadena del prefijo si coincide con el patrón, o None en caso contrario.
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
        """Obtiene e imprime por consola los modelos de IA de Google Gemini disponibles.

        Returns:
            list[str]: Lista de nombres de modelos recuperados.
        """
        models = get_available_ai_models()
        for m in models:
            print(f"Found model: {m}")
        return models

    def get_mail_subject_with_ia(self):
        """Genera un asunto conciso resumiendo el cuerpo del correo mediante la API de Google Gemini.

        Envía una muestra del cuerpo del mensaje (máximo 3.000 caracteres) al modelo configurado
        usando ajustes optimizados para bajo consumo de tokens (temperature=0.1, thinking_budget=0,
        max_output_tokens=50). Si la llamada a la IA falla, recurre automáticamente al asunto original del correo.

        Returns:
            str: Resumen del contenido generado por la IA o el asunto extraído en caso de error.

        Raises:
            Exception: Si google-genai no está instalado o no se encuentra GOOGLE_API_KEY.
        """
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
                model=self.ai_model,
                contents=f"Correo:\n{body_sample}",
                config=config,
            )
            if response and response.text:
                return self.remove_illegal_chars(response.text)
        except Exception as e:
            self.error_message.append(f"AI Error: {str(e)}")
            return self.get_mail_subject() # Fallback to non-AI subject if AI fails

    def final_name(self):
        """Calcula el nombre de archivo final estandarizado para el correo.

        El formato es: 'YYYYMMDD HHMM [remitente] asunto.eml'.
        Si la longitud excede self.length, recorta el nombre manteniendo la extensión .eml.

        Returns:
            str: Nombre de archivo resultante con extensión .eml.
        """
        basename=f"{casts.dtaware2str(self.dt, '%Y%m%d %H%M')} [{self.from_}] {self.subject}"
        if len(basename)>self.length:
            basename=basename[0:self.length-4]
        return basename+".eml"

    def remove_illegal_chars(self, s):
        """Elimina caracteres ilegales o conflictivos para nombres de archivo en sistemas de ficheros.

        Suprime caracteres reservados (<, >, :, \", /, \\, |, ?, *, saltos de línea, corchetes, etc.)
        y colapsa espacios o puntos consecutivos.

        Args:
            s (str): Cadena de texto a sanitizar.

        Returns:
            str: Cadena limpia y apta para formar parte de un nombre de fichero.
        """
        illegal_chars = '<>:"/\\|?*\n\t-_()[]{}¿'
        s = s.strip()
        s = s[:-1] if s.endswith(".") else s
        s = s.translate(str.maketrans('', '', illegal_chars))
        for i in range(5):
            s = s.replace("..", ".")
            s = s.replace("  ", " ")
        return s

    def filename_format_detected(self):
        """Comprueba si el nombre del archivo actual ya cuenta con el formato estándar 'YYYYMMDD HHMM [remitente]'.

        Returns:
            bool: True si el nombre actual ya sigue el patrón, False en caso contrario.
        """
        return self._get_prefix_from_filename(self.path) is not None
        
    def will_be_renamed(self, force):
        """Determina si el archivo debe ser renombrado según las reglas de negocio y flags.

        Tiene en cuenta si hubo errores de parseo, si el flag 'force' está activo,
        y si el archivo ya tiene el prefijo de fecha/remitente exacto para proteger
        asuntos modificados manualmente.

        Args:
            force (bool): Si es True, fuerza el renombrado salvo que existan errores en el archivo.

        Returns:
            bool: True si el archivo debe ser renombrado, False en caso contrario.
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
        """Genera una línea de informe formateada con colores ANSI para mostrar en consola.

        Indica si se detectaron errores, si fue o será renombrado, o si se detectó el formato previo.

        Args:
            force (bool): Si se aplicó la opción de forzar renombrado.
            save (bool): Si los cambios se están guardando en disco (True) o simulando (False).

        Returns:
            str: Cadena formateada con códigos de color ANSI lista para imprimir.
        """
        if len(self.error_message)>0:
            aclaration=_("[Error detected. Won't be renamed]") if save is False else _("[Error detected. Not Renamed]") 
            return  colors.red(self.error_message)+  " " + colors.blue(aclaration)
        if self.will_be_renamed(force):
            aclaration=_("[Will be renamed]") if save is False else _("[Renamed]") 
            return colors.green(self.final_name()) +  " " + colors.blue(aclaration)
        else:
            aclaration=_("[Format detected. Won't de renamed]") if save is False else _("[Format detected. Not renamed]") 
            return colors.yellow(self.final_name())+  " " + colors.blue(aclaration)
            
    def final_path(self):
        """Calcula la ruta completa final del archivo conservando su directorio padre original.

        Returns:
            Path: Objeto Path con la ruta completa y el nuevo nombre final.
        """
        return Path(self.path).parent / self.final_name()

    def write(self, force):
        """Renombra físicamente el archivo en el sistema de archivos si corresponde.

        Utiliza final_path() para asegurar que el archivo se mantiene en su directorio correspondiente.

        Args:
            force (bool): Si es True, fuerza el renombrado incluso si ya tenía prefijo detectado.
        """
        if self.will_be_renamed(force):
            rename(self.path, self.final_path())
            
