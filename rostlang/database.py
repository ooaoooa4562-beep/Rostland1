"""SQLite standard-library support for RostLang."""
import re
import sqlite3

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_COLUMN_TYPES = {
    "INTEGER", "REAL", "TEXT", "BLOB",
    "INTEGER PRIMARY KEY",
    "INTEGER PRIMARY KEY AUTOINCREMENT",
    "TEXT NOT NULL", "REAL NOT NULL", "INTEGER NOT NULL",
    "TEXT UNIQUE", "INTEGER UNIQUE",
}


class DatabaseManager:
    def __init__(self):
        self._connections = {}
        self._next_id = 1

    @staticmethod
    def _identifier(value, label="identifier"):
        value = str(value)
        if not _IDENTIFIER.fullmatch(value):
            raise ValueError(f"Database: invalid {label}: {value!r}")
        return '"' + value + '"'

    def _connection(self, handle):
        try:
            return self._connections[int(handle)]
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"Database: unknown or closed connection: {handle!r}")

    def open(self, path):
        connection = sqlite3.connect(str(path))
        connection.row_factory = sqlite3.Row
        handle = self._next_id
        self._next_id += 1
        self._connections[handle] = connection
        return handle

    def close(self, handle):
        connection = self._connection(handle)
        connection.close()
        del self._connections[int(handle)]
        return True

    def create_table(self, handle, table, columns):
        if not isinstance(columns, dict) or not columns:
            raise ValueError("DBCreateTable(): columns must be a non-empty dictionary")
        definitions = []
        for name, declaration in columns.items():
            column_sql = self._identifier(name, "column name")
            declaration = str(declaration).strip().upper()
            if declaration not in _COLUMN_TYPES:
                raise ValueError(f"DBCreateTable(): unsupported column declaration: {declaration}")
            definitions.append(f"{column_sql} {declaration}")
        sql = f"CREATE TABLE {self._identifier(table, 'table name')} ({', '.join(definitions)})"
        self._connection(handle).execute(sql)
        return True

    def insert(self, handle, table, values):
        if not isinstance(values, dict) or not values:
            raise ValueError("DBInsert(): values must be a non-empty dictionary")
        names = list(values)
        columns = ", ".join(self._identifier(name, "column name") for name in names)
        placeholders = ", ".join("?" for _ in names)
        sql = f"INSERT INTO {self._identifier(table, 'table name')} ({columns}) VALUES ({placeholders})"
        cursor = self._connection(handle).execute(sql, [values[name] for name in names])
        return cursor.lastrowid

    def select(self, handle, table, columns=None, where="", params=None):
        columns = ["*"] if columns is None else columns
        if not isinstance(columns, (list, tuple)) or not columns:
            raise ValueError("DBSelect(): columns must be a non-empty list")
        if list(columns) == ["*"]:
            columns_sql = "*"
        else:
            columns_sql = ", ".join(self._identifier(name, "column name") for name in columns)
        sql = f"SELECT {columns_sql} FROM {self._identifier(table, 'table name')}"
        if where:
            sql += " WHERE " + str(where)
        cursor = self._connection(handle).execute(sql, list(params or []))
        return [dict(row) for row in cursor.fetchall()]

    def update(self, handle, table, values, where, params=None):
        if not isinstance(values, dict) or not values:
            raise ValueError("DBUpdate(): values must be a non-empty dictionary")
        if not str(where).strip():
            raise ValueError("DBUpdate(): a WHERE condition is required")
        assignments = ", ".join(
            f"{self._identifier(name, 'column name')} = ?" for name in values
        )
        sql = f"UPDATE {self._identifier(table, 'table name')} SET {assignments} WHERE {where}"
        cursor = self._connection(handle).execute(
            sql, list(values.values()) + list(params or [])
        )
        return cursor.rowcount

    def delete(self, handle, table, where, params=None):
        if not str(where).strip():
            raise ValueError("DBDelete(): a WHERE condition is required")
        sql = f"DELETE FROM {self._identifier(table, 'table name')} WHERE {where}"
        return self._connection(handle).execute(sql, list(params or [])).rowcount

    def count(self, handle, table, where="", params=None):
        sql = f"SELECT COUNT(*) AS total FROM {self._identifier(table, 'table name')}"
        if where:
            sql += " WHERE " + str(where)
        row = self._connection(handle).execute(sql, list(params or [])).fetchone()
        return row["total"]

    def tables(self, handle):
        rows = self._connection(handle).execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return [row["name"] for row in rows]

    def commit(self, handle):
        self._connection(handle).commit()
        return True
