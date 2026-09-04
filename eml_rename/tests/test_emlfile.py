from datetime import datetime
from zoneinfo import ZoneInfo
from eml_rename.tests.test_core import test_fs
from eml_rename.emlfile import EmlFile
from os import path
import pytest




def test_emlfile(test_fs, monkeypatch):
    # Mock get_system_timezone_name to return a canonical timezone for testing.
    # This is necessary because eml_rename.commons.get_system_timezone_name()
    # returns time.tzname[0] (e.g., "CET"), which is an abbreviation and
    # not a valid key for zoneinfo.ZoneInfo directly.
    monkeypatch.setattr("eml_rename.emlfile.get_system_timezone_name", lambda: "Europe/Berlin")

    eml=EmlFile(test_fs["mail1.eml"], 140, ia=False, force=False, ia_delay=2) # Updated constructor call
    assert eml.system_timezone=="Europe/Berlin" # Now asserts against the mocked canonical name
    assert eml.file_encoding=="ascii"
    assert eml.dt== datetime(2023, 9, 15, 9, 45, tzinfo=ZoneInfo(key='Europe/Berlin')) # Use canonical name
    assert eml.from_=="jane.smith@example.org"
    assert eml.subject=="Project Update EML Rename"
    assert eml.final_name()=="20230915 0945 [jane.smith@example.org] Project Update EML Rename.eml"
    assert eml.will_be_renamed(False)
    assert eml.filename_format_detected() is False
    assert path.exists(test_fs["mail1.eml"])
    assert not path.exists(eml.final_name())
    eml.write(False)
    assert not path.exists(test_fs["mail1.eml"])
    assert path.exists(eml.final_name())


def test_emlfile_utf7_and_parse_error(tmp_path, monkeypatch):
    monkeypatch.setattr("eml_rename.emlfile.get_system_timezone_name", lambda: "Europe/Berlin")

    # Email file containing + shift sequences that might trigger UTF-7 or decode issues
    eml_path = tmp_path / "utf7_test.eml"
    eml_path.write_bytes(b"From: test@example.com\r\nDate: Fri, 15 Sep 2023 09:45:00 +0200\r\nSubject: Test +ABC\r\n\r\nBody")

    eml = EmlFile(str(eml_path), 140, ia=False, force=False, ia_delay=2)
    # Ensure it parsed without UnboundLocalError or crash
    assert isinstance(eml.error_message, list)
    assert eml.subject == "Test +ABC"

    # Now simulate a case where file_encoding is set to utf-7 and decode fails during get_mail_subject
    eml.file_encoding = "utf-7"
    # Even if an error happens when reading, it shouldn't raise UnboundLocalError
    subject = eml.get_mail_subject()
    assert isinstance(eml.error_message, list)
    assert isinstance(subject, str)


def test_remove_illegal_chars():
    eml = EmlFile.__new__(EmlFile)
    assert eml.remove_illegal_chars("") == ""
    assert eml.remove_illegal_chars("Test.") == "Test"
    assert eml.remove_illegal_chars("Hello: World?") == "Hello World"


def test_get_mail_subject_with_ia_mocked(monkeypatch):
    from unittest.mock import MagicMock
    from eml_rename.emlfile import EmlFile

    eml = EmlFile.__new__(EmlFile)
    eml.body = "Sample email body content"
    eml.google_api_key = "dummy-api-key"
    eml.error_message = []
    eml.ai_model = "gemini-2.5-flash"

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Mocked AI Summary"
    mock_client.models.generate_content.return_value = mock_response

    monkeypatch.setattr("google.genai.Client", lambda api_key: mock_client)

    subject = eml.get_mail_subject_with_ia()
    assert subject == "Mocked AI Summary"
    assert mock_client.models.generate_content.called
    assert mock_client.models.generate_content.call_args.kwargs["model"] == "gemini-2.5-flash"