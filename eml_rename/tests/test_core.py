from pytest import fixture, raises
from tempfile import mkdtemp
from shutil import rmtree, copyfile
from os import path,chdir
from eml_rename.core import eml_rename, main

@fixture
def test_fs(monkeypatch):
    """Set up a temporary directory with a file structure for each test and changes into it."""
    # Ensure tests are completely isolated and never call real external APIs
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setattr("eml_rename.commons.get_google_api_key", lambda: None)
    monkeypatch.setattr("eml_rename.emlfile.get_system_timezone_name", lambda: "Europe/Berlin")
    test_dir = mkdtemp()
    monkeypatch.chdir(test_dir)
    # Create a structure inside the temp directory
    fs = {
        "test_dir": test_dir,
        "mail1.eml": path.join(test_dir, "mail1.eml"),
        "mail2.eml": path.join(test_dir, "mail2.eml"),
        "mail3.eml": path.join(test_dir, "mail3.eml"),
        "fake.eml": path.join(test_dir, "fake.eml")
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

    fake="""This is not a mail"""

    create_file(fs["mail1.eml"], mail1)
    create_file(fs["mail2.eml"], mail2)
    create_file(fs["mail3.eml"], mail3)
    create_file(fs["fake.eml"], fake)
    yield fs

    # Teardown: remove the temporary directory
    rmtree(test_dir)

def create_file(name, text):
    with open(name, "w") as f:
        f.write(text)

def test_emlrename(test_fs):
    eml_rename(save=True)
    assert not path.exists(test_fs["mail1.eml"])
    assert not path.exists(test_fs["mail2.eml"])
    assert not path.exists(test_fs["mail3.eml"])
    assert path.exists(test_fs["fake.eml"])
    assert path.exists("20230915 0945 [jane.smith@example.org] Project Update EML Rename.eml")
    assert path.exists("20240522 1400 [info@conciencia-global.org] La urgente realidad del cambio climatico.eml")
    assert path.exists("20240522 1530 [skeptic@example.com] Re La urgente realidad del cambio climatico.eml")

def test_main_with_help_args(monkeypatch, test_fs): # Added test_fs to ensure fixture is loaded
    """Test that main exits when no arguments are provided."""
    # Prevent sys.argv from being used by argparse
    monkeypatch.setattr('sys.argv', ['eml_rename', "--help"])
    with raises(SystemExit) as e:
        main()
    assert e.type == SystemExit
    assert e.value.code == 0

def test_main_with_no_args(monkeypatch, test_fs):
    """Test that main exits when no arguments are provided."""
    # Prevent sys.argv from being used by argparse"
    monkeypatch.setattr('sys.argv', ['eml_rename', '--save'])
    main()
    assert not path.exists(test_fs["mail1.eml"])
    assert not path.exists(test_fs["mail2.eml"])
    assert not path.exists(test_fs["mail3.eml"])
    assert path.exists(test_fs["fake.eml"])
    assert path.exists("20230915 0945 [jane.smith@example.org] Project Update EML Rename.eml")
    assert path.exists("20240522 1400 [info@conciencia-global.org] La urgente realidad del cambio climatico.eml")
    assert path.exists("20240522 1530 [skeptic@example.com] Re La urgente realidad del cambio climatico.eml")


def test_commons_ai_model_config(tmp_path, monkeypatch):
    from eml_rename.commons import get_ai_model, save_ai_model, DEFAULT_AI_MODEL
    mock_config = tmp_path / "config.ini"
    monkeypatch.setattr("eml_rename.commons.get_config_path", lambda: mock_config)

    # Defaults to DEFAULT_AI_MODEL when no config exists
    assert get_ai_model() == DEFAULT_AI_MODEL

    # Save model and verify it persists
    save_ai_model("custom-model-1")
    assert get_ai_model() == "custom-model-1"
    assert mock_config.exists()


def test_main_ai_models(monkeypatch, test_fs, capsys):
    monkeypatch.setattr("eml_rename.core.get_available_ai_models", lambda: ["model-a", "model-b"])
    monkeypatch.setattr("eml_rename.core.get_ai_model", lambda: "model-a")
    monkeypatch.setattr('sys.argv', ['eml_rename', '--ai_models'])
    main()
    captured = capsys.readouterr()
    assert "model-a" in captured.out
    assert "model-b" in captured.out


def test_main_ai_model_save_and_warning(tmp_path, monkeypatch, test_fs, capsys):
    mock_config = tmp_path / "config.ini"
    monkeypatch.setattr("eml_rename.commons.get_config_path", lambda: mock_config)
    monkeypatch.setattr("eml_rename.core.get_available_ai_models", lambda: ["gemini-2.5-flash"])

    # Test setting model via CLI saves to config
    monkeypatch.setattr('sys.argv', ['eml_rename', '--ai_model', 'new-model'])
    main()
    captured = capsys.readouterr()
    assert "new-model" in captured.out

    # Mock get_mail_subject_with_ia to ensure no AI call is made during --ai
    monkeypatch.setattr("eml_rename.emlfile.EmlFile.get_mail_subject_with_ia", lambda self: "Mocked AI Subject")

    # Test warning when unavailable model is used with --ai
    monkeypatch.setattr('sys.argv', ['eml_rename', '--ai'])
    main()
    captured2 = capsys.readouterr()
    assert "new-model" in captured2.out
    assert "gemini-2.5-flash" in captured2.out


def test_eml_rename_with_specific_file_and_directory(test_fs, monkeypatch):
    import os
    from pathlib import Path

    # Create a subfolder with an email
    subfolder = Path(test_fs["test_dir"]) / "subfolder"
    subfolder.mkdir()
    sub_email = subfolder / "custom_sub.eml"
    sub_email.write_text("""From: "Sub Test" <sub@example.org>
Date: Fri, 15 Sep 2023 10:00:00 +0200
Subject: Subfolder Email
Content-Type: text/plain; charset="utf-8"

Content inside subfolder.
""")

    # 1. Test passing a specific file path
    eml_rename(save=True, path=str(sub_email))
    assert not sub_email.exists()
    expected_sub_file = subfolder / "20230915 1000 [sub@example.org] Subfolder Email.eml"
    assert expected_sub_file.exists()

    # Create another email inside subfolder to test passing directory path
    sub_email2 = subfolder / "another.eml"
    sub_email2.write_text("""From: "Dir Test" <dir@example.org>
Date: Fri, 15 Sep 2023 11:00:00 +0200
Subject: Directory Test
Content-Type: text/plain; charset="utf-8"

Another inside subfolder.
""")

    # 2. Test passing directory path via CLI
    monkeypatch.setattr('sys.argv', ['eml_rename', '--save', str(subfolder)])
    main()
    assert not sub_email2.exists()
    expected_sub_file2 = subfolder / "20230915 1100 [dir@example.org] Directory Test.eml"
    assert expected_sub_file2.exists()


