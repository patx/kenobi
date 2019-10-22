#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    KenobiDB is a stupid and small document based DB, supporting very simple
    usage including insertion, removal and basic search. It useses pickle.
    Written by Harrison Erd (https://patx.github.io/)
    https://patx.github.io/kenobi/
"""

# Copyright 2019 Harrison Erd

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

import pickle
import os

class KenobiDB(object):

    def __init__(self, file, auto_save=False):
        """Creates a database object and loads the data from the location path.
        If the file does not exist it will be created. Also allows you to set
        auto_save to True or False (default=False). If auto_save is set to
        True the database is written to file after all changes.
        """
        self.file = os.path.expanduser(file)
        self.auto_save = auto_save
        if os.path.exists(self.file):
            self.db = pickle.load(open(self.file, 'rb'))
        else:
            self.db = []

    # Utility functions

    def save_db(self):
        """Force dump the database to a file, return True."""
        pickle.dump(self.db, open(self.file, 'wb'))
        return True

    def _autosave(self):
        """Save database to file if auto_save=True"""
        if self.auto_save:
            self.save_db()

    # Add/delete functions

    def insert(self, document):
        """Add a document (a python dict) to the database and return True.
        Example:
            insert({'name': 'user1', 'groups': ['user', 'sudo']})
        """
        self.db.append(document)
        self._autosave()
        return True

    def remove(self, key, value):
        """Remove a document with the matching key: value pair as key
        and value args given, return document(s) that were removed.
        Example:
            remove('name', 'user1')
        """
        result = []
        for document in self.db:
            if (key, value) in document.items():
                result.append(document)
                self.db.remove(document)
        self._autosave()
        return result

    def update(self, id_key, id_value, new_dict):
        """Update a document, takes three arguments,
        one key and one value to find which document to update,
        and a dict which contains the key/value pair to be updated/
        inserted.
        Example: 
            update('name', 'user1', {'groups': ['user', 'admin', 'sudo']})
        """
        for document in self.db:
            if (id_key, id_value) in document.items():
                self.db.remove(document)
                document.update(new_dict)
                self.insert(document)
        self._autosave()
        return True

    def purge(self):
        """Remove all documents from the database, return True.
        Example:
            purge()
        """
        self.db = []
        self._autosave()
        return True

    # Search functions

    def all(self):
        """Return a list of all documents in the database.
        Example:
            all()
        """
        return self.db

    def search(self, key, value):
        """Return a list of documents with key: value pairs matching the
        given key and value args given.
        Example:
            search('name', 'user1')
        """
        result = []
        for document in self.db:
            if (key, value) in document.items():
                result.append(document)
        return result

    def find_any(self, key, value):
        """For use with a value that is a list. Return a list of documents 
        with keys including all matches from the list value.
        Example:
            find_any('groups', ['admin', 'sudo'])
        """
        result = []
        for document in self.db:
            if key in document.keys():
                doc_list = document[key]
                if any(elem in doc_list for elem in value):
                    result.append(document)
        return result

    def find_all(self, key, value):
        """For use with a value that is a list. Return a list of documents
        with keys including at least one match from the list value.
        Example:
            find_all('groups', ['admin', 'user'])
        """
        result = []
        for document in self.db:
            if key in document.keys():
                doc_list = document[key]
                if all(elem in doc_list for elem in value):
                    result.append(document)
        return result

