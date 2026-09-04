"""Development and automation tasks for eml_rename project with Poe the Poet.

Includes tasks for releases (release), gettext translation compilation (translate),
test coverage reporting (coverage), and demonstration GIF generation (video) with VHS.
"""

from os import system, chdir
from pathlib import Path
from shutil import which
import sys
from eml_rename import __version__


def create_demo_emails(demo_dir: Path) -> None:
    """Create a set of fictitious email (.eml) files for video demonstration.

    Args:
        demo_dir (Path): Directory where sample .eml files will be created.
    """
    demo_dir.mkdir(parents=True, exist_ok=True)
    # Clear prior demo files if any
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
    """Display checklist and instructions to release a new version."""
    print("""New version checklist:
  * Update version and date in commons.py and pyproject.toml
  * poe translate
  * linguist
  * poe translate
  * poe coverage
  * poe video
  * git commit -a -m 'eml_rename-{0}'
  * git push
  * Create a new release/tag on GitHub
  * git checkout main
  * git pull
  * poetry build 
  * poetry publish
  * Create a new Gentoo ebuild of eml_rename with the new version
  * Upload it to the portage repository

""".format(__version__))


def translate():
    """Extract translatable strings and compile gettext .po files to binary .mo catalogs."""
    languages = ["es", "fr", "pt", "ru", "ro", "zh_CN", "hi"]
    system("xgettext -L Python --no-wrap --no-location --from-code='UTF-8' -o eml_rename/locale/eml_rename.pot eml_rename/*.py")
    for lang in languages:
        mo_dir = Path(f"eml_rename/locale/{lang}/LC_MESSAGES")
        mo_dir.mkdir(parents=True, exist_ok=True)
        system(f"msgmerge -N --no-wrap -U eml_rename/locale/{lang}.po eml_rename/locale/eml_rename.pot")
        system(f"msgfmt -cv -o eml_rename/locale/{lang}/LC_MESSAGES/eml_rename.mo eml_rename/locale/{lang}.po")

    # Also compile to 'zh' so both 'zh' and 'zh_CN' work
    zh_dir = Path("eml_rename/locale/zh/LC_MESSAGES")
    zh_dir.mkdir(parents=True, exist_ok=True)
    system("msgfmt -cv -o eml_rename/locale/zh/LC_MESSAGES/eml_rename.mo eml_rename/locale/zh_CN.po")


def coverage():
    """Run unit tests with code coverage analysis and generate HTML report."""
    system("coverage run -m pytest && coverage report && coverage html")


def video():
    """Generate demonstration GIF animations (command.gif and help.gif) using VHS and demo emails.

    Checks VHS tool availability (vhs-bin package), generates test emails in doc/demo/,
    and runs VHS on command.tape and help.tape in doc/.
    """
    vhs = which("vhs")
    if vhs is None:
        print("The 'vhs' tool is required (package 'vhs-bin' on Arch Linux or https://github.com/charmbracelet/vhs).")
        sys.exit(1)

    project_root = Path(__file__).resolve().parent.parent
    doc_dir = project_root / "doc"
    demo_dir = doc_dir / "demo"
    tape_files = [doc_dir / "command.tape", doc_dir / "help.tape"]

    for tape_file in tape_files:
        if not tape_file.exists():
            print(f"Error: tape recording file not found: {tape_file}")
            sys.exit(1)

    print("Preparing fictitious demo emails in doc/demo/...")
    create_demo_emails(demo_dir)

    chdir(doc_dir)
    for tape_file in tape_files:
        print(f"Generating GIF with {vhs} {tape_file.name}...")
        ret = system(f"{vhs} {tape_file.name}")
        if ret != 0:
            print(f"Error running vhs for {tape_file.name} (exit code: {ret}).")
            sys.exit(ret)
        print(f"Demo GIF successfully generated from {tape_file.name}.")

    print("All recording GIFs (command.gif and help.gif) generated successfully in doc/.")

