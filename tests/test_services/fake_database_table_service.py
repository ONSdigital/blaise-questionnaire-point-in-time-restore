from typing import Any

from sqlalchemy import Table

from services.database_table_service import DatabaseTableService


class FakeDatabaseTableService(DatabaseTableService):

    def __init__(self, table: Table, instance_name: str):
        self._table = table
        self._instance_name = instance_name
        self._records: list[Any] = []  # store added records in memory

    @property
    def session(self):
        # no-op context manager for "with session.begin():"
        from contextlib import contextmanager

        @contextmanager
        def noop_context(self):
            yield

        return type("FakeSession", (), {"begin": noop_context})()

    def get_records(self) -> list[Table]:
        print(
            f"Fake service {self._instance_name}: get_records count {len(self._records)}"  # type: ignore[attr-defined]
        )
        return list(self._records)

    def add_record(self, record: Table) -> None:
        print(f"Fake service {self._instance_name}: add_record {record.Serial_Number}")  # type: ignore[attr-defined]
        self._records.append(record)

    def delete_records(self) -> None:
        print(f"Fake service {self._instance_name}: delete_records")
        self._records.clear()
