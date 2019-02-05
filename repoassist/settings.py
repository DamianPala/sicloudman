#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime
from enum import Enum
from pathlib import Path
import dataclasses
from collections import namedtuple

from . import (__version__, MIN_PYTHON)


SUGGESTED_INITIAL_RELEASE_TAG = '0.1.0'
EXAMPLE_RELEASE_TAG = '1.17.3rc2'
TIP_MSG_MARK = '# [TIP]: '


class Options:
    force = False
    cloud = False
    sample_layout = False
    project_type = None


class ProjectType(Enum):
    PACKAGE = 'package'
    MODULE = 'module'
    

class ChangelogType(Enum):
    GENERATED = 'generated'
    PREPARED = 'prepared'


class AuthorsType(Enum):
    GENERATED = 'generated'
    PREPARED = 'prepared'


class DirName():
    TEMPLATES = 'templates'
    TESTS = 'tests'
    DOCS = 'docs'
    DISTRIBUTION = 'dist'
    REPOASSIST = 'repoassist'
    GIT = '.git'
    RELEASE = 'release'
    HTMLCOV = 'htmlcov'


REPO_CONFIG_SECTION_NAME = 'repoconfig'
METADATA_CONFIG_SECTION_NAME = 'metadata'
GENERATOR_CONFIG_SECTION_NAME = 'pyrepogen'
    
TESTS_PATH = './' + DirName.TESTS
PROJECT_NAME_PATH_PLACEHOLDER = '<project_name>'
TEMPLATES_PACKAGE_PATH = 'templates/package'
TEMPLATES_PACKAGE_TESTS_PATH = 'templates/package/tests'
TEMPLATES_MODULE_PATH = 'templates/module'

REPOASSIST_VERSION = f'{DirName.REPOASSIST}_version'
AUTOMATIC_RELEASE_COMMIT_MSG = 'Automatic update of release data files.'
LICENSE = 'MIT'
RELEASE_PACKAGE_SUFFIX = '_release'
JINJA2_TEMPLATE_EXT = '.j2'
TARBALL_SUFFIX = '.tar'

ENTRY_POINT_PLACEHOLDER = '<project_name>'
MODULE_ENTRY_POINT = f'{ENTRY_POINT_PLACEHOLDER} = {ENTRY_POINT_PLACEHOLDER}:main'
PACKAGE_ENTRY_POINT = f'{ENTRY_POINT_PLACEHOLDER} = {ENTRY_POINT_PLACEHOLDER}.cli:main'


class FileName():
    REPO_CONFIG = 'gen_repo.cfg'
    SETUP_CFG = 'setup.cfg'
    SETUP_PY = 'setup.py'
    CHANGELOG = 'CHANGELOG.md'
    CHANGELOG_GENERATED = 'CHANGELOG_generated.md'
    CHANGELOG_PREPARED = 'CHANGELOG_prepared.md'
    AUTHORS = 'AUTHORS'
    AUTHORS_PREPARED = 'AUTHORS_prepared.md'
    GITIGNORE = '.gitignore'
    README = 'README.md'
    TODO = 'TODO.md'
    LICENSE = 'LICENSE'
    MAKEFILE = 'Makefile'
    CONFTEST = 'conftest.py'
    MODULE_SAMPLE = 'sample.py'
    MODULE_SAMPLE_TEST_FILENAME = 'sample_test.py'
    TOX = 'tox.ini'
    PYINIT = '__init__.py'
    MAIN = '__main__.py'
    CLI = 'cli.py'
    PACKAGE_SAMPLE_MODULE = 'modulo.py'
    PACKAGE_SAMPLE_TEST = 'modulo_test.py'
    SAMPLE_MODULE = 'module.py'
    REPOASSIST_CLI = 'repoassist_cli.py'
    COLREQS = 'colreqs.py'
    SETTINGS = 'settings.py'
    LOGGER = 'logger.py'
    RELEASE = 'release.py'
    EXCEPTIONS = 'exceptions.py'
    UTILS = 'utils.py'
    PYGITTOOLS = 'pygittools.py'
    CLOUD = 'cloud.py'
    WIZARD = 'wizard.py'
    FORMATTER = 'formatter.py'
    PREPARE = 'prepare.py'
    CLEAN = 'clean.py'
    CLOUD_CREDENTIALS = 'cloud_credentials.txt'
    REQUIREMENTS = 'requirements.txt'
    REQUIREMENTS_DEV = 'requirements-dev.txt'
    REPOASSIST_README = 'REPOASSIST_README.md'


