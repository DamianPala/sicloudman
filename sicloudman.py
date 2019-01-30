#!/usr/bin/env python
# -*- coding: utf-8 -*-


import jinja2
import ftplib
import inspect
import logging
import datetime
import configparser
import dataclasses
from pathlib import Path
from collections import namedtuple
from types import SimpleNamespace


__author__ = 'Damian Pala'
__version__ = '0.1.0'

CLOUD_CREDENTIALS_FILENAME = 'cloud_credentials.txt'
CLOUD_CREDENTIALS_FILE_TEMPLATE = """# This file must not be commited! It contains confidentials.
server = {{server}}
username = {{username}}
password = {{password}}

# The path when you store files
# The Final Path will be: <main_bucket_path>/<client_name>/<project_name>
main_bucket_path = {{main_bucket_path}}
# Leave empty if not attached to the final path
client_name = {{client_name}}
# Leave empty if not attached to the final path
project_name = {{project_name}}
"""

FTP_ERR_CODE_FILE_UNAVAILABLE = 550


class SiCloudManError(Exception):
    def __init__(self, msg, logger):
        super().__init__(msg)
        self.logger = logger


class NameError(SiCloudManError):
    pass


class TypeError(SiCloudManError):
    pass


class ValueError(SiCloudManError):
    pass


class FileNotFoundError(SiCloudManError):
    pass


class BucketNotFoundError(SiCloudManError):
    pass


class CredentialsError(SiCloudManError):
    pass


class FtpError(SiCloudManError):
    pass


def handle_ftplib_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ftplib.all_errors as e:
            sign = inspect.signature(func)
            arg_names = list(sign.parameters.keys())
            passed = {k: v for k, v in zip(arg_names[:len(args)], args)}
            self = passed['self']
            raise FtpError(f'Ftp error occured: {e}', self._logger)

    return wrapper


@dataclasses.dataclass
class Credentials(object):
    server: str
    username: str
    password: str
    main_bucket_path: str
    client_name: str = ''
    project_name: str = ''

    @staticmethod
    def get_fields():
        return [field.name for field in dataclasses.fields(Credentials)]

    @staticmethod
    def get_default_fields():
        return dir(Credentials)


Bucket = namedtuple('Bucket', 'name keywords')


