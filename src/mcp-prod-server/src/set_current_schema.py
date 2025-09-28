from sqlalchemy import text

class SetCurrentSchema:
    
    # Constructor
    def __init__(self, conn, schema) -> None:
        self.conn = conn
        self.schema = schema
    
    # Methods
    def set(self):
        try:
            self.conn.execute(text(f"SET CURRENT SCHEMA {self.schema}"))
            return f"Schema set to '{self.schema}' successfully."
        except Exception as e:
            raise RuntimeError(f"Failed to set schema to '{self.schema}': {e}")