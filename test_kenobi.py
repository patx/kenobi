import unittest
import os
import threading
from kenobi import KenobiDB


class TestKenobiDB(unittest.TestCase):
    def setUp(self):
        """Create a fresh instance of KenobiDB before each test."""
        self.test_file = "test_db.yaml"
        self.db = KenobiDB(self.test_file)

    def tearDown(self):
        """Clean up test files after each test."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    # Test insert single document
    def test_insert(self):
        document = {"name": "Alice", "age": 30}
        self.assertTrue(self.db.insert(document))
        self.assertIn(document, self.db.all())

    # Test insert invalid document
    def test_insert_invalid(self):
        with self.assertRaises(TypeError):
            self.db.insert(["not", "a", "dict"])

    # Test insert multiple documents
    def test_insert_many(self):
        documents = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        self.assertTrue(self.db.insert_many(documents))
        self.assertEqual(len(self.db.all()), len(documents))

    # Test insert invalid multiple documents
    def test_insert_many_invalid(self):
        with self.assertRaises(TypeError):
            self.db.insert_many("not a list")
        with self.assertRaises(TypeError):
            self.db.insert_many([{"valid": "dict"}, "not a dict"])

    # Test remove document by key-value pair
    def test_remove(self):
        self.db.insert({"name": "Alice", "age": 30})
        self.db.insert({"name": "Bob", "age": 25})
        removed = self.db.remove("name", "Alice")
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0]["name"], "Alice")
        self.assertNotIn({"name": "Alice", "age": 30}, self.db.all())

    # Test update document
    def test_update(self):
        self.db.insert({"id": 1, "name": "Alice"})
        self.db.update("id", 1, {"age": 30})
        updated = self.db.search("id", 1)[0]
        self.assertIn("age", updated)
        self.assertEqual(updated["age"], 30)

    # Test purge all documents
    def test_purge(self):
        self.db.insert({"name": "Alice"})
        self.db.insert({"name": "Bob"})
        self.assertTrue(self.db.purge())
        self.assertEqual(len(self.db.all()), 0)

    # Test retrieve all documents
    def test_all(self):
        documents = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        self.db.insert_many(documents)
        self.assertEqual(self.db.all(), documents)

    # Test search by key-value
    def test_search(self):
        documents = [{"name": "Alice", "age": 30}, {"name": "Alice", "age": 25}]
        self.db.insert_many(documents)
        result = self.db.search("name", "Alice")
        self.assertEqual(len(result), 2)

    # Test find any matching values
    def test_find_any(self):
        documents = [{"tags": ["python", "coding"]}, {"tags": ["cooking", "baking"]}]
        self.db.insert_many(documents)
        result = self.db.find_any("tags", ["python", "baking"])
        self.assertEqual(len(result), 2)

    # Test find all matching values
    def test_find_all(self):
        documents = [{"tags": ["python", "coding", "testing"]}, {"tags": ["coding", "testing"]}]
        self.db.insert_many(documents)
        result = self.db.find_all("tags", ["coding", "testing"])
        self.assertEqual(len(result), 2)

    # Edge case: test inserting invalid data type (not dict)
    def test_insert_invalid_type(self):
        with self.assertRaises(TypeError):
            self.db.insert(["invalid", "document"])

    # Edge case: test searching for non-existent key
    def test_search_non_existent_key(self):
        documents = [{"name": "Alice", "age": 30}]
        self.db.insert_many(documents)
        result = self.db.search("gender", "female")
        self.assertEqual(result, [])

    # Edge case: test removing from empty database
    def test_remove_empty_db(self):
        removed = self.db.remove("name", "Nonexistent")
        self.assertEqual(removed, [])

    # Edge case: test purging from an empty database
    def test_purge_empty_db(self):
        self.assertTrue(self.db.purge())
        self.assertEqual(len(self.db.all()), 0)

    # Edge case: test update on non-existent document
    def test_update_non_existent(self):
        self.db.insert({"id": 1, "name": "Alice"})
        self.db.update("id", 99, {"age": 30})
        result = self.db.search("id", 99)
        self.assertEqual(result, [])

    # Test file creation on insert
    def test_file_creation(self):
        document = {"name": "Alice", "age": 30}
        self.db.insert(document)
        # Manually trigger save to ensure file creation
        self.db.save_db()
        self.assertTrue(os.path.exists(self.test_file))

    # Test file persistence after purging
    def test_file_deletion_after_purge(self):
        self.db.insert({"name": "Alice", "age": 30})
        self.db.purge()
        # Manually trigger save after purge
        self.db.save_db()
        self.assertTrue(os.path.exists(self.test_file))

    # Test concurrency: Simulate multiple threads inserting documents simultaneously
    def test_concurrent_inserts(self):
        def insert_documents():
            for i in range(10):
                self.db.insert({"name": f"Person {i}", "age": 20 + i})

        threads = [threading.Thread(target=insert_documents) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(self.db.all()), 50)  # 5 threads, each inserting 10 documents


    # Test file persistence under concurrent operations
    def test_file_persistence_concurrent_operations(self):
        def insert_and_save():
            for i in range(10):
                self.db.insert({"name": f"Person {i}", "age": 20 + i})
            self.db.save_db()

        threads = [threading.Thread(target=insert_and_save) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertTrue(os.path.exists(self.test_file))  # Ensure file is created after concurrent operations


if __name__ == "__main__":
    unittest.main()

