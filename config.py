import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import google.auth
import requests
from google.auth.transport.requests import Request
from google.cloud import secretmanager


def parse_uk_local_timestamp(value: str) -> datetime:
    cleaned = value.strip()
    normalized = cleaned.replace("T", " ")

    local_naive = datetime.fromisoformat(normalized)
    if local_naive.tzinfo is not None:
        return local_naive

    return local_naive.replace(tzinfo=ZoneInfo("Europe/London"))


def discover_project_id() -> str:
    try:
        _, project_id = google.auth.default()
        if project_id:
            return str(project_id)
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            check=True,
            capture_output=True,
            text=True,
        )
        project_id = result.stdout.strip()
        if project_id and project_id != "(unset)":
            return project_id
    except Exception:
        pass

    sys.exit(
        "Error: Could not determine the active GCP project. "
        "Authenticate with gcloud and run 'gcloud config set project <PROJECT_ID>'."
    )


def _discover_access_token() -> str:
    try:
        credentials, _ = google.auth.default()
        credentials.refresh(Request())
        token = str(credentials.token)
        if token:
            return token
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            check=True,
            capture_output=True,
            text=True,
        )
        token = result.stdout.strip()
        if token:
            return token
    except Exception:
        pass

    sys.exit(
        "Error: Could not acquire GCP access token. "
        "Authenticate with 'gcloud auth application-default login'."
    )


def discover_destination_instance_name(project_id: str) -> str:

    connection_names: list[str] = []

    try:
        token = _discover_access_token()
        response = requests.get(
            url=(
                "https://sqladmin.googleapis.com/sql/v1beta4/projects/"
                f"{project_id}/instances"
            ),
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        response.raise_for_status()

        instances = response.json().get("items", [])
        connection_names = [
            str(instance["connectionName"])
            for instance in instances
            if "connectionName" in instance
        ]
    except Exception:
        connection_names = []

    if not connection_names:
        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "sql",
                    "instances",
                    "list",
                    "--project",
                    project_id,
                    "--format=value(connectionName)",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            connection_names = [
                line.strip() for line in result.stdout.splitlines() if line.strip()
            ]
        except Exception:
            connection_names = []

    if not connection_names:
        sys.exit(
            "Error: Could not discover a Cloud SQL instance automatically. "
            "Ensure gcloud auth works and a project is configured."
        )

    if len(connection_names) == 1:
        return connection_names[0]

    preferred_instances = [
        name
        for name in connection_names
        if "clone" not in name.lower() and "pitr" not in name.lower()
    ]
    if len(preferred_instances) == 1:
        return preferred_instances[0]

    sys.exit(
        "Error: Multiple Cloud SQL instances found and no unambiguous live "
        "instance could be selected automatically."
    )


def discover_database_name(project_id: str, instance_connection_name: str) -> str:
    instance_name = instance_connection_name.rsplit(":", maxsplit=1)[-1]
    database_names: list[str] = []

    try:
        token = _discover_access_token()
        response = requests.get(
            url=(
                "https://sqladmin.googleapis.com/sql/v1beta4/projects/"
                f"{project_id}/instances/{instance_name}/databases"
            ),
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        response.raise_for_status()

        items = response.json().get("items", [])
        database_names = [str(item["name"]) for item in items if "name" in item]
    except Exception:
        database_names = []

    if not database_names:
        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "sql",
                    "databases",
                    "list",
                    "--project",
                    project_id,
                    "--instance",
                    instance_name,
                    "--format=value(name)",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            database_names = [
                line.strip() for line in result.stdout.splitlines() if line.strip()
            ]
        except Exception:
            database_names = []

    if not database_names:
        sys.exit(
            "Error: Could not discover the destination database name automatically."
        )

    system_database_names = {
        "cloudsqladmin",
        "information_schema",
        "mysql",
        "performance_schema",
        "sys",
    }
    user_databases = [
        name for name in database_names if name.lower() not in system_database_names
    ]

    if len(user_databases) == 1:
        return user_databases[0]

    if len(user_databases) > 1:
        preferred_names = [name for name in user_databases if name.lower() == "blaise"]
        if len(preferred_names) == 1:
            return preferred_names[0]

        return sorted(user_databases)[0]

    return database_names[0]


def discover_database_username() -> str:
    return "blaise"


def discover_database_password(project_id: str) -> str:
    secret_name = "cloudsql_pw"

    try:
        secret_client = secretmanager.SecretManagerServiceClient()
        secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        secret_version = secret_client.access_secret_version(name=secret_path)
        password_value = secret_version.payload.data.decode("UTF-8")
        if password_value:
            return password_value
    except Exception:
        pass

    try:
        result = subprocess.run(
            [
                "gcloud",
                "secrets",
                "versions",
                "access",
                "latest",
                f"--secret={secret_name}",
                f"--project={project_id}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        password_value = result.stdout.strip()
        if password_value:
            return password_value
    except Exception:
        pass

    sys.exit(
        "Error: Could not discover destination database password automatically. "
        "Grant Secret Manager access for secret "
        f"'{secret_name}'."
    )


class Settings:
    DEST_PROJECT_ID = discover_project_id()
    DEST_INSTANCE_NAME = discover_destination_instance_name(DEST_PROJECT_ID)
    RESTORE_SOURCE_INSTANCE_NAME = DEST_INSTANCE_NAME
    DEST_DB_NAME = discover_database_name(DEST_PROJECT_ID, DEST_INSTANCE_NAME)
    DEST_DB_DRIVER = "pymysql"
    DEST_DB_URL = "mysql+pymysql://"
    DEST_DB_USERNAME = discover_database_username()
    DEST_DB_PASSWORD = discover_database_password(DEST_PROJECT_ID)

    CLONE_NAME_PREFIX = "pitr"
    CLONE_OPERATION_POLL_SECONDS = 5
    CLONE_OPERATION_TIMEOUT_SECONDS = 1800
