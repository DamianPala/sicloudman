#!/usr/bin/env python
# -*- coding: utf-8 -*-


import subprocess
import configparser
import platform
import tempfile
from pathlib import Path
from collections import namedtuple

from . import pygittools
from . import settings
from . import exceptions
from . import logger


_logger = logger.get_logger(__name__)


def execute_cmd(args, cwd='.'):
    try:
        p = subprocess.run(args,
                           check=True,
                           cwd=str(cwd),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           encoding='utf-8')
    except subprocess.CalledProcessError as e:
        raise exceptions.ExecuteCmdError(e.returncode, msg=e.output, logger=_logger)
    else:
        return p.stdout


def execute_cmd_and_split_lines_to_list(args, cwd='.'):
    try:
        p = subprocess.run(args,
                           check=True,
                           cwd=str(cwd),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           encoding='utf-8')
    except subprocess.CalledProcessError as e:
        raise exceptions.ExecuteCmdError(e.returncode, msg=e.output, logger=_logger)
    else:
        return p.stdout.split('\n')


def get_git_repo_tree(cwd='.'):
    return [Path(cwd).resolve() / path for path in pygittools.list_repo_tree(str(cwd))]


def read_repo_config_file(path):
    config = _prepare_config(path, [settings.REPO_CONFIG_SECTION_NAME], is_repo_config_file=True)
    _validate_config(config, extra_fields=settings.GEN_REPO_CONFIG_MANDATORY_FIELDS)
    return config

def get_repo_config_from_setup_cfg(path):
    config = _prepare_config(path, [settings.METADATA_CONFIG_SECTION_NAME, settings.GENERATOR_CONFIG_SECTION_NAME])
    _validate_config(config)
    return config


def _prepare_config(path, sections, is_repo_config_file=False):
    raw_config = _read_config_file(path, is_repo_config_file)
    config_dict = {}

    for section in sections:
        for field, value in raw_config[section].items():
            config_dict.update(_parse_config_field(field, value))

    _remove_junk_fields(config_dict)

    try:
        config = settings.Config(**config_dict)
    except TypeError as e:
        raise exceptions.ConfigError(f'Invalid config file structure: {str(e)}', _logger)

    return config


def _read_config_file(path, is_repo_config_file=False):
    def is_list_option(option):
        if option and '"' not in option[0]:
            return True if '\n' in option[0] else False

    config_dict = {}
    filepath = Path(path)
    
    if not filepath.exists():
        raise exceptions.FileNotFoundError(f'{filepath.name} file not found!', _logger)
    
    if is_repo_config_file:
        with open(filepath, 'r', encoding='utf-8') as file:
            config_string = f'[{settings.REPO_CONFIG_SECTION_NAME}]\n' + file.read()

        config = configparser.RawConfigParser()
        config.read_string(config_string)
    else:
        config = configparser.ConfigParser()
        config.read(filepath, 'utf-8')

    for section in config.sections():
        config_dict[section] = {}

        for option in config.options(section):
            option_val = config.get(section, option)
            if is_list_option(option_val):
                config_dict[section][option] = list(filter(None, option_val.split('\n')))
            else:
                config_dict[section][option] = option_val

    return config_dict


def _parse_config_field(field, value):
    if not isinstance(value, list):
        try:
            new_value = str2bool(value)
        except exceptions.ValueError:
            new_value = value
    else:
        new_value = value

    if field == 'name':
        new_field = 'project_name'
    elif field == 'summary':
        new_field = 'short_description'
    else:
        new_field = field.replace('-', '_')

    return {new_field: new_value}


def _remove_junk_fields(config_dict):
    fields_to_remove = [field for field in config_dict if field not in settings.Config.get_fields()]

    for field in fields_to_remove:
        config_dict.pop(field)


