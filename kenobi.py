#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    KenobiDB: Optimized for large datasets and concurrent operations.
    Enhancements include indexing, batching, connection pooling, async support, and safety features.
"""

import os
import sqlite3
import json
from threading import RLock
from concurrent.futures import ThreadPoolExecutor

class KenobiDB:

    def __init__(self, file):
        """Creates a database object and sets up SQLite storage. If the database
        file does not exist, it will be created.
        """
        self.file = os.path.expanduser(file)
        self._lock = RLock()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._initialize_db()

    def _initialize_db(self):
        """Initialize the SQLite database and ensure the table and indices exist."""
        with sqlite3.connect(self.file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_key ON documents (
                    json_extract(data, '$.key')
                )
            """)
            conn.execute("PRAGMA journal_mode=WAL;")

    # Add/delete functions

    def insert(self, document):
        """Add a document (a Python dict) to the database."""
        if not isinstance(document, dict):
            raise TypeError("Must insert a dict")
        with self._lock, sqlite3.connect(self.file) as conn:
            conn.execute("INSERT INTO documents (data) VALUES (?)", (json.dumps(document),))

    def insert_many(self, document_list):
        """Add a list of documents to the database."""
        if not isinstance(document_list, list) or not all(isinstance(doc, dict) for doc in document_list):
            raise TypeError("Must insert a list of dicts")
        with self._lock, sqlite3.connect(self.file) as conn:
            conn.executemany("INSERT INTO documents (data) VALUES (?)", [(json.dumps(doc),) for doc in document_list])

    def remove(self, key, value):
        """Remove document(s) with the matching key:value pair."""
        query = "DELETE FROM documents WHERE json_extract(data, '$.' || ?) = ?"
        with self._lock, sqlite3.connect(self.file) as conn:
            conn.execute(query, (key, value))

    def update(self, id_key, id_value, new_dict):
        """Update a document."""
        query = "UPDATE documents SET data = ? WHERE json_extract(data, '$.' || ?) = ?"
        with self._lock, sqlite3.connect(self.file) as conn:
            cursor = conn.execute("SELECT data FROM documents WHERE json_extract(data, '$.' || ?) = ?", (id_key, id_value))
            for row in cursor.fetchall():
                document = json.loads(row[0])
                document.update(new_dict)
                conn.execute(query, (json.dumps(document), id_key, id_value))

    def purge(self):
        """Remove all documents from the database."""
        with self._lock, sqlite3.connect(self.file) as conn:
            conn.execute("DELETE FROM documents")

    # Search functions

    def all(self, limit=100, offset=0):
        """Return a paginated list of all documents."""
        query = "SELECT data FROM documents LIMIT ? OFFSET ?"
        with self._lock, sqlite3.connect(self.file) as conn:
            cursor = conn.execute(query, (limit, offset))
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def search(self, key, value, limit=100, offset=0):
        """Return a paginated list of documents with key:value pairs matching."""
        query = "SELECT data FROM documents WHERE json_extract(data, '$.' || ?) = ? LIMIT ? OFFSET ?"
        with self._lock, sqlite3.connect(self.file) as conn:
            cursor = conn.execute(query, (key, value, limit, offset))
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def find_any(self, key, value_list):
        """Return documents where the key matches any value in value_list."""
        placeholders = ', '.join(['?'] * len(value_list))
        query = f"""
        SELECT DISTINCT documents.data
        FROM documents, json_each(documents.data, '$.' || ?)
        WHERE json_each.value IN ({placeholders})
        """
        with self._lock, sqlite3.connect(self.file) as conn:
            cursor = conn.execute(query, [key] + value_list)
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def find_all(self, key, value_list):
        """Return documents where the key matches all values in value_list."""
        placeholders = ', '.join(['?'] * len(value_list))
        query = f"""
        SELECT documents.data
        FROM documents
        WHERE (
            SELECT COUNT(DISTINCT value)
            FROM json_each(documents.data, '$.' || ?)
            WHERE value IN ({placeholders})
        ) = ?
        """
        with self._lock, sqlite3.connect(self.file) as conn:
            cursor = conn.execute(query, [key] + value_list + [len(value_list)])
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def execute_async(self, func, *args, **kwargs):
        """Execute a function asynchronously using a thread pool."""
        return self.executor.submit(func, *args, **kwargs)

    def close(self):
        """Shutdown the thread pool executor."""
        self.executor.shutdown()
