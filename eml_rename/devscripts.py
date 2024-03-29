from eml_rename import __version__
from os import system


def release():
        print("""Nueva versión:
  * Cambiar la versión y la fecha en commons.py
  * Modificar el Changelog en README
  * python setup.py translate
  * linguist
  * python setup.py translate
  * python setup.py uninstall; python setup.py install
  * python setup.py documentation
  * python setup.py doxygen
  * git commit -a -m 'unogenerator-{0}'
  * git push
  * Hacer un nuevo tag en GitHub
  * python setup.py sdist
  * twine upload dist/unogenerator-{0}.tar.gz 
  * python setup.py uninstall
  * Crea un nuevo ebuild de UNOGENERATOR Gentoo con la nueva versión
  * Subelo al repositorio del portage

""".format(__version__))


def translate():
        #es
        system("xgettext -L Python --no-wrap --no-location --from-code='UTF-8' -o eml_rename/locale/eml_rename.pot eml_rename/*.py")
        system("msgmerge -N --no-wrap -U eml_rename/locale/es.po eml_rename/locale/eml_rename.pot")
        system("msgfmt -cv -o eml_rename/locale/es/LC_MESSAGES/eml_rename.mo eml_rename/locale/es.po")
        system("msgfmt -cv -o eml_rename/locale/en/LC_MESSAGES/eml_rename.mo eml_rename/locale/en.po")

#    def run(self):
#        print("Creating Doxygen Documentation")
#        system("""sed -i -e "41d" doc/Doxyfile""")#Delete line 41
#        system("""sed -i -e "41iPROJECT_NUMBER         = {}" doc/Doxyfile""".format(__version__))#Insert line 41
#        system("rm -Rf build")
#        os.chdir("doc")
#        system("doxygen Doxyfile")      
#        command=f"""rsync -avzP -e 'ssh -l {self.user} -p {self.port} ' html/ {self.server}:{self.directory} --delete-after"""
#        print(command)
#        system(command)
#        os.chdir("..")
#  
### Class to define uninstall command
#class Uninstall(Command):
#    description = "Uninstall installed files with install"
#    user_options = []
#
#    def initialize_options(self):
#        pass
#
#    def finalize_options(self):
#        pass
#
#    def run(self):
#        if platform.system()=="Linux":
#            system("rm -Rf {}/unogenerator*".format(site.getsitepackages()[0]))
#            system("rm /usr/bin/unogenerator*")
#        else:
#            system("pip uninstall unogenerator")
#
#########################################################################
#
### Version of unogenerator captured from commons to avoid problems with package dependencies
#__version__= None
#with open('unogenerator/commons.py', encoding='utf-8') as f:
#    for line in f.readlines():
#        if line.find("__version__ =")!=-1:
#            __version__=line.split("'")[1]
#
#
#setup(name='unogenerator',
#     version=__version__,
#     description='Python module to read and write LibreOffice and MS Office files using uno API',
#     long_description='Project web page is in https://github.com/turulomio/unogenerator',
#     long_description_content_type='text/markdown',
#     classifiers=['Development Status :: 4 - Beta',
#                  'Intended Audience :: Developers',
#                  'Topic :: Software Development :: Build Tools',
#                  'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
#                  'Programming Language :: Python :: 3',
#                 ], 
#     keywords='office generator uno pyuno libreoffice',
#     url='https://github.com/turulomio/unogenerator',
#     author='Turulomio',
#     author_email='turulomio@yahoo.es',
#     license='GPL-3',
#     packages=['unogenerator'],
#     install_requires=["tqdm", "humanize", "colorama","polib", "psutil", "pytz"],
#     entry_points = {'console_scripts': [
#                            'unogenerator_demo=unogenerator.demo:main',
#                            'unogenerator_demo_concurrent=unogenerator.demo:main_concurrent',
#                            'unogenerator_start=unogenerator.server:server_start',
#                            'unogenerator_stop=unogenerator.server:server_stop',
#                            'unogenerator_monitor=unogenerator.server:monitor',
#                            'unogenerator_translation=unogenerator.translation:main',
#                        ],
#                    },
#     cmdclass={'doxygen': Doxygen,
#               'uninstall':Uninstall, 
#               'translate': Translate,
#               'documentation': Documentation,
#               'procedure': Procedure,
#               'reusing': Reusing,
#              },
#     zip_safe=False,
#     test_suite = 'unogenerator.tests',
#     include_package_data=True
#)
