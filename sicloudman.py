#!/usr/bin/env python
# -*- coding: utf-8 -*-


import jinja2
import ftplib
import logging
import datetime
import configparser
from pathlib import Path
from collections import namedtuple
from types import SimpleNamespace
from repoassist import _logger


__author__ = 'Damian Pala'
__version__ = '0.1.0'

CLOUD_CREDENTIALS_FILENAME = 'cloud_credentials.txt'
CLOUD_CREDENTIALS_FILE_TEMPLATE = """# This file must not be commited! It contains confidentials.
server = {{server}}
username = {{username}}
password = {{password}}

# Path to bucket when you store this kind of stuff
# Final Path will be: <main_bucket_path>/<client_name>/<project_name>
main_bucket_path = {{main_bucket_path}}
# Leave empty if not attached to final path
client_name = {{client_name}}
# Leave empty if not attached to final path
project_name = {{project_name}}
"""

class SiCloudManError(Exception):
    def __init__(self, msg, logger):
        super().__init__(msg)
        self.logger = logger
        

class NameError(SiCloudManError):
    pass


class TypeError(SiCloudManError):
    pass


class FileNotFoundError(SiCloudManError):
    pass


class CredentialsError(SiCloudManError):
    pass


class BucketNotFoudError(SiCloudManError):
    pass


Bucket = namedtuple('Bucket', 'name keyword')


class CloudManager():
    _logger = logging.getLogger(__name__)
    
    def __init__(self, artifacts_path, credentials_path, buckets_list, get_logger=None, cwd='.'):
        if not isinstance(buckets_list, list):
            raise TypeError('buckets_list parameter must be a list!', self._logger)
        self.cwd = Path(cwd)
        self.artifacts_path = Path(artifacts_path) if Path(artifacts_path).is_absolute() else self.cwd / artifacts_path
        self.credentials_path = Path(credentials_path) if Path(credentials_path).is_absolute() else self.cwd / credentials_path
        self.buckets_list = buckets_list
        if get_logger:
            self._logger = get_logger(__name__)


    @staticmethod
    def touch_credentials(path, keywords=None):
        file_path = Path(path) / CLOUD_CREDENTIALS_FILENAME
        
        if keywords:
            rtemplate = jinja2.Environment(loader=jinja2.BaseLoader).from_string(CLOUD_CREDENTIALS_FILE_TEMPLATE)
            final_content = rtemplate.render(**keywords)
        else:
            final_content = CLOUD_CREDENTIALS_FILE_TEMPLATE
        
        file_path.write_text(final_content, 'utf-8')
        return file_path


    @staticmethod
    def get_latest_file_with_keyword(directory, keyword):
        if directory:
            directory = Path(directory)
            if directory.exists() and directory.is_dir():
                FileTime = namedtuple('FileTime', ['path', 'mtime'])
                files_list = [FileTime(item, Path(item).stat().st_mtime) 
                              for item in directory.iterdir() 
                              if item.is_file() and keyword in item.name]
    
                if files_list:
                    return max(files_list, key=lambda x: x.mtime).path
    
        return None


    def _read_cloud_credentials(self):
        file_path = Path(self.cwd) / CLOUD_CREDENTIALS_FILENAME
    
        if not file_path.exists():
            raise FileNotFoundError(f'{file_path.name} file not found!', _logger)
    
        properties_string = f'[dummy_section]\n{file_path.read_text()}'
    
        credentials = configparser.RawConfigParser()
        credentials.read_string(properties_string)
    
        credentials_dict = {param: value.strip() for param, value in credentials['dummy_section'].items()}
    
        for field, value in credentials_dict.items():
            if not value:
                raise CredentialsError(f'{field} field is empty in {file_path.name} file!', _logger)
    
        return SimpleNamespace(**credentials_dict)
    
    
    def _is_cloud_project_bucket_exists(self, ftp_conn, credentials):
        ftp_conn.cwd('/')
    
        if not credentials.main_bucket_path in ftp_conn.nlst():
            return False
        ftp_conn.cwd(credentials.main_bucket_path)
    
        if credentials.client_name not in ftp_conn.nlst():
            return False
        ftp_conn.cwd(credentials.client_name)
    
        if credentials.project_name not in ftp_conn.nlst():
            return False
    
        return True




def upload_to_cloud(self, prompt=True):
    _logger.info('Upload packages to the cloud server...')
    latest_release_package_path = get_latest_file(Path(cwd) / settings.DirName.RELEASE)

    if prompt:
        if latest_release_package_path:
            if not is_checkpoint_ok(__name__, f'Upload the {latest_release_package_path} package?'):
                latest_release_package_path = None

    if not latest_release_package_path:
        _logger.info('No package to upload.')
        return

    credentials = _read_cloud_credentials(cwd)
    cloud_project_bucket_path = _get_cloud_project_bucket_path(credentials)

    with ftplib.FTP(credentials['server'], credentials['username'], credentials['password']) as ftp_conn:
        _create_main_bucket_tree(ftp_conn, credentials)

        _upload_package(ftp_conn, latest_release_package_path, cloud_project_bucket_path, settings.DirName.RELEASE)


def list_cloud(cwd='.'):
    _logger.info('List cloud buckets...')
    credentials = _read_cloud_credentials(cwd)
    with ftplib.FTP(credentials['server'], credentials['username'], credentials['password']) as ftp_conn:
        cloud_project_bucket_path = _get_cloud_project_bucket_path(credentials)

        if _is_cloud_project_bucket_exists(ftp_conn, credentials):
            _print_bucket_files(ftp_conn, cloud_project_bucket_path, settings.DirName.RELEASE)
        else:
            _logger.info('There are no buckets on the cloud server.')


