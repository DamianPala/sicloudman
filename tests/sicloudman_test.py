#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import stat
import time
import copy
import pytest
import shutil
import ftplib
import tempfile
from pathlib import Path
from pprint import pprint
from types import SimpleNamespace

import sicloudman


RUN_ALL_TESTS = False

TEST_CLOUD_CREDENTIALS_PATH = Path(__file__) / '../..' / sicloudman.CLOUD_CREDENTIALS_FILENAME


def _error_remove_readonly(_action, name, _exc):
    Path(name).chmod(stat.S_IWRITE)
    Path(name).unlink()
    
    
def ftp_rmtree(ftp, path):
    try:
        names = ftp.nlst(path)
    except ftplib.all_errors as e:
        raise RuntimeError(f'Could not remove {path} - nlst cmd error: {e}')
    else:
        for name in names:
            if Path(name).name in ('.', '..'): continue
    
            try:
                ftp.cwd(name)
                ftp_rmtree(ftp, name)
            except ftplib.all_errors as e:
                ftp.delete(name)
    
        try:
            ftp.rmd(path)
        except ftplib.all_errors as e:
            raise RuntimeError(f'Could not remove {path}: {e}')


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
    

@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_touch_and_read_credentials_WHEN_keywords(cwd):
    credentials_expected = sicloudman.Credentials(
        server='my_server',
        username='user',
        password='pass',
        main_bucket_path='main_bucket',
        client_name='client',
        project_name='project',
    )
    file_path = sicloudman.CloudManager.touch_credentials(cwd, keywords=credentials_expected.__dict__)
    file_content = file_path.read_text()
    print(file_content)
    
    cloud_manager = sicloudman.CloudManager('artifacts',
                                            [sicloudman.Bucket(name='release', keywords=['_release'])], cwd=cwd)
    pprint(cloud_manager.credentials.__dict__)
    
    assert set(cloud_manager.credentials.__dict__) ==  set(credentials_expected.__dict__)


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_read_credentials_SHOULD_rise_error_when_mandatory_field_empty(cwd):
    credentials_expected = sicloudman.Credentials(
        server='',
        username='user',
        password='pass',
        main_bucket_path='main_bucket',
        client_name='client',
        project_name='project',
    )
    sicloudman.CloudManager.touch_credentials(cwd, keywords=credentials_expected.__dict__)
    
    with pytest.raises(sicloudman.CredentialsError): 
        sicloudman.CloudManager('artifacts', [sicloudman.Bucket(name='release', keywords=['_release'])], cwd=cwd)


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_read_credentials_SHOULD_not_rise_error_when_extra_field_empty(cwd):
    credentials_expected = sicloudman.Credentials(
        server='my_server',
        username='user',
        password='pass',
        main_bucket_path='main_bucket',
        client_name='',
        project_name='',
    )
    sicloudman.CloudManager.touch_credentials(cwd, keywords=credentials_expected.__dict__)
    
    cloud_manager = sicloudman.CloudManager('artifacts',
                                            [sicloudman.Bucket(name='release', keywords=['_release'])], cwd=cwd)
    
    assert set(cloud_manager.credentials.__dict__) ==  set(credentials_expected.__dict__)


get_project_bucket_path_testdata = [
    (
        sicloudman.Credentials(
            server='my_server',
            username='user',
            password='pass',
            main_bucket_path='main_bucket',
            client_name='',
            project_name='',
        ),
        '/main_bucket'
    ),
    (
        sicloudman.Credentials(
            server='my_server',
            username='user',
            password='pass',
            main_bucket_path='main_bucket',
            client_name='client',
            project_name='',
        ),
        '/main_bucket/client'
    ),
    (
        sicloudman.Credentials(
            server='my_server',
            username='user',
            password='pass',
            main_bucket_path='main_bucket',
            client_name='client',
            project_name='project',
        ),
        '/main_bucket/client/project'
    ),
    (
        sicloudman.Credentials(
            server='my_server',
            username='user',
            password='pass',
            main_bucket_path='/main_bucket',
            client_name='client',
            project_name='project',
        ),
        '/main_bucket/client/project'
    ),
    (
        sicloudman.Credentials(
            server='my_server',
            username='user',
            password='pass',
            main_bucket_path='/dir1/dir2/main_bucket',
            client_name='client',
            project_name='project',
        ),
        '/dir1/dir2/main_bucket/client/project'
    ),
    (
        sicloudman.Credentials(
            server='my_server',
            username='user',
            password='pass',
            main_bucket_path='main_bucket',
            client_name='',
            project_name='project',
        ),
        '/main_bucket/project'
    ),
]

