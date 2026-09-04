"""Tareas de automatización y desarrollo para el proyecto eml_rename con Poe the Poet.

Incluye tareas para lanzamiento de versiones (release), compilación de traducciones (translate),
cobertura de pruebas (coverage) y generación de vídeos demostrativos (video) con VHS.
"""

from os import system, chdir
from pathlib import Path
from shutil import which
import sys
from eml_rename import __version__


def create_demo_emails(demo_dir: Path) -> None:
    """Crea un conjunto de correos electrónicos ficticios (.eml) para la grabación demostrativa.

    Args:
        demo_dir (Path): Directorio donde se crearán los archivos .eml de prueba.
    """
    demo_dir.mkdir(parents=True, exist_ok=True)
    # Limpiar posibles ficheros previos
    for f in demo_dir.glob("*.eml"):
        f.unlink()

    sample_emails = [
        {
            "filename": "factura_marzo.eml",
            "from": "facturacion@servicios-cloud.es",
            "date": "Wed, 11 Mar 2026 09:15:20 +0100",
            "subject": "Factura mensual servicios fibra y hosting marzo 2026",
            "body": (
                "Estimado cliente,\n\n"
                "Le adjuntamos la factura correspondiente a sus servicios contratados.\n"
                "Importe total: 45.90 EUR.\n\n"
                "Atentamente,\n"
                "Departamento de Facturación\n"
                "Servicios Cloud S.L.\n"
            ),
        },
        {
            "filename": "reunion_equipo.eml",
            "from": "carlos.mendoza@empresa-innovacion.es",
            "date": "Thu, 12 Mar 2026 15:40:00 +0100",
            "subject": "Convocatoria reunion de planificacion Q2",
            "body": (
                "Hola a todos,\n\n"
                "Os convoco a la reunión de planificación del segundo trimestre para el próximo lunes a las 10:00.\n\n"
                "Saludos,\n"
                "Carlos Mendoza\n"
            ),
        },
        {
            "filename": "confirmacion_reserva.eml",
            "from": "reservas@hotel-paraiso.es",
            "date": "Fri, 13 Mar 2026 18:25:45 +0100",
            "subject": "Confirmacion de reserva habitacion doble #74829",
            "body": (
                "Estimado huésped,\n\n"
                "Su reserva para las noches del 24 al 26 de abril ha sido confirmada.\n\n"
                "Gracias por confiar en nosotros,\n"
                "Hotel Paraíso\n"
            ),
        },
        {
            "filename": "aviso_seguridad.eml",
            "from": "seguridad@banco-digital.com",
            "date": "Sat, 14 Mar 2026 11:05:10 +0100",
            "subject": "Nuevo inicio de sesion detectado en su cuenta",
            "body": (
                "Estimado/a cliente,\n\n"
                "Se ha detectado un nuevo inicio de sesión desde un dispositivo no habitual.\n"
                "Si ha sido usted, ignore este mensaje.\n\n"
                "Banco Digital\n"
            ),
        },
    ]

    for mail in sample_emails:
        content = (
            f"From: {mail['from']}\n"
            f"Date: {mail['date']}\n"
            f"Subject: {mail['subject']}\n"
            f"Content-Type: text/plain; charset=\"utf-8\"\n\n"
            f"{mail['body']}\n"
        )
        (demo_dir / mail["filename"]).write_text(content, encoding="utf-8")


def release():
    """Muestra la lista de comprobación y pasos necesarios para publicar una nueva versión."""
    print("""Nueva versión:
  * Cambiar la versión y la fecha en commons.py y en pyproject
  * poe translate
  * linguist
  * poe translate
  * poe coverage
  * poe video
  * git commit -a -m 'eml_rename-{0}'
  * git push
  * Hacer un nuevo tag en GitHub
  * git checkout main
  * git pull
  * poetry build 
  * poetry publish
  * Crea un nuevo ebuild de eml_rename Gentoo con la nueva versión
  * Subelo al repositorio del portage

""".format(__version__))


def translate():
    """Extrae las cadenas traducibles y compila los archivos de mensajes gettext .po a .mo."""
    # es
    system("xgettext -L Python --no-wrap --no-location --from-code='UTF-8' -o eml_rename/locale/eml_rename.pot eml_rename/*.py")
    system("msgmerge -N --no-wrap -U eml_rename/locale/es.po eml_rename/locale/eml_rename.pot")
    system("msgfmt -cv -o eml_rename/locale/es/LC_MESSAGES/eml_rename.mo eml_rename/locale/es.po")
    system("msgfmt -cv -o eml_rename/locale/en/LC_MESSAGES/eml_rename.mo eml_rename/locale/en.po")


def coverage():
    """Ejecuta los tests unitarios con medición de cobertura y genera el informe HTML."""
    system("coverage run -m pytest && coverage report && coverage html")


def video():
    """Genera las animaciones GIF demostrativas (command.gif y help.gif) utilizando vhs y correos ficticios.

    Comprueba la disponibilidad de la herramienta 'vhs' (vhs-bin), genera correos de prueba
    en doc/demo/ y ejecuta 'vhs' sobre command.tape y help.tape dentro de la carpeta doc/.
    """
    vhs = which("vhs")
    if vhs is None:
        print("Se necesita la herramienta 'vhs' (paquete 'vhs-bin' en Arch Linux o https://github.com/charmbracelet/vhs).")
        sys.exit(1)

    project_root = Path(__file__).resolve().parent.parent
    doc_dir = project_root / "doc"
    demo_dir = doc_dir / "demo"
    tape_files = [doc_dir / "command.tape", doc_dir / "help.tape"]

    for tape_file in tape_files:
        if not tape_file.exists():
            print(f"Error: no se encontró el archivo de grabación: {tape_file}")
            sys.exit(1)

    print("Preparando correos electrónicos ficticios en doc/demo/...")
    create_demo_emails(demo_dir)

    chdir(doc_dir)
    for tape_file in tape_files:
        print(f"Generando GIF con {vhs} {tape_file.name}...")
        ret = system(f"{vhs} {tape_file.name}")
        if ret != 0:
            print(f"Error durante la ejecución de vhs para {tape_file.name} (código de salida: {ret}).")
            sys.exit(ret)
        print(f"Demostración generada con éxito a partir de {tape_file.name}.")

    print("Todas las grabaciones (command.gif y help.gif) han sido generadas con éxito en doc/.")

