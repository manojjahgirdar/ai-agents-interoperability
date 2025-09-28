from fastapi import FastAPI, HTTPException, Query, Depends, Security
from pydantic import BaseModel, EmailStr
from typing import Generator, Optional, List
import uvicorn
import sqlite3
import os

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.db_crud import SQLiteDB

security = HTTPBearer(auto_error=False)

def verify_bearer(credentials: HTTPAuthorizationCredentials = Security(security)) -> None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    expected = os.getenv("API_BEARER_TOKEN")
    if not expected or credentials.credentials != expected:
        raise HTTPException(status_code=401, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})

app = FastAPI(title="Database operations Server", dependencies=[Depends(verify_bearer)])

def get_db() -> Generator[SQLiteDB, None, None]:
    with SQLiteDB("database/customer_database.db") as db:
        yield db

class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    phone: int
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[int] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    phone: int
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

@app.post("/init-db", operation_id="init_db")
def init_db(db: SQLiteDB = Depends(get_db)):
    """
    Initialize the database and create the users table if it doesn't exist.
    :return: A dictionary indicating whether the table was created.
    """
    created = False
    if not db.table_exists("users"):
        db.create_table(
            "users",
            columns={
                "id": "INTEGER", 
                "email": "TEXT NOT NULL", 
                "name": "TEXT",
                "phone": "TEXT NOT NULL",
                "city": "TEXT",
                "state": "TEXT",
                "country": "TEXT"
            },
            primary_key="id",
            uniques=[["email"], ["phone"]],
        )
        created = True
    return {"ok": True, "created": created}

@app.post("/users", response_model=UserOut, status_code=201, operation_id="create_user")
def create_user(payload: UserCreate, db: SQLiteDB = Depends(get_db)):
    """
    Create a new user.
    :param payload: The user data to create the user. Example: {"name": "John Doe", "email": "john@example.com", "phone": 1234567890, "city": "New York", "state": "NY", "country": "USA"}
    :return: The created user as a UserOut model.
    """
    try:
        user_id = db.insert(
            "users", 
            {
                "email": payload.email, 
                "name": payload.name, 
                "phone": payload.phone, 
                "city": payload.city, 
                "state": payload.state, 
                "country": payload.country
            }
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Email/Phone number already exists")
    rows = db.select("users", where={"id": user_id})
    return rows[0]

@app.get("/users", response_model=List[UserOut], operation_id="list_users")
def list_users(
    email: Optional[EmailStr] = Query(default=None),
    name: Optional[str] = Query(default=None),
    phone: Optional[int] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: SQLiteDB = Depends(get_db)
):
    """
    List users with optional filtering by email and name, and pagination support.
    :param email: Optional email to filter users.
    :param name: Optional name to filter users.
    :param phone: Optional phone number to filter users.
    :param limit: Maximum number of users to return (default is 100, max is 1000).
    :param offset: Number of users to skip (default is 0). 
    :return: A list of users matching the criteria.
    """
    where = {}
    if email is not None:
        where["email"] = str(email)
    if name is not None:
        where["name"] = name
    if phone is not None:
        where["phone"] = phone
    
    return db.select("users", where=where or None, order_by='"id" DESC', limit=limit, offset=offset)

@app.get("/users/{user_id}", response_model=UserOut, operation_id="get_user")
def get_user(user_id: int, db: SQLiteDB = Depends(get_db)):
    """
    Get a user by ID.
    :param user_id: The ID of the user to retrieve.
    :return: The user as a UserOut model.
    """
    rows = db.select("users", where={"id": user_id})
    if not rows:
        raise HTTPException(status_code=404, detail="User not found")
    return rows[0]

@app.patch("/users/{user_id}", response_model=UserOut, operation_id="update_user")
def update_user(user_id: int, payload: UserUpdate, db: SQLiteDB = Depends(get_db)):
    """
    Update a user by ID.
    :param user_id: The ID of the user to update.
    :param payload: The user data to update. Example: {"name": "John Doe", "email": "john@example.com", "phone": 1234567890, "city": "New York", "state": "NY", "country": "USA"}
    :return: The updated user as a UserOut model.
    """
    data = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "email" in data:
        data["email"] = str(data["email"])
    try:
        updated = db.update("users", data, where={"id": user_id})
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Email already exists")
    if updated == 0:
        raise HTTPException(status_code=404, detail="User not found")
    rows = db.select("users", where={"id": user_id})
    return rows[0]

@app.delete("/users/{user_id}", operation_id="delete_user")
def delete_user(user_id: int, db: SQLiteDB = Depends(get_db)):
    """
    Delete a user by ID.
    :param user_id: The ID of the user to delete.
    :return: A dictionary indicating whether the user was deleted.
    """
    deleted = db.delete("users", where={"id": user_id})
    if deleted == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True, "deleted": deleted}

from fastapi_mcp import FastApiMCP, AuthConfig

mcp = FastApiMCP(
    app,
    name="My SQL MCP Server",
    description="MCP Server to interact with database",
    exclude_operations=["init_db", "delete_user"],
    auth_config=AuthConfig(
        dependencies=[Depends(verify_bearer)],
    ),
)

mcp.mount_http()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)