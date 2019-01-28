# Assumptions
- do not change module code
- settings must be set by fucntion argument, or modification module state variable
- on cloud could many buckets 
- mlsd server required
- check if file is uploeaded properly feature
- upload specified file to specified bucket
- file name cannot containt keywords from different buckets
- check if file downloaded is actually in download dir
- buckets configured in CLoudManager are only valid. Additional buckets from server are omitted.

## List Cloud
- list all of bucket on server

## Cloud Upload
- upload files from artifacts dir
- all latest generated files must be uploaded with sorting to proper bucket

# Config
- cwd
- artifacts path
- credential file path
- bucket: file-trait dict


