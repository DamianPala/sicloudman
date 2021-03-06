# Sicloudman

Sicloudman is a simple cloud manager for easy and convenient storage of your software packages, releases, builds etc. This tool is designed as a support for software development. It is like a bridge between your project and the cloud server. You can easily integrate it with your project and easily upload the project output to the cloud, for instance to share files with your client.

To communicate with a server Sicloudman uses FTP connection. Credentials used in a connection with the server are stored in the `cloud_credentials.txt` file.

Sicloudman is intended to use only as a python module.


## Requirements

Python >= 3.7

Server with:

- an account with read and write access
- support for the MLSD command

## Convention

Sicloudman has some basic features:

- upload artifacts
- upload specified file
- list cloud
- download specified file

### Upload Artifacts

Files on a cloud server are stored in buckets. In the case when you have multiple project configurations where different output files or builds are generated then you can automatically separate them and upload to different buckets. It means that a project configuration which produce distinguishable files regarding functionality is intended for storing in a separate bucket.

Sicloudman **searches recursively** specified location where your project output files are generated and automatically detects which files belongs to which buckets and upload these files into the cloud server.

Only a latest created file belonging to the given project configuration - bucket will be uploaded.

To upload artifacts use `upload_artifacts` method.

When uploading process is finished, the existence of uploaded files is finally confirmed.

> If a file already exists on the server it will not be overwritten and an appropriate warning will be printed.
>
> Buckets configured during initialization are only ones that are relevant. If there are other buckets in the specified server location they will not be taken into account.

#### File distunguishing

The process of distinguishing which file belongs to which bucket is based on the file name. During initialization of `CloudManager` class you have to specify a list of `Buckets`. A `bucket` object has two properties: a `name` and `keywords`. When `upload_artifacts` method is called, artifacts are scanned and proper files are selected when their name contains keyword from `keywords` parameter of given bucket. Only latest created files are uploaded to the cloud server.

> One file can be uploaded to many buckets. To achieve this add keywords to the file name that belongs to many buckets.

### Upload Specified File

It is possible to specify manually which file should be uploaded to a given cloud bucket. In case like this use `upload_file` method.

### List Cloud

All files from all buckets can be listed from your cloud sever using the `list_cloud` method.

### Download File

By using the `download_file` method you can download a file specified by the name to your artifacts location. In the case when in an artifacts location exists directories named as buckets on the server then downloaded file will be placed directly in the first matched directory corresponding to the bucket name. When the `filename` parameter is not provided then a file name will be prompted in command line.

> If a file already exists in an artifacts location it will not be overwritten and an appropriate warning will be printed.
>
> If the same file is stored in many buckets it will be downloaded from the first matched bucket.

### File Removal

There are no way to remove already uploaded files. This is a deliberate implementation to protect the cloud from unintended deletion of stored files. When you want to remove a file, you should do it manually using other tool.

## Configuration

The main configuration is injected during the initialization of the `CloudManager`. Initialization parameters are:

- `artifacts_path` - path where files to upload are sought
- `buckets_list` - list of used buckets
- `credentials` - object of the `Credentials` class (optional parameter).
- `credentials_path` - path where the `cloud_credentials.txt` file is stored. By default this file is searched in the current working directory (optional parameter).
- `get_logger` - function that returns a logger object (optional parameter).

The rest of configuration is stored in the `cloud_credentials.txt` file or can be injected via a `credentials` parameter.

### cloud_credentials.txt

- `server` - your server address 
- `username` - a ftp client username
- `password` - a ftp client password
- `main_bucket_path` - a directory where your files will be stored
- `client_name` - a name of the client directory in the `main bucket`
- `project_name` - a name of the project directory in the `main bucket` or `client` directory

The final path, where files will be stored is constructed from the `main_bucket_path `, `client_name `, `project_name `. For instance where all of them is specified then the path will look like following:

```
<main_bucket_path>/<client_name>/<project_name>
```

If the `client_name` or `project_name` will be omitted (for example `client_name`) , final path is constructed like this:

```
<main_bucket_path>/<project_name>
```

Only the `main_bucket_path` path is mandatory.

> `main_bucket_path`  must contain a parent directory e.g. `main_bucket_path = /fw_cloud` . Cannot be root('/'). If only the parent directory exists the rest directories will be created.

#### How to create cloud_credentials.txt file

The `cloud_credentials.txt` file can be easily created using the `touch_credentials` method.

Another way is to prepare from the following template:

```
# This file must not be commited! It contains confidentials.
server = 
username = 
password = 

# The path when you store files
# The Final Path will be: <main_bucket_path>/<client_name>/<project_name>
main_bucket_path = 
# Leave empty if not attached to the final path
client_name = 
# Leave empty if not attached to the final path
project_name = 
```