class CloudManager(object):
    _logger = logging.getLogger(__name__)

    def __init__(self, artifacts_path, buckets_list, credentials=None,
                 credentials_path=None, get_logger=None, cwd='.'):
        if not isinstance(buckets_list, list):
            raise TypeError('buckets_list parameter must be a list!', self._logger)
        self.cwd = Path(cwd)
        self.artifacts_path = Path(artifacts_path) if Path(
            artifacts_path).is_absolute() else self.cwd / artifacts_path
        if credentials_path:
            self.credentials_path = Path(credentials_path) if Path(
                credentials_path).is_absolute() else self.cwd / credentials_path
        else:
            self.credentials_path = self.cwd / CLOUD_CREDENTIALS_FILENAME
        self.buckets_list = buckets_list
        if get_logger:
            _logger = get_logger(__name__)

        if credentials:
            if isinstance(credentials, Credentials):
                self.credentials = credentials
            else:
                raise TypeError('credentials parameter is not an instance of Credentials class', self._logger)
        else:
            self.credentials = self._read_cloud_credentials()

    @staticmethod
    def touch_credentials(path, keywords={}):
        file_path = Path(path) / CLOUD_CREDENTIALS_FILENAME
        rtemplate = jinja2.Environment(loader=jinja2.BaseLoader).from_string(CLOUD_CREDENTIALS_FILE_TEMPLATE)
        final_content = rtemplate.render(keywords)
        file_path.write_text(final_content, 'utf-8')

        return file_path

    @handle_ftplib_error
    def upload_artifacts(self, prompt=True):
        self._logger.info('Upload files to the cloud server...')
        uploaded_files = []

        with ftplib.FTP(self.credentials.server,
                        self.credentials.username,
                        self.credentials.password) as ftp_conn:
            for bucket in self.buckets_list:
                files_to_upload = []
                for keyword in bucket.keywords:
                    file = self.get_latest_file_with_keyword(self.artifacts_path, keyword)
                    if file:
                        files_to_upload.append(file)

                for file in files_to_upload:
                    if prompt:
                        if not self._is_checkpoint_ok(__name__, f'Upload the {file} file?'):
                            file = None

                    if file:
                        self._create_buckets_tree(ftp_conn)
                        self._upload_file_to_bucket(ftp_conn, file, bucket.name)
                        uploaded_files.append((Path(ftp_conn.pwd()) / file.name).as_posix())

        if not uploaded_files:
            self._logger.info('No files to upload.')

        return uploaded_files

    @handle_ftplib_error
    def upload_file(self, file_path=None, bucket_name=None, prompt=True):
        self._logger.info('Upload specified file to the cloud server...')

        if prompt:
            file_path = (Path().cwd() / input('Enter a file path: ')).resolve()
            bucket_name = input('Enter a bucket name: ')
        else:
            if file_path is None:
                raise ValueError('file_path cannnot be None', self._logger)
            if bucket_name is None:
                raise ValueError('bucket_name cannnot be None', self._logger)

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f'File {file_path} not found!', self._logger)

        available_buckets = [bucket.name for bucket in self.buckets_list]
        if bucket_name not in available_buckets:
            raise BucketNotFoundError(f'Bucket {file_path} not found on the cloud server!', self._logger)

        with ftplib.FTP(self.credentials.server,
                        self.credentials.username,
                        self.credentials.password) as ftp_conn:
            self._create_buckets_tree(ftp_conn)
            self._upload_file_to_bucket(ftp_conn, file_path, bucket_name)

            return (Path(ftp_conn.pwd()) / file_path.name).as_posix()

    @handle_ftplib_error
    def list_cloud(self):
        self._logger.info('List cloud buckets...')

        with ftplib.FTP(self.credentials.server,
                        self.credentials.username,
                        self.credentials.password) as ftp_conn:
            project_bucket_path = self._get_project_bucket_path()
            if not self._is_path_exists(ftp_conn, project_bucket_path):
                self._logger.info('There are no buckets on the cloud server.')
            else:
                self._logger.info(f'List buckets in the project path: {project_bucket_path}')
                cloud_files = SimpleNamespace()
                for bucket in self.buckets_list:
                    bucket_files = self._print_bucket_files(ftp_conn, project_bucket_path, bucket.name)
                    setattr(cloud_files, bucket.name, bucket_files)

                return cloud_files
        return None

    @handle_ftplib_error
    def download_file(self, filename=None):
        self._logger.info('Download a specified file from the cloud server...')

        if not filename:
            filename = input('Enter the name of a file to download: ')

        bucket_name = self._get_bucket_name_from_filename(filename)
        if bucket_name is None:
            raise FileNotFoundError('File not found on the cloud server. Bucket not found!', self._logger)

        with ftplib.FTP(self.credentials.server,
                        self.credentials.username,
                        self.credentials.password) as ftp_conn:
            file_dir = self._get_project_bucket_path() / bucket_name
            if not self._is_path_exists(ftp_conn, file_dir):
                raise FileNotFoundError('File not found on the cloud server!', self._logger)

            ftp_conn.cwd(file_dir.as_posix())
            if filename not in ftp_conn.nlst():
                raise FileNotFoundError('File not found on the cloud server!', self._logger)

            dir_where_to_download = self.artifacts_path
            if not dir_where_to_download.exists():
                Path.mkdir(dir_where_to_download, parents=True)

            path_where_to_download = dir_where_to_download / filename
            if path_where_to_download.exists():
                self._logger.warning(f'File {filename} already exists in {path_where_to_download.parent}.')
                self._logger.info('Downloading aborted.')
                return

            with open(path_where_to_download, 'wb') as file:
                ftp_conn.retrbinary('RETR ' + filename, file.write)

        if path_where_to_download.exists():
            self._logger.info(f'File {filename} downloding to '
                              f'{path_where_to_download.parent} directory completeted.')
        else:
            raise FileNotFoundError(f'File {filename} downloading error! Please try again.', self._logger)

        return path_where_to_download.as_posix()

    def _get_bucket_name_from_filename(self, filename):
        for bucket in self.buckets_list:
            for keyword in bucket.keywords:
                if keyword in filename:
                    return bucket.name

        return None

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

    @handle_ftplib_error
    def _upload_file_to_bucket(self, ftp_conn, file_path, bucket_name):
        ftp_conn.cwd((self._get_project_bucket_path() / bucket_name).as_posix())
        buckets_contents = ftp_conn.nlst()
        if file_path.name not in buckets_contents:
            with open(file_path, 'rb') as file:
                ftp_conn.storbinary('STOR ' + file_path.name, file)
            if file_path.name in ftp_conn.nlst():
                self._logger.info(f'File {file_path.name} uploaded properly to the bucket {ftp_conn.pwd()}!')
            else:
                self._logger.info(f'File {file_path.name} uploading error!')
        else:
            self._logger.warning(f'{file_path.name} already exists in the server bucket: {ftp_conn.pwd()}. '
                                 f'Uploading aborted.')

    @handle_ftplib_error
    def _print_bucket_files(self, ftp_conn, project_bucket_path, bucket):
        ftp_conn.cwd(project_bucket_path.as_posix())
        if bucket in ftp_conn.nlst():
            ftp_conn.cwd(bucket)
            bucket_files = sorted(list(ftp_conn.mlsd()), key=lambda k: k[1]['modify'])
            if bucket_files:
                self._logger.info(f'The {bucket} bucket files:')
                files_list = []
                for file in bucket_files:
                    files_list.append(file[0])
                    self._logger.info(f"{'Owner':10} {'Size':10} {'Time':19} Name")
                    self._logger.info(f"{file[1]['unix.owner']:10} {file[1]['size']:10} "
                                      f"{datetime.datetime.strptime(file[1]['modify'], '%Y%m%d%H%M%S')} {file[0]}")

                return files_list
            else:
                self._logger.info(f'No files in bucket: {bucket}')
        else:
            self._logger.warning(f'Bucket: {bucket} not exists on the cloud server.')

        return []

    def _read_cloud_credentials(self):
        if not self.credentials_path.exists():
            raise FileNotFoundError(f'{self.credentials_path} file not found!', self._logger)

        properties_string = f'[dummy_section]\n{self.credentials_path.read_text()}'

        credentials = configparser.RawConfigParser()
        credentials.read_string(properties_string)

        credentials_dict = {param: value.strip() for param, value in credentials['dummy_section'].items()}

        for field, value in credentials_dict.items():
            if field not in Credentials.get_default_fields() and not value:
                raise CredentialsError(f'{field} field is empty in {self.credentials_path.name} file!',
                                       self._logger)
            elif field == 'main_bucket_path' and value == '/':
                raise CredentialsError(f'{field} field has invalid value {value} '
                                       f'in {self.credentials_path.name} file!', self._logger)

        return Credentials(**credentials_dict)

    def _get_project_bucket_path(self):
        path = Path('/') / self.credentials.main_bucket_path
        if self.credentials.client_name:
            path = path / self.credentials.client_name
        if self.credentials.project_name:
            path = path / self.credentials.project_name

        return path

    @staticmethod
    def _get_main_bucket_first_dir(path):
        parents = list(Path(path).parents)
        return parents[-2] if parents.__len__() > 1 else Path(path)

    @handle_ftplib_error
    def _is_path_exists(self, ftp_conn, path):
        try:
            ftp_conn.cwd(path.as_posix())
        except ftplib.all_errors as e:
            if self.get_ftp_errorcode(e) == FTP_ERR_CODE_FILE_UNAVAILABLE:
                return False
            else:
                raise RuntimeError(f'Unknown error occured: {e}', self._logger)
        else:
            return True

    @staticmethod
    def get_ftp_errorcode(error):
        return int(str(error).split(None, 1)[0])

    @handle_ftplib_error
    def _create_buckets_tree(self, ftp_conn):
        ftp_conn.cwd('/')
        project_bucket_path = self._get_project_bucket_path()
        main_bucket_first_dir = self._get_main_bucket_first_dir(self.credentials.main_bucket_path)
        if not self._is_path_exists(ftp_conn, main_bucket_first_dir):
            raise BucketNotFoundError(f'Directory {main_bucket_first_dir.as_posix()} not found on the server! '
                                      'Create it and try again.', self._logger)

        path_parents = list(Path(project_bucket_path).parents)
        for parent in reversed(path_parents):
            if not self._is_path_exists(ftp_conn, parent):
                ftp_conn.mkd(parent.as_posix())
                self._logger.info(f'Bucket {parent.as_posix()} created.')

        if not self._is_path_exists(ftp_conn, project_bucket_path):
            ftp_conn.mkd(project_bucket_path.as_posix())
            self._logger.info(f'Bucket {project_bucket_path.as_posix()} created.')

        for bucket in self.buckets_list:
            ftp_conn.cwd(project_bucket_path.as_posix())
            if not self._is_path_exists(ftp_conn, project_bucket_path / bucket.name):
                ftp_conn.mkd(bucket.name)
                self._logger.info(f'Bucket {bucket.name} created.')

    @staticmethod
    def _is_checkpoint_ok(name, msg, choices=['y', 'n'], valid_value='y'):
        no_choice = True
        while no_choice:
            choice = input(f"{name}: [CHECKPOINT]: {msg} ({'/'.join(choices)}): ")
            for item in choices:
                if item == choice:
                    no_choice = False
                    break

        return True if choice == valid_value else False
