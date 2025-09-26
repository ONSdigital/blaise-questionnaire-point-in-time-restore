from unittest.mock import MagicMock, call, patch

from functions.factories.table_factory import TableFactory
import pytest
import sqlalchemy
from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import Table, insert
from sqlalchemy.orm import Session

from models.database_connection_model import DatabaseConnectionModel
from services.database_service import DatabaseService


class TestCopyFunctionality:
    @pytest.fixture()
    def connection_model(self):
        return DatabaseConnectionModel(
            instance_name="ons-blaise-v2-dev-b4team:europe-west2:bens-clone2",
            database_name="blaise",
            database_username="blaise_user",
            database_password="password_12345",
            database_driver="pymsql",
            database_ip_connection_type=IPTypes.PRIVATE,
            database_url="mysql+pymysql://",
        )

    @pytest.fixture()
    def service_under_test(self, connection_model) -> DatabaseService:
        return DatabaseService(connection_model=connection_model)

    @patch("services.database_service.Session", autospec=True)
    @patch.object(sqlalchemy, "create_engine")
    @patch.object(Connector, "connect")
    def test_copy_database_table_uses_the_connection_model_to_connect_to_the_database(
        self, mock_connector, __mock_engine, __mock_session_class, service_under_test, connection_model
    ):

        # arrange
        table_name = "LMS2301_DD1_FORM"
        source_instance_name = "b4team:europe-west2:blaise-dev-test-clone"
        destination_instance_name = "blaise-dev-test"

        # act
        service_under_test.copy_table_data(
            table_name, source_instance_name, destination_instance_name
        )

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
    def test_copy_database_table_uses_the_connection_model_database_url_to_create_an_engine(
        self, mock_connector, mock_engine, mock_session_class, service_under_test, connection_model
    ):
        # arrange
        table_name = "LMS2301_DD1_FORM"
        source_instance_name = "b4team:europe-west2:blaise-dev-test-clone"
        destination_instance_name = "blaise-dev-test"

        mock_source_database_connection = MagicMock()
        mock_destination_database_connection = MagicMock()
        mock_connector.side_effect = [
            mock_source_database_connection,
            mock_destination_database_connection,
        ]



        # act
        service_under_test.copy_table_data(
            table_name, source_instance_name, destination_instance_name
        )

        # assert
        mock_engine.assert_has_calls(
            [
                call(
                    url=connection_model.database_url,
                    creator=mock_source_database_connection,
                    pool_pre_ping=True,
                ),
                call(
                    url=connection_model.database_url,
                    creator=mock_destination_database_connection,
                    pool_pre_ping=True,
                ),
            ]
        )

    @patch.object(Table, "delete")
    @patch.object(Table, "select")
    @patch.object(Session, "execute")
    @patch.object(sqlalchemy, "create_engine")
    @patch.object(Connector, "connect")
    def test_copy_database_table_selects_the_correct_table_data_to_copy_from(
        self,
        __mock_connector,
        __mock_engine,
        mock_session_execute,
        mock_table_select,
        mock_table_delete,
        service_under_test,
    ):
        # arrange
        table_name = "LMS2301_DD1_FORM"
        table_select = f"select * from {table_name}"
        table_delete = f"delete * from {table_name}"
        source_instance_name = "b4team:europe-west2:blaise-dev-test-clone"
        destination_instance_name = "blaise-dev-test"

        # Mock select/delete return values
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
        service_under_test.copy_table_data(
            table_name, source_instance_name, destination_instance_name
        )

        # assert
        print(mock_session_execute.call_args_list)
        mock_session_execute.assert_has_calls(expected_calls,any_order=True)


    # @patch("sqlalchemy.insert")
    # @patch("services.database_service.Session", autospec=True)
    # @patch.object(DatabaseService, "_DatabaseService__get_table")
    # @patch.object(Connector, "connect")
    # @patch.object(sqlalchemy, "create_engine")
    # def test_deletes_previous_records_before_inserting(
    #     self, mock_engine, mock_connector, mock_get_table, mock_session_class, mock_insert, service_under_test
    # ):
    #     # Arrange
    #     table_name = "LMS2301_DD1_FORM"
    #     source_instance_name = "source_instance_name"
    #     destination_instance_name = "destination_instance_name"

    #     # Mock connector connections
    #     mock_source_conn = MagicMock()
    #     mock_dest_conn = MagicMock()
    #     mock_connector.side_effect = [mock_source_conn, mock_dest_conn]

    #     # Mock tables
    #     mock_source_table = MagicMock()
    #     mock_dest_table = MagicMock()
    #     mock_get_table.side_effect = [mock_source_table, mock_dest_table]

    #     # Mock source session result
    #     mock_source_result = MagicMock()
    #     mock_source_result.all.return_value = [{"id": 1, "name": "row1"}]

    #     mock_source_session = MagicMock()
    #     mock_source_session.execute.return_value = mock_source_result

    #     # Mock destination session
    #     mock_dest_session = MagicMock()
    #     mock_dest_session.execute.return_value = None

    #     # Patch Session context manager
    #     mock_session_class.side_effect = [mock_source_session, mock_dest_session]
    #     mock_session_class.return_value.__enter__.side_effect = [mock_source_session, mock_dest_session]

    #     mock_insert.return_value = MagicMock()
    #     # Act
    #     service_under_test.copy_table_data(table_name, source_instance_name, destination_instance_name)

    #     # Assert: destination session deletes before inserting
    #     expected_calls = [
    #         call(mock_dest_table.delete()),  # delete called first
    #         call(insert(mock_dest_table).values({"id": 1, "name": "row1"})),  # then insert
    #     ]
    #     mock_dest_session.execute.assert_has_calls(expected_calls)