class Tools():
    FILE_FORMATTER = 'autopep8'
    LINTER = 'flake8'
    MERGE_TOOL = 'Meld Merge'
    PYTHON = 'python'


@dataclasses.dataclass
class Config():
    project_type : str
    project_name : str
    author : str
    author_email : str
    short_description : str
    changelog_type : str
    authors_type : str
    repo_name : str = '.'
    is_cloud : bool = None
    is_sample_layout : bool = None
    maintainer : str = ''
    maintainer_email : str = ''
    home_page : str = ''
    year : str = str(datetime.datetime.now().year)
    min_python : str = f'{MIN_PYTHON[0]}.{MIN_PYTHON[1]}'
    tests_path : str = TESTS_PATH
    description_file : str = FileName.README
    tests_dirname : str = DirName.TESTS
    repoassist_name : str = DirName.REPOASSIST
    license : str = LICENSE
    generator_section : str = GENERATOR_CONFIG_SECTION_NAME
    metadata_section : str = METADATA_CONFIG_SECTION_NAME
    keywords : list = None
    is_git : bool = False
    git_origin : str = ''
    pipreqs_ignore : list = None
    
    def __post_init__(self):
        setattr(self, REPOASSIST_VERSION, __version__)
    
    @staticmethod
    def get_fields():
        return [field.name for field in dataclasses.fields(Config)]
    
    @staticmethod
    def get_mandatory_fields():
        return [field.name for field in dataclasses.fields(Config) if field.default == dataclasses.MISSING]
    
    @staticmethod
    def get_default_fields():
        return dir(Config)


DEMO_CONFIG = Config(
    repo_name='demo_repo',
    project_type=ProjectType.PACKAGE.value,
    project_name='demo_project',
    author='You',
    author_email='you@mail.com',
    short_description='This is demo project for demo purposes.',
    changelog_type=ChangelogType.GENERATED,
    authors_type=AuthorsType.GENERATED,
    is_cloud=True,
    is_sample_layout=True
)


FileGenEntry = namedtuple('FileGeneratorEntry', 'src dst is_sample')

MODULE_REPO_FILES_TO_GEN = [
    FileGenEntry(src=Path('') / FileName.README, dst=Path('.') / FileName.README, is_sample=False),
    FileGenEntry(src=Path('') / FileName.TODO, dst=Path('.') / FileName.TODO, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.CONFTEST, dst=Path('.') / FileName.CONFTEST, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.GITIGNORE, dst=Path('.') / FileName.GITIGNORE, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.TOX, dst=Path('.') / FileName.TOX, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.MAKEFILE, dst=Path('.') / FileName.MAKEFILE, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.LICENSE, dst=Path('.') / FileName.LICENSE, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.SETUP_CFG, dst=Path('.') / FileName.SETUP_CFG, is_sample=False),
    FileGenEntry(src=Path(TEMPLATES_PACKAGE_PATH) / FileName.SETUP_PY, dst=Path('.') / FileName.SETUP_PY, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.CLOUD_CREDENTIALS, dst=Path('.') / FileName.CLOUD_CREDENTIALS, is_sample=False),
    FileGenEntry(src=Path(TEMPLATES_MODULE_PATH) / FileName.REQUIREMENTS, dst=Path('.') / FileName.REQUIREMENTS, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.REQUIREMENTS_DEV, dst=Path('.') / FileName.REQUIREMENTS_DEV, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.SAMPLE_MODULE, dst=Path('.') / DirName.TESTS / FileName.PYINIT, is_sample=False),
    FileGenEntry(src=Path(TEMPLATES_MODULE_PATH) / FileName.MODULE_SAMPLE, dst=Path('.') / (PROJECT_NAME_PATH_PLACEHOLDER + '.py'), is_sample=True),
    FileGenEntry(src=Path(TEMPLATES_MODULE_PATH) / FileName.MODULE_SAMPLE_TEST_FILENAME, dst=Path('.') / DirName.TESTS / (PROJECT_NAME_PATH_PLACEHOLDER + '_test.py'), is_sample=True),
]