@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
@pytest.mark.parametrize("credentials, expected_path", get_project_bucket_path_testdata)
def test_get_project_bucket_path(credentials, expected_path, cwd):
    sicloudman.CloudManager.touch_credentials(cwd, keywords=credentials.__dict__)
    
    cloud_manager = sicloudman.CloudManager('artifacts',
                                            [sicloudman.Bucket(name='release', keywords=['_release'])], cwd=cwd)
    path = cloud_manager._get_project_bucket_path().as_posix()
    
    assert path == expected_path


get_main_bucket_path_from_project_path_testdata = [
    ('/main_bucket/client/project', '/main_bucket'),
    ('/dir1/main_bucket/client/project', '/dir1/main_bucket'),
    ('/dir1/dir2/main_bucket/client/project', '/dir1/dir2/main_bucket'),
]

@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
@pytest.mark.parametrize("project_path, main_pucket_path", get_main_bucket_path_from_project_path_testdata)
def test_get_main_bucket_path_from_project_path(project_path, main_pucket_path, cwd):
    path = sicloudman.CloudManager._get_main_bucket_path_from_project_path(project_path).as_posix()
    
    assert path == main_pucket_path


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_is_path_exists_SHOULD_return_false_if_not_exists(cwd):
    cloud_manager = sicloudman.CloudManager('artifacts',
                                            [sicloudman.Bucket(name='release', keywords=['_release'])], 
                                            credentials_path=TEST_CLOUD_CREDENTIALS_PATH, cwd=cwd)
    credentials = copy.copy(cloud_manager.credentials)
    credentials.client_name = 'this_is_abstrac_client_path_173'
    sicloudman.CloudManager.touch_credentials(cwd, keywords=credentials.__dict__)
    cloud_manager = sicloudman.CloudManager('artifacts',
                                            [sicloudman.Bucket(name='release', keywords=['_release'])], cwd=cwd)
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        project_bucket_path = cloud_manager._get_project_bucket_path()
        
        assert cloud_manager._is_path_exists(ftp_conn, project_bucket_path) == False
        
        
@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_is_path_exists_SHOULD_return_true_if_exists(cwd):
    cloud_manager = sicloudman.CloudManager('artifacts',
                                            [sicloudman.Bucket(name='release', keywords=['_release'])], 
                                            credentials_path=TEST_CLOUD_CREDENTIALS_PATH, cwd=cwd)
    credentials = copy.copy(cloud_manager.credentials)
    credentials.client_name = 'this_is_abstrac_client_path_173'
    sicloudman.CloudManager.touch_credentials(cwd, keywords=credentials.__dict__)
    cloud_manager = sicloudman.CloudManager('artifacts',
                                            [sicloudman.Bucket(name='release', keywords=['_release'])], cwd=cwd)
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        project_bucket_path = cloud_manager._get_project_bucket_path()
        
        assert cloud_manager._is_path_exists(ftp_conn, project_bucket_path) == False


