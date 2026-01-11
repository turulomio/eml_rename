from argparse import ArgumentParser, RawTextHelpFormatter

from eml_rename.commons import EmlFile, signal_handler,__version__, __versiondate__, __versiondatetime__, _, argparse_epilog
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from glob import glob

from multiprocessing import cpu_count
from signal import signal,  SIGINT
from tqdm import tqdm
from pydicts import colors



def main():
    signal(SIGINT, signal_handler)
    default_length=140
    parser=ArgumentParser(description=_('Script renames all eml files in a directory using mail metadata '), epilog=argparse_epilog(), formatter_class=RawTextHelpFormatter)
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--force', help=_("Forces subject update when 'YYYMMDD HHMM [from]' format is detected"), action="store_true", default=False)
    parser.add_argument('--length', help=_("Maximum length allowed to final name using 'YYYMMDD HHMM [from]'. Default: {0}").format(default_length), action="store", default=default_length,  type=int)
    parser.add_argument('--save', help=_("Without this parameter files won't be renamed. Script only pretend the result"), action="store_true", default=False)
    args=parser.parse_args()
    
    eml_rename(args.force, args.length, args.save)

def eml_rename(force=False, length=140, save=False):        
    start=datetime.now()
    
    filenames=[]
    for filename in glob( "*.eml", recursive=False):
        filenames.append(filename)

    
    futures=[]
    with ThreadPoolExecutor(max_workers=cpu_count()+1) as executor:
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
        print(colors.white(_("{0} files were renamed.").format(number_to_be_renamed)))
    else:
        print(colors.white(_("Process was simulated, files weren't renamed. Use --save to rename {0} files.").format(number_to_be_renamed)))
    print(colors.white(_("It took {}").format(datetime.now()-start)))
