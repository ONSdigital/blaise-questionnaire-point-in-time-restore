import logging
import time

from functions.argument_validation import (
    throw_error_if_empty_list,
    throw_error_if_empty_string,
)
from services.database_service import DatabaseService

LOGGER = logging.getLogger(__name__)


class DatabaseRestoreService:
    def __init__(self, database_service: DatabaseService):
        self._database_service = database_service

    def restore_questionnaire_data(
        self,
        questionnaire_names: list[str],
        source_instance_name: str,
        destination_instance_name: str,
    ) -> None:

        throw_error_if_empty_list(questionnaire_names, "questionnaire_names")
        throw_error_if_empty_string(source_instance_name, "source_instance_name")
        throw_error_if_empty_string(
            destination_instance_name, "destination_instance_name"
        )

        table_names = self.__build_questionnaire_table_names(questionnaire_names)

        self.__restore_tables(
            table_names, source_instance_name, destination_instance_name
        )

    def restore_questionnaire_dml_data(
        self,
        questionnaire_name: str,
        source_instance_name: str,
        destination_instance_name: str,
    ) -> None:
        throw_error_if_empty_string(questionnaire_name, "questionnaire_name")
        throw_error_if_empty_string(source_instance_name, "source_instance_name")
        throw_error_if_empty_string(
            destination_instance_name, "destination_instance_name"
        )

        table_names = [f"{questionnaire_name}_DML", f"{questionnaire_name}_FORM"]

        self.__restore_tables(
            table_names, source_instance_name, destination_instance_name
        )

    @staticmethod
    def __build_questionnaire_table_names(questionnaire_names: list[str]) -> list[str]:
        table_names: list[str] = []
        for name in questionnaire_names:
            table_names.append(f"{name}_DML")
            table_names.append(f"{name}_FORM")

        return table_names

    def __restore_tables(
        self, table_names: list[str], source_instance: str, destination_instance: str
    ) -> None:
        started_at = time.monotonic()
        LOGGER.info(
            "Table restore phase started; source=%s destination=%s table_count=%s",
            source_instance,
            destination_instance,
            len(table_names),
        )

        for index, table_name in enumerate(table_names, start=1):
            table_started_at = time.monotonic()
            LOGGER.info(
                "Restoring table; table=%s index=%s total=%s",
                table_name,
                index,
                len(table_names),
            )
            self._database_service.copy_table_data(
                table_name, source_instance, destination_instance
            )
            LOGGER.info(
                "Table restored; table=%s index=%s total=%s duration_seconds=%.2f",
                table_name,
                index,
                len(table_names),
                time.monotonic() - table_started_at,
            )

        LOGGER.info(
            (
                "Table restore phase completed; source=%s destination=%s "
                "table_count=%s duration_seconds=%.2f"
            ),
            source_instance,
            destination_instance,
            len(table_names),
            time.monotonic() - started_at,
        )
