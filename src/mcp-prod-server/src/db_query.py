from sqlalchemy import text
from config.app_config import AppConfig
app_config = AppConfig()

from .create_connection import CreateConnection
from .set_current_schema import SetCurrentSchema

class QueryDatabaseTable:
    """
    Class to query a specific table in a DB2 database.
    """

    def __init__(self, query, schema):
        self.query = query
        self.schema = schema
        self.output_format = app_config.OUTPUT_FORMAT

    def list_of_dicts_to_markdown_table(self, data):
        """
        Converts a list of dictionaries to a Markdown formatted table string.

        Args:
            data (list): A list of dictionaries, where each dictionary represents a row.
                        All dictionaries should ideally have the same keys.

        Returns:
            str: A string representing the Markdown table.
        """
        if not data:
            return ""

        # Get headers from the keys of the first dictionary
        headers = list(data[0].keys())

        # Create the header row
        header_row = "| " + " | ".join(headers) + " |"

        # Create the separator row
        separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"

        # Create the data rows
        data_rows = []
        for row_dict in data:
            row_values = [str(row_dict.get(header, "")) for header in headers]
            data_rows.append("| " + " | ".join(row_values) + " |")

        # Combine all parts
        markdown_table = [header_row, separator_row] + data_rows
        return "\n".join(markdown_table)

    def exec_sql(self):
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

            with engine.connect() as conn:
                conn.execute(text(f"SET CURRENT SCHEMA {self.schema}"))
                result = conn.execute(text(self.query))
                rows = [dict(row._mapping) for row in result]
                if self.output_format == 'json':
                    return {"query_results": rows}
                elif self.output_format == 'md':
                    return {"query_results": self.list_of_dicts_to_markdown_table(rows)}
                else:
                    return {"query_results": rows}

        except Exception as e:
            return {"error": str(e)}