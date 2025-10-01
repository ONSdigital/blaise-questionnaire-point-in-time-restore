from sqlalchemy import Table
from sqlalchemy.orm import Session


class DatabaseOrmService:
    def get_case_ids(self, table: Table, source_database_session: Session) -> list[int]:
        print("Getting Case Ids...")
        case_id_list = []
        table_rows = source_database_session.query(table).all()
        for table_row in table_rows:
            case_id_list.append(table_row.Serial_Number)
            print(table_row.Serial_Number)

        return case_id_list

    def copies_table_data(
        self,
        table_name: str,
        table: Table,
        source_database_session: Session,
        destination_database_session: Session,
    ) -> None:
        print("Getting all cases from source table...")
        with source_database_session.begin():
            table_rows = source_database_session.query(table).all()

        print("Merging records in destination table...")
        with destination_database_session.begin():
            for table_row in table_rows:
                destination_database_session.merge(table_row)
        print(f"Successfully restored data for {table_name}...")
