"""Processing and representation module for email (.eml) files.

Defines the EmlFile class, responsible for parsing MIME headers, extracting and normalizing
dates to system timezone, detecting encodings, sanitizing text, generating AI summaries
via Google Gemini, and renaming files.
"""

import codecs
from chardet import detect
from datetime import datetime
from email import message_from_string
from email.parser import HeaderParser
from email.utils import parsedate_to_datetime, parseaddr
from email.header import decode_header
import json
from os import rename
from pathlib import Path
import urllib.error
import urllib.request
from pydicts import colors, casts
from zoneinfo import ZoneInfo
from .commons import DEFAULT_AI_URL, get_ai_url, get_system_timezone_name, _


class EmlFile:
    """Represents and manages an individual email (.eml) file.

    Extracts essential metadata (date, sender, subject, and body), determines encoding,
    supports AI-based subject generation (Ollama), and computes the standardized
    filename in the format 'YYYYMMDD HHMM [sender] subject.eml'.
    """

    def __init__(self, path, length, ai=None, force=False, ai_url=DEFAULT_AI_URL, **kwargs):
        """Initialize an EmlFile instance and parse its metadata.

        Args:
            path (str | Path): Path to the .eml file to process.
            length (int): Maximum allowed length for the final filename.
            ai (str | None, optional): Ollama model name to use for subject summary. If None, AI is not used. Defaults to None.
            force (bool, optional): Forces renaming even if the file already has standard prefix. Defaults to False.
            ai_url (str, optional): Ollama server URL. Defaults to DEFAULT_AI_URL.
        """
        self.path=path
        if ai is None and "ia" in kwargs:
            ia_val = kwargs["ia"]
            ai = ia_val if isinstance(ia_val, str) else None
        self.ai = ai # Ollama model name or None
        self.ai_url = ai_url
        self.length=length
        self.error_message=[]
        self.force = force

        self.system_timezone=get_system_timezone_name()
        self.file_encoding=self.get_file_encoding()
        self.dt=self.get_mail_datetime()
        self.from_=self.get_mail_from()
        self.body=self.get_mail_body()
        
        # Determine if AI should be used for subject generation
        # AI should only be used if it was requested (ai is not None) AND the file is not already in the target format (or force is True)
        if self.ai and not (not self.force and self.filename_format_detected()):
            self.subject=self.get_mail_subject_with_ia()
        else:
            self.subject=self.get_mail_subject()
                
    def get_file_encoding(self) -> str:
        """Detect character encoding of the .eml file using chardet.

        Reads an initial sample of up to 10,000 bytes. Falls back to 'utf-8' if
        encoding cannot be determined or if 'utf-7' is detected.

        Returns:
            str: Detected encoding name or 'utf-8' upon exceptions or unrecognized encodings.
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
        """Extract sender email address from the 'From' header.

        Returns:
            str | None: Sender email address (e.g. 'user@example.com') or None on error.
        """
        try:
            with open(self.path, "r", encoding=self.file_encoding, errors="replace") as f:
                metadata=HeaderParser().parse(f)
                from_=parseaddr(metadata["From"])[1]
                return from_
        except Exception as e:
            self.error_message.append(str(e))

    def get_mail_datetime(self):
        """Extract email date and convert it to system timezone.

        Reads the MIME 'Date' header, parses it, and transforms the datetime object
        to the local timezone configured in the host operating system.

        Returns:
            datetime | None: Timezone-aware datetime object or None if parsing fails.
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
        """Extract plain text content from the email message body.

        If the message is multipart, walks parts until the first 'text/plain' part is found.
        If not multipart, decodes the payload directly.

        Returns:
            str: Decoded plain text email body, or empty string if not found.
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
        """Extract, decode, and sanitize email Subject from headers.

        Handles RFC 2047 encoded-word headers with multiple chunks and charsets.
        Returns '(Without subject)' if missing or blank after sanitization.

        Returns:
            str: Decoded and sanitized subject string safe for filesystem usage.
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
        """Extract 'YYYYMMDD HHMM [sender]' prefix from filename if it matches pattern.

        Args:
            filename (str | Path): Filename or path to inspect.

        Returns:
            str | None: The matched prefix string or None if it does not match.
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

    def get_mail_subject_with_ia(self):
        """Generate a concise subject summarizing the email body using Ollama API.

        Sends a body sample (up to 3,000 characters) to the Ollama server at self.ai_url
        using self.ai model. Falls back to header subject if AI call fails.

        Returns:
            str: AI-generated summary or extracted subject on failure.
        """
        if casts.is_noe(self.body):
            return self.get_mail_subject()

        try:
            body_sample = self.body[:3000] if len(self.body) > 3000 else self.body
            prompt = f"Correo:\n{body_sample}"
            system_instruction = (
                "Resume el correo en una sola frase breve (máximo 80 caracteres) "
                "en español para usar como asunto de archivo. "
                "Esquemático, conciso, sin artículos innecesarios, sin punto final ni formato markdown."
            )
            url = f"{self.ai_url.rstrip('/')}/api/generate"
            payload = {
                "model": self.ai,
                "prompt": prompt,
                "system": system_instruction,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 50,
                },
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                text = result.get("response", "").strip()
                if text:
                    return self.remove_illegal_chars(text)
            return self.get_mail_subject()
        except Exception as e:
            self.error_message.append(f"AI Error: {str(e)}")
            return self.get_mail_subject()

    get_mail_subject_with_ai = get_mail_subject_with_ia

    def final_name(self):
        """Compute the standardized final filename for the email.

        Format: 'YYYYMMDD HHMM [sender] subject.eml'.
        Truncates if length exceeds self.length while preserving the .eml extension.

        Returns:
            str: Resulting filename with .eml extension.
        """
        basename=f"{casts.dtaware2str(self.dt, '%Y%m%d %H%M')} [{self.from_}] {self.subject}"
        if len(basename)>self.length:
            basename=basename[0:self.length-4]
        return basename+".eml"

    def remove_illegal_chars(self, s):
        """Remove illegal or conflicting filesystem characters from a string.

        Strips forbidden characters (<, >, :, \", /, \\, |, ?, *, newlines, brackets)
        and collapses duplicate spaces and dots.

        Args:
            s (str): String to sanitize.

        Returns:
            str: Clean string safe for filename usage.
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
        """Check if the current file already matches 'YYYYMMDD HHMM [sender]' prefix format.

        Returns:
            bool: True if current filename matches the expected pattern, False otherwise.
        """
        return self._get_prefix_from_filename(self.path) is not None
        
    def will_be_renamed(self, force):
        """Determine whether the file should be renamed based on rules and flags.

        Considers parsing errors, the 'force' flag, and protects manually edited subjects
        when current and generated prefixes are identical.

        Args:
            force (bool): If True, forces renaming unless parsing errors occurred.

        Returns:
            bool: True if the file should be renamed, False otherwise.
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
        """Generate formatted ANSI colored report line for terminal output.

        Args:
            force (bool): Whether force renaming was requested.
            save (bool): True if changes are committed to disk, False if simulated.

        Returns:
            str: Formatted ANSI string ready for printing.
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
        """Compute complete final path for the file preserving its parent directory.

        Returns:
            Path: Path object containing original parent directory and new final filename.
        """
        return Path(self.path).parent / self.final_name()

    def write(self, force):
        """Physically rename file on filesystem if applicable.

        Uses final_path() to ensure file remains in its parent directory.

        Args:
            force (bool): If True, forces renaming even if format was previously detected.
        """
        if self.will_be_renamed(force):
            rename(self.path, self.final_path())
            
