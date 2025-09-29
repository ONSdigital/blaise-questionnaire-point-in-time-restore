import pytest
from sqlalchemy.testing.schema import Table

from functions.factories.table_factory import TableFactory
from services.database_orm_service2 import DatabaseOrmService2
from tests.test_services.fake_database_table_service import FakeDatabaseTableService


class TestOrmFunctionality:

    @pytest.fixture()
    def source_table(self) -> Table:
        return TableFactory.create_form_table_model("MockTable")

    @pytest.fixture()
    def destination_table(self) -> Table:
        return TableFactory.create_form_table_model("MockTable")

    @pytest.fixture()
    def fake_source_database_table_service(
        self, source_table
    ) -> FakeDatabaseTableService:
        return FakeDatabaseTableService(source_table, "source")

    @pytest.fixture()
    def fake_destination_database_table_service(
        self, destination_table
    ) -> FakeDatabaseTableService:
        return FakeDatabaseTableService(destination_table, "destination")

    @pytest.fixture()
    def service_under_test(self) -> DatabaseOrmService2:
        return DatabaseOrmService2()

    def test_copy_table_data_copies_source_to_destination(
        self,
        source_table,
        service_under_test,
        fake_source_database_table_service,
        fake_destination_database_table_service,
    ):
        # arrange

        fake_source_database_table_service.add_record(
            source_table(FormID=1, Serial_Number=900001)
        )
        fake_source_database_table_service.add_record(
            source_table(FormID=2, Serial_Number=900002)
        )
        fake_source_database_table_service.add_record(
            source_table(FormID=3, Serial_Number=900003)
        )
        expected = fake_source_database_table_service.get_records()

        # act
        service_under_test.copies_table_data(
            fake_source_database_table_service, fake_destination_database_table_service
        )

        actual = fake_destination_database_table_service.get_records()

        # assert
        assert len(actual) == len(expected)
        assert all([a == b for a, b in zip(actual, expected)])
