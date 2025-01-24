#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KenobiDB is a small document-based DB, supporting simple usage including
insertion, removal, and basic search.
Written by Harrison Erd (https://patx.github.io/)
https://patx.github.io/kenobi/
"""
# Copyright Harrison Erd
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

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
    execution.
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
        self._regexp_connections = set()  # Track connections with REGEXP added
        self._connection = sqlite3.connect(self.file, check_same_thread=False)
        self._add_regexp_support(self._connection)  # Add REGEXP support lazily

    def _add_regexp_support(self, conn):
        """
        Add REGEXP function support to the SQLite connection.
        """
        def regexp(pattern, value):
            return re.search(pattern, value) is not None
        conn.create_function("REGEXP", 2, regexp)

    def table(self, name):
        """
        Access or create a specific table.

        Args:
            name (str): The name of the table.

        Returns:
            KenobiTable: An object for interacting with the table.
        """
        if not name or not isinstance(name, str):
            raise ValueError("Table name must be a non-empty string.")
        return KenobiTable(self, name)

    def execute_async(self, func, *args, **kwargs):
        """
        Execute a function asynchronously using a thread pool.

        Args:
            func (callable): The function to execute.
            *args: Arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            concurrent.futures.Future: A Future object representing
            the execution.
        """
        return self.executor.submit(func, *args, **kwargs)

    def close(self):
        """
        Shutdown the thread pool executor and close the database connection.
        """
        self.executor.shutdown()
        with self._lock:
            self._connection.close()

class KenobiTable:
    """
    A class to represent and interact with a specific table within KenobiDB.
    """

    def __init__(self, db, name):
        self.db = db
        self.name = name
        self._lock = db._lock
        self._create_table()

    def _create_table(self):
        """
        Create the table if it does not exist.
        """
        with self._lock:
            self.db._connection.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL
                )
            """)

    def insert(self, document):
        """
        Insert a document into this table.

        Args:
            document (dict): The document to insert.

        Returns:
            bool: True upon successful insertion.
        """
        if not isinstance(document, dict):
            raise TypeError("Must insert a dict")
        with self._lock:
            self.db._connection.execute(
                f"INSERT INTO {self.name} (data) VALUES (?)",
                (json.dumps(document),)
            )
            self.db._connection.commit()
            return True

    def rename(self, new_name):
        """
        Rename the table.

        Args:
            new_name (str): The new name of the table.
        """
        if not new_name or not isinstance(new_name, str):
            raise ValueError("New table name must be a non-empty string.")
        with self._lock:
            self.db._connection.execute(
                f"ALTER TABLE {self.name} RENAME TO {new_name}"
            )
            self.name = new_name

    def drop(self):
        """
        Drop the table.
        """
        with self._lock:
            self.db._connection.execute(f"DROP TABLE {self.name}")

    def all(self, limit=100, offset=0):
        """
        Return a paginated list of all documents in the table.

        Args:
            limit (int): The maximum number of documents to return.
            offset (int): The starting point for retrieval.

        Returns:
            list: A list of all documents (dicts).
        """
        query = f"SELECT data FROM {self.name} LIMIT ? OFFSET ?"
        with self._lock:
            cursor = self.db._connection.execute(query, (limit, offset))
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def search(self, key, value, limit=100, offset=0):
        """
        Return a list of documents matching (key == value) in the table.

        Args:
            key (str): The document field to match on.
            value (Any): The value for which to search.
            limit (int): The maximum number of documents to return.
            offset (int): The starting point for retrieval.

        Returns:
            list: A list of matching documents (dicts).
        """
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")

        query = (
            f"SELECT data FROM {self.name} "
            "WHERE json_extract(data, '$.' || ?) = ? "
            "LIMIT ? OFFSET ?"
        )
        with self._lock:
            cursor = self.db._connection.execute(query, (key, value, limit, offset))
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def remove(self, key, value):
        """
        Remove all documents where the given key matches the specified value.

        Args:
            key (str): The field name to match.
            value (Any): The value to match.

        Returns:
            int: Number of documents removed.
        """
        if not key or not isinstance(key, str):
            raise ValueError("key must be a non-empty string")
        if value is None:
            raise ValueError("value cannot be None")
        query = (
            f"DELETE FROM {self.name} "
            "WHERE json_extract(data, '$.' || ?) = ?"
        )
        with self._lock:
            result = self.db._connection.execute(query, (key, value))
            self.db._connection.commit()
            return result.rowcount

    def update(self, id_key, id_value, new_dict):
        """
        Update documents that match (id_key == id_value) by merging new_dict.

        Args:
            id_key (str): The field name to match.
            id_value (Any): The value to match.
            new_dict (dict): A dictionary of changes to apply.

        Returns:
            bool: True if at least one document was updated, False otherwise.
        """
        if not isinstance(new_dict, dict):
            raise TypeError("new_dict must be a dictionary")
        if not id_key or not isinstance(id_key, str):
            raise ValueError("id_key must be a non-empty string")
        if id_value is None:
            raise ValueError("id_value cannot be None")

        select_query = (
            f"SELECT data FROM {self.name} "
            "WHERE json_extract(data, '$.' || ?) = ?"
        )
        update_query = (
            f"UPDATE {self.name} "
            "SET data = ? "
            "WHERE json_extract(data, '$.' || ?) = ?"
        )
        with self._lock:
            cursor = self.db._connection.execute(select_query, (id_key, id_value))
            documents = cursor.fetchall()
            if not documents:
                return False
            for row in documents:
                document = json.loads(row[0])
                if not isinstance(document, dict):
                    continue
                document.update(new_dict)
                self.db._connection.execute(
                    update_query,
                    (json.dumps(document), id_key, id_value)
                )
            self.db._connection.commit()
            return True

