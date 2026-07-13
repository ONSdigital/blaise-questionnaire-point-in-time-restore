#!/usr/bin/env bash
set -euo pipefail

QUESTIONNAIRE="${1:?Usage: run_restore.sh <questionnaire_name> <timestamp>}"
TIMESTAMP="${2:?Usage: run_restore.sh <questionnaire_name> <timestamp>}"

PROJECT="$(gcloud config get-value project 2>/dev/null)"
USER_EMAIL="$(gcloud config get-value account 2>/dev/null)"
REGION="$(gcloud config get-value functions/region 2>/dev/null)"

if [[ -z "${REGION}" || "${REGION}" == "(unset)" ]]; then
    REGION=$(gcloud sql instances list \
        --project="${PROJECT}" \
        --format='value(region)' \
        --limit=1 2>/dev/null || true)
fi

if [[ -z "${PROJECT}" ]]; then
    echo "Error: No active gcloud project. Run: gcloud config set project <PROJECT_ID>" >&2
    exit 1
fi

if [[ -z "${REGION}" || "${REGION}" == "(unset)" ]]; then
    echo "Error: Could not determine deploy region automatically." >&2
    echo "Run: gcloud config set functions/region <REGION>" >&2
    exit 1
fi

SA_NAME="pitr-$(date +%s)"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
FUNCTION_NAME="${SA_NAME}"
BACKUP_BUCKET="${PROJECT}-backups"

cleanup() {
    echo "Deleting Cloud Function ${FUNCTION_NAME} ..."
    gcloud functions delete "${FUNCTION_NAME}" \
        --region="${REGION}" --gen2 --quiet 2>/dev/null || true
    rm -f requirements.txt
    echo "Cleaning up temporary service account ${SA_EMAIL} ..."
    gcloud projects remove-iam-policy-binding "${PROJECT}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/cloudsql.admin" --quiet --format=none 2>/dev/null || true
    gcloud projects remove-iam-policy-binding "${PROJECT}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/secretmanager.secretAccessor" --quiet --format=none 2>/dev/null || true
    gcloud projects remove-iam-policy-binding "${PROJECT}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/logging.logWriter" --quiet --format=none 2>/dev/null || true
    gcloud storage buckets remove-iam-policy-binding "gs://${BACKUP_BUCKET}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/storage.admin" \
        --quiet 2>/dev/null || true
    gcloud iam service-accounts delete "${SA_EMAIL}" --quiet 2>/dev/null || true
}

echo "Creating temporary service account ${SA_EMAIL} ..."
gcloud iam service-accounts create "${SA_NAME}" \
    --display-name="PITR (temporary)" \
    --project="${PROJECT}"

trap cleanup EXIT

echo "Waiting for service account to become visible ..."
for i in $(seq 1 12); do
    if gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT}" \
        >/dev/null 2>&1; then
        break
    fi
    if [[ "${i}" -eq 12 ]]; then
        echo "Error: Service account did not become visible after 60s" >&2
        exit 1
    fi
    echo "  Attempt ${i}/12, retrying in 5s ..."
    sleep 5
done

echo "Granting roles to ${SA_EMAIL} ..."
gcloud projects add-iam-policy-binding "${PROJECT}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/cloudsql.admin" --quiet --format=none

gcloud projects add-iam-policy-binding "${PROJECT}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" --quiet --format=none

gcloud projects add-iam-policy-binding "${PROJECT}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/logging.logWriter" --quiet --format=none

gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
    --member="user:${USER_EMAIL}" \
    --role="roles/iam.serviceAccountTokenCreator" --format=none

gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
    --member="user:${USER_EMAIL}" \
    --role="roles/iam.serviceAccountUser" --format=none

echo "Granting bucket permissions for Cloud SQL export/import ..."
if ! gcloud storage buckets describe "gs://${BACKUP_BUCKET}" >/dev/null 2>&1; then
    echo "Error: Backup bucket gs://${BACKUP_BUCKET} not found." >&2
    exit 1
fi

gcloud storage buckets add-iam-policy-binding "gs://${BACKUP_BUCKET}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.admin" \
    --quiet

mapfile -t CLOUD_SQL_INSTANCE_SERVICE_ACCOUNTS < <(
    gcloud sql instances list \
        --project="${PROJECT}" \
        --format='value(serviceAccountEmailAddress)' \
    | awk 'NF' \
    | sort -u
)

if [[ "${#CLOUD_SQL_INSTANCE_SERVICE_ACCOUNTS[@]}" -eq 0 ]]; then
    echo "Error: No Cloud SQL instance service accounts found in project ${PROJECT}." >&2
    exit 1
fi

for cloud_sql_service_account in "${CLOUD_SQL_INSTANCE_SERVICE_ACCOUNTS[@]}"; do
    echo "  Granting bucket access to ${cloud_sql_service_account} ..."
    gcloud storage buckets add-iam-policy-binding "gs://${BACKUP_BUCKET}" \
        --member="serviceAccount:${cloud_sql_service_account}" \
        --role="roles/storage.objectAdmin" \
        --quiet
done

echo "Waiting for bucket IAM to propagate for ${SA_EMAIL} ..."
for i in $(seq 1 24); do
    if CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT="${SA_EMAIL}" \
        gcloud storage buckets get-iam-policy "gs://${BACKUP_BUCKET}" \
        >/dev/null 2>&1; then
        echo "  Bucket IAM ready after $((i * 5 - 5))s"
        break
    fi
    if [[ "${i}" -eq 24 ]]; then
        echo "Error: Bucket IAM propagation timed out after 120s" >&2
        exit 1
    fi
    echo "  Attempt ${i}/24, retrying in 5s ..."
    sleep 5