def download_package(cwd='.', package_name=None):
    if not package_name:
        package_name = input('Enter the name of the package to donwload: ')
    if settings.RELEASE_PACKAGE_SUFFIX in package_name:
        bucket = settings.DirName.RELEASE
    else:
        raise NameError('Incorrect package name!', logger=_logger)

    credentials = _read_cloud_credentials(cwd)
    cloud_project_bucket_path = _get_cloud_project_bucket_path(credentials)

    with ftplib.FTP(credentials['server'], credentials['username'], credentials['password']) as ftp_conn:
        ftp_conn.cwd(cloud_project_bucket_path)
        ftp_conn.cwd(bucket)
        if package_name not in ftp_conn.nlst():
            raise FileNotFoundError(
                f'{package_name} package not found on the cloud server', logger=_logger)

        dir_where_to_download = Path(cwd) / settings.DirName.RELEASE
        if not dir_where_to_download.exists():
            Path.mkdir(dir_where_to_download, parents=True)

        path_where_to_download = dir_where_to_download / package_name

        if (path_where_to_download).exists():
            _logger.warning(f'File {package_name} already exists in {path_where_to_download.parent}.')
            _logger.info('Downloading aborted.')
            return

        with open(path_where_to_download, 'wb') as file:
            ftp_conn.retrbinary('RETR ' + package_name, file.write)

    if (path_where_to_download).exists():
        _logger.info(f'File {package_name} downloding to {path_where_to_download.parent} directory completeted.')
    else:
        raise FileNotFoundError(f'File {package_name} downloading error! Please try again.', _logger)


def _print_bucket_files(ftp_conn, cloud_project_bucket_path, bucket):
    ftp_conn.cwd(cloud_project_bucket_path)
    if bucket in ftp_conn.nlst():
        ftp_conn.cwd(bucket)
        files_in_bucket = list(ftp_conn.mlsd())
        files_in_bucket = sorted(files_in_bucket, key=lambda k: k[1]['modify'])
        if files_in_bucket:
            _logger.info(f'{bucket} bucket files:')
            for bucket_file in files_in_bucket:
                _logger.info('{0:10} {1:10} {2} {3}'.format(bucket_file[1]['unix.owner'],
                                                            bucket_file[1]['size'],
                                                            datetime.datetime.strptime(bucket_file[1]['modify'],
                                                                                       '%Y%m%d%H%M%S'),
                                                            bucket_file[0]))
        else:
            _logger.info(f'No files in bucket: {bucket}')
    else:
        _logger.info(f'Bucket: {bucket} not exists on cloud server.')




def _get_cloud_project_bucket_path(credentials):
    return (Path('/') / credentials['main_bucket_path'] / credentials['client_name'] / credentials['project_name']
            ).as_posix()


def _upload_package(ftp_conn, package_path, cloud_project_bucket_path, bucket):
    ftp_conn.cwd(cloud_project_bucket_path)
    if package_path:
        package_name = package_path.name
        ftp_conn.cwd(bucket)
        buckets_contents = ftp_conn.nlst()
        if package_name not in buckets_contents:
            fh = open(package_path, 'rb')
            ftp_conn.storbinary('STOR ' + package_name, fh)
            fh.close()
            if package_name in ftp_conn.nlst():
                _logger.info(
                    f'File {package_name} uploaded properly to directory {ftp_conn.pwd()} of the cloud server!')
            else:
                _logger.info(f'File {package_name} uploading error!')
        else:
            _logger.info(f"{package_path.name} already on server's bucket: {ftp_conn.pwd()}.")





def _create_main_bucket_tree(ftp_conn, credentials):
    if not credentials['main_bucket_path'] in ftp_conn.nlst():
        raise BucketNotFoudError(
            f"Bucket {credentials['main_bucket_path']} not found on server!", _logger)

    ftp_conn.cwd(credentials['main_bucket_path'])

    if credentials['client_name'] not in ftp_conn.nlst():
        ftp_conn.mkd(credentials['client_name'])
    ftp_conn.cwd(credentials['client_name'])

    if credentials['project_name'] not in ftp_conn.nlst():
        ftp_conn.mkd(credentials['project_name'])
    ftp_conn.cwd(credentials['project_name'])

    if settings.DirName.RELEASE not in ftp_conn.nlst():
        ftp_conn.mkd(settings.DirName.RELEASE)
        
        


def is_checkpoint_ok(name, msg, choices=['y', 'n'], valid_value='y'):
    no_choice = True
    while no_choice:
        choice = input(f'{name}: [CHECKPOINT]: {msg} ({get_choices_string(choices)}): ')
        for item in choices:
            if item == choice:
                no_choice = False
                break
            
    return True if choice == valid_value else False


def get_choices_string(choices):
    choices_string = ''
    for choice in choices:
        choices_string += f'{choice}/'
        
    return choices_string[:-1]


def get_latest_file(path):
    if path:
        path = Path(path)
        if path.exists() and path.is_dir():
            FileTime = namedtuple('FileTime', ['path', 'mtime'])
            files_list = [FileTime(item, Path(item).stat().st_mtime) for item in path.iterdir() if item.is_file()]

            if files_list:
                return max(files_list, key=lambda x: x.mtime).path

    return None


