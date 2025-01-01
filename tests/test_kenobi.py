import unittest
import os
from kenobi import KenobiDB
from typing import List, Dict, Any
import threading

class TestKenobiDB(unittest.TestCase):

    def setUp(self):
        """Set up a temporary test database file."""
        self.test_file = "test_db.yaml"
        self.db = KenobiDB(self.test_file)

    def tearDown(self):
        """Remove the test database file after each test."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_insert_single_document(self):
        """Test inserting a single valid document."""
        document = {"name": "Alice", "age": 30}
        self.assertTrue(self.db.insert(document))
        self.assertIn(document, self.db.all())

    def test_insert_invalid_document(self):
        """Test inserting an invalid document (non-dict)."""
        with self.assertRaises(TypeError):
            self.db.insert(["invalid", "document"])

    def test_insert_many_documents(self):
        """Test inserting multiple valid documents."""
        documents = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        self.assertTrue(self.db.insert_many(documents))
        self.assertEqual(len(self.db.all()), len(documents))

    def test_remove_documents(self):
        """Test removing documents by key-value pair."""
        self.db.insert({"name": "Alice", "age": 30})
        self.db.insert({"name": "Bob", "age": 25})
        removed = self.db.remove("name", "Alice")
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0]["name"], "Alice")
        self.assertNotIn({"name": "Alice", "age": 30}, self.db.all())

    def test_update_document(self):
        """Test updating a document."""
        self.db.insert({"id": 1, "name": "Alice"})
        self.assertTrue(self.db.update("id", 1, {"age": 30}))
        updated = self.db.search("id", 1)[0]
        self.assertIn("age", updated)
        self.assertEqual(updated["age"], 30)

    def test_purge_database(self):
        """Test purging all documents from the database."""
        self.db.insert({"name": "Alice"})
        self.db.insert({"name": "Bob"})
        self.assertTrue(self.db.purge())
        self.assertEqual(len(self.db.all()), 0)

    def test_search_by_key_value(self):
        """Test searching for documents by key-value pair."""
        documents = [{"name": "Alice", "age": 30}, {"name": "Alice", "age": 25}]
        self.db.insert_many(documents)
        result = self.db.search("name", "Alice")
        self.assertEqual(len(result), 2)

    def test_find_any_values(self):
        """Test finding documents where a key matches any value in a list."""
        documents = [{"tags": ["python", "coding"]}, {"tags": ["cooking", "baking"]}]
        self.db.insert_many(documents)
        result = self.db.find_any("tags", ["python", "baking"])
        self.assertEqual(len(result), 2)

    def test_find_all_values(self):
        """Test finding documents where a key matches all values in a list."""
        documents = [{"tags": ["python", "coding", "testing"]}, {"tags": ["coding", "testing"]}]
        self.db.insert_many(documents)
        result = self.db.find_all("tags", ["coding", "testing"])
        self.assertEqual(len(result), 2)

    def test_file_persistence(self):
        """Test that data persists to the file after saving."""
        document = {"name": "Alice", "age": 30}
        self.db.insert(document)
        self.db.save_db()
        self.assertTrue(os.path.exists(self.test_file))
        new_db = KenobiDB(self.test_file)
        self.assertIn(document, new_db.all())

    def test_concurrent_insert_operations(self):
        """Test concurrent inserts from multiple threads."""
        def insert_documents():
            for i in range(10):
                self.db.insert({"name": f"Person {i}", "age": i})

        threads = [threading.Thread(target=insert_documents) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(self.db.all()), 50)  # 5 threads * 10 inserts each

    def test_large_dataset_handling(self):
        """Test inserting a large number of documents."""
        large_dataset = [{"id": i, "value": i * 2} for i in range(100000)]
        self.db.insert_many(large_dataset)
        self.assertEqual(len(self.db.all()), len(large_dataset))

    def test_invalid_yaml_file(self):
        """Test behavior with an invalid YAML file."""
        invalid_content = "::invalid_yaml::"
        with open(self.test_file, "w") as invalid_file:
            invalid_file.write(invalid_content)

        # Verify that a RuntimeError is raised when attempting to load
        with self.assertRaises(RuntimeError):
            KenobiDB(self.test_file)

if __name__ == "__main__":
    unittest.main()

