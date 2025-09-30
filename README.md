# Blaise Point In Time Restore
This Python Service provides functionality to perform Blaise Point in time restore.  



[![codecov](https://codecov.io/gh/ONSdigital/blaise-point-in-time-restore/branch/main/graph/badge.svg)](https://codecov.io/gh/ONSdigital/blaise-point-in-time-restore)
[![CI status](https://github.com/ONSdigital/blaise-point-in-time-restore/workflows/Test%20coverage%20report/badge.svg)](https://github.com/ONSdigital/blaise-point-in-time-restore/workflows/Test%20coverage%20report/badge.svg)
<img src="https://img.shields.io/github/release/ONSdigital/blaise-point-in-time-restore.svg?style=flat-square" alt="Blaise Point In Time Restore release verison">

If whole SQL Instance needs to be restored i-e, all the Questionnaires within SQL Instance, recommended solution is to perform restore from Google Cloud Console. https://cloud.google.com/sql/docs/mysql/backup-recovery/restoring

This service helps with PITR, and supports cloning SQL instance from desired Backup Instance and copy specific Questionnaire table data to the active SQL Instance's Questionnaire table.


### Setup for Local development

| Environment Variable | Description                                                                                                                                                                                                                                    | Example                            |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------|
| SOURCE_INSTANCE_NAME   | Name of the source SQL instance created from backup.                                                                                                                                                                            | `ons-blaise-v2-dev-rr4:europe-west2:blaise-dev-backup-restore`                         |
| SOURCE_DB_NAME    | Name of the database.                                                                                                                                                                                    | `blaise`             |
| SOURCE_DB_DRIVER     | Python MySQL client library that is used to to communicate with the MySQL database.                                                                                                                          | `pymysql`         |
| SOURCE_DB_URL            | This is the SQLAlchemy database URL, which tells SQLAlchemy which database type and driver to use.                                                                                                                                                                                                         | `mysql+pymysql://`                               |
| SOURCE_DB_USERNAME            | Valid username of existing user with access to the database.                                                                                                                                                                                                         | `blaise`                        |
| SOURCE_DB_PASSWORD        | Valid password for the username provided.                                                                                                                                                                                                         | `abcd1234`                        |
| SOURCE_DB_IP_TYPE        | Determines which IP type the Cloud SQL connector will use. PUBLIC is used if Public IP allowed. However, for PRIVATE IP, it will require VPC access.                                                                                                                                                                                                     | `PUBLIC OR PRIVATE`                   |
| DEST_INSTANCE_NAME       | Name of the destination SQL instance where we need to copy the data from restored backup instance. | `ons-blaise-v2-dev-rr4:europe-west2:blaise-dev`                     |
| DEST_DB_NAME          | Name of the database.                                                                                                                                                                | `blaise`                            |
| DEST_DB_DRIVER           | Python MySQL client library that is used to to communicate with the MySQL database.                                                                                                                                                                    | `pymysql`                |
| DEST_DB_URL | This is the SQLAlchemy database URL, which tells SQLAlchemy which database type and driver to use                                                                                                                                                                                                                           | `mysql+pymysql://`  |
| DEST_DB_USERNAME     | Valid username of existing user with access to the database.                                                                                                           | `blaise` |
| DEST_DB_PASSWORD        | Valid password for the username provided.                                                                                                                                                                                                         | `abcd1234`                        |
| SOURCE_DB_IP_TYPE        | Determines which IP type the Cloud SQL connector will use. PUBLIC is used if Public IP allowed. However, for PRIVATE IP, it will require VPC access.                                                                                                                                                                                                     | `PUBLIC OR PRIVATE`                   |
| TABLE_NAME        | Name of the Questionnaire Table that needs to be restored from restored backup instance.                                                                                                                                                               | `LMS2509_KO1_Form`                   |

Create a .env file with the following environment variables:

```
# Source database
SOURCE_INSTANCE_NAME=ons-blaise-v2-dev-rr4:europe-west2:blaise-dev-restored-backup
SOURCE_DB_NAME=database
SOURCE_DB_DRIVER=pymysql
SOURCE_DB_URL=mysql+pymysql://
SOURCE_DB_USERNAME=blaise
SOURCE_DB_PASSWORD=abcd1234
SOURCE_DB_IP_TYPE=PUBLIC

# Destination database
DEST_INSTANCE_NAME=gcp-project:europe-west2:blaise-dev-actual
DEST_DB_NAME=database
DEST_DB_DRIVER=pymysql
DEST_DB_URL=mysql+pymysql://
DEST_DB_USERNAME=user
DEST_DB_PASSWORD=abcd1234
DEST_DB_IP_TYPE=PUBLIC

# Common table name for restore
TABLE_NAME="LMS2509_KO1_Form"
```

This configuration will attempt to restore data for specific Questionnaire i-e, LMS2509_KO1_Form from restored backup instance into actual SQL Instance.

##### Authentication for Successful Restore:

Run the following gcloud command to authenticate from local VS code terminal to successfully run the python code: 

```bash
gcloud auth application-default login
```

Then set the intented GCP project in the config by running following command:
```bash
gcloud config set project <GCP_PROJECT_ID>
```

##### Install dependencies:

```
poetry install
```

## Running Development Tasks

This project includes a `Makefile` with common development commands.

-   **Format:**
    Formats the code.
    ```bash
    make format
    ```

-   **Lint:**
    Checks code quality.
    ```bash
    make lint
    ```

-   **Test:**
    Executes test suite.
    ```bash
    make test
    ```

-   **Restore data for specific Questionnaire:** 
    Execute main.py
    ```bash
    poetry run python main.py
    ```
    
Copyright (c) 2021 Crown Copyright (Government Digital Service)
