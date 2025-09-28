from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus

class CreateConnection:
    
    # Constructor
    def __init__(self, user, password, host, port, db_name, ssl) -> None:
        self.user = user
        self.password = quote_plus(password)
        self.host = host
        self.port = port
        self.db_name = db_name
        self.ssl = ssl
    
    # Methods
    def create(self):
        try:
            user = self.user
            pwd = self.password
            host = self.host
            port = self.port
            db_name = self.db_name

            if not all([user, pwd, host, port, db_name]):
                raise ValueError("Missing one or more DB connection environment variables")
            
            connection_string = f'mysql+pymysql://{user}:{pwd}@{host}:{port}/{db_name}'
            
            engine = create_engine(connection_string)

            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM SYSIBM.SYSDUMMY1"))
            return engine
        except SQLAlchemyError as e:
            print(f"[SQLAlchemyError] DB connection failed: {e}")
            return None
        except Exception as e:
            print(f"[Error] DB connection failed: {e}")
            return None