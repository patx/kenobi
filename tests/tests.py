import unittest
import os
import json
import time
from kenobi import KenobiDB

class TestKenobiDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Setup a temporary database file for testing."""
        cls.db_file = "test_kenobi.db"
        cls.db = KenobiDB(cls.db_file)

    @classmethod
    def tearDownClass(cls):
        """Cleanup the temporary database file."""
        cls.db.close()
        if os.path.exists(cls.db_file):
            os.remove(cls.db_file)

    def setUp(self):
        """Ensure the database is empty before each test."""
        self.db.purge()

    def test_insert_single_document(self):
        """Test inserting a single document."""
        document = {"key": "value"}
        self.db.insert(document)
        results = self.db.all()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], document)

    def test_insert_many_documents(self):
        """Test inserting multiple documents."""
        documents = [{"key": "value1"}, {"key": "value2"}]
        self.db.insert_many(documents)
        results = self.db.all()
        self.assertEqual(len(results), 2)
        self.assertIn(documents[0], results)
        self.assertIn(documents[1], results)

    def test_remove_document(self):
        """Test removing a document by key:value."""
        document = {"key": "value"}
        self.db.insert(document)
        self.db.remove("key", "value")
        results = self.db.all()
        self.assertEqual(len(results), 0)

    def test_update_document(self):
        """Test updating a document by key:value."""
        document = {"id": 1, "key": "value"}
        updated_fields = {"key": "new_value"}
        self.db.insert(document)
        self.db.update("id", 1, updated_fields)
        results = self.db.all()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["key"], "new_value")

    def test_purge_database(self):
        """Test purging all documents from the database."""
        documents = [{"key": "value1"}, {"key": "value2"}]
        self.db.insert_many(documents)
        self.db.purge()
        results = self.db.all()
        self.assertEqual(len(results), 0)

    def test_search_by_key_value(self):
        """Test searching documents by key:value."""
        documents = [{"key": "value1"}, {"key": "value2"}]
        self.db.insert_many(documents)
        results = self.db.search("key", "value1")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], documents[0])

    def test_find_any(self):
        """Test finding documents where a key matches any value in a list."""
        documents = [{"key": "value1"}, {"key": "value2"}, {"key": "value3"}]
        self.db.insert_many(documents)
        results = self.db.find_any("key", ["value1", "value3"])
        self.assertEqual(len(results), 2)
        self.assertIn(documents[0], results)
        self.assertIn(documents[2], results)

    def test_find_all(self):
        """Test finding documents where a key matches all values in a list."""
        documents = [
            {"key": ["value1", "value2"]},
            {"key": ["value1"]},
            {"key": ["value2", "value3"]}
        ]
        self.db.insert_many(documents)
        results = self.db.find_all("key", ["value1", "value2"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], documents[0])

    def test_pagination_all(self):
        """Test paginated retrieval of all documents."""
        documents = [{"key": f"value{i}"} for i in range(10)]
        self.db.insert_many(documents)
        results = self.db.all(limit=5, offset=0)
        self.assertEqual(len(results), 5)
        self.assertEqual(results, documents[:5])

    def test_pagination_search(self):
        """Test paginated search by key:value."""
        documents = [{"key": f"value{i}"} for i in range(10)]
        self.db.insert_many(documents)
        results = self.db.search("key", "value1", limit=1, offset=0)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], {"key": "value1"})

    def test_concurrent_inserts(self):
        """Test concurrent inserts to ensure thread safety."""
        def insert_task(doc):
            self.db.insert(doc)

        documents = [{"key": f"value{i}"} for i in range(50)]
        with self.db.executor as executor:
            executor.map(insert_task, documents)
        results = self.db.all()
        self.assertEqual(len(results), 50)

    def test_performance_bulk_insert(self):
        """Test the performance of bulk inserting a large number of documents."""
        documents = [{"key": f"value{i}"} for i in range(1000)]
        start_time = time.time()
        self.db.insert_many(documents)
        end_time = time.time()
        duration = end_time - start_time
        self.assertLess(duration, 5, "Bulk insert took too long")

    def test_safe_query_handling(self):
        """Test safe handling of potentially harmful input to prevent SQL injection."""
        document = {"key": "value"}
        self.db.insert(document)
        results = self.db.search("key", "value OR 1=1")
        self.assertEqual(len(results), 0, "Unsafe query execution detected")

if __name__ == "__main__":
    unittest.main()

