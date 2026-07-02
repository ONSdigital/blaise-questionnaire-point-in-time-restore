# Blaise Table Point-in-Time Restore

Provides functionality to perform a point-in-time restore for specific Blaise questionnaire data table. Full database restores should be done via the GCP console.

## How it Works

The service performs the following steps:

1.  **Connects to Databases:** Establishes a connection to both the source (restored backup) and destination (live) Google Cloud SQL for MySQL instances using the Cloud SQL Python Connector.
2.  **Reads Configuration:** Reads database connection details and the target table name from environment variables.
3.  **Copies Data:** Copies the data from the specified table in the source database to the corresponding table in the destination database using SQLAlchemy.

## Prerequisites

-   Python 3.13+
-   [Poetry](https://python-poetry.org/) for dependency management
-   [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud` CLI) installed and authenticated

## Setup & Configuration

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd blaise-point-in-time-restore
    ```

2.  **Install dependencies:**
    ```bash
    poetry install
    ```

3.  **Authenticate with Google Cloud:**
    You need to authenticate your local environment to access Google Cloud resources.

    ```bash
    gcloud auth application-default login
    gcloud config set project <GCP_PROJECT_ID>
    ```

4.  **Create a `.env` file:**
    Create a `.env` file in the root of the project with your specific configuration.

### Environment Variables

| Variable | Description |
| --- | --- |
| `SOURCE_INSTANCE_NAME` | The connection name of the source Cloud SQL instance (the restored backup). |
| `SOURCE_DB_NAME` | The name of the source database. |
| `SOURCE_DB_DRIVER` | The Python MySQL client library to use (e.g., `pymysql`). |
| `SOURCE_DB_URL` | The SQLAlchemy database URL prefix. |
| `SOURCE_DB_USERNAME` | The username for the source database. |
| `SOURCE_DB_PASSWORD` | The password for the source database user. |
| `SOURCE_DB_IP_TYPE` | The IP type for the Cloud SQL connector (`PUBLIC` or `PRIVATE`). Requires VPC access for `PRIVATE`. |
| `DEST_INSTANCE_NAME` | The connection name of the destination Cloud SQL instance (the live instance). |
| `DEST_DB_NAME` | The name of the destination database. |
| `DEST_DB_DRIVER` | The Python MySQL client library to use. |
| `DEST_DB_URL` | The SQLAlchemy database URL prefix. |
| `DEST_DB_USERNAME` | The username for the destination database. |
| `DEST_DB_PASSWORD` | The password for the destination database user. |
| `DEST_DB_IP_TYPE` | The IP type for the Cloud SQL connector (`PUBLIC` or `PRIVATE`). |
| `TABLE_NAME` | The name of the questionnaire table to restore. |

**Note:** To perform the restore, you may need to authorise your local IP address in the "Authorized Networks" section of your Cloud SQL instances if you are using a `PUBLIC` IP connection.

Example `.env` file:

```
# Source Database (Restored Backup)
SOURCE_INSTANCE_NAME="your-gcp-project:your-region:your-restored-instance-name"
SOURCE_DB_NAME="blaise"
SOURCE_DB_DRIVER="pymysql"
SOURCE_DB_URL="mysql+pymysql://"
SOURCE_DB_USERNAME="your-db-user"
SOURCE_DB_PASSWORD="your-db-password"
SOURCE_DB_IP_TYPE="PUBLIC" # or PRIVATE

# Destination Database (Live)
DEST_INSTANCE_NAME="your-gcp-project:your-region:your-live-instance-name"
DEST_DB_NAME="blaise"
DEST_DB_DRIVER="pymysql"
DEST_DB_URL="mysql+pymysql://"
DEST_DB_USERNAME="your-db-user"
DEST_DB_PASSWORD="your-db-password"
DEST_DB_IP_TYPE="PUBLIC" # or PRIVATE

# Table to Restore
TABLE_NAME="LMS2509_KO1_Form"
```

## Usage

Follow these steps to perform a point-in-time restore for a specific questionnaire.

### 1. Find the Backup ID

List the available backups for your SQL instance to find the ID of the backup you want to restore from.

```bash
gcloud sql backups list --instance=YOUR_SQL_INSTANCE_NAME
```

### 2. Create a Restored Instance

Create a new Cloud SQL instance from the selected backup using the Google Cloud Console. Follow the official documentation: [Restoring a Cloud SQL instance](https://cloud.google.com/sql/docs/mysql/backup-recovery/restoring).

### 3. Run the Restore Script

Once the new instance is running and you have configured your `.env` file, run the script to copy the data.

```bash
poetry run python main.py
```
Or using the Makefile:
```bash
make run
```

The script will copy the data for the specified `TABLE_NAME` from the source to the destination instance.

## Development

This project includes a `Makefile` with commands for common development tasks.

-   **Format Code:**
    ```bash
    make format
    ```

-   **Lint Code:**
    ```bash
    make lint
    ```

-   **Run Tests:**
    ```bash
    make test
    ```
