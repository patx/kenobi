#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    KenobiDB is a small document based DB, supporting very simple
    usage including insertion, removal and basic search.
    Written by Harrison Erd (https://patx.github.io/)
    https://patx.github.io/kenobi/
"""

# Copyright Harrison Erd

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from this
# software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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

    # Asynchronous functions

    def execute_async(self, func, *args, **kwargs):
        """Execute a function asynchronously using a thread pool."""
        return self.executor.submit(func, *args, **kwargs)

    def close(self):
        """Shutdown the thread pool executor."""
        self.executor.shutdown()
