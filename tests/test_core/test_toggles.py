import pytest
from unittest import mock
from unittest.mock import call

from app.core.toggles import Toggles
from app.core import files
from app.core import toggles

#######################
# Fixures

@pytest.fixture(scope="function")
def toggles():
    return Toggles()

#######################
# Tests

def test_initialize__empty_files(toggles, mocker):
    mock_load_toggles = mocker.patch.object(files, "load_toggles")
    mock_load_toggles.return_value = {}
    toggles.initialize()

    assert True == toggles.run_script
    assert 1 == mock_load_toggles.call_count

def test_initialize(toggles, mocker):
    mock_load_toggles = mocker.patch.object(files, "load_toggles")
    mock_load_toggles.return_value = {
        'run_script': False,
    }
    toggles.initialize()

    assert False == toggles.run_script
    assert 1 == mock_load_toggles.call_count

def test_save_toggles(toggles, mocker):
    mock_save_toggles_file = mocker.patch.object(files, "save_toggles_file")
    
    toggles.run_script = "SOME VALUE"
    toggles.save_toggles()
    expected = [call({'run_script': 'SOME VALUE'})]
    assert expected == mock_save_toggles_file.mock_calls

def test_toggle_run_script(toggles, mocker):
    mock_save_toggles = mocker.patch.object(toggles, "save_toggles")
    
    toggles.run_script = True
    toggles.toggle_run_script()
    assert False == toggles.run_script
    assert 1 == mock_save_toggles.call_count

    toggles.toggle_run_script()
    assert True == toggles.run_script
    assert 2 == mock_save_toggles.call_count
