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