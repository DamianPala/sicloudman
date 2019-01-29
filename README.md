# Sicloudman

Sicloudman is a simple cloud manager for simple and convenient storage of your software packages, releases, builds etc. This tool is designed as a support for software development. It is like a bridge between your project and the cloud server. You can easily integrate it with your project and simply upload the project output to cloud for instance to share these files with your client.

To communicate with a server Sicloudman uses FTP connection. Credentials used in a connection with the server are stored in `cloud_credentials.txt` file.

Sicloudman is intended to use only as a python module.

## Convention

Sicloudman has 3 basic features:

- upload artifacts
- upload specified file
- list cloud
- download specified file

### Upload Artifacts

Files on a cloud server are stored in buckets. In the case when you have multiple project configurations where different output files, builds are generated then you can automatically separate them and upload to different buckets. It means that a project configuration which produce distinguishable files regarding functionality is intended for storing in a separate bucket.

Sicloudman searches specified location where your project output files are and automatically detects which files belongs to which buckets and upload these files into the cloud server.

Only a latest created file belonging to the given project configuration - bucket will be uploaded.

To upload artifacts use `upload_artifacts` function.

#### File distunguishing

The process of distinguishing which file belongs to which bucket is based on the file name. During initialization of `CloudManager` class you have to specify a list of `Buckets`. `Bucket` object has two properties: `name` and `keywords`. When `upload_artifacts` function is called, artifacts are scanned and proper files are selected when their name contains keyword from `keywords` parameter of given bucket. Only latest created file are uploaded to the cloud server.

### Upload Specified File

There is possibility to manually specify of which file should be uploaded to given cloud bucket. In case like this use `upload_file` function.

### List Cloud

All files from all buckets can be listed from your cloud sever using `list_cloud` function.

### Download File

Using `download_file` function you can download specified file by name to your artifacts location.

## Configuration

Main configuration is injected during initialization of `CloudManager`. It contains parameters:

- `artifacts_path` - path where files to upload are seek
- `buckets_list` - list of used buckets
- `credentials_path` - path where `cloud_credentials.txt` file is stored. By default this file is searched in current working directory.
- `get_logger` - function that returns logger object.

The rest of configuration is stored in `cloud_credentials.txt` file.

### cloud_credentials.txt

- `server` - your server address 
- `username` - ftp client username
- `password` - ftp client password
- `main_bucket_path` - a directory where your files will be stored
- `client_name` - a name of the client directory in `main bucket`
- `project_name` - a name of project directory in the `main bucket` or `client` directory

Final path, where files will be stored is constructed from `main_bucket_path `, `client_name `, `project_name `. For instance where all of them is specified then path will look like following:

```
<main_bucket_path>/<client_name>/<project_name>
```

If `client_name` or `project_name` will be omitted (for example `client_name`) , final path is constructed like this:

```
<main_bucket_path>/<project_name>
```

Only `main_bucket_path` path is mandatory.

> `main_bucket_path`  must contain parent directory e.g. `main_bucket_path = /fw_cloud` . Cannot be root('/'). If only parent directory is exists the rest directory will be created.



TODO: credentials file can be touched!















#### File Removal

There are no way to remove already uploaded files. This is deliberately implementation to protected the cloud from unintended deletion of archival files. When you want to remove a files, you should do it manually using other tool.





















# Assumptions

- mlsd server required
- check if file is uploeaded properly feature
- upload specified file to specified bucket
- file name cannot containt keywords from different buckets
- check if file downloaded is actually in download dir
- buckets configured in CLoudManager are only valid. Additional buckets from server are omitted.