PACKAGE_REPO_FILES_TO_GEN = [
    FileGenEntry(src=Path('') / FileName.README, dst=Path('.') / FileName.README, is_sample=False),
    FileGenEntry(src=Path('') / FileName.TODO, dst=Path('.') / FileName.TODO, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.CONFTEST, dst=Path('.') / FileName.CONFTEST, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.GITIGNORE, dst=Path('.') / FileName.GITIGNORE, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.TOX, dst=Path('.') / FileName.TOX, is_sample=False),
    FileGenEntry(src=Path(TEMPLATES_PACKAGE_PATH) / FileName.PYINIT, dst=Path('.') / PROJECT_NAME_PATH_PLACEHOLDER / FileName.PYINIT, is_sample=True),
    FileGenEntry(src=Path(TEMPLATES_PACKAGE_PATH) / FileName.MAIN, dst=Path('.') / PROJECT_NAME_PATH_PLACEHOLDER / FileName.MAIN, is_sample=True),
    FileGenEntry(src=Path(TEMPLATES_PACKAGE_PATH) / FileName.CLI, dst=Path('.') / PROJECT_NAME_PATH_PLACEHOLDER / FileName.CLI, is_sample=True),
    FileGenEntry(src=Path(TEMPLATES_PACKAGE_PATH) / FileName.PACKAGE_SAMPLE_MODULE, dst=Path('.') / PROJECT_NAME_PATH_PLACEHOLDER / FileName.PACKAGE_SAMPLE_MODULE, is_sample=True),
    FileGenEntry(src=Path(TEMPLATES_PACKAGE_TESTS_PATH) / FileName.PYINIT, dst=Path('.') / DirName.TESTS / FileName.PYINIT, is_sample=True),
    FileGenEntry(src=Path(TEMPLATES_PACKAGE_TESTS_PATH) / FileName.PACKAGE_SAMPLE_TEST, dst=Path('.') / DirName.TESTS / FileName.PACKAGE_SAMPLE_TEST, is_sample=True),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.MAKEFILE, dst=Path('.') / FileName.MAKEFILE, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.LICENSE, dst=Path('.') / FileName.LICENSE, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.SETUP_CFG, dst=Path('.') / FileName.SETUP_CFG, is_sample=False),
    FileGenEntry(src=Path(TEMPLATES_PACKAGE_PATH) / FileName.SETUP_PY, dst=Path('.') / FileName.SETUP_PY, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.CLOUD_CREDENTIALS, dst=Path('.') / FileName.CLOUD_CREDENTIALS, is_sample=False),
    FileGenEntry(src=Path(TEMPLATES_PACKAGE_PATH) / FileName.REQUIREMENTS, dst=Path('.') / FileName.REQUIREMENTS, is_sample=False),
    FileGenEntry(src=Path(DirName.TEMPLATES) / FileName.REQUIREMENTS_DEV, dst=Path('.') / FileName.REQUIREMENTS_DEV, is_sample=False),
]

REPO_DIRS_TO_GEN = [
    DirName.DOCS,
    DirName.TESTS,
    DirName.REPOASSIST,
    str(Path(DirName.REPOASSIST) / DirName.TEMPLATES)
]


RepoassistFileGenEntry = namedtuple('RepoassistFileGeneratorEntry', 'src dst is_templ')

