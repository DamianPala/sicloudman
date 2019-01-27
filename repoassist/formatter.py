#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import autopep8
import webbrowser
import tempfile
from pathlib import Path

from . import exceptions
from . import utils
from . import settings
from . import logger


_logger = logger.get_logger(__name__)


def format_file(path, with_meld=True, cwd='.'):
    _logger.info(f'Format the file: {path} using {settings.Tools.FILE_FORMATTER} '
                 f'with merge mode in {settings.Tools.MERGE_TOOL}')
    
    
    path = Path(cwd) / path
    formatted_file_descriptor, formated_file_path = tempfile.mkstemp(prefix=f'{path.stem}_', suffix='.py', text=True)
    os.close(formatted_file_descriptor)
    formated_file_path = Path(formated_file_path)
    setup_file_path = (Path(cwd) / settings.FileName.SETUP_CFG).resolve()
    if path.is_file():
        with open(formated_file_path, 'w') as file:
            options = autopep8.parse_args(['--global-config='+str(setup_file_path), str(path)], apply_config=True)
            autopep8.fix_file(str(path), output=file, options=options)
    else:
        raise exceptions.NotAFileError('Path must point to a file!', _logger)
    
    if with_meld:
        utils.execute_cmd(['meld', str(path), str(path), str(formated_file_path), '-o', str(path)], str(cwd))
        formated_file_path.unlink()
    else:
        _logger.info(f'Formatted file has ben written to {formated_file_path}')
    
    _logger.info('Lint formatted file and show report')
    try:
        utils.execute_cmd([settings.Tools.LINTER, str(path), f'--config={setup_file_path}'], cwd)
    except exceptions.ExecuteCmdError as e:
        print(e)
    else:
        _logger.info('Linter report is empty - file ok')
        
        
def coverage_report(cwd='.'):
    _logger.info('Open the coverage html report in the default system browser.')
    
    path_to_report = (Path(cwd).resolve() / settings.DirName.HTMLCOV / 'index.html')
    if not path_to_report.exists():
        raise exceptions.FileNotFoundError('Coverage html report file not exists!', _logger)
    
    url = f'file://{path_to_report.as_posix()}'
    webbrowser.open(url)
