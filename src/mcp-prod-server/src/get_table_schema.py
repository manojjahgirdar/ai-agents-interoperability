from sqlalchemy import inspect
from config.app_config import AppConfig
app_config = AppConfig()

from .create_connection import CreateConnection
from .set_current_schema import SetCurrentSchema

class GetTableSchema:
    """
    Class to get the schema of a specific table in a DB2 database.
    """

    def __init__(self, table_name, schema):
        self.table_name = table_name
        self.schema = schema

    def generate_sql_schema(self, fields):
        sql = f"CREATE TABLE {self.table_name.upper()} (\n"
        field_lines = []
        for field in fields:
            name = field['name'].upper()
            type_ = field['type'].upper()
            # Replace "NULL" with TEXT or another default type
            if type_ == "NULL":
                type_ = "TEXT"
            field_lines.append(f"    {name:<30} {type_}")
        sql += ",\n".join(field_lines)
        sql += "\n);"
        return sql
        
    def get(self):
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
                return {"error": "DB connection failed"}

            inspector = inspect(engine)
            columns = inspector.get_columns(self.table_name, schema=self.schema)
            
            # return [{"name": col["name"], "type": str(col["type"])} for col in columns]
            return {"table_schema": self.generate_sql_schema([{"name": col["name"], "type": str(col["type"])} for col in columns])}

        except Exception as e:
            return {"error": str(e)}