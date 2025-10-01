from sqlalchemy.orm import Session

from config import Settings
from functions.factories.table_factory import TableFactory
from models.database_connection_model import DatabaseConnectionModel
from services.database_connection_service import DatabaseConnectionService
from services.database_orm_service import DatabaseOrmService

connection_model_source = DatabaseConnectionModel(
    instance_name=Settings.SOURCE_INSTANCE_NAME,
    database_name=Settings.SOURCE_DB_NAME,
    database_driver=Settings.SOURCE_DB_DRIVER,
    database_url=Settings.SOURCE_DB_URL,
    database_username=Settings.SOURCE_DB_USERNAME,
    database_password=Settings.SOURCE_DB_PASSWORD,
    database_ip_connection_type=Settings.SOURCE_DB_IP_TYPE,
)

connection_model_destination = DatabaseConnectionModel(
    instance_name=Settings.DEST_INSTANCE_NAME,
    database_name=Settings.DEST_DB_NAME,
    database_driver=Settings.DEST_DB_DRIVER,
    database_url=Settings.DEST_DB_URL,
    database_username=Settings.DEST_DB_USERNAME,
    database_password=Settings.DEST_DB_PASSWORD,
    database_ip_connection_type=Settings.DEST_DB_IP_TYPE,
)

source_database = DatabaseConnectionService(connection_model_source).get_database()
destination_database = DatabaseConnectionService(
    connection_model_destination
).get_database()

source_session = Session(source_database)
destination_session = Session(destination_database)

databaseOrmService = DatabaseOrmService()

source_table_model = TableFactory.create_form_table_model(Settings.TABLE_NAME)

destination_table_model = TableFactory.create_form_table_model(Settings.TABLE_NAME)

databaseOrmService.copies_table_data(
    Settings.TABLE_NAME, source_table_model, source_session, destination_session
)


# another variant of the similar pitr, to-be-explored in follow-up tickets
# source_database_table_service = DatabaseTableService(source_table_model, source_session)
# destination_database_table_service = DatabaseTableService(source_table_model, destination_session)
# databaseOrmService2 = DatabaseOrmService2()
# databaseOrmService2.copies_table_data(source_database_table_service, destination_database_table_service)
