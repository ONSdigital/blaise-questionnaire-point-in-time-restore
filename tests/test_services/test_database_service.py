from typing import Any, cast
from unittest.mock import Mock, patch

import pytest

from services.database_service import DatabaseService


@pytest.fixture
def auth_service() -> Mock:
    service = Mock()
    service.get_credentials_token.return_value = "token-123"
    return service


@pytest.fixture
def service_under_test(auth_service: Mock) -> DatabaseService:
    return DatabaseService(
        authorisation_service=auth_service,
        project_id="project-1",
        database_name="blaise",
        export_bucket_name="ons-blaise-v2-dev-backups",
        export_prefix="questionnaire-pitr",
        operation_timeout_seconds=120,
        operation_poll_seconds=2,
        http_connect_timeout_seconds=3.0,
        http_read_timeout_seconds=45.0,
    )


def test_headers_include_bearer_token(service_under_test: DatabaseService) -> None:
    headers = cast(
        Any, service_under_test
    )._DatabaseService__create_authorisation_headers()

    assert headers == {
        "Authorization": "Bearer token-123",
        "Content-Type": "application/json",
    }


def test_instance_api_url_normalizes_connection_name(
    service_under_test: DatabaseService,
) -> None:
    url = cast(Any, service_under_test)._DatabaseService__get_instance_api_url(
        "project-1:region:instance-1"
    )

    assert url.endswith("/projects/project-1/instances/instance-1")


def test_copy_table_data_uses_configured_http_timeout(
    service_under_test: DatabaseService,
) -> None:
    with (
        patch(
            "services.database_service.requests.post",
            side_effect=[
                _operation_response("export-op"),
                _operation_response("import-op"),
            ],
        ) as mock_post,
        patch("services.database_service.requests.get", return_value=_done_response()),
    ):
        service_under_test.copy_table_data(
            "TABLE_DML", "project-1:region:source", "project-1:region:destination"
        )

    assert mock_post.call_args_list[0].kwargs["timeout"] == (3.0, 45.0)
    assert mock_post.call_args_list[1].kwargs["timeout"] == (3.0, 45.0)


@pytest.mark.parametrize("table_name", [None, "", " ", "   "])
def test_copy_table_data_raises_for_empty_table_name(
    service_under_test: DatabaseService,
    table_name: str,
) -> None:
    with pytest.raises(ValueError, match="table_name cannot be empty or none"):
        service_under_test.copy_table_data(
            table_name,
            "project-1:region:source",
            "project-1:region:destination",
        )


def _operation_response(operation_name: str) -> Mock:
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"name": operation_name}
    return response


def _done_response() -> Mock:
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"status": "DONE"}
    return response
