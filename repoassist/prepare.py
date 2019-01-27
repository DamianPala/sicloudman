#!/usr/bin/env python
# -*- coding: utf-8 -*-


import shutil
import jinja2
from pathlib import Path
from collections import namedtuple

from . import settings
from . import PARDIR
from . import exceptions
from . import pygittools
from . import logger
from . import utils
from . import wizard


_logger = logger.get_logger(__name__)


def generate_repo(config, cwd='.', options=None):
    _logger.info('Generate repository files...')

    paths = []

    Path(cwd).mkdir(parents=True, exist_ok=True)
    
    if config.is_git:
        _init_git_repo(config, cwd)
        
    paths.extend(_generate_repo_dirs(config, cwd))
    if config.project_type == settings.ProjectType.PACKAGE.value:
        if options.sample_layout:
            config.entry_point = settings.PACKAGE_ENTRY_POINT.replace(settings.ENTRY_POINT_PLACEHOLDER,
                                                                      config.project_name)
        paths.extend(_generate_repo_files(settings.PACKAGE_REPO_FILES_TO_GEN, config, cwd, options))
    elif config.project_type == settings.ProjectType.MODULE.value:
        if options.sample_layout:
            config.entry_point = settings.MODULE_ENTRY_POINT.replace(settings.ENTRY_POINT_PLACEHOLDER, 
                                                                     config.project_name)
        paths.extend(_generate_repo_files(settings.MODULE_REPO_FILES_TO_GEN, config, cwd, options))
    else:
        raise exceptions.RuntimeError('Unknown project type.', _logger)
    paths.extend(_generate_repoasist(config, cwd, options).paths)
    
    if config.is_git:
        for path in paths:
            try:
                pygittools.add(path, cwd)
            except pygittools.PygittoolsError as e:
                if 'following paths are ignored' not in e.__str__():
                    raise exceptions.GitAddError(f'Error occured while adding file '
                                                 f'{utils.get_rel_path(path, cwd)} into repository tree: {e}', 
                                                 _logger)

        _logger.info('Generated files added into repository tree.')

    _logger.info(f'Repository files generated in directory: {cwd}')

    return paths


def _init_git_repo(config, cwd):
    if config.git_origin:
        try:
            pygittools.clone(config.git_origin, cwd.parent)
        except pygittools.PygittoolsError as e:
            raise exceptions.RuntimeError(f'Git repository clone error: {e}', _logger)
    else:
        try:
            pygittools.init(cwd)
        except pygittools.PygittoolsError as e:
            raise exceptions.RuntimeError(f'Git repository initializing error: {e}', _logger)
    

def _generate_repo_dirs(config, cwd):
    paths = []

    for dirname in settings.REPO_DIRS_TO_GEN:
        paths.extend(_generate_directory(dirname, cwd))
        
    if config.project_type == settings.ProjectType.PACKAGE.value:
        paths.extend(_generate_directory(config.project_name, cwd))
        
    return paths


def _generate_directory(dirname, cwd):
    try:
        Path(Path(cwd) / dirname).mkdir()
    except FileExistsError:
        _logger.warning(f'{dirname} directory exists, not overwritten.')
        return []
    else:
        _logger.info(f'{dirname} directory generated.')
        return [Path(cwd) / dirname]
        


def generate_repo_config(cwd='.', options=None):
    _logger.info(f'Creating the predefined repository config file '
                 f'{settings.FileName.REPO_CONFIG} in your current working directory...')
    path = _copy_template_file(settings.FileName.REPO_CONFIG, 
                               Path(cwd) / settings.FileName.REPO_CONFIG, cwd, options, verbose=False)
    _logger.info('Predefined repository config file created. Please fill it with relevant data '
                 'and try to generate repository again!')
    
    return path
    
    
def _generate_repo_files(files_list, config, cwd, options=None):
    paths = []

    for file in files_list:
        src = file.src
        dst = Path(cwd) / file.dst
        
        if not file.is_sample or (file.is_sample and config.is_sample_layout):
            if not options.cloud and (src.name == settings.FileName.CLOUD_CREDENTIALS):
                continue
            
            if settings.PROJECT_NAME_PATH_PLACEHOLDER in str(dst):
                dst = Path(str(dst).replace(settings.PROJECT_NAME_PATH_PLACEHOLDER, config.project_name))
                
            src_parents = [item for item in src.parents]
            if src_parents.__len__() >= 2 and (str(src_parents[-2]) == settings.DirName.TEMPLATES):
                is_from_template = True
            else:
                is_from_template = False
            
            if is_from_template:
                paths.extend(write_file_from_template(src, dst, config.__dict__, cwd, options))
            else:
                paths.extend(_generate_empty_file(dst, cwd, options))

    return paths