done

echo "Waiting for IAM to propagate ..."
for i in $(seq 1 24); do
    if CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT="${SA_EMAIL}" \
        gcloud sql instances list --project="${PROJECT}" --limit=1 \
        >/dev/null 2>&1; then
        echo "  IAM ready after $((i * 5 - 5))s"
        break
    fi
    if [[ "${i}" -eq 24 ]]; then
        echo "Error: IAM propagation timed out after 120s" >&2
        exit 1
    fi
    echo "  Attempt ${i}/24, retrying in 5s ..."
    sleep 5
done

echo "Discovering VPC connector in ${REGION} ..."
VPC_CONNECTOR=$(gcloud compute networks vpc-access connectors list \
    --region="${REGION}" \
    --project="${PROJECT}" \
    --format='value(name)' \
    --limit=1 2>/dev/null || true)

if [[ -z "${VPC_CONNECTOR}" ]]; then
    echo "Error: No VPC Access Connector found in ${REGION}." >&2
    echo "  Create one with: gcloud compute networks vpc-access connectors create ..." >&2
    exit 1
fi
echo "Using VPC connector: ${VPC_CONNECTOR}"

echo "Exporting requirements.txt ..."
python - <<'PY'
from pathlib import Path
import tomllib

pyproject_path = Path("pyproject.toml")
project = tomllib.loads(pyproject_path.read_text())["project"]
dependencies = project.get("dependencies", [])


def normalize(requirement: str) -> str:
    requirement = requirement.strip()
    if " (" in requirement and requirement.endswith(")"):
        name, spec = requirement.split(" (", maxsplit=1)
        return f"{name}{spec[:-1]}"
    return requirement


Path("requirements.txt").write_text(
    "\n".join(normalize(requirement) for requirement in dependencies) + "\n"
)
PY

echo "Deploying Cloud Function ${FUNCTION_NAME} ..."
gcloud functions deploy "${FUNCTION_NAME}" \
    --gen2 \
    --region="${REGION}" \
    --runtime=python313 \
    --entry-point=restore_questionnaire \
    --trigger-http \
    --no-allow-unauthenticated \
    --service-account="${SA_EMAIL}" \
    --vpc-connector="${VPC_CONNECTOR}" \
    --memory=512Mi \
    --timeout=3600s \
    --source=.

rm -f requirements.txt

FUNCTION_URL=$(gcloud functions describe "${FUNCTION_NAME}" \
    --region="${REGION}" \
    --gen2 \
    --format='value(serviceConfig.uri)')

echo "Granting invoker role on Cloud Run service ${FUNCTION_NAME} ..."
gcloud run services add-iam-policy-binding "${FUNCTION_NAME}" \
    --project="${PROJECT}" \
    --region="${REGION}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/run.invoker" \
    --quiet --format=none

gcloud run services add-iam-policy-binding "${FUNCTION_NAME}" \
    --project="${PROJECT}" \
    --region="${REGION}" \
    --member="user:${USER_EMAIL}" \
    --role="roles/run.invoker" \
    --quiet --format=none

if TOKEN=$(gcloud auth print-identity-token \
    --impersonate-service-account="${SA_EMAIL}" \
    "--audiences=${FUNCTION_URL}" 2>/dev/null); then
    :
else
    echo "Falling back to access token invocation..."
    TOKEN=$(gcloud auth print-access-token)
fi

echo "Invoking PITR: questionnaire=${QUESTIONNAIRE} timestamp=${TIMESTAMP} ..."
RESPONSE_FILE=$(mktemp)
RESPONSE_BODY=""
AUTH_READY=false
for i in $(seq 1 24); do
    AUTH_CODE=$(curl -sS --max-time 10 \
        -H "Authorization: Bearer ${TOKEN}" \
        -w "%{http_code}" \
        -o "${RESPONSE_FILE}" \
        "${FUNCTION_URL}" || true)

    if [[ "${AUTH_CODE}" == "401" || "${AUTH_CODE}" == "403" ]]; then
        if [[ "${i}" -lt 24 ]]; then
            echo "  Invoke auth not ready yet (HTTP ${AUTH_CODE}), retrying in 5s ..."
            sleep 5
            continue
        fi
        RESPONSE_BODY=$(cat "${RESPONSE_FILE}")
        rm -f "${RESPONSE_FILE}"
        echo "${RESPONSE_BODY}"
        echo "Error: Invocation auth did not become ready after retries (HTTP ${AUTH_CODE})" >&2
        exit 1
    fi

    AUTH_READY=true
    break
done

if [[ "${AUTH_READY}" != true ]]; then
    rm -f "${RESPONSE_FILE}"
    echo "Error: Invocation auth readiness check failed unexpectedly." >&2
    exit 1
fi

echo "Auth ready; sending PITR request..."
HTTP_CODE=$(curl -sS --max-time 3600 \
    -X POST \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"questionnaire_name\":\"${QUESTIONNAIRE}\",\"timestamp\":\"${TIMESTAMP}\"}" \
    -w "%{http_code}" \
    -o "${RESPONSE_FILE}" \
    "${FUNCTION_URL}" || true)
if [[ -f "${RESPONSE_FILE}" ]]; then
    RESPONSE_BODY=$(cat "${RESPONSE_FILE}")
fi
rm -f "${RESPONSE_FILE}"

echo "${RESPONSE_BODY}"
if [[ "${HTTP_CODE}" != "200" ]]; then
    echo "Error: Cloud Function returned HTTP ${HTTP_CODE}" >&2
    exit 1
fi

echo "PITR completed successfully."
