from datetime import datetime
from zoneinfo import ZoneInfo
from test_core import test_fs
from eml_rename.emlfile import EmlFile
from os import path




def test_emlfile(test_fs):

    eml=EmlFile(test_fs["mail1.eml"], 140, False)
    assert eml.system_timezone=="UTC"
    assert eml.file_encoding=="ascii"
    assert eml.dt== datetime(2023, 9, 15, 7, 45, tzinfo=ZoneInfo(key='UTC')) 
    assert eml.from_=="jane.smith@example.org"
    assert eml.subject=="Project Update EML Rename"
    assert eml.final_name()=="20230915 0745 [jane.smith@example.org] Project Update EML Rename.eml"
    assert eml.will_be_renamed(False)
    assert eml.filename_format_detected() is False
    assert path.exists(test_fs["mail1.eml"])
    assert not path.exists(eml.final_name())
    eml.write(False)
    assert not path.exists(test_fs["mail1.eml"])
    assert path.exists(eml.final_name())