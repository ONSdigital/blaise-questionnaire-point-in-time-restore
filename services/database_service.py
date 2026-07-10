import logging
import time
from typing import cast

import pymysql
import sqlalchemy
from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import Engine, MetaData, Table, insert
from sqlalchemy.orm import Session

from models.database_connection_model import DatabaseConnectionModel

LOGGER = logging.getLogger(__name__)


class DatabaseService:
    def __init__(self, connection_model: DatabaseConnectionModel):
        self._connection_model = connection_model

    def copy_table_data(
        self, table_name: str, source_instance_name: str, destination_instance_name: str
    ) -> None:
        started_at = time.monotonic()
        LOGGER.info(
            "Copying table data started; table=%s source=%s destination=%s",
            table_name,
            source_instance_name,
            destination_instance_name,
        )
        source_database_engine = self.__get_database(source_instance_name)
        destination_database_engine = self.__get_database(destination_instance_name)
        source_table_name = self.__resolve_table_name(
            source_database_engine, table_name
        )
        destination_table_name = self.__resolve_table_name(
            destination_database_engine, table_name
        )
        source_table = self.__get_table(source_database_engine, source_table_name)
        destination_table = self.__get_table(
            destination_database_engine, destination_table_name
        )
        if source_table_name != table_name or destination_table_name != table_name:
            LOGGER.info(
                (
                    "Resolved table names; requested=%s source_resolved=%s "
                    "destination_resolved=%s"
                ),
                table_name,
                source_table_name,
                destination_table_name,
            )

        with Session(source_database_engine) as source_session, source_session.begin():
            table_data = source_session.execute(source_table.select())

        copied_row_count = 0
        with (
            Session(destination_database_engine) as destination_session,
            destination_session.begin(),
        ):
            destination_session.execute(destination_table.delete())
            for row in table_data:
                destination_session.execute(insert(destination_table).values(row))
                copied_row_count += 1

        LOGGER.info(
            (
                "Copying table data completed; table=%s source=%s destination=%s "
                "rows_copied=%s duration_seconds=%.2f"
            ),
            table_name,
            source_instance_name,
            destination_instance_name,
            copied_row_count,
            time.monotonic() - started_at,
        )

    def __get_database(self, instance_name: str) -> Engine:
        return sqlalchemy.create_engine(
            url=self._connection_model.database_url,
            creator=lambda: self.__get_connection(
                instance_name, self._connection_model
            ),
            pool_pre_ping=True,
        )

    @staticmethod
    def __get_table(database: Engine, table_name: str) -> Table:
        meta_data = MetaData()
        return Table(table_name, meta_data, autoload_with=database)

    @staticmethod
    def __resolve_table_name(database: Engine, table_name: str) -> str:
        try:
            table_names = cast(object, sqlalchemy.inspect(database).get_table_names())
        except Exception:
            return table_name

        if not isinstance(table_names, list):
            return table_name

        if table_name in table_names:
            return table_name

        target_lower = table_name.lower()
        for existing_name in table_names:
            if existing_name.lower() == target_lower:
                return existing_name

        return table_name

    @staticmethod
    def __get_connection(
        instance_name: str, sql_connection: DatabaseConnectionModel
    ) -> pymysql.connections.Connection:
        connector = Connector(IPTypes.PRIVATE)

        if sql_connection.database_password:
            return connector.connect(
                instance_connection_string=instance_name,
                driver=sql_connection.database_driver,
                user=sql_connection.database_username,
                password=sql_connection.database_password,
                db=sql_connection.database_name,
            )

        return connector.connect(
            instance_connection_string=instance_name,
            driver=sql_connection.database_driver,
            user=sql_connection.database_username,
            db=sql_connection.database_name,
            enable_iam_auth=True,
        )