def get_updated_cloud_manager(cwd, bucket_paths, buckets):
    artifacts_path = cwd / 'artifacts'
    artifacts_path.mkdir()
    
    cloud_manager = sicloudman.CloudManager(artifacts_path,
                                            [sicloudman.Bucket(name='release', keywords=['_release'])], 
                                            credentials_path=TEST_CLOUD_CREDENTIALS_PATH, cwd=cwd)
    credentials = copy.copy(cloud_manager.credentials)
    credentials.main_bucket_path = bucket_paths.main_bucket_path
    credentials.client_name = bucket_paths.client_name
    credentials.project_name = bucket_paths.project_name
    sicloudman.CloudManager.touch_credentials(cwd, keywords=credentials.__dict__)
    cloud_manager = sicloudman.CloudManager(artifacts_path, buckets, cwd=cwd)
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        main_bucket_path = cloud_manager._get_main_bucket_path_from_project_path(cloud_manager._get_project_bucket_path())
        if main_bucket_path == cloud_manager._get_project_bucket_path().parent:
            path_to_rm = cloud_manager._get_project_bucket_path()
        else:
            path_to_rm = cloud_manager._get_project_bucket_path().parent
        if cloud_manager._is_path_exists(ftp_conn, path_to_rm):
            ftp_rmtree(ftp_conn, path_to_rm.as_posix())
    
    return cloud_manager, artifacts_path

    
