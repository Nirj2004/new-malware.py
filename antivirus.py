#! /usr/bin/env bash
##########################################
# DO NOT MAKE LOCAL CHANGES TO THIS FILE #
#                                        #
# Vars in this file can be overridden by #
# exporting them in .envrc.local         #
##########################################
# Add local paths for binaries and scripts

# ShellCheck complains about things like `foo=$(cmd)` because you lose the
# return value of `cmd`. That said, we're not using `set -e`, so we aren't
# really concerned about return values. The following `true`, applies the
# rule to the entire file.
# See: https://github.com/koalaman/shellcheck/wiki/SC2155
# shellcheck disable=SC2155
true
required_vars=()
var_docs=()
# Declare an environment variable as required.
#
#   require VAR_NAME "Documentation about how to define valid values"

# Check all variables declared as required. If any are missing, print a message and
# exit with a non-zero status.
check_required_variables() {
for i in "${!required_vars[@]}"; do
 var=${required_vars[i]}
    if [[ -z "${!var}" ]]; then
      log_status "${var} is not set: ${var_docs[i]}"
      missing_var=true
    fi
  done
  if [[ $missing_var == "true" ]]; then
    log_error "Your environment is missing some variables!"
    log_error "Set the above variables in .envrc.local and try again."
  fi
}
#########################
# Project Configuration #
#########################

# Lamdba resource constraints (Override in .envrc.local)
# https://docs.docker.com/config/containers/resource_constraints/
export MEM= 512m
export MEM= 1024m
export CPUS=1.0

require AV_DEFINITION_S3_BUCKET "Add this variable to your .envrc.local"
require AV_DEFINITION_S3_PREFIX "Add this variable to your .envrc.local"
require TEST_BUCKET "Add this variable to your .envrc.local"
require TEST_KEY "Add this variable to your .envrc.local"
##############################################
# Load Local Overrides and Check Environment #
##############################################
# Load a local overrides file. Any changes you want to make for your local
# environment should live in that file.
if [ -e .envrc.local ]
then
  source_env .envrc.local
fi
# Check that all required environment variables are set
check_required_variables
  2  .envrc.local.template 
@@ -1,20 +1,20 @@
#! /usr/bin/env bash
#
# Copy this file `cp .envrc.local.template .envrc.local` and modify the variables below for testing
#
# Optional AWS Parameters
# WARNING: It's not recommended to keep credentials in this file!
# export AWS_ACCESS_KEY_ID
# export AWS_DEFAULT_REGION
# export AWS_REGION
# export AWS_SECRET_ACCESS_KEY
# export AWS_SESSION_TOKEN

# Lamdba resource constraints you can override here
# https://docs.docker.com/config/containers/resource_constraints/
# export MEM=512m
# export MEM=1024m
# export CPUS=1.0

# Required for both scan and update lambdas scripts
export AV_DEFINITION_S3_BUCKET=""
export AV_DEFINITION_S3_PREFIX=""
# Required for scan lambda script
export TEST_BUCKET=""
export TEST_KEY=""
# Uncomment and change as needed for lambda scripts
# export AV_DEFINITION_FILE_PREFIXES
# export AV_DEFINITION_FILE_SUFFIXES
# export AV_DEFINITION_PATH
# export AV_DELETE_INFECTED_FILES
# export AV_PROCESS_ORIGINAL_VERSION_ONLY
# export AV_SCAN_START_METADATA
# export AV_SCAN_START_SNS_ARN
# export AV_SIGNATURE_METADATA
# export AV_SIGNATURE_OK
# export AV_SIGNATURE_UNKNOWN
# export AV_STATUS_CLEAN
# export AV_STATUS_INFECTED
# export AV_STATUS_METADATA
# export AV_STATUS_SNS_ARN
# export AV_STATUS_SNS_PUBLISH_CLEAN
# export AV_STATUS_SNS_PUBLISH_INFECTED
# export AV_TIMESTAMP_METADATA
# export CLAMAVLIB_PATH
# export CLAMSCAN_PATH
# export FRESHCLAM_PATH
  2  README.md 
