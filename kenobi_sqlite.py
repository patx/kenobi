#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    KenobiDB is a small document-based DB, supporting very simple
    usage including insertion, removal and basic search.
    Enhanced to use SQLite for better performance and scalability.
"""

import os
import sqlite3
import json
from threading import RLock
from multiprocessing import Lock as ProcessLock

class KenobiDB:

    def __init__(self, file):
        """Creates a database object and sets up SQLite storage. If the database
        file does not exist, it will be created.
        """
        self.file = os.path.expanduser(file)
        self._lock = RLock()
        self._process_lock = ProcessLock()

        with self._lock, self._process_lock:
            self._initialize_db()

    def _initialize_db(self):
        """Initialize the SQLite database and ensure the table exists."""
        with sqlite3.connect(self.file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL
                )
            """)

    # Add/delete functions

    def insert(self, document):
        """Add a document (a Python dict) to the database and return True."""
        if not isinstance(document, dict):
            raise TypeError("Must insert a dict")
        with self._lock, self._process_lock, sqlite3.connect(self.file, isolation_level="EXCLUSIVE") as conn:
            conn.execute("INSERT INTO documents (data) VALUES (?)", (json.dumps(document),))
        return True

    def insert_many(self, document_list):
        """Add a list of documents to the database and return True."""
        if not isinstance(document_list, list) or not all(isinstance(doc, dict) for doc in document_list):
            raise TypeError("Must insert a list of dicts")
        with self._lock, self._process_lock, sqlite3.connect(self.file, isolation_level="EXCLUSIVE") as conn:
            conn.executemany("INSERT INTO documents (data) VALUES (?)", [(json.dumps(doc),) for doc in document_list])
        return True

    def remove(self, key, value):
        """Remove document(s) with the matching key:value pair."""
        query = f"DELETE FROM documents WHERE json_extract(data, '$.{key}') = ?"
        with self._lock, self._process_lock, sqlite3.connect(self.file, isolation_level="EXCLUSIVE") as conn:
            cursor = conn.execute("SELECT data FROM documents WHERE json_extract(data, '$.{key}') = ?", (value,))
            removed_items = [json.loads(row[0]) for row in cursor.fetchall()]
            conn.execute(query, (value,))
        return removed_items

    def update(self, id_key, id_value, new_dict):
        """Update a document and return True."""
        query = f"UPDATE documents SET data = ? WHERE json_extract(data, '$.{id_key}') = ?"
        with self._lock, self._process_lock, sqlite3.connect(self.file, isolation_level="EXCLUSIVE") as conn:
            cursor = conn.execute(f"SELECT data FROM documents WHERE json_extract(data, '$.{id_key}') = ?", (id_value,))
            for row in cursor.fetchall():
                document = json.loads(row[0])  # Deserialize the existing document
                document.update(new_dict)  # Apply updates
                conn.execute(query, (json.dumps(document), id_value))  # Serialize and save
        return True

    def purge(self):
        """Remove all documents from the database, return True."""
        with self._lock, self._process_lock, sqlite3.connect(self.file, isolation_level="EXCLUSIVE") as conn:
            conn.execute("DELETE FROM documents")
        return True

    # Search functions

    def all(self):
        """Return a list of all documents in the database."""
        with self._lock, sqlite3.connect(self.file) as conn:
            cursor = conn.execute("SELECT data FROM documents")
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def search(self, key, value):
        """Return a list of documents with key:value pairs matching."""
        query = f"SELECT data FROM documents WHERE json_extract(data, '$.{key}') = ?"
        with self._lock, sqlite3.connect(self.file) as conn:
            cursor = conn.execute(query, (value,))
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def find_any(self, key, value_list):
        """Return a list of documents where the key matches any value in value_list."""
        placeholders = ', '.join(['?'] * len(value_list))
        query = f"""
        SELECT DISTINCT documents.data
        FROM documents, json_each(documents.data, '$.{key}')
        WHERE json_each.value IN ({placeholders})
        """
        with self._lock, sqlite3.connect(self.file) as conn:
            cursor = conn.execute(query, value_list)
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def find_all(self, key, value_list):
        """Return a list of documents where the key matches all values in value_list."""
        placeholders = ', '.join(['?'] * len(value_list))
        query = f"""
        SELECT documents.data
        FROM documents
        WHERE (
            SELECT COUNT(DISTINCT value)
            FROM json_each(documents.data, '$.{key}')
            WHERE value IN ({placeholders})
        ) = ?
        """
        with self._lock, sqlite3.connect(self.file) as conn:
            cursor = conn.execute(query, value_list + [len(value_list)])
            return [json.loads(row[0]) for row in cursor.fetchall()]

