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
import yaml
from threading import RLock
from multiprocessing import Lock as ProcessLock
from tempfile import NamedTemporaryFile

class KenobiDB:

    def __init__(self, file, auto_save=False):
        """Creates a database object and loads the data from the location
        path. If the file does not exist it will be created. Also allows
        you to set auto_save to True or False (default=False). If auto_save
        is set to True the database is written to file after every change.
        """
        self.file = os.path.expanduser(file)
        self.auto_save = auto_save
        self._lock = RLock()
        self._process_lock = ProcessLock()

        with self._lock, self._process_lock:
            if os.path.exists(self.file):
                if os.stat(self.file).st_size == 0:
                    self.db = []
                    self._autosave()
                else:
                    with open(self.file, 'r') as read_file:
                        self.db = yaml.safe_load(read_file) or []
            else:
                self.db = []
                self._autosave()


    # Utility functions

    def _save_to_file(self):
        temp_file = NamedTemporaryFile("w", delete=False, dir=os.path.dirname(self.file))
        try:
            # Write the database to the temporary file
            yaml.dump(self.db, temp_file)
            temp_file.close()
            # Replace the original database file with the temp file atomically
            os.replace(temp_file.name, self.file)
        except Exception as e:
            os.unlink(temp_file.name)  # Cleanup temp file on failure
            raise e

    def _autosave(self):
        if self.auto_save:
            self.save_db()

    def save_db(self):
        """Save the database, ensuring thread and process safety."""
        # If already inside a locked context, just call _save_to_file directly
        if self.auto_save and self._lock._is_owned():
            self._save_to_file()
        else:
            # Otherwise, acquire both locks to save the database
            with self._lock, self._process_lock:
                self._save_to_file()
        return True


    # Add/delete functions

    def insert(self, document):
        """Add a document (a python dict) to the database and return True."""
        if not isinstance(document, dict):
            raise TypeError("Must insert a dict")
        with self._lock, self._process_lock:
            self.db.append(document)
            self._autosave()
        return True

    def insert_many(self, document_list):
        """Add a list of documents to the database and return True."""
        if not isinstance(document_list, list) or not all(isinstance(doc, dict) for doc in document_list):
            raise TypeError("Must insert a list of dicts")
        with self._lock, self._process_lock:
            self.db.extend(document_list)
            self._autosave()
        return True

    def remove(self, key, value):
        """Remove document(s) with the matching key: value pair."""
        with self._lock, self._process_lock:
            original_db = self.db[:]
            self.db = [doc for doc in self.db if (key, value) not in doc.items()]
            removed_items = [doc for doc in original_db if doc not in self.db]
            self._autosave()
        return removed_items

    def update(self, id_key, id_value, new_dict):
        """Update a document, takes three arguments."""
        with self._lock, self._process_lock:
            for idx, document in enumerate(self.db):
                if document.get(id_key) == id_value:
                    self.db[idx] = {**document, **new_dict}
            self._autosave()
        return True

    def purge(self):
        """Remove all documents from the database, return True."""
        with self._lock, self._process_lock:
            self.db = []
            self._autosave()
        return True


    # Search functions

    def all(self):
        """Return a list of all documents in the database."""
        with self._lock:
            return self.db[:]

    def search(self, key, value):
        """Return a list of documents with key: value pairs matching."""
        with self._lock:
            return [doc for doc in self.db if doc.get(key) == value]

    def find_any(self, key, value_list):
        """Return a list of documents with values including any matches."""
        with self._lock:
            return [doc for doc in self.db if key in doc and any(v in doc[key] for v in value_list)]

    def find_all(self, key, value_list):
        """Return a list of documents with values including all matches."""
        with self._lock:
            return [doc for doc in self.db if key in doc and all(v in doc[key] for v in value_list)]

