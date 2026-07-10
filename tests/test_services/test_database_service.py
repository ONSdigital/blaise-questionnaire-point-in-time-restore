from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import ANY, MagicMock, call, patch

import pytest
import sqlalchemy
from google.cloud.sql.connector import Connector
from sqlalchemy import Table
from sqlalchemy.orm import Session

from models.database_connection_model import DatabaseConnectionModel
from services.database_service import DatabaseService


class TestCopyFunctionality:
    @pytest.fixture()
    def connection_model(self):
        return DatabaseConnectionModel(
            instance_name="gcp-project:europe-west2:bens-clone2",
            database_name="database",
            database_username="blaise_user",
            database_password="password_12345",
            database_driver="pymsql",
            database_url="mysql+pymysql://",
        )

    @pytest.fixture()
    def service_under_test(
        self, connection_model: DatabaseConnectionModel
    ) -> DatabaseService:
        return DatabaseService(connection_model=connection_model)

    @pytest.fixture
    def mock_creds(self):
        return SimpleNamespace(universe_domain="googleapis.com")

    @patch("services.database_service.Session", autospec=True)
    @patch.object(sqlalchemy, "create_engine")
    @patch.object(Connector, "connect")
    def test_copy_database_table_uses_the_connection_model_to_connect_to_the_database(
        self,
        mock_connector,
        _mock_engine,
        _mock_session_class,
        mock_creds,
        service_under_test,
        connection_model,
    ):

        # arrange
        table_name = "LMS2301_DD1_FORM"
        source_instance_name = "b4team:europe-west2:blaise-dev-test-clone"
        destination_instance_name = "blaise-dev-test"

        # act
        with patch("google.auth.default", return_value=(mock_creds, "gcp-project")):
            service_under_test.copy_table_data(
                table_name, source_instance_name, destination_instance_name
            )

        creator_source = _mock_engine.call_args_list[0].kwargs["creator"]
        creator_destination = _mock_engine.call_args_list[1].kwargs["creator"]
        creator_source()
        creator_destination()

        # assert
        mock_connector.assert_has_calls(
            [
                call(
                    instance_connection_string=source_instance_name,
                    driver=connection_model.database_driver,
                    user=connection_model.database_username,
                    password=connection_model.database_password,
                    db=connection_model.database_name,
                ),
                call(
                    instance_connection_string=destination_instance_name,
                    driver=connection_model.database_driver,
                    user=connection_model.database_username,
                    password=connection_model.database_password,
                    db=connection_model.database_name,
                ),
            ],
            any_order=True,
        )

    @patch("services.database_service.Session", autospec=True)
    @patch.object(sqlalchemy, "create_engine")
    @patch.object(Connector, "connect")
    def test_copy_database_table_uses_database_url_to_create_engine(
        self,
        mock_connector,
        mock_engine,
        _mock_session_class,
        mock_creds,
        service_under_test,
        connection_model,
    ):
        # arrange
        table_name = "LMS2301_DD1_FORM"
        source_instance_name = "b4team:europe-west2:blaise-dev-test-clone"
        destination_instance_name = "blaise-dev-test"

        mock_source_database_connection = MagicMock()
        mock_destination_database_connection = MagicMock()
        mock_connector.configure_mock(
            side_effect=[
                mock_source_database_connection,
                mock_destination_database_connection,
            ]
        )

        # act
        with patch("google.auth.default", return_value=(mock_creds, "gcp-project")):
            service_under_test.copy_table_data(
                table_name, source_instance_name, destination_instance_name
            )

        # assert
        mock_engine.assert_has_calls(
            [
                call(
                    url=connection_model.database_url,
                    creator=ANY,
                    pool_pre_ping=True,
                ),
                call(
                    url=connection_model.database_url,
                    creator=ANY,
                    pool_pre_ping=True,
                ),
            ]
        )

        creator_source = mock_engine.call_args_list[0].kwargs["creator"]
        creator_destination = mock_engine.call_args_list[1].kwargs["creator"]
        assert creator_source() is mock_source_database_connection
        assert creator_destination() is mock_destination_database_connection

    @patch.object(Table, "delete")
    @patch.object(Table, "select")
    @patch.object(Session, "execute")
    @patch.object(sqlalchemy, "create_engine")
    @patch.object(Connector, "connect")
    def test_copy_database_table_selects_the_correct_table_data_to_copy_from(
        self,
        _mock_connector,
        _mock_engine,
        mock_session_execute,
        mock_table_select,
        mock_table_delete,
        mock_creds,
        service_under_test,
    ):
        # arrange
        table_name = "LMS2301_DD1_FORM"
        source_instance_name = "b4team:europe-west2:blaise-dev-test-clone"
        destination_instance_name = "blaise-dev-test"

        mock_table_select.return_value = MagicMock()
        mock_table_delete.return_value = MagicMock()

        mock_result = MagicMock()
        mock_result.return_value = ["1", "2", "3"]
        mock_session_execute.return_value = mock_result

        expected_calls = [
            call(mock_table_select.return_value),
            call(mock_table_delete.return_value),
        ]

        # act
        with patch("google.auth.default", return_value=(mock_creds, "gcp-project")):
            service_under_test.copy_table_data(
                table_name, source_instance_name, destination_instance_name
            )

        # assert
        print(cast(Any, mock_session_execute.call_args_list))
        mock_session_execute.assert_has_calls(expected_calls, any_order=True)
