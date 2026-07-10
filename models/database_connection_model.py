from dataclasses import dataclass


@dataclass(slots=True)
class DatabaseConnectionModel:
    instance_name: str
    database_name: str
    database_username: str
    database_password: str
    database_driver: str
    database_url: str
