from argparse import ArgumentParser, RawTextHelpFormatter

from eml_rename.commons import (
    signal_handler, __version__, __versiondate__, __versiondatetime__, _, argparse_epilog,
    get_ai_model, save_ai_model, get_available_ai_models, DEFAULT_AI_MODEL
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
    signal(SIGINT, signal_handler)
    default_length=140
    parser=ArgumentParser(description=_('Script renames all eml files in a directory using mail metadata '), epilog=argparse_epilog(), formatter_class=RawTextHelpFormatter)
    parser.add_argument('path', nargs='*', default=None, help=_("Optional path(s) to .eml file(s) or directory. Defaults to current directory."))
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--force', help=_("Forces subject update when 'YYYYMMDD HHMM [from]' format is detected"), action="store_true", default=False)
    parser.add_argument('--length', help=_("Maximum length allowed to final name using 'YYYYMMDD HHMM [from]'. Default: {0}").format(default_length), action="store", default=default_length,  type=int)
    parser.add_argument('--save', help=_("Without this parameter files won't be renamed. Script only pretend the result"), action="store_true", default=False)
    parser.add_argument('--ai', help=_("Use Gemini AI to summarize email content as subject"), action="store_true", default=False)
    parser.add_argument('--ai_delay', help=_("Delay between AI requests"), action="store", type=int, default=2)
    parser.add_argument('--ai_models', '--ai-models', help=_("List available Gemini AI models for content generation and exit"), action="store_true", default=False)
    parser.add_argument('--ai_model', '--ai-model', help=_("Specify Gemini AI model to use and save it to configfile"), action="store", default=None, type=str)
    args=parser.parse_args()

    if args.ai_models:
        try:
            models = get_available_ai_models()
            current_model = get_ai_model()
            print(colors.blue(_("Available Gemini AI models:")))
            for m in models:
                current_indicator = f" {colors.green(_('(configured)'))}" if m == current_model else ""
                print(f"  - {m}{current_indicator}")
            return
        except Exception as e:
            print(colors.red(f"{_('Error retrieving models')}: {str(e)}"))
            return

    if args.ai_model:
        save_ai_model(args.ai_model)
        print(colors.green(_("AI model set to '{0}' and saved to configuration.").format(args.ai_model)))

    ai_model = args.ai_model or get_ai_model()
    if args.ai:
        try:
            available_models = get_available_ai_models()
            if ai_model not in available_models and f"models/{ai_model}" not in available_models:
                print(colors.yellow(
                    _("Warning: Configured model '{0}' is not available in the API. Defaulting to '{1}'.").format(ai_model, DEFAULT_AI_MODEL)
                ))
                ai_model = DEFAULT_AI_MODEL
        except Exception:
            pass

    eml_rename(args.force, args.length, args.save, args.ai, args.ai_delay, ai_model, args.path)

def eml_rename(force=False, length=140, save=False, ia=False, ia_delay=2, ai_model=None, path=None):        
    start=datetime.now()
    if ai_model is None:
        ai_model = get_ai_model()
    
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
    with ThreadPoolExecutor(max_workers=1 if ia else cpu_count()+1) as executor:
            with tqdm(total=len(filenames), desc=_("Processing eml files")) as progress:
                for filename in filenames:
                        # Pass 'force', 'ia_delay', and 'ai_model' to EmlFile constructor
                        future=executor.submit(EmlFile, filename, length, ia, force, ia_delay, ai_model)
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
