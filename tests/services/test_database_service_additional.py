from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock, patch

from models.database_connection_model import DatabaseConnectionModel
from services.database_service import DatabaseService


def _build_connection_model(password: str) -> DatabaseConnectionModel:
    return DatabaseConnectionModel(
        instance_name="proj:reg:instance",
        database_name="db",
        database_username="user",
        database_password=password,
        database_driver="pymysql",
        database_url="mysql+pymysql://",
    )


def test_resolve_table_name_returns_input_when_inspector_raises() -> None:
    service = DatabaseService(_build_connection_model("password"))

    with patch(
        "services.database_service.sqlalchemy.inspect", side_effect=RuntimeError("boom")
    ):
        resolved = cast(Any, service)._DatabaseService__resolve_table_name(
            Mock(), "LMS2601_DML"
        )

    assert resolved == "LMS2601_DML"


def test_resolve_table_name_returns_input_when_table_names_not_list() -> None:
    service = DatabaseService(_build_connection_model("password"))
    inspector = SimpleNamespace(get_table_names=lambda: "not-a-list")

    with patch("services.database_service.sqlalchemy.inspect", return_value=inspector):
        resolved = cast(Any, service)._DatabaseService__resolve_table_name(
            Mock(), "LMS2601_DML"
        )

    assert resolved == "LMS2601_DML"


def test_resolve_table_name_finds_case_insensitive_match() -> None:
    service = DatabaseService(_build_connection_model("password"))
    inspector = SimpleNamespace(get_table_names=lambda: ["lms2601_dml", "other"])

    with patch("services.database_service.sqlalchemy.inspect", return_value=inspector):
        resolved = cast(Any, service)._DatabaseService__resolve_table_name(
            Mock(), "LMS2601_DML"
        )

    assert resolved == "lms2601_dml"


def test_resolve_table_name_returns_exact_match_when_present() -> None:
    service = DatabaseService(_build_connection_model("password"))
    inspector = SimpleNamespace(get_table_names=lambda: ["LMS2601_DML", "other"])

    with patch("services.database_service.sqlalchemy.inspect", return_value=inspector):
        resolved = cast(Any, service)._DatabaseService__resolve_table_name(
            Mock(), "LMS2601_DML"
        )

    assert resolved == "LMS2601_DML"


def test_resolve_table_name_returns_input_when_no_match_exists() -> None:
    service = DatabaseService(_build_connection_model("password"))
    inspector = SimpleNamespace(get_table_names=lambda: ["different_table"])

    with patch("services.database_service.sqlalchemy.inspect", return_value=inspector):
        resolved = cast(Any, service)._DatabaseService__resolve_table_name(
            Mock(), "LMS2601_DML"
        )

    assert resolved == "LMS2601_DML"


def test_get_connection_uses_iam_auth_when_password_empty() -> None:
    connection_model = _build_connection_model("")
    service = DatabaseService(connection_model)

    with patch("services.database_service.Connector") as mock_connector_class:
        mock_connector = Mock()
        mock_connector.connect.return_value = Mock()
        mock_connector_class.return_value = mock_connector

        cast(Any, service)._DatabaseService__get_connection(
            "proj:reg:inst", connection_model
        )

    connect_kwargs = mock_connector.connect.call_args.kwargs
    assert connect_kwargs["enable_iam_auth"] is True
    assert "password" not in connect_kwargs


def test_copy_table_data_inserts_each_source_row_into_destination() -> None:
    service = DatabaseService(_build_connection_model("password"))

    source_engine = Mock()
    destination_engine = Mock()
    source_table = Mock()
    destination_table = Mock()
    source_table.select.return_value = "source-select"
    destination_table.delete.return_value = "destination-delete"

    source_session = Mock()
    destination_session = Mock()
    source_session.execute.return_value = [{"id": 1}, {"id": 2}]

    source_begin_context = Mock()
    source_begin_context.__enter__ = Mock(return_value=None)
    source_begin_context.__exit__ = Mock(return_value=False)
    source_session.begin.return_value = source_begin_context

    destination_begin_context = Mock()
    destination_begin_context.__enter__ = Mock(return_value=None)
    destination_begin_context.__exit__ = Mock(return_value=False)
    destination_session.begin.return_value = destination_begin_context

    source_context = Mock()
    source_context.__enter__ = Mock(return_value=source_session)
    source_context.__exit__ = Mock(return_value=False)

    destination_context = Mock()
    destination_context.__enter__ = Mock(return_value=destination_session)
    destination_context.__exit__ = Mock(return_value=False)

    with (
        patch.object(
            service,
            "_DatabaseService__get_database",
            side_effect=[source_engine, destination_engine],
        ),
        patch.object(
            service,
            "_DatabaseService__resolve_table_name",
            side_effect=["TABLE_DML", "TABLE_DML"],
        ),
        patch.object(
            service,
            "_DatabaseService__get_table",
            side_effect=[source_table, destination_table],
        ),
        patch(
            "services.database_service.Session",
            side_effect=[source_context, destination_context],
        ),
        patch("services.database_service.insert") as mock_insert,
    ):
        insert_builder = Mock()
        insert_builder.values.side_effect = ["insert-row-1", "insert-row-2"]
        mock_insert.return_value = insert_builder

        service.copy_table_data("TABLE_DML", "source", "destination")

    destination_session.execute.assert_any_call("destination-delete")
    destination_session.execute.assert_any_call("insert-row-1")
    destination_session.execute.assert_any_call("insert-row-2")


def test_copy_table_data_logs_when_resolved_table_names_differ() -> None:
    service = DatabaseService(_build_connection_model("password"))

    source_engine = Mock()
    destination_engine = Mock()
    source_table = Mock()
    destination_table = Mock()
    source_table.select.return_value = "source-select"
    destination_table.delete.return_value = "destination-delete"

    source_session = Mock()
    destination_session = Mock()
    source_session.execute.return_value = []

    source_begin_context = Mock()
    source_begin_context.__enter__ = Mock(return_value=None)
    source_begin_context.__exit__ = Mock(return_value=False)
    source_session.begin.return_value = source_begin_context

    destination_begin_context = Mock()
    destination_begin_context.__enter__ = Mock(return_value=None)
    destination_begin_context.__exit__ = Mock(return_value=False)
    destination_session.begin.return_value = destination_begin_context

    source_context = Mock()
    source_context.__enter__ = Mock(return_value=source_session)
    source_context.__exit__ = Mock(return_value=False)

    destination_context = Mock()
    destination_context.__enter__ = Mock(return_value=destination_session)
    destination_context.__exit__ = Mock(return_value=False)

    with (
        patch.object(
            service,
            "_DatabaseService__get_database",
            side_effect=[source_engine, destination_engine],
        ),
        patch.object(
            service,
            "_DatabaseService__resolve_table_name",
            side_effect=["table_dml", "TABLE_DML"],
        ),
        patch.object(
            service,
            "_DatabaseService__get_table",
            side_effect=[source_table, destination_table],
        ),
        patch(
            "services.database_service.Session",
            side_effect=[source_context, destination_context],
        ),
        patch("services.database_service.insert") as mock_insert,
        patch("services.database_service.LOGGER.info") as mock_logger_info,
    ):
        insert_builder = Mock()
        insert_builder.values.return_value = "unused-insert"
        mock_insert.return_value = insert_builder

        service.copy_table_data("TABLE_DML", "source", "destination")

    assert any(
        call.args
        and call.args[0]
        == (
            "Resolved table names; requested=%s source_resolved=%s "
            "destination_resolved=%s"
        )
        for call in mock_logger_info.call_args_list
    )
