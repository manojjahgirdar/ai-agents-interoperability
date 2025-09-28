from fastmcp import FastMCP
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse
import anyio

# Read environment variables
from config.app_config import AppConfig
app_config = AppConfig()

# Define MCP authentication
auth_token = app_config.MCP_AUTH_TOKEN

# Define MCP server
mcp = FastMCP(name="IBM db2 MCP server")

# Define health check endpoint for the mcp server
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    return JSONResponse({"status": "healthy", "service": "mcp-server"})

# Define MCP tools
@mcp.tool(
    name="list_tables",
    description="Input is an empty string, output is a comma-separated list of tables in the database.",
    tags={"db2", "read-only"},
    meta={"version": "1.2", "author": "Manoj Jahgirdar"},
    output_schema={"type": "object", "tables": "dict"}
)
async def list_tables() -> dict:
    """
    Returns a comma-separated list of tables in the SQLite database.
    """
    from src.db_list_tables import ListTables
    return await anyio.to_thread.run_sync(
        ListTables(
            schema=app_config.DB2_SCHEMA
            ).list_table
        )

@mcp.tool(
    name="get_table_schema",
    description="Input to this tool is a comma-separated list of tables, output is the schema and sample rows for those tables. Be sure to list the tables before calling this tool!",
    tags={"db2", "read-only"},
    meta={"version": "1.2", "author": "Manoj Jahgirdar"},
    output_schema={"type": "object", "table_schema": "dict"}
)
async def get_table_schema(table_name: str) -> dict:
    """
    Returns schema and 2 sample rows for each valid table.
    Input: Comma-separated list of table names (e.g., 'orders, vendors')
    """
    from src.get_table_schema import GetTableSchema
    return await anyio.to_thread.run_sync(
        GetTableSchema(
            table_name=table_name,
            schema=app_config.DB2_SCHEMA
            ).get
        )

@mcp.tool(
    name="sql_query_checker",
    description="Use this tool to double check if your query is correct before executing it. Always use this tool before executing a query with sql_db_query!",
    tags={"db2", "read-only"},
    meta={"version": "1.2", "author": "Manoj Jahgirdar"},
    output_schema={"type": "object", "message": "dict"}
)
async def sql_query_checker(query: str) -> dict:
    """
    Performs basic validation of the SQL query string.
    :returns: a natural language evaluation.
    """
    from src.db_query_checker import DatabaseQueryChecker
    return await anyio.to_thread.run_sync(
        DatabaseQueryChecker(
            query=query
            ).check
        )

@mcp.tool(
    name="sql_db_query",
    description="Input is a valid SQL query, output is the results of that query in JSON format. Always use sql_query_checker before calling this tool!",
    tags={"db2", "read-write"},
    meta={"version": "1.2", "author": "Manoj Jahgirdar"},
    output_schema={"type": "object", "query_results": "dict"},
)
def sql_db_query(sql_query: str) -> dict:
    """
    Executes a SQL query against the database and returns the results in JSON format.
    Input: A valid SQL query string (e.g., 'SELECT * FROM orders LIMIT 5')
    """
    from src.db_query import QueryDatabaseTable
    obj = QueryDatabaseTable(query=sql_query, schema=app_config.DB2_SCHEMA)
    output = obj.exec_sql()
    return output

# Mount the MCP server to the FastAPI app
mcp_app = mcp.http_app(path='/mcp')

# Define FastAPI app
api = FastAPI(lifespan=mcp_app.lifespan)

# Define a simple status endpoint
@api.get("/api/status")
def status():
    return {"status": "ok"}

api.mount("/dbtools", mcp_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)