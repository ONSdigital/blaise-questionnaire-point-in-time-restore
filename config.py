import os
import sys

from dotenv import load_dotenv
from google.cloud.sql.connector import IPTypes

load_dotenv()


def get_ip_type(ip_type_str: str) -> IPTypes:
    if ip_type_str.upper() == "PUBLIC":
        return IPTypes.PUBLIC
    if ip_type_str.upper() == "PRIVATE":
        return IPTypes.PRIVATE
    raise ValueError(f"Invalid IP type: {ip_type_str}")


def get_required_env(name: str) -> str:
    """Get an environment variable or exit if it is not set."""
    value = os.getenv(name)
    if not value:
        sys.exit(f"Error: Required environment variable '{name}' is not set.")
    return value


class Settings:
    SOURCE_INSTANCE_NAME = get_required_env("SOURCE_INSTANCE_NAME")
    SOURCE_DB_NAME = get_required_env("SOURCE_DB_NAME")
    SOURCE_DB_DRIVER = get_required_env("SOURCE_DB_DRIVER")
    SOURCE_DB_URL = get_required_env("SOURCE_DB_URL")
    SOURCE_DB_USERNAME = get_required_env("SOURCE_DB_USERNAME")
    SOURCE_DB_PASSWORD = get_required_env("SOURCE_DB_PASSWORD")
    SOURCE_DB_IP_TYPE = get_ip_type(get_required_env("SOURCE_DB_IP_TYPE"))

    DEST_INSTANCE_NAME = get_required_env("DEST_INSTANCE_NAME")
    DEST_DB_NAME = get_required_env("DEST_DB_NAME")
    DEST_DB_DRIVER = get_required_env("DEST_DB_DRIVER")
    DEST_DB_URL = get_required_env("DEST_DB_URL")
    DEST_DB_USERNAME = get_required_env("DEST_DB_USERNAME")
    DEST_DB_PASSWORD = get_required_env("DEST_DB_PASSWORD")
    DEST_DB_IP_TYPE = get_ip_type(get_required_env("DEST_DB_IP_TYPE"))

    TABLE_NAME = get_required_env("TABLE_NAME")
