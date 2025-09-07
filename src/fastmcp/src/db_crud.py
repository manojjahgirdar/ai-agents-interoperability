#
# Code assisted by OpenAI: GPT-5
# Simple SQLite helper for common CRUD and DDL operations.
#
# Data source: https://www.mysqltutorial.org/wp-content/uploads/2023/10/mysqlsampledatabase.zip

import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

RowDict = Dict[str, Any]
Where = Optional[Mapping[str, Any]]

class SQLiteDB:
    """
    Simple SQLite helper for common CRUD and DDL operations.
    """

    def __init__(self, path: str):
        self.path = path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        if self._conn is None:
            self._conn = sqlite3.connect(self.path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON;")

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "SQLiteDB":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        # Auto-commit or rollback on exit
        if self._conn is not None:
            if exc is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        self.close()

    @property
    def conn(self) -> sqlite3.Connection:
        self.connect()
        assert self._conn is not None
        return self._conn

    @contextmanager
    def cursor(self) -> Iterable[sqlite3.Cursor]:
        cur = self.conn.cursor()
        try:
            yield cur
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    # ------------ DDL ------------

    def create_table(
        self,
        name: str,
        columns: Mapping[str, str],
        primary_key: Optional[Union[str, Sequence[str]]] = None,
        uniques: Optional[Sequence[Sequence[str]]] = None,
        foreign_keys: Optional[Sequence[str]] = None,
        if_not_exists: bool = True,
        without_rowid: bool = False,
    ) -> None:
        """
        Create a table.
        columns: {"id": "INTEGER", "name": "TEXT NOT NULL", ...}
        primary_key: "id" or ["a", "b"]
        uniques: e.g. [["email"], ["a", "b"]]
        foreign_keys: raw constraints, e.g. ['FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE']
        """
        self._validate_ident(name)
        col_defs = [f'{self._quote_ident(col)} {type_}' for col, type_ in columns.items()]

        constraints: List[str] = []
        if primary_key:
            if isinstance(primary_key, str):
                constraints.append(f"PRIMARY KEY ({self._quote_ident(primary_key)})")
            else:
                cols = ", ".join(self._quote_ident(c) for c in primary_key)
                constraints.append(f"PRIMARY KEY ({cols})")

        if uniques:
            for uniq in uniques:
                cols = ", ".join(self._quote_ident(c) for c in uniq)
                constraints.append(f"UNIQUE ({cols})")

        if foreign_keys:
            for fk in foreign_keys:
                constraints.append(fk)

        parts = col_defs + constraints
        ine = "IF NOT EXISTS " if if_not_exists else ""
        tail = " WITHOUT ROWID" if without_rowid else ""
        sql = f"CREATE TABLE {ine}{self._quote_ident(name)} (\n  " + ",\n  ".join(parts) + f"\n){tail};"
        with self.cursor() as cur:
            cur.execute(sql)

    def drop_table(self, name: str, if_exists: bool = True) -> None:
        self._validate_ident(name)
        ie = "IF EXISTS " if if_exists else ""
        with self.cursor() as cur:
            cur.execute(f"DROP TABLE {ie}{self._quote_ident(name)};")

    def table_exists(self, name: str) -> bool:
        q = "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1;"
        with self.cursor() as cur:
            cur.execute(q, (name,))
            return cur.fetchone() is not None

    def list_tables(self) -> List[str]:
        q = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
        with self.cursor() as cur:
            cur.execute(q)
            return [r[0] for r in cur.fetchall()]

    # ------------ CRUD ------------

    def insert(
        self,
        table: str,
        data: Union[RowDict, Sequence[RowDict]],
        or_replace: bool = False,
        or_ignore: bool = False,
        return_ids: bool = True,
    ) -> Union[int, List[int], None]:
        """
        Insert one or many rows.
        Returns lastrowid for single insert, or list of ids for multiple inserts if return_ids=True.
        """
        self._validate_ident(table)

        def _insert_one(row: RowDict) -> int:
            if not row:
                raise ValueError("Insert data cannot be empty.")
            cols = list(row.keys())
            self._validate_ids(cols)
            placeholders = ", ".join(["?"] * len(cols))
            col_sql = ", ".join(self._quote_ident(c) for c in cols)
            verb = "INSERT"
            if or_replace:
                verb = "INSERT OR REPLACE"
            elif or_ignore:
                verb = "INSERT OR IGNORE"
            sql = f"{verb} INTO {self._quote_ident(table)} ({col_sql}) VALUES ({placeholders});"
            with self.cursor() as cur:
                cur.execute(sql, tuple(row[c] for c in cols))
                return cur.lastrowid

        if isinstance(data, Mapping):
            last_id = _insert_one(data) if return_ids else None
            return last_id
        else:
            ids: List[int] = []
            if return_ids:
                for row in data:
                    ids.append(_insert_one(row))
                return ids
            else:
                # Fast path without collecting ids
                if not data:
                    return None
                cols = list(data[0].keys())
                self._validate_ids(cols)
                placeholders = ", ".join(["?"] * len(cols))
                col_sql = ", ".join(self._quote_ident(c) for c in cols)
                verb = "INSERT"
                if or_replace:
                    verb = "INSERT OR REPLACE"
                elif or_ignore:
                    verb = "INSERT OR IGNORE"
                sql = f"{verb} INTO {self._quote_ident(table)} ({col_sql}) VALUES ({placeholders});"
                with self.cursor() as cur:
                    cur.executemany(sql, [tuple(row[c] for c in cols) for row in data])
                return None

    def select(
        self,
        table: str,
        columns: Union[str, Sequence[str]] = "*",
        where: Where = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[RowDict]:
        self._validate_ident(table)
        cols_sql = "*"
        if isinstance(columns, str):
            cols_sql = columns if columns.strip() != "" else "*"
        else:
            self._validate_ids(columns)
            cols_sql = ", ".join(self._quote_ident(c) for c in columns)

        sql = f"SELECT {cols_sql} FROM {self._quote_ident(table)}"
        where_sql, params = self._build_where(where)
        if where_sql:
            sql += " WHERE " + where_sql
        if order_by:
            sql += " ORDER BY " + order_by
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            if limit is None:
                # SQLite requires LIMIT when using OFFSET; use a very large limit
                sql += " LIMIT -1"
            sql += " OFFSET ?"
            params.append(offset)

        with self.cursor() as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def update(
        self,
        table: str,
        data: RowDict,
        where: Where = None,
        allow_all: bool = False,
    ) -> int:
        """
        Update rows. Returns number of affected rows.
        To update all rows, set allow_all=True and where=None.
        """
        self._validate_ident(table)
        if not data:
            return 0
        if where is None and not allow_all:
            raise ValueError("Refusing to update all rows without allow_all=True")

        self._validate_ids(data.keys())
        set_sql = ", ".join(f"{self._quote_ident(k)}=?" for k in data.keys())
        set_params = list(data.values())

        where_sql, where_params = self._build_where(where)
        sql = f"UPDATE {self._quote_ident(table)} SET {set_sql}"
        params: List[Any] = set_params
        if where_sql:
            sql += " WHERE " + where_sql
            params += where_params

        with self.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount

    def delete(
        self,
        table: str,
        where: Where = None,
        allow_all: bool = False,
    ) -> int:
        """
        Delete rows. Returns number of affected rows.
        To delete all rows, set allow_all=True and where=None.
        """
        self._validate_ident(table)
        if where is None and not allow_all:
            raise ValueError("Refusing to delete all rows without allow_all=True")

        where_sql, params = self._build_where(where)
        sql = f"DELETE FROM {self._quote_ident(table)}"
        if where_sql:
            sql += " WHERE " + where_sql

        with self.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount

    # ------------ Utilities ------------

    def execute(self, sql: str, params: Sequence[Any] = ()) -> List[RowDict]:
        """
        Execute arbitrary SQL (parameterized). Returns rows if any.
        """
        with self.cursor() as cur:
            cur.execute(sql, params)
            try:
                rows = cur.fetchall()
                return [dict(r) for r in rows]
            except sqlite3.ProgrammingError:
                return []

    @contextmanager
    def transaction(self) -> Iterable[None]:
        """
        Explicit transaction block:
            with db.transaction():
                ...
        """
        try:
            self.conn.execute("BEGIN;")
            yield
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    # ------------ Internal helpers ------------

    def _build_where(self, where: Where) -> Tuple[str, List[Any]]:
        """
        Build a simple WHERE clause from a dict of equality matches, None -> IS NULL,
        list/tuple -> IN (...).
        """
        if not where:
            return "", []
        clauses: List[str] = []
        params: List[Any] = []
        for k, v in where.items():
            self._validate_ident(k)
            col = self._quote_ident(k)
            if v is None:
                clauses.append(f"{col} IS NULL")
            elif isinstance(v, (list, tuple)):
                if len(v) == 0:
                    # IN () is invalid; use a clause that is always false
                    clauses.append("1=0")
                else:
                    placeholders = ", ".join(["?"] * len(v))
                    clauses.append(f"{col} IN ({placeholders})")
                    params.extend(list(v))
            else:
                clauses.append(f"{col} = ?")
                params.append(v)
        return " AND ".join(clauses), params

    def _validate_ident(self, name: str) -> None:
        if not isinstance(name, str) or not name or any(c in name for c in "\"'`;"):
            raise ValueError(f"Invalid identifier: {name!r}")
        # Basic whitelist: letters, digits, underscore, and optional dot for schema.table
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$.")
        if not set(name) <= allowed:
            raise ValueError(f"Invalid identifier characters in: {name!r}")

    def _validate_ids(self, names: Iterable[str]) -> None:
        for n in names:
            self._validate_ident(n)

    def _quote_ident(self, name: str) -> str:
        # Quote identifiers with double-quotes for safety
        self._validate_ident(name)
        return f'"{name}"'