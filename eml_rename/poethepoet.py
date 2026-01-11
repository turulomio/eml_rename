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
  * git commit -a -m 'eml_rename-{0}'
  * git push
  * Hacer un nuevo tag en GitHub
  * python setup.py sdist
  * twine upload dist/eml_rename-{0}.tar.gz 
  * python setup.py uninstall
  * Crea un nuevo ebuild de eml_rename Gentoo con la nueva versión
  * Subelo al repositorio del portage

""".format(__version__))


def translate():
	#es
	system("xgettext -L Python --no-wrap --no-location --from-code='UTF-8' -o eml_rename/locale/eml_rename.pot eml_rename/*.py")
	system("msgmerge -N --no-wrap -U eml_rename/locale/es.po eml_rename/locale/eml_rename.pot")
	system("msgfmt -cv -o eml_rename/locale/es/LC_MESSAGES/eml_rename.mo eml_rename/locale/es.po")
	system("msgfmt -cv -o eml_rename/locale/en/LC_MESSAGES/eml_rename.mo eml_rename/locale/en.po")
