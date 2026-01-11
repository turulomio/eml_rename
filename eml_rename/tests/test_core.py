from pytest import fixture, raises
from tempfile import mkdtemp
from shutil import rmtree
from os import path,chdir
from renamebyreplace.core import renamebyreplace, main

@fixture
def test_fs(monkeypatch):
    """Set up a temporary directory with a file structure for each test and changes into it."""
    # Suppress print output for all tests using this fixture
    monkeypatch.setattr('builtins.print', lambda *args, **kwargs: None)
    test_dir = mkdtemp()
    monkeypatch.chdir(test_dir)
    # Create a structure inside the temp directory
    fs = {
        "test_dir": test_dir,
        "mail1.eml": path.join(test_dir, "file a.txt"),
        "mail2.eml": path.join(test_dir, "file b.txt"),
        "mail3.eml": path.join(test_dir, "file c.txt"),
    }
    mail1="""From: "Jane Smith" <jane.smith@example.org>
Date: Fri, 15 Sep 2023 09:45:00 +0200
Subject: Project Update: EML Rename
Message-ID: <54321@example.org>
Content-Type: text/plain; charset="utf-8"

Hello,

This is a sample email for testing the eml_rename script.

Regards.
"""

    mail2="""From: "Conciencia Global" <info@conciencia-global.org>
Date: Wed, 22 May 2024 14:00:00 +0200
Subject: La urgente realidad del cambio climatico
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 8bit

Hola a todos,

La realidad del cambio climático es innegable. Los datos científicos muestran un aumento constante de la temperatura global, impulsado principalmente por las emisiones de gases de efecto invernadero. No es solo un problema ambiental, sino un desafío social y económico que requiere nuestra atención inmediata.

Es momento de actuar.
"""

    mail3="""From: "Angry Skeptic" <skeptic@example.com>
Date: Wed, 22 May 2024 15:30:00 +0200
Subject: Re: La urgente realidad del cambio climatico
Content-Type: text/plain; charset="utf-8"

This is absolute nonsense! I don't agree with a single word you said.
Climate change is a hoax and you are just trying to scare people for no reason.
Stop sending me this garbage!
"""

    create_file(fs["mail1.eml"], mail1)
    create_file(fs["mail2.eml"], mail2)
    create_file(fs["mail3.eml"], mail3)
    yield fs

    # Teardown: remove the temporary directory
    rmtree(test_dir)

def create_file(name, text):
    with open(name, "w") as f:
        f.write(text)

def test_emlrename(test_fs):
    renamebyreplace("a", "b", True, False)
    assert path.exists(test_fs["b"])
    assert not path.exists(test_fs["a"])
    #Undo
    renamebyreplace("a", "b", True, True)
    assert path.exists(test_fs["a"])
    assert not path.exists(test_fs["b"]) #In this example b is lost


def test_main_with_no_args(monkeypatch):
    """Test that main exits when no arguments are provided."""
    # Prevent sys.argv from being used by argparse
    monkeypatch.setattr('sys.argv', ['renamebyreplace'])
    with raises(SystemExit) as e:
        main()
    assert e.type == SystemExit
    assert e.value.code == 2

def test_main_with_args(monkeypatch, test_fs):
    """Test that main exits when no arguments are provided."""
    # Prevent sys.argv from being used by argparse"
    monkeypatch.setattr('sys.argv', ['renamebyreplace', "--search", "a", "--replace", "b", "--write"])
    main()
    assert path.exists(test_fs["b"])
    assert not path.exists(test_fs["a"])
