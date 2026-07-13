# Blaise Questionnaire Point-in-Time Restore 🔄

This function restores questionnaire data for a specific point in time by creating a temporary Cloud SQL clone, exporting the questionnaire tables to GCS, and importing them into the live database.

Full instance-level restore operations are still done through the GCP console.

## Current Execution Model

You run a wrapper script with two parameters:

- `questionnaire_name`
- `timestamp` (for example `2026-07-08 14:30:00`)

The wrapper script then:

1. Creates a temporary service account.
2. Grants required IAM roles.
3. Deploys a temporary HTTP Cloud Function.
4. Invokes that function with your parameters.
5. Cleans up the temporary Cloud Function and service account.

Inside the Cloud Function, the Python application:

1. Builds a point-in-time clone of the source Cloud SQL instance.
2. Exports questionnaire tables from the clone to GCS.
3. Imports those exported SQL files into the destination instance.
3. Deletes the temporary Cloud SQL clone.

## What Gets Restored

The restore currently targets two tables per questionnaire:

- `<QUESTIONNAIRE_NAME>_Dml`
- `<QUESTIONNAIRE_NAME>_Form`

The destination table is restored from SQL export files generated from the clone.

## Prerequisites

- Python 3.13+
- [Poetry](https://python-poetry.org/) for dependency management
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud` CLI) installed and authenticated
- Permissions to create/delete service accounts, deploy Cloud Functions, manage Cloud SQL, and invoke Cloud Functions

## Setup

1. Clone the repository and install dependencies:

```bash
git clone https://github.com/ONSdigital/blaise-questionnaire-point-in-time-restore.git
cd blaise-questionnaire-point-in-time-restore
poetry install
```

2. Authenticate with Google Cloud:

```bash
gcloud auth application-default login
gcloud auth login
gcloud config set project <GCP_PROJECT_ID>
```

## Configuration

No runtime environment variables are required or supported for restore behavior.

The function discovers everything from the authenticated project context:

- Active project from ADC/gcloud auth context
- Destination Cloud SQL instance from the project instances list
- Destination database name from the instance database list
- GCS backup bucket derived from instance environment, e.g. `ons-blaise-v2-dev-backups`
- Source instance is the same as destination instance (clone from live)

## Usage

Run via Make:

```bash
make run LMS2601_KX2 "2026-07-08 14:30:00"
```

### Request Parameters Sent to the Cloud Function

The wrapper invokes the HTTP function with JSON:

```json
{
  "questionnaire_name": "LMS2601_KX2",
  "timestamp": "2026-07-08 14:30:00"
}
```

Timestamp input is parsed as UK local time (`Europe/London`) when no timezone is provided.

## End-to-End Flow Details

When you run `make run <questionnaire_name> <timestamp>`:

1. A temporary service account is created.
2. IAM roles are granted for Cloud SQL, Secret Manager, logging, and invocation.
3. A temporary Cloud Function is deployed (`restore_questionnaire` entry point).
4. The function is invoked with your `questionnaire_name` and `timestamp`.
5. In function runtime:
   - Validate source/destination instances are available.
   - Create point-in-time clone.
   - Export `<QUESTIONNAIRE>_Dml` from clone to GCS and import to destination.
   - Export `<QUESTIONNAIRE>_Form` from clone to GCS and import to destination.
   - Delete clone.
6. Wrapper cleanup runs (even on failure):
   - Delete temporary function.
   - Remove temporary service account and role bindings.

## Future Deployment Direction

This temporary deployment model is intended as a bridge. The target model is to deploy this Cloud Function permanently in each project/environment so it can be invoked directly from GCP (for example via Cloud Console/Cloud Functions invocation) without creating a temporary function per run.

## Development

This project includes a `Makefile` with common commands:

- Lint: `make lint`
- Lint + format fixes: `make lint-fix`
- Type check: `make typecheck`
- Dependency check: `make deptry`
- Dead code scan: `make vulture`
- Tests: `make test`
