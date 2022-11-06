from setuptools import setup, Command
from platform import system as platform_system
from os import system, chdir
from site import getsitepackages
from sys import path

class Reusing(Command):
    description = "Fetch remote modules"
    user_options = [
      # The format is (long option, short option, description).
      ( 'local', None, 'Update files without internet'),
  ]

    def initialize_options(self):
        self.local=False

    def finalize_options(self):
        pass

    def run(self):
        path.append("eml_rename/reusing")
        if self.local is False:
            from github import download_from_github
            download_from_github('turulomio','reusingcode','python/github.py', 'eml_rename/reusing/')
            download_from_github('turulomio','reusingcode','python/datetime_functions.py', 'eml_rename/reusing/')

## Class to define doc command
class Translate(Command):
    description = "Update translations"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        #es
        system("xgettext -L Python --no-wrap --no-location --from-code='UTF-8' -o eml_rename/locale/eml_rename.pot *.py eml_rename/*.py eml_rename/reusing/*.py setup.py")
        system("msgmerge -N --no-wrap -U eml_rename/locale/es.po eml_rename/locale/eml_rename.pot")
        system("msgfmt -cv -o eml_rename/locale/es/LC_MESSAGES/eml_rename.mo eml_rename/locale/es.po")
        system("msgfmt -cv -o eml_rename/locale/en/LC_MESSAGES/eml_rename.mo eml_rename/locale/en.po")

    
class Procedure(Command):
    description = "Show release procedure"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print("""Nueva versión:
  * Cambiar la versión y la fecha en __init__.py
  * Modificar el Changelog en README
  * python setup.py translate
  * linguist
  * python setup.py translate
  * python setup.py uninstall; python setup.py install
  * git commit -a -m 'eml_rename-{0}'
  * git push
  * Hacer un nuevo tag en GitHub
  * python setup.py sdist
  * twine upload dist/eml_rename-{0}.tar.gz 
  * python setup.py uninstall
  * Crea un nuevo ebuild de eml_rename Gentoo con la nueva versión
  * Subelo al repositorio del portage

""".format(__version__))


## Class to define doxygen command
class Doxygen(Command):
    description = "Create/update doxygen documentation in doc/html"

    user_options = [
      # The format is (long option, short option, description).
      ( 'user=', None, 'Remote ssh user'),
      ( 'directory=', None, 'Remote ssh path'),
      ( 'port=', None, 'Remote ssh port'),
      ( 'server=', None, 'Remote ssh server'),
  ]

    def initialize_options(self):
        self.user="root"
        self.directory="/var/www/html/doxygen/eml_rename/"
        self.port=22
        self.server="127.0.0.1"

    def finalize_options(self):
        pass

    def run(self):
        print("Creating Doxygen Documentation")
        system("""sed -i -e "41d" doc/Doxyfile""")#Delete line 41
        system("""sed -i -e "41iPROJECT_NUMBER         = {}" doc/Doxyfile""".format(__version__))#Insert line 41
        system("rm -Rf build")
        chdir("doc")
        system("doxygen Doxyfile")      
        command=f"""rsync -avzP -e 'ssh -l {self.user} -p {self.port} ' html/ {self.server}:{self.directory} --delete-after"""
        print(command)
        system(command)
        chdir("..")

## Class to define uninstall command
class Uninstall(Command):
    description = "Uninstall installed files with install"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if platform_system()=="Linux":
            system("rm -Rf {}/eml_rename*".format(getsitepackages()[0]))
            system("rm /usr/bin/eml_rename*")
        else:
            system("pip uninstall eml_rename")

########################################################################

## Version of eml_rename captured from commons to avoid problems with package dependencies
__version__= None
with open('eml_rename/__init__.py', encoding='utf-8') as f:
    for line in f.readlines():
        if line.find("__version__ =")!=-1:
            __version__=line.split("'")[1]


setup(name='eml_rename',
     version=__version__,
     description='Script renames all eml files in a directory using mail metadata',
     long_description='Project web page is in https://github.com/turulomio/eml_rename',
     long_description_content_type='text/markdown',
     classifiers=['Development Status :: 5 - Production/Stable',
                  'Intended Audience :: End Users/Desktop',
                  'Topic :: Utilities',
                  'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                  'Programming Language :: Python :: 3',
                 ], 
     keywords='eml email rename files directory',
     url='https://github.com/turulomio/eml_rename',
     author='Turulomio',
     author_email='turulomio@yahoo.es',
     license='GPL-3',
     packages=['eml_rename', 'eml_rename.locale', 'eml_rename.locale.es.LC_MESSAGES', 'eml_rename.locale.en.LC_MESSAGES', 'eml_rename.reusing'],
     install_requires=['colorama', 'chardet', 'tqdm'],
     entry_points = {'console_scripts': [
                            'eml_rename=eml_rename.core:main',
                        ],
                    },
     cmdclass={'doxygen': Doxygen,
               'uninstall':Uninstall, 
               'translate': Translate,
               'procedure': Procedure,
               'reusing': Reusing,
              },
     zip_safe=False,
     include_package_data=True
)
