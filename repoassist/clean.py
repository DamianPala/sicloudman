#!/usr/bin/env python
# -*- coding: utf-8 -*-


import stat
import shutil
from pathlib import Path

from . import settings
from . import exceptions
from . import logger


_logger = logger.get_logger(__name__)


def clean(cwd='.'):
    _clean_files(cwd)
    _clean_dirs(cwd)


def _clean_files(cwd, files_list=None):
    files_list = settings.FILES_TO_CLEAN if files_list is None else files_list
    for file_pattern in files_list:
        files_paths = sorted(Path(cwd).glob(file_pattern))
        for file_path in files_paths:
            _logger.info(f'Remove file: {file_path.relative_to(Path(cwd).resolve())}')
            file_path.unlink()


def _clean_dirs(cwd, dirs_list=None):
    dirs_list = settings.DIRS_TO_CLEAN if dirs_list is None else dirs_list
    for directory in dirs_list:
        if directory['flag'] == '.':
            dirs_paths = sorted(Path(cwd).glob(directory['name']))
        elif directory['flag'] == 'r':
            dirs_paths = sorted(Path(cwd).rglob(directory['name']))
        else:
            raise exceptions.ValueError(f'Unknown remove flag {directory["flag"]}', _logger)

        for dir_path in dirs_paths:
            if dir_path.is_dir():
                _logger.info(f'Remove directory: {dir_path.relative_to(Path(cwd).resolve())}')
                shutil.rmtree(dir_path, ignore_errors=False, onerror=_error_remove_readonly)


def _error_remove_readonly(_action, name, _exc):
    Path(name).chmod(stat.S_IWRITE)
    Path(name).unlink()