@@ -1,139 +1,139 @@
# bucket-antivirus-function
[![CircleCI](https://circleci.com/gh/upsidetravel/bucket-antivirus-function.svg?style=svg)](https://circleci.com/gh/upsidetravel/bucket-antivirus-function)
Scan new objects added to any s3 bucket using AWS Lambda. [more details in this post](https://engineering.upside.com/s3-antivirus-scanning-with-lambda-and-clamav-7d33f9c5092e)
## Features
- Easy to install
- Send events from an unlimited number of S3 buckets
- Prevent reading of infected files using S3 bucket policies
- Accesses the end-user’s separate installation of
open source antivirus engine [ClamAV](http://www.clamav.net/)
## How It Works
![architecture-diagram](../master/images/bucket-antivirus-function.png)
- Each time a new object is added to a bucket, S3 invokes the Lambda
function to scan the object
- The function package will download (if needed) current antivirus
definitions from a S3 bucket. Transfer speeds between a S3 bucket and
Lambda are typically faster and more reliable than another source
- The object is scanned for viruses and malware.  Archive files are
extracted and the files inside scanned also
- The objects tags are updated to reflect the result of the scan, CLEAN
or INFECTED, along with the date and time of the scan.
- Object metadata is updated to reflect the result of the scan (optional)
- Metrics are sent to [DataDog](https://www.datadoghq.com/) (optional)
- Scan results are published to a SNS topic (optional) (Optionally choose to only publish INFECTED results)
- Files found to be INFECTED are automatically deleted (optional)
## Installation
### Build from Source
To build the archive to upload to AWS Lambda, run `make`.  The build process is completed using
the [amazonlinux](https://hub.docker.com/_/amazonlinux/) [Docker](https://www.docker.com)
 image.  The resulting archive will be built at `build/lambda.zip`.  This file will be
 uploaded to AWS for both Lambda functions below.
### AV Definition Bucket
 Create an s3 bucket to store current antivirus definitions.  This
 provides the fastest download speeds for the scanner.  This bucket can
 be kept as private.
 To allow public access, useful for other accounts,
 add the following policy to the bucket.
 #json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPublic",
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:GetObject",
                "s3:GetObjectTagging"
            ],
            "Resource": "arn:aws:s3:::<bucket-name>/*"
        }
    ]
}
```
### Definition Update Lambda
This function accesses the user’s ClamAV instance to download
updated definitions using `freshclam`.  It is recommended to run
this every 3 hours to stay protected from the latest threats.
1. Create the archive using the method in the
 [Build from Source](#build-from-source) section.
2. From the AWS Lambda Dashboard, click **Create function**
3. Choose **Author from scratch** on the *Create function* page
4. Name your function `bucket-antivirus-update` when prompted on the
*Configure function* step.
5. Set *Runtime* to `Python 2.7`
6. Create a new role name `bucket-antivirus-update` that uses the
following policy document
 #json
    {
       "Version":"2012-10-17",
       "Statement":[
          {
             "Sid":"WriteCloudWatchLogs",
             "Effect":"Allow",
             "Action":[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
             ],
             "Resource":"*"
          },
          {
             "Sid":"s3GetAndPutWithTagging",
             "Action":[
                "s3:GetObject",
                "s3:GetObjectTagging",
                "s3:PutObject",
                "s3:PutObjectTagging",
                "s3:PutObjectVersionTagging"
             ],
             "Effect":"Allow",
             "Resource":[
                "arn:aws:s3:::<av-definition-s3-bucket>/*"
             ]
          },
          {
             "Sid": "s3HeadObject",
             "Effect": "Allow",
             "Action": "s3:ListBucket",
             "Resource": [
                 "arn:aws:s3:::<av-definition-s3-bucket>/*",
                 "arn:aws:s3:::<av-definition-s3-bucket>"
             ]
          }
       ]
    }
    ```
7. Click next to go to the Configuration page
8. Add a trigger from the left of **CloudWatch Event** using `rate(3 hours)`
for the **Schedule expression**.  Be sure to check **Enable trigger**
9. Choose **Upload a ZIP file** for *Code entry type* and select the archive
downloaded in step 1.
10. Add a single environment variable named `AV_DEFINITION_S3_BUCKET`
and set its value to the name of the bucket created to store your AV
definitions.
11. Set *Lambda handler* to `update.lambda_handler`
12. Under *Basic Settings*, set *Timeout* to **5 minutes** and *Memory* to
**512**
**1024**
13. Save and test your function.  If prompted for test data, just use
the default provided.

### AV Scanner Lambda
1. Create the archive using the method in the
 [Build from Source](#build-from-source) section.
2. From the AWS Lambda Dashboard, click **Create function**
3. Choose **Author from scratch** on the *Create function* page
4. Name your function `bucket-antivirus-function`
5. Set *Runtime* to `Python 2.7`
6. Create a new role name `bucket-antivirus-function` that uses the
following policy document
    ```json
    {
       "Version":"2012-10-17",
       "Statement":[
          {
             "Sid":"WriteCloudWatchLogs",
             "Effect":"Allow",
             "Action":[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
             ],
             "Resource":"*"
          },
          {
             "Sid":"s3AntiVirusScan",
             "Action":[
                "s3:GetObject",
                "s3:GetObjectTagging",
                "s3:GetObjectVersion",
                "s3:PutObjectTagging",
                "s3:PutObjectVersionTagging"
             ],
             "Effect":"Allow",
             "Resource": [
               "arn:aws:s3:::<bucket-name-1>/*",
               "arn:aws:s3:::<bucket-name-2>/*"
             ]
          },
          {
             "Sid":"s3AntiVirusDefinitions",
             "Action":[
                "s3:GetObject",
                "s3:GetObjectTagging"
             ],
             "Effect":"Allow",
             "Resource": [
               "arn:aws:s3:::<av-definition-s3-bucket>/*"
             ]
          },
          {
             "Sid":"kmsDecrypt",
             "Action":[
                "kms:Decrypt"
             ],
             "Effect":"Allow",
             "Resource": [
               "arn:aws:s3:::<bucket-name-1>/*",
               "arn:aws:s3:::<bucket-name-2>/*"
             ]
          },
          {
             "Sid":"snsPublish",
             "Action": [
                "sns:Publish"
             ],
             "Effect":"Allow",
             "Resource": [
               "arn:aws:sns:::<av-scan-start>",
               "arn:aws:sns:::<av-status>"
             ]
          },
          {
             "Sid":"s3HeadObject",
             "Effect":"Allow",
             "Action":"s3:ListBucket",
             "Resource":[
                 "arn:aws:s3:::<av-definition-s3-bucket>/*",
                 "arn:aws:s3:::<av-definition-s3-bucket>"
             ]
          }
       ]
    }
    ```
7. Click *next* to head to the Configuration page
8. Add a new trigger of type **S3 Event** using `ObjectCreate(all)`.
9. Choose **Upload a ZIP file** for *Code entry type* and select the archive
created in step 1.
10. Set *Lambda handler* to `scan.lambda_handler`
11. Add a single environment variable named `AV_DEFINITION_S3_BUCKET`
and set its value to the name of the bucket created to store your AV
definitions. If your bucket is `s3://my-bucket`, the value should be `my-bucket`.
12. Under *Basic settings*, set *Timeout* to **5 minutes** and *Memory* to
**1024**
13. Save the function.  Testing is easiest performed by uploading a
file to the bucket configured as the trigger in step 4.
### S3 Events
Configure scanning of additional buckets by adding a new S3 event to
invoke the Lambda function.  This is done from the properties of any
bucket in the AWS console.
![s3-event](../master/images/s3-event.png)
Note: If configured to update object metadata, events must only be
configured for `PUT` and `POST`. Metadata is immutable, which requires
the function to copy the object over itself with updated metadata. This
can cause a continuous loop of scanning if improperly configured.
## Configuration
Runtime configuration is accomplished using environment variables.  See
the table below for reference.
| Variable | Description | Default | Required |
| --- | --- | --- | --- |
| AV_DEFINITION_S3_BUCKET | Bucket containing antivirus definition files |  | Yes |
| AV_DEFINITION_S3_PREFIX | Prefix for antivirus definition files | clamav_defs | No |
| AV_DEFINITION_PATH | Path containing files at runtime | /tmp/clamav_defs | No |
| AV_SCAN_START_SNS_ARN | SNS topic ARN to publish notification about start of scan | | No |
| AV_SCAN_START_METADATA | The tag/metadata indicating the start of the scan | av-scan-start | No |
| AV_SIGNATURE_METADATA | The tag/metadata name representing file's AV type | av-signature | No |
| AV_STATUS_CLEAN | The value assigned to clean items inside of tags/metadata | CLEAN | No |
| AV_STATUS_INFECTED | The value assigned to clean items inside of tags/metadata | INFECTED | No |
| AV_STATUS_METADATA | The tag/metadata name representing file's AV status | av-status | No |
| AV_STATUS_SNS_ARN | SNS topic ARN to publish scan results (optional) | | No |
| AV_STATUS_SNS_PUBLISH_CLEAN | Publish AV_STATUS_CLEAN results to AV_STATUS_SNS_ARN | True | No |
| AV_STATUS_SNS_PUBLISH_INFECTED | Publish AV_STATUS_INFECTED results to AV_STATUS_SNS_ARN | True | No |
| AV_TIMESTAMP_METADATA | The tag/metadata name representing file's scan time | av-timestamp | No |
| CLAMAVLIB_PATH | Path to ClamAV library files | ./bin | No |
| CLAMSCAN_PATH | Path to ClamAV clamscan binary | ./bin/clamscan | No |
| FRESHCLAM_PATH | Path to ClamAV freshclam binary | ./bin/freshclam | No |
| DATADOG_API_KEY | API Key for pushing metrics to DataDog (optional) | | No |
| AV_PROCESS_ORIGINAL_VERSION_ONLY | Controls that only original version of an S3 key is processed (if bucket versioning is enabled) | False | No |
| AV_DELETE_INFECTED_FILES | Controls whether infected files should be automatically deleted | False | No |
| EVENT_SOURCE | The source of antivirus scan event "S3" or "SNS" (optional) | S3 | No |
## S3 Bucket Policy Examples
### Deny to download the object if not "CLEAN"
This policy doesn't allow to download the object until:
1. The lambda that run Clam-AV is finished (so the object has a tag)
2. The file is not CLEAN
Please make sure to check cloudtrail for the arn:aws:sts, just find the event open it and copy the sts.
It should be in the format provided below:
```json
 {
    "Effect": "Deny",
    "NotPrincipal": {
        "AWS": [
            "arn:aws:iam::<<aws-account-number>>:role/<<bucket-antivirus-role>>",
            "arn:aws:sts::<<aws-account-number>>:assumed-role/<<bucket-antivirus-role>>/<<bucket-antivirus-role>>",
            "arn:aws:iam::<<aws-account-number>>:root"
        ]
    },
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::<<bucket-name>>/*",
    "Condition": {
        "StringNotEquals": {
            "s3:ExistingObjectTag/av-status": "CLEAN"
        }
    }
}
```
### Deny to download and re-tag "INFECTED" object
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": ["s3:GetObject", "s3:PutObjectTagging"],
      "Principal": "*",
      "Resource": ["arn:aws:s3:::<<bucket-name>>/*"],
      "Condition": {
        "StringEquals": {
          "s3:ExistingObjectTag/av-status": "INFECTED"
        }
      }
    }
  ]
}
```
## Manually Scanning Buckets
You may want to scan all the objects in a bucket that have not previously been scanned or were created
prior to setting up your lambda functions. To do this you can use the `scan_bucket.py` utility.
```sh
pip install boto3
scan_bucket.py --lambda-function-name=<lambda_function_name> --s3-bucket-name=<s3-bucket-to-scan>
```
This tool will scan all objects that have not been previously scanned in the bucket and invoke the lambda function
asynchronously. As such you'll have to go to your cloudwatch logs to see the scan results or failures. Additionally,
the script uses the same environment variables you'd use in your lambda so you can configure them similarly.
## Testing
There are two types of tests in this repository. The first is pre-commit tests and the second are python tests. All of
these tests are run by CircleCI.
### pre-commit Tests
The pre-commit tests ensure that code submitted to this repository meet the standards of the repository. To get started
with these tests run `make pre_commit_install`. This will install the pre-commit tool and then install it in this
repository. Then the github pre-commit hook will run these tests before you commit your code.
To run the tests manually run `make pre_commit_tests` or `pre-commit run -a`.
### Python Tests
The python tests in this repository use `unittest` and are run via the `nose` utility. To run them you will need
to install the developer resources and then run the tests:
```sh
pip install -r requirements-dev.txt
make test
```
### Local lambdas
You can run the lambdas locally to test out what they are doing without deploying to AWS. This is accomplished
by using docker containers that act similarly to lambda. You will need to have set up some local variables in your
`.envrc.local` file and modify them appropriately first before running `direnv allow`. If you do not have `direnv`
it can be installed with `brew install direnv`.
For the Scan lambda you will need a test file uploaded to S3 and the variables `TEST_BUCKET` and `TEST_KEY`
set in your `.envrc.local` file. Then you can run:
```sh
direnv allow
make archive scan

If you want a file that will be recognized as a virus you can download a test file from the [EICAR](https://www.eicar.org/?page_id=3950)
website and uploaded to your bucket.
For the Update lambda you can run:
'''sh
direnv allow
make archive update
'''
## License
#text