def update_repoassist(config, cwd, add_to_tree=None, options=None):
    new_files = _generate_repoasist(config, cwd, options=options).new_files
    
    if new_files.__len__() > 0 and pygittools.is_work_tree(cwd):
        if add_to_tree is None:
            add_to_tree = wizard.choose_bool(__name__, 'There are new files in repoassist. '
                                             'Add them to the repository tree?')
    
        for file in new_files:
            if add_to_tree:
                pygittools.add(file, cwd)
                _logger.info(f'New {utils.get_rel_path(file, cwd)} file added to the repository tree.')
            else:
                _logger.info(f'New {utils.get_rel_path(file, cwd)} file added to the repoassist.')
                
    return new_files


def _generate_repoasist(config, cwd, options=None):
    paths = []
    new_files = []
    
    if options is None:
        options = settings.Options()
        
    options.force = True
    
    for file in settings.REPOASSIST_FILES:
        src = Path(PARDIR) / file.src
        dst = Path(cwd) / file.dst
        is_templ = file.is_templ
        
        if not dst.exists():
            new_files.append(dst)
        
        if is_templ:
            paths.extend(write_file_from_template(src, dst, config.__dict__, cwd, options=options))
        else:
            paths.extend(_copy_file_from(src, dst, cwd, options=options))
    
    return namedtuple('GeneratedPaths', ['paths', 'new_files'])(paths, new_files)
    

def _generate_empty_file(path, cwd, options=None):
    try:
        if options and options.force:
            with open(Path(path), 'w'):
                pass
        else:
            with open(Path(path), 'x'):
                pass
    except FileExistsError:
        _logger.warning(f'{utils.get_rel_path(path, cwd)} file exists, not overwritten.')
        return []
    else:
        _logger.info(f'{utils.get_rel_path(path, cwd)} file generated.')
        return [path]


def _copy_file(filename, dst, cwd, options=None, verbose=True):
    return _copy_file_from(PARDIR / filename, dst, cwd, options, verbose)


def _copy_template_file(filename, dst, cwd, options=None, verbose=True):
    filename = f'{filename}{settings.JINJA2_TEMPLATE_EXT}'
    return _copy_file_from(PARDIR / settings.DirName.TEMPLATES / filename, dst, cwd, options, verbose)


def _copy_file_from(src, dst, cwd, options=None, verbose=True):
    if (options and options.force) or (not Path(dst).exists()):
        file_exists = Path(dst).exists()
        shutil.copy(src, dst)
        
        if verbose:
            if file_exists:
                _logger.info(f'{utils.get_rel_path(dst, cwd)} file updated.')
            else:
                _logger.info(f'{utils.get_rel_path(dst, cwd)} file generated.')

        return [dst]
    else:
        if verbose:
            _logger.warning(f'{utils.get_rel_path(dst, cwd)} file exists, not overwritten.')

        return []


def write_file_from_template(src, dst, keywords, cwd, options=None, verbose=True):
    src = src.parent / f'{src.name}{settings.JINJA2_TEMPLATE_EXT}'
    if (options and options.force) or (not Path(dst).exists()):
        file_exists = Path(dst).exists()
        templateLoader = jinja2.FileSystemLoader(searchpath=str(Path(PARDIR) / src.parent))
        templateEnv = jinja2.Environment(loader=templateLoader,
                                         trim_blocks=True,
                                         lstrip_blocks=True,
                                         newline_sequence='\r\n',
                                         keep_trailing_newline=True)
        template = templateEnv.get_template(src.name)
        template.stream(keywords, options=options).dump(str(dst))

        if verbose:
            if file_exists:
                _logger.info(f'{utils.get_rel_path(dst, cwd)} file updated.')
            else:
                _logger.info(f'{utils.get_rel_path(dst, cwd)} file generated.')

        return [dst]
    else:
        if verbose:
            _logger.warning(f'{utils.get_rel_path(dst, cwd)} file exists, not overwritten.')

        return []
