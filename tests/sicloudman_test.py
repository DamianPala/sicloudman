#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import stat
import time
import copy
import pytest
import shutil
import ftplib
import logging
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
    
    expected_content = sicloudman.CLOUD_CREDENTIALS_FILE_TEMPLATE
    expected_content = expected_content.replace('{{server}}', '')
    expected_content = expected_content.replace('{{username}}', '')
    expected_content = expected_content.replace('{{password}}', '')
    expected_content = expected_content.replace('{{main_bucket_path}}', '')
    expected_content = expected_content.replace('{{client_name}}', '')
    expected_content = expected_content.replace('{{project_name}}', '').strip('\n')
    
    assert file_path.read_text() == expected_content
    

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
def test_read_credentials_SHOULD_rise_error_when_field_has_invalid_value(cwd):
    credentials_expected = sicloudman.Credentials(
        server='',
        username='user',
        password='pass',
        main_bucket_path='/',
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


get_main_bucket_first_dir_testdata = [
    ('/main_bucket', '/main_bucket'),
    ('/main_bucket/client/project', '/main_bucket'),
    ('/dir1/main_bucket/client/project', '/dir1'),
    ('/dir1/dir2/main_bucket/client/project', '/dir1'),
    ('/dir1/dir2/main_bucket/project', '/dir1'),
]

@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
@pytest.mark.parametrize("main_pucket_path, first_dir", get_main_bucket_first_dir_testdata)
def test_get_main_bucket_first_dir(main_pucket_path, first_dir, cwd):
    path = sicloudman.CloudManager._get_main_bucket_first_dir(main_pucket_path).as_posix()
    
    assert path == first_dir


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_get_bucket_name_from_filename_SHOULD_return_bucket_name_WHEN_one_keyword(cwd):
    cloud_manager = sicloudman.CloudManager('artifacts',
                                            [sicloudman.Bucket(name='release', keywords=['_release'])], 
                                            credentials_path=TEST_CLOUD_CREDENTIALS_PATH, cwd=cwd)
    
    bucket = cloud_manager._get_bucket_name_from_filename('sample_file_release.whl')
    
    assert bucket == 'release'
    
    
@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_get_bucket_name_from_filename_SHOULD_return_bucket_name_WHEN_many_keywords(cwd):
    cloud_manager = sicloudman.CloudManager('artifacts',
                                            [sicloudman.Bucket(name='release', keywords=['_release']),
                                             sicloudman.Bucket(name='client', keywords=['_client', '.whl'])], 
                                            credentials_path=TEST_CLOUD_CREDENTIALS_PATH, cwd=cwd)
    
    bucket = cloud_manager._get_bucket_name_from_filename('sample_file.whl')
    
    assert bucket == 'client'


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


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_CloudManager_init_SHOULD_raise_error_when_credentials_are_not_credentials(cwd):
    with pytest.raises(sicloudman.TypeError) as exc:
        sicloudman.CloudManager('artifacts', [sicloudman.Bucket(name='release', keywords=['_release'])],
                                credentials={'server': 'serverro'}, cwd=cwd)
    
    assert 'not an instance' in str(exc.value)


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
        main_bucket_path = cloud_manager.credentials.main_bucket_path
        if main_bucket_path == cloud_manager._get_project_bucket_path().parent:
            path_to_rm = cloud_manager._get_project_bucket_path()
        else:
            path_to_rm = cloud_manager._get_project_bucket_path().parent
        if cloud_manager._is_path_exists(ftp_conn, path_to_rm):
            ftp_rmtree(ftp_conn, path_to_rm.as_posix())
    
    return cloud_manager, artifacts_path

    
@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_create_buckets_tree_SHOULD_create_tree_properly_when_simple_main_bucket_path(cwd):
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
def test_create_buckets_tree_SHOULD_create_tree_properly_when_complex_main_bucket_path(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud/test_cloud',
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
def test_create_buckets_tree_SHOULD_raise_error_when_main_bucket_not_exists(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='main_bucket_dummy_dir',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, _ = get_updated_cloud_manager(cwd, bucket_paths,
                                                 [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                  sicloudman.Bucket(name='client', keywords=['_client'])])
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        with pytest.raises(sicloudman.BucketNotFoundError):
            cloud_manager._create_buckets_tree(ftp_conn)


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_list_cloud_SHOULD_print_proper_info_when_no_buckets(cwd, caplog):
    bucket_paths = SimpleNamespace(
        main_bucket_path='main_bucket_dummy_dir',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, _ = get_updated_cloud_manager(cwd, bucket_paths,
                                                 [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                  sicloudman.Bucket(name='client', keywords=['_client'])])
    
    cloud_manager._logger.setLevel(logging.INFO)
    cloud_manager.list_cloud()
    
    assert 'no buckets' in caplog.text


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_list_cloud_SHOULD_print_that_bucket_is_empty_WHEN_bucket_empty(cwd, caplog):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, artifacts_path = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    Path(artifacts_path / 'test_1_release.txt').touch()
    Path(artifacts_path / 'test_1_dev.txt').touch()
    
    cloud_manager._logger.setLevel(logging.INFO)
    cloud_manager.upload_artifacts(prompt=False)
    cloud_manager.list_cloud()
    
    assert 'No files in bucket: client' in caplog.text
    assert 0
        

@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_artifacts_and_list_cloud_SHOULD_upload_files_to_buckets_properly_and_list(cwd):
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
    
    uploaded_files_paths = cloud_manager.upload_artifacts(prompt=False)
    cloud_files = cloud_manager.list_cloud()
    
    assert set(cloud_files.release) == {'test_2_release.txt'}
    assert cloud_files.release.__len__() == 1
    assert set(cloud_files.client) == {'test_2_client.txt'}
    assert cloud_files.client.__len__() == 1
    assert (cloud_manager._get_project_bucket_path() / 'release' / 'test_2_release.txt').as_posix() in uploaded_files_paths
    assert (cloud_manager._get_project_bucket_path() / 'client' / 'test_2_client.txt').as_posix() in uploaded_files_paths
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        ftp_rmtree(ftp_conn, cloud_manager._get_project_bucket_path().parent.as_posix())
        
        
@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_artifacts_SHOULD_upload_files_to_buckets_properly_WHEN_multiple_keywords(cwd):
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
    
    cloud_manager.upload_artifacts(prompt=False)
    cloud_files = cloud_manager.list_cloud()
    
    assert set(cloud_files.release) == {'test_2_release.txt', 'test_2.whl'}
    assert cloud_files.release.__len__() == 2
    assert set(cloud_files.client) == {'test_2_client.txt'}
    assert cloud_files.client.__len__() == 1
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        ftp_rmtree(ftp_conn, cloud_manager._get_project_bucket_path().parent.as_posix())


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_artifacts_SHOULD_upload_files_to_buckets_properly_WHEN_multiple_uploads(cwd):
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
    
    cloud_manager.upload_artifacts(prompt=False)
    cloud_files = cloud_manager.list_cloud()
    
    assert set(cloud_files.release) == {'test_2_release.txt', 'test_2.whl'}
    assert cloud_files.release.__len__() == 2
    assert set(cloud_files.client) == {'test_2_client.txt'}
    assert cloud_files.client.__len__() == 1
    
    Path(artifacts_path / 'test_3_release.txt').touch()
    Path(artifacts_path / 'test_3.whl').touch()
    Path(artifacts_path / 'test_3_client.txt').touch()
    Path(artifacts_path / 'test_3_dev.txt').touch()
    
    cloud_manager.upload_artifacts(prompt=False)
    cloud_files = cloud_manager.list_cloud()
    
    assert set(cloud_files.release) == {'test_2_release.txt', 'test_2.whl', 'test_3_release.txt', 'test_3.whl'}
    assert cloud_files.release.__len__() == 4
    assert set(cloud_files.client) == {'test_2_client.txt', 'test_3_client.txt'}
    assert cloud_files.client.__len__() == 2
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        ftp_rmtree(ftp_conn, cloud_manager._get_project_bucket_path().parent.as_posix())


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_artifacts_SHOULD_upload_one_file_to_many_buckets(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, artifacts_path = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release', '.whl']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    Path(artifacts_path / 'test_1_release.txt').touch()
    Path(artifacts_path / 'test_1_client.whl').touch()
    Path(artifacts_path / 'test_1_dev.txt').touch()
    
    cloud_manager.upload_artifacts(prompt=False)
    cloud_files = cloud_manager.list_cloud()
    
    assert set(cloud_files.release) == {'test_1_release.txt', 'test_1_client.whl'}
    assert cloud_files.release.__len__() == 2
    assert set(cloud_files.client) == {'test_1_client.whl'}
    assert cloud_files.client.__len__() == 1
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        ftp_rmtree(ftp_conn, cloud_manager._get_project_bucket_path().parent.as_posix())


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_artifacts_SHOULD_not_upload_files_to_buckets_properly_WHEN_no_match_files(cwd, caplog):
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
    
    cloud_manager._logger.setLevel(logging.INFO)
    cloud_manager.upload_artifacts(prompt=False)
    cloud_files = cloud_manager.list_cloud()
    
    assert cloud_files is None
    assert 'No files to upload' in caplog.text
    
    
@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_file_SHOULD_upload_file_properly(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, artifacts_path = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    Path(artifacts_path / 'test_1_release.txt').touch()
    Path(artifacts_path / 'test_1.whl').touch()
    
    uploaded_file_path = cloud_manager.upload_file(file_path=artifacts_path / 'test_1_release.txt', bucket_name='release', prompt=False)
    cloud_files = cloud_manager.list_cloud()
    
    assert set(cloud_files.release) == {'test_1_release.txt'}
    assert cloud_files.release.__len__() == 1
    assert cloud_files.client.__len__() == 0
    assert (cloud_manager._get_project_bucket_path() / 'release' / 'test_1_release.txt').as_posix() == uploaded_file_path
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        ftp_rmtree(ftp_conn, cloud_manager._get_project_bucket_path().parent.as_posix())


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_file_SHOULD_upload_file_properly_WHEN_credentials_as_parameter(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, artifacts_path = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    credentials = cloud_manager.credentials
    cloud_manager = sicloudman.CloudManager(artifacts_path,
                                            [sicloudman.Bucket(name='release', keywords=['_release'])], 
                                            credentials=credentials, cwd=cwd)
    
    Path(artifacts_path / 'test_1_release.txt').touch()
    Path(artifacts_path / 'test_1.whl').touch()
    
    uploaded_file_path = cloud_manager.upload_file(file_path=artifacts_path / 'test_1_release.txt', bucket_name='release', prompt=False)
    cloud_files = cloud_manager.list_cloud()
    
    assert set(cloud_files.release) == {'test_1_release.txt'}
    assert cloud_files.release.__len__() == 1
    assert (cloud_manager._get_project_bucket_path() / 'release' / 'test_1_release.txt').as_posix() == uploaded_file_path
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        ftp_rmtree(ftp_conn, cloud_manager._get_project_bucket_path().parent.as_posix())


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_file_SHOULD_print_warning_when_file_already_exists(cwd, caplog):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, artifacts_path = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    Path(artifacts_path / 'test_1_release.txt').touch()
    Path(artifacts_path / 'test_1.whl').touch()
    
    cloud_manager._logger.setLevel(logging.INFO)
    cloud_manager.upload_file(file_path=artifacts_path / 'test_1_release.txt', bucket_name='release', prompt=False)
    
    cloud_manager.upload_file(file_path=artifacts_path / 'test_1_release.txt', bucket_name='release', prompt=False)
    
    assert 'already exists' in caplog.text
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        ftp_rmtree(ftp_conn, cloud_manager._get_project_bucket_path().parent.as_posix())


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_file_SHOULD_raise_error_when_file_path_not_specified(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, _ = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    with pytest.raises(sicloudman.ValueError) as exc:
        cloud_manager.upload_file(bucket_name='release', prompt=False)
        
    assert 'file_path' in str(exc.value)
        

@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_file_SHOULD_raise_error_when_bucket_name_not_specified(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, _ = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    with pytest.raises(sicloudman.ValueError) as exc:
        cloud_manager.upload_file(file_path='file.txt', prompt=False)
        
    assert 'bucket_name' in str(exc.value)
    
    
@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_file_SHOULD_raise_error_when_file_not_exists(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, _ = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    with pytest.raises(sicloudman.FileNotFoundError):
        cloud_manager.upload_file(file_path='file.txt', bucket_name='release', prompt=False)
        

@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_upload_file_SHOULD_raise_error_when_bucket_not_exists(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, artifacts_path = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    Path(artifacts_path / 'test_1_release.txt').touch()
    
    with pytest.raises(sicloudman.BucketNotFoundError):
        cloud_manager.upload_file(file_path=artifacts_path / 'test_1_release.txt', bucket_name='dummy_bucket', prompt=False)


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_download_file_SHOULD_raise_error_when_bucket_not_found(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, _ = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    with pytest.raises(sicloudman.FileNotFoundError):
        cloud_manager.download_file(filename='file.txt')


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_download_file_SHOULD_raise_error_when_file_not_on_cloud(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, _ = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    with pytest.raises(sicloudman.FileNotFoundError) as exc:
        cloud_manager.download_file(filename='file_release.whl')
    
    assert 'bucket' not in str(exc).lower()


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_download_file_SHOULD_download_file_properly(cwd):
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
    
    cloud_manager.upload_artifacts(prompt=False)
    
    shutil.rmtree(artifacts_path)

    downloaded_file_path = cloud_manager.download_file(filename='test_1.whl')
    
    assert (artifacts_path / 'test_1.whl') in set(artifacts_path.iterdir())
    assert downloaded_file_path == (artifacts_path / 'test_1.whl').as_posix()
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        ftp_rmtree(ftp_conn, cloud_manager._get_project_bucket_path().parent.as_posix())


@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_download_file_SHOULD_not_download_file_if_already_exists(cwd, caplog):
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
    
    cloud_manager._logger.setLevel(logging.INFO)
    cloud_manager.upload_artifacts(prompt=False)
    
    cloud_manager.download_file(filename='test_1.whl')
    
    assert (artifacts_path / 'test_1.whl') in set(artifacts_path.iterdir())
    assert 'test_1.whl already exists' in caplog.text
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        ftp_rmtree(ftp_conn, cloud_manager._get_project_bucket_path().parent.as_posix())









@pytest.mark.skip()
@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_dummy2(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client_dummy',
        project_name='sicloudman_project')
    cloud_manager, artifacts_path = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release', '.whl']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])

    
#     with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
#         pprint(ftp_conn.retrlines('FEAT'))
    
    
    assert 0


@pytest.mark.skip()
@pytest.mark.skipif(RUN_ALL_TESTS == False, reason='Skipped on demand')
def test_dummy(cwd):
    bucket_paths = SimpleNamespace(
        main_bucket_path='fw_cloud',
        client_name='sicloudman_client',
        project_name='sicloudman_project')
    cloud_manager, artifacts_path = get_updated_cloud_manager(cwd, bucket_paths,
                                                              [sicloudman.Bucket(name='release', keywords=['_release']), 
                                                               sicloudman.Bucket(name='client', keywords=['_client'])])
    
    with ftplib.FTP(cloud_manager.credentials.server, cloud_manager.credentials.username, cloud_manager.credentials.password) as ftp_conn:
        cloud_manager._upload_file_to_bucket(ftp_conn, 'file.txt', 'dummy_bucket')
    
    
    assert 0
