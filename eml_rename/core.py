"""Main execution and CLI module for eml_rename.

Handles command-line argument parsing, concurrent processing of email (.eml) files,
and safe file renaming either in simulation (dry-run) mode or saved to disk.
"""

from argparse import ArgumentParser, RawTextHelpFormatter

from eml_rename.commons import (
    signal_handler, __version__, __versiondate__, __versiondatetime__, _, argparse_epilog,
    DEFAULT_AI_URL, get_ai_url
)
from eml_rename.emlfile import EmlFile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from glob import glob
from pathlib import Path

from multiprocessing import cpu_count
from signal import signal,  SIGINT
from tqdm import tqdm
from pydicts import colors



def main():
    """Command-line interface (CLI) entry point.

    Configures the SIGINT handler (Ctrl+C), parses command-line arguments,
    and delegates execution to eml_rename().
    """
    signal(SIGINT, signal_handler)
    default_length=140
    parser=ArgumentParser(description=_('Script renames all eml files in a directory using mail metadata '), epilog=argparse_epilog(), formatter_class=RawTextHelpFormatter)
    parser.add_argument('path', nargs='*', default=None, help=_("Optional path(s) to .eml file(s) or directory. Defaults to current directory."))
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--force', help=_("Forces subject update when 'YYYYMMDD HHMM [from]' format is detected"), action="store_true", default=False)
    parser.add_argument('--length', help=_("Maximum length allowed to final name using 'YYYYMMDD HHMM [from]'. Default: {0}").format(default_length), action="store", default=default_length,  type=int)
    parser.add_argument('--save', help=_("Without this parameter files won't be renamed. Script only pretend the result"), action="store_true", default=False)
    parser.add_argument('--ai', help=_("Use Ollama AI with specified model to summarize email content as subject. Default: None (no AI)"), action="store", default=None, type=str)
    parser.add_argument('--ai_url', '--ai-url', help=_("Ollama server URL. Default: {0}").format(DEFAULT_AI_URL), action="store", default=DEFAULT_AI_URL, type=str)
    args=parser.parse_args()

    eml_rename(args.force, args.length, args.save, args.ai, args.ai_url, args.path)

def eml_rename(force=False, length=140, save=False, ai=None, ai_url=DEFAULT_AI_URL, path=None, **kwargs):
    """Process and rename email (.eml) files using metadata or AI summary.

    Enables renaming of individual files, lists of file paths, or all .eml files
    in the specified or current directory. Can run in preview/dry-run mode (save=False)
    or commit renames to disk (save=True).

    Args:
        force (bool): If True, forces renaming even if standard prefix format is detected.
        length (int): Maximum total length of resulting filename. Defaults to 140.
        save (bool): If True, renames files on disk; if False, simulates only.
        ai (str | None): Ollama model name to summarize email content as subject. If None, AI is not used.
        ai_url (str): Ollama server base URL. Defaults to DEFAULT_AI_URL.
        path (str | Path | list[str | Path] | None): Path to file(s) or directory. If None, uses current working directory.
    """        
    if ai is None and "ia" in kwargs:
        ia_val = kwargs["ia"]
        ai = ia_val if isinstance(ia_val, str) else None

    start=datetime.now()
    
    filenames=[]
    if path:
        paths = [path] if isinstance(path, (str, Path)) else path
        for p in paths:
            p_obj = Path(p)
            if p_obj.is_dir():
                filenames.extend(sorted(str(f) for f in p_obj.glob("*.eml")))
            elif p_obj.is_file():
                filenames.append(str(p_obj))
            else:
                matched = sorted(glob(str(p)))
                if matched:
                    filenames.extend(matched)
                else:
                    print(colors.red(_("File or path not found: {0}").format(p)))
    else:
        for filename in sorted(glob( "*.eml", recursive=False)):
            filenames.append(filename)

    
    futures=[]
    with ThreadPoolExecutor(max_workers=1 if ai else cpu_count()+1) as executor:
            with tqdm(total=len(filenames), desc=_("Processing eml files")) as progress:
                for filename in filenames:
                        future=executor.submit(EmlFile, filename, length, ai, force, ai_url)
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

        print(f"-- ({i+1}/{len(futures)}) ({o.file_encoding})-----------------------------------------")
        print(o.path)
        print(o.report(force, save))
        if o.will_be_renamed(force):
            number_to_be_renamed+=1
        if save is True:
            o.write(force)
            
    print("-----------------------------------------------------------")
    print("")
    print("")
    if save is True:
        print(colors.white(_("{0} files were renamed.").format(number_to_be_renamed)))
    else:
        print(colors.white(_("Process was simulated, files weren't renamed. Use --save to rename {0} files.").format(number_to_be_renamed)))
    print(colors.white(_("It took {}").format(datetime.now()-start)))