REPOASSIST_FILES = [
    RepoassistFileGenEntry(src=Path(FileName.MAIN), dst=Path('.') / DirName.REPOASSIST / FileName.MAIN, is_templ=False),
    RepoassistFileGenEntry(src=Path(DirName.TEMPLATES) / FileName.PYINIT, dst=Path('.') / DirName.REPOASSIST / FileName.PYINIT, is_templ=True),
    RepoassistFileGenEntry(src=Path(FileName.COLREQS), dst=Path('.') / DirName.REPOASSIST / FileName.COLREQS, is_templ=False),
    RepoassistFileGenEntry(src=Path(FileName.SETTINGS), dst=Path('.') / DirName.REPOASSIST / FileName.SETTINGS, is_templ=False),
    RepoassistFileGenEntry(src=Path(FileName.LOGGER), dst=Path('.') / DirName.REPOASSIST / FileName.LOGGER, is_templ=False),
    RepoassistFileGenEntry(src=Path(FileName.RELEASE), dst=Path('.') / DirName.REPOASSIST / FileName.RELEASE, is_templ=False),
    RepoassistFileGenEntry(src=Path(FileName.EXCEPTIONS), dst=Path('.') / DirName.REPOASSIST / FileName.EXCEPTIONS, is_templ=False),
    RepoassistFileGenEntry(src=Path(FileName.UTILS), dst=Path('.') / DirName.REPOASSIST / FileName.UTILS, is_templ=False),
    RepoassistFileGenEntry(src=Path(FileName.PYGITTOOLS), dst=Path('.') / DirName.REPOASSIST / FileName.PYGITTOOLS, is_templ=False),
    RepoassistFileGenEntry(src=Path(FileName.CLOUD), dst=Path('.') / DirName.REPOASSIST / FileName.CLOUD, is_templ=False),
    RepoassistFileGenEntry(src=Path(FileName.WIZARD), dst=Path('.') / DirName.REPOASSIST / FileName.WIZARD, is_templ=False),
    RepoassistFileGenEntry(src=Path(FileName.FORMATTER), dst=Path('.') / DirName.REPOASSIST / FileName.FORMATTER, is_templ=False),
    RepoassistFileGenEntry(src=Path(FileName.PREPARE), dst=Path('.') / DirName.REPOASSIST / FileName.PREPARE, is_templ=False),
    RepoassistFileGenEntry(src=Path(FileName.CLEAN), dst=Path('.') / DirName.REPOASSIST / FileName.CLEAN, is_templ=False),
    RepoassistFileGenEntry(src=Path(FileName.REPOASSIST_CLI), dst=Path('.') / DirName.REPOASSIST / FileName.CLI, is_templ=False),
    RepoassistFileGenEntry(src=Path(DirName.TEMPLATES) / f'{FileName.CHANGELOG_GENERATED}{JINJA2_TEMPLATE_EXT}', 
                           dst=Path('.') / DirName.REPOASSIST / DirName.TEMPLATES / f'{FileName.CHANGELOG_GENERATED}{JINJA2_TEMPLATE_EXT}', 
                           is_templ=False),
    RepoassistFileGenEntry(src=Path(DirName.TEMPLATES) / f'{FileName.CHANGELOG_PREPARED}{JINJA2_TEMPLATE_EXT}', 
                           dst=Path('.') / DirName.REPOASSIST / DirName.TEMPLATES / f'{FileName.CHANGELOG_PREPARED}{JINJA2_TEMPLATE_EXT}', 
                           is_templ=False),
    RepoassistFileGenEntry(src=Path(DirName.TEMPLATES) / f'{FileName.AUTHORS_PREPARED}{JINJA2_TEMPLATE_EXT}', 
                           dst=Path('.') / DirName.REPOASSIST / DirName.TEMPLATES / f'{FileName.AUTHORS_PREPARED}{JINJA2_TEMPLATE_EXT}', 
                           is_templ=False),
    RepoassistFileGenEntry(src=Path(DirName.TEMPLATES) / f'{FileName.REQUIREMENTS_DEV}{JINJA2_TEMPLATE_EXT}', 
                           dst=Path('.') / DirName.REPOASSIST / DirName.TEMPLATES / f'{FileName.REQUIREMENTS_DEV}{JINJA2_TEMPLATE_EXT}', 
                           is_templ=False),
    RepoassistFileGenEntry(src=Path(DirName.TEMPLATES) / f'{FileName.REPOASSIST_README}{JINJA2_TEMPLATE_EXT}', 
                       dst=Path('.') / DirName.REPOASSIST / f'{FileName.README}', is_templ=False),
]

GEN_REPO_CONFIG_MANDATORY_FIELDS = [
    'repo_name',
    'is_cloud',
    'is_sample_layout'
]

# Only from root directory
FILES_TO_CLEAN = [
    '*.egg'
]

DIRS_TO_CLEAN = [
    {'name': '*.egg-info', 'flag': '.'},
    {'name': '.eggs', 'flag': '.'},
    {'name': '__pycache__', 'flag': 'r'},
    {'name': '.pytest_cache', 'flag': 'r'},
    {'name': '.tox', 'flag': '.'},
    {'name': 'build', 'flag': '.'},
    {'name': 'dist', 'flag': '.'},
    {'name': 'venv*', 'flag': '.'},
    {'name': 'htmlcov', 'flag': '.'},
]

DEFAULT_REQUIREMENTS = ['setuptools']
