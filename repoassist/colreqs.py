#!/usr/bin/env python
# -*- coding: utf-8 -*-


from pathlib import Path
from pipreqs import pipreqs

from . import settings
from . import logger
from . import prepare
from . import wizard
from . import clean


_logger = logger.get_logger(__name__)


def collect_reqs_min(config, prompt=False, cwd='.'):
    if prompt:
        _prompt_and_clean(cwd)
    reqs_equal = collect_reqs_specific(config, prompt=False, cwd=cwd)
    return _transform_to_min(reqs_equal)


def collect_reqs_latest(config, prompt=False, cwd='.'):
    if prompt:
        _prompt_and_clean(cwd)
    reqs_equal = collect_reqs_specific(config, prompt=False, cwd=cwd)
    return _transform_to_latest(reqs_equal)


def collect_reqs_specific(config, prompt=False, cwd='.'):
    if prompt:
        _prompt_and_clean(cwd)
    candidates = pipreqs.get_all_imports(str(cwd), extra_ignore_dirs=config.pipreqs_ignore)
    candidates = pipreqs.get_pkg_names(candidates)
    local = pipreqs.get_import_local(candidates)
    difference = [x for x in candidates
                  if x.lower() not in [z['name'].lower() for z in local]]
    imports = local + pipreqs.get_imports_info(difference)
    reqs = [f"{item['name']}=={item['version']}" for item in imports if 'INFO' not in item]
            
    return reqs


def _prompt_and_clean(cwd='.'):
    if wizard.choose_bool(__name__, 
                          'Run cleaner to clean generated directories? '
                          'Recommended to better requirements discovery.'):
        clean.clean(cwd)


def write_requirements(reqs, cwd='.'):
    file_path = Path(cwd) / settings.FileName.REQUIREMENTS
    file_exists = True if file_path.exists() else False
    
    with open(file_path, 'w') as file:
        for reg in reqs:
            file.write(f'{reg}\n')
            
        for def_req in settings.DEFAULT_REQUIREMENTS:
            write_def_req = True
            for req in reqs:
                if def_req in str(req):
                    write_def_req = False
                    
            if write_def_req:
                file.write(f'{def_req}\n')
            
        if file_exists:
            _logger.info(f'{settings.FileName.REQUIREMENTS} file updated.')
        else:
            _logger.info(f'{settings.FileName.REQUIREMENTS} file prepared.')
            
    return file_path


def write_requirements_dev(cwd='.'):
    file_path = Path(cwd) / settings.FileName.REQUIREMENTS_DEV
    
    if file_path.exists():
        _logger.warning(f'{settings.FileName.REQUIREMENTS_DEV} file already exists, not overwritten.')
    else:
        prepare.write_file_from_template(Path(settings.DirName.TEMPLATES) / file_path.name, 
                                         file_path, {}, cwd, verbose=False)
        _logger.info(f'{file_path.name} file prepared.')
    
    return file_path
            
            
def _transform_to_min(reqs):
    final_reqs = []
    for req in reqs:
        splitted = req.split('==')
        try:
            final_reqs.append(f'{splitted[0]}>={splitted[1]}')
        except IndexError:
            final_reqs.append(req) 
        
    return final_reqs


def _transform_to_latest(reqs):
    final_reqs = []
    for req in reqs:
        splitted = req.split('==')
        if splitted.__len__() == 1:
            splitted = req.split('>=')
        final_reqs.append(splitted[0]) 
        
    return final_reqs
