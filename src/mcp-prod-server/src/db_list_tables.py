from sqlalchemy import inspect
from config.app_config import AppConfig
app_config = AppConfig()

from .create_connection import CreateConnection

class ListTables:
    """
    Class to list tables in a DB2 database.
    """

    def __init__(self, schema):
        self.schema = schema

    def list_table(self) -> dict:
        try:
            engine = CreateConnection(
                user=app_config.USER,
                password=app_config.PASSWORD,
                host=app_config.DB2_HOST,
                port=app_config.DB2_PORT,
                db_name=app_config.DB2_DATABASE,
                ssl=app_config.SSL
            ).create()
            if engine is None:
                return []

            inspector = inspect(engine)
            output = inspector.get_table_names(schema=self.schema)
            return {"tables": output}

        except Exception as e:
            print(f"[Error] Could not list tables: {e}")
            return {"tables": []}