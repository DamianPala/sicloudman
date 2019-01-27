#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import stat
import time
import pytest
import shutil
import tempfile
from pathlib import Path
from pprint import pprint

import sicloudman


RUN_ALL_TESTS = False


def _error_remove_readonly(_action, name, _exc):
    Path(name).chmod(stat.S_IWRITE)
    Path(name).unlink()


@pytest.fixture()
def cwd():
    workspace_path = Path(tempfile.mkdtemp())
    yield workspace_path
    if getattr(sys, 'last_value'):
        print(f'Tests workspace path: {workspace_path}')
    else:
        shutil.rmtree(workspace_path, ignore_errors=False, onerror=_error_remove_readonly)
        

@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_get_latest_file_with_keyword_SHOULD_return_none_if_path_not_exists():
    assert sicloudman.CloudManager.get_latest_file_with_keyword('some_path', '.txt') == None


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_get_latest_file_with_keyword_SHOULD_return_none_if_path_is_empty(cwd):
    assert sicloudman.CloudManager.get_latest_file_with_keyword(cwd, '.txt') == None
    
    
@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_get_latest_file_with_keyword_SHOULD_return_none_if_path_is_file(cwd):
    cwd.touch('test.txt')
    assert sicloudman.CloudManager.get_latest_file_with_keyword(cwd / 'test.txt', '.txt') == None


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_get_latest_file_with_keyword_SHOULD_return_none_if_does_not_contain_files(cwd):
    (cwd / 'dir1').mkdir()
    (cwd / 'dir2').mkdir()
    assert sicloudman.CloudManager.get_latest_file_with_keyword(cwd / 'test.txt', '.txt') == None


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_get_latest_file_with_keyword_SHOULD_get_latest_file_properly_by_extension(cwd):
    Path(Path(cwd) / 'test1.txt').touch()
    Path(Path(cwd) / 'test1.ini').touch()
    time.sleep(1)
    Path(Path(cwd) / 'test2.txt').touch()
    Path(Path(cwd) / 'test2.cfg').touch()
    time.sleep(1)
    Path(Path(cwd) / 'test3.txt').touch()
    Path(Path(cwd) / 'test3.py').touch()
    time.sleep(1)
    Path(Path(cwd) / 'test4.py').touch()
    
    assert sicloudman.CloudManager.get_latest_file_with_keyword(cwd, '.txt') == Path(cwd) / 'test3.txt'


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_get_latest_file_with_keyword_SHOULD_get_latest_file_properly_by_keyword(cwd):
    
    Path(Path(cwd) / 'test_release_1.txt').touch()
    Path(Path(cwd) / 'test_client_1.txt').touch()
    time.sleep(1)
    Path(Path(cwd) / 'test_release_2.txt').touch()
    Path(Path(cwd) / 'test_client_2.txt').touch()
    time.sleep(1)
    Path(Path(cwd) / 'test_client_3.txt').touch()
    
    assert sicloudman.CloudManager.get_latest_file_with_keyword(cwd, '_release') == Path(cwd) / 'test_release_2.txt'
    

@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_touch_credentials_WHEN_no_keywords(cwd):
    file_path = sicloudman.CloudManager.touch_credentials(cwd)
    file_content = file_path.read_text()
    print(file_content)
    
    assert file_path.read_text() == sicloudman.CLOUD_CREDENTIALS_FILE_TEMPLATE
    

# @pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_touchand_read_credentials_WHEN_keywords(cwd):
    file_path = sicloudman.CloudManager.touch_credentials(cwd)
    file_content = file_path.read_text()
    print(file_content)
    
    assert file_path.read_text() == sicloudman.CLOUD_CREDENTIALS_FILE_TEMPLATE