def _validate_config(config, extra_fields=[]):
    for field in extra_fields:
        if getattr(config, field) == '' or getattr(config, field) is None:
            raise exceptions.ConfigError(f"The {field.replace('_', '-')} field is empty in the config!", _logger)

    for field, value in config.__dict__.items():
        if field not in config.get_default_fields() and value == '':
            raise exceptions.ConfigError(f"The {field.replace('_', '-')} field is empty in the config!", _logger)
        
        invalid_value_msg = f"The {field.replace('_', '-')} field has invalid value: {value} in the config!"
        if field == 'project_type':
            valid_values = [item.value for item in settings.ProjectType]
            if value not in valid_values:
                raise exceptions.ConfigError(invalid_value_msg, _logger)
        elif field == 'changelog_type' or field == 'authors_type':
            if field == 'changelog_type':
                valid_values = [item.value for item in settings.ChangelogType]
            if field == 'authors_type':
                valid_values = [item.value for item in settings.AuthorsType]
            if value not in valid_values:
                raise exceptions.ConfigError(invalid_value_msg, _logger)
        elif extra_fields and ((field == 'is_cloud') or (field == 'is_sample_layout')):
            valid_values = [True, False]
            if value not in valid_values:
                raise exceptions.ConfigError(invalid_value_msg, _logger)


def str2bool(string):
    if string.lower() in ['yes', 'true', 't', 'y', '1']:
        return True
    elif string.lower() in ['no', 'false', 'f', 'n', '0']:
        return False
    else:
        raise exceptions.ValueError('No boolean', _logger)


def get_module_name_with_suffix(module_name):
    return f'{module_name}.py'


def get_project_module_path(config, cwd='.'):
    path = Path(cwd) / f'{config.project_name}.py'

    if not path.exists():
        raise exceptions.FileNotFoundError(f'File {path.relative_to(cwd.resolve())} not found. '
                                           f'Please check repository and a project_name field in '
                                           f'{settings.FileName.SETUP_CFG} file', _logger)

    return path


def get_dir_from_arg(prompt_dir):
    return (Path().cwd() / str(prompt_dir).strip('\"')).resolve()


def get_latest_file(path):
    if path:
        path = Path(path)
        if path.exists() and path.is_dir():
            FileTime = namedtuple('FileTime', ['path', 'mtime'])
            files_list = [FileTime(item, Path(item).stat().st_mtime) for item in path.iterdir() if item.is_file()]

            if files_list:
                return max(files_list, key=lambda x: x.mtime).path

    return None


def get_latest_tarball(path):
    if path:
        path = Path(path)
        if path.exists() and path.is_dir():
            FileTime = namedtuple('FileTime', ['path', 'mtime'])
            files_list = [FileTime(item, Path(item).stat().st_mtime) for item in path.iterdir() \
                          if item.is_file() \
                          and (item.suffixes.__len__() >= 2) \
                          and (item.suffixes[-2] == settings.TARBALL_SUFFIX)]

            if files_list:
                return max(files_list, key=lambda x: x.mtime).path

    return None


def get_rel_path(path, cwd):
    return Path(path).resolve().relative_to(Path(cwd).resolve())


def input_with_editor(msg=''):
    platform_name = platform.system()
    if platform_name == 'Windows':
        cmd = 'start'
        options = ['/WAIT']
    elif platform_name == 'Linux':
        cmd = 'xdg-open'
        options = []
    elif platform_name == 'Darwin':
        cmd = 'open' 
        options = []
    else:
        cmd = 'open'
        options = []
        
    fd, filepath = tempfile.mkstemp(suffix='.txt', text=True)
    filepath = Path(filepath)
    
    with open(fd, 'wt', encoding='utf-8') as file:
        file.write(msg)
    
    cmd_list = [cmd] + options + [filepath.name]
        
    try:
        subprocess.run(cmd_list, 
                       cwd=filepath.parent, 
                       shell=True, 
                       check=True, 
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, 
                       encoding='utf-8')
    except subprocess.CalledProcessError as e:
        raise exceptions.RuntimeError(f'Editor open error occured: {e.output}', _logger)
    else:
        return filepath.read_text(encoding='utf-8')
    finally:
        filepath.unlink()
