#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KenobiDB is a small document-based DB, supporting simple usage including
insertion, removal, and basic search, now extended to support collections.
"""
import os
import json
import sqlite3
from threading import RLock
from concurrent.futures import ThreadPoolExecutor
import re

class KenobiDB:
    """
    A lightweight document-based database built on SQLite. Supports basic
    operations such as insert, remove, search, update, and asynchronous
    execution, now with MongoDB-like collection support.
    """

    def __init__(self, file):
        """
        Initialize the KenobiDB instance.

        Args:
            file (str): Path to the SQLite file. If it does not exist,
                it will be created.
        """
        self.file = os.path.expanduser(file)
        self._lock = RLock()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._connection = sqlite3.connect(self.file, check_same_thread=False)
        self._add_regexp_support(self._connection)
        self._initialize_db()

    def _initialize_db(self):
        """
        Create the table and index if they do not exist, and set
        journal mode to WAL.
        """
        with self._lock:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    collection TEXT NOT NULL DEFAULT 'default'
                )
                """
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_key
                ON documents (
                    json_extract(data, '$.key')
                )
                """
            )
            self._connection.execute("PRAGMA journal_mode=WAL;")

    @staticmethod
    def _add_regexp_support(conn):
        """
        Add REGEXP function support to the SQLite connection.
        """
        def regexp(pattern, value):
            return re.search(pattern, value) is not None
        conn.create_function("REGEXP", 2, regexp)

    def insert(self, document, collection="default"):
        """
        Insert a single document into a specific collection.

        Args:
            document (dict): The document to insert.
            collection (str): The collection name. Defaults to 'default'.

        Returns:
            bool: True upon successful insertion.
        """
        if not isinstance(document, dict):
            raise TypeError("Must insert a dict")
        if not isinstance(collection, str) or not collection:
            raise ValueError("Collection must be a non-empty string")
        with self._lock:
            self._connection.execute(
                "INSERT INTO documents (data, collection) VALUES (?, ?)",
                (json.dumps(document), collection)
            )
            self._connection.commit()
            return True

    def insert_many(self, document_list, collection="default"):
        """
        Insert multiple documents into a specific collection.

        Args:
            document_list (list): The list of documents to insert.
            collection (str): The collection name. Defaults to 'default'.

        Returns:
            bool: True upon successful insertion.
        """
        if (
            not isinstance(document_list, list)
            or not all(isinstance(doc, dict) for doc in document_list)
        ):
            raise TypeError("Must insert a list of dicts")
        if not isinstance(collection, str) or not collection:
            raise ValueError("Collection must be a non-empty string")
        with self._lock:
            self._connection.executemany(
                "INSERT INTO documents (data, collection) VALUES (?, ?)",
                [(json.dumps(doc), collection) for doc in document_list]
            )
            self._connection.commit()
            return True

    def remove(self, key, value, collection="default"):
        """
        Remove all documents from a specific collection where key matches value.

        Args:
            key (str): The field name to match.
            value (Any): The value to match.
            collection (str): The collection name. Defaults to 'default'.

        Returns:
            int: Number of documents removed.
        """
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")
        if value is None:
            raise ValueError("Value cannot be None")
        if not isinstance(collection, str) or not collection:
            raise ValueError("Collection must be a non-empty string")
        query = (
            "DELETE FROM documents "
            "WHERE json_extract(data, '$.' || ?) = ? AND collection = ?"
        )
        with self._lock:
            result = self._connection.execute(query, (key, value, collection))
            self._connection.commit()
            return result.rowcount

    def search(self, key, value, collection="default", limit=100, offset=0):
        """
        Search documents in a specific collection matching (key == value).

        Args:
            key (str): The document field to match on.
            value (Any): The value for which to search.
            collection (str): The collection name. Defaults to 'default'.
            limit (int): The maximum number of documents to return.
            offset (int): The starting point for retrieval.

        Returns:
            list: A list of matching documents (dicts).
        """
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")
        if not isinstance(collection, str) or not collection:
            raise ValueError("Collection must be a non-empty string")

        query = (
            "SELECT data FROM documents "
            "WHERE json_extract(data, '$.' || ?) = ? AND collection = ? "
            "LIMIT ? OFFSET ?"
        )
        with self._lock:
            cursor = self._connection.execute(query, (key, value, collection, limit, offset))
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def all(self, collection="default", limit=100, offset=0):
        """
        Return a paginated list of all documents in a specific collection.

        Args:
            collection (str): The collection name. Defaults to 'default'.
            limit (int): The maximum number of documents to return.
            offset (int): The starting point for retrieval.

        Returns:
            list: A list of all documents (dicts).
        """
        if not isinstance(collection, str) or not collection:
            raise ValueError("Collection must be a non-empty string")

        query = "SELECT data FROM documents WHERE collection = ? LIMIT ? OFFSET ?"
        with self._lock:
            cursor = self._connection.execute(query, (collection, limit, offset))
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def list_collections(self):
        """
        List all unique collections in the database.

        Returns:
            list: A list of collection names.
        """
        query = "SELECT DISTINCT collection FROM documents"
        with self._lock:
            cursor = self._connection.execute(query)
            return [row[0] for row in cursor.fetchall()]

    def remove_collection(self, collection):
        """
        Remove all documents in a specific collection.

        Args:
            collection (str): The collection name.

        Returns:
            int: Number of documents removed.
        """
        if not isinstance(collection, str) or not collection:
            raise ValueError("Collection must be a non-empty string")
        query = "DELETE FROM documents WHERE collection = ?"
        with self._lock:
            result = self._connection.execute(query, (collection,))
            self._connection.commit()
            return result.rowcount

    def close(self):
        """
        Shutdown the thread pool executor and close the database connection.
        """
        self.executor.shutdown()
        with self._lock:
            self._connection.close()