@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_create_buckets_tree(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, _ = get_updated_cloud_manager(cwd, bucket_paths,
                                                 [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                  sicloudman.Bucket(name='client', keywords=['_client'])])
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        cloud_manager._create_buckets_tree(ftp_conn)
        assert cloud_manager._is_path_exists(ftp_conn, cloud_manager._get_project_bucket_path() / 'release') == True
        assert cloud_manager._is_path_exists(ftp_conn, cloud_manager._get_project_bucket_path() / 'client') == True
        
        ftp_rmtree(ftp_conn, cloud_manager._get_project_bucket_path().parent.as_posix())


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_to_cloud_and_list_cloud_SHOULD_upload_files_to_buckets_properly_and_list(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, artifacts_path = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    Path(artifacts_path / 'test_1_release.txt').touch()
    Path(artifacts_path / 'test_1_client.txt').touch()
    Path(artifacts_path / 'test_1_dev.txt').touch()
    time.sleep(1)
    Path(artifacts_path / 'test_2_release.txt').touch()
    Path(artifacts_path / 'test_2_client.txt').touch()
    Path(artifacts_path / 'test_2_dev.txt').touch()
    
    cloud_manager.upload_to_cloud(prompt=False)
    cloud_files = cloud_manager.list_cloud()
    
    assert set(cloud_files.release) == {'test_2_release.txt'}
    assert cloud_files.release.__len__() == 1
    assert set(cloud_files.client) == {'test_2_client.txt'}
    assert cloud_files.client.__len__() == 1
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        ftp_rmtree(ftp_conn, cloud_manager._get_project_bucket_path().parent.as_posix())
        
        
@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_to_cloud_SHOULD_upload_files_to_buckets_properly_WHEN_multiple_keywords(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, artifacts_path = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release', '.whl']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    Path(artifacts_path / 'test_1_release.txt').touch()
    Path(artifacts_path / 'test_1.whl').touch()
    Path(artifacts_path / 'test_1_client.txt').touch()
    Path(artifacts_path / 'test_1_dev.txt').touch()
    time.sleep(1)
    Path(artifacts_path / 'test_2_release.txt').touch()
    Path(artifacts_path / 'test_2.whl').touch()
    Path(artifacts_path / 'test_2_client.txt').touch()
    Path(artifacts_path / 'test_2_dev.txt').touch()
    
    cloud_manager.upload_to_cloud(prompt=False)
    cloud_files = cloud_manager.list_cloud()
    
    assert set(cloud_files.release) == {'test_2_release.txt', 'test_2.whl'}
    assert cloud_files.release.__len__() == 2
    assert set(cloud_files.client) == {'test_2_client.txt'}
    assert cloud_files.client.__len__() == 1
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        ftp_rmtree(ftp_conn, cloud_manager._get_project_bucket_path().parent.as_posix())


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_to_cloud_SHOULD_upload_files_to_buckets_properly_WHEN_multiple_uploads(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, artifacts_path = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release', '.whl']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    Path(artifacts_path / 'test_1_release.txt').touch()
    Path(artifacts_path / 'test_1.whl').touch()
    Path(artifacts_path / 'test_1_client.txt').touch()
    Path(artifacts_path / 'test_1_dev.txt').touch()
    time.sleep(1)
    Path(artifacts_path / 'test_2_release.txt').touch()
    Path(artifacts_path / 'test_2.whl').touch()
    Path(artifacts_path / 'test_2_client.txt').touch()
    Path(artifacts_path / 'test_2_dev.txt').touch()
    
    cloud_manager.upload_to_cloud(prompt=False)
    cloud_files = cloud_manager.list_cloud()
    
    assert set(cloud_files.release) == {'test_2_release.txt', 'test_2.whl'}
    assert cloud_files.release.__len__() == 2
    assert set(cloud_files.client) == {'test_2_client.txt'}
    assert cloud_files.client.__len__() == 1
    
    Path(artifacts_path / 'test_3_release.txt').touch()
    Path(artifacts_path / 'test_3.whl').touch()
    Path(artifacts_path / 'test_3_client.txt').touch()
    Path(artifacts_path / 'test_3_dev.txt').touch()
    
    cloud_manager.upload_to_cloud(prompt=False)
    cloud_files = cloud_manager.list_cloud()
    
    assert set(cloud_files.release) == {'test_2_release.txt', 'test_2.whl', 'test_3_release.txt', 'test_3.whl'}
    assert cloud_files.release.__len__() == 4
    assert set(cloud_files.client) == {'test_2_client.txt', 'test_3_client.txt'}
    assert cloud_files.client.__len__() == 2
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        ftp_rmtree(ftp_conn, cloud_manager._get_project_bucket_path().parent.as_posix())


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_to_cloud_SHOULD_not_upload_files_to_buckets_properly_WHEN_no_match_files(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, artifacts_path = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    Path(artifacts_path / 'test_1.whl').touch()
    Path(artifacts_path / 'test_1_dev.txt').touch()
    time.sleep(1)
    Path(artifacts_path / 'test_2.whl').touch()
    Path(artifacts_path / 'test_2_dev.txt').touch()
    
    cloud_manager.upload_to_cloud(prompt=False)
    cloud_files = cloud_manager.list_cloud()
    
    assert cloud_files is None
    
    
@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_file_to_cloud_SHOULD_upload_file_properly(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, artifacts_path = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    Path(artifacts_path / 'test_1_release.txt').touch()
    Path(artifacts_path / 'test_1.whl').touch()
    
    cloud_manager.upload_file_to_cloud(file_path=artifacts_path / 'test_1_release.txt', bucket_name='release', prompt=False)
    cloud_files = cloud_manager.list_cloud()
    
    assert set(cloud_files.release) == {'test_1_release.txt'}
    assert cloud_files.release.__len__() == 1
    assert cloud_files.client.__len__() == 0
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        ftp_rmtree(ftp_conn, cloud_manager._get_project_bucket_path().parent.as_posix())


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_file_to_cloud_SHOULD_raise_error_when_file_path_not_specified(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, _ = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    with pytest.raises(sicloudman.ValueError) as exc:
        cloud_manager.upload_file_to_cloud(bucket_name='release', prompt=False)
        
    assert 'file_path' in str(exc.value)
        

@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_file_to_cloud_SHOULD_raise_error_when_bucket_name_not_specified(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, _ = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    with pytest.raises(sicloudman.ValueError) as exc:
        cloud_manager.upload_file_to_cloud(file_path='file.txt', prompt=False)
        
    assert 'bucket_name' in str(exc.value)
    
    
@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_file_to_cloud_SHOULD_raise_error_when_file_not_exists(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, _ = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    with pytest.raises(sicloudman.FileNotFoundError):
        cloud_manager.upload_file_to_cloud(file_path='file.txt', bucket_name='release', prompt=False)
        

@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_file_to_cloud_SHOULD_raise_error_when_bucket_not_exists(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, artifacts_path = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    Path(artifacts_path / 'test_1_release.txt').touch()
    
    with pytest.raises(sicloudman.BucketNotFoundError):
        cloud_manager.upload_file_to_cloud(file_path=artifacts_path / 'test_1_release.txt', bucket_name='dummy_bucket', prompt=False)
        

# @pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_dummy(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, artifacts_path = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        cloud_manager._upload_file(ftp_conn, 'file.txt', 'dummy_bucket')
    
    
    assert 0
