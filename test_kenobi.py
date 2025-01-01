import unittest
import os
import yaml
from kenobi import KenobiDB

class TestKenobiDB(unittest.TestCase):

    def setUp(self):
        self.test_file = "test_db.yaml"
        self.db = KenobiDB(self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_insert(self):
        document = {"name": "Alice", "age": 30}
        self.assertTrue(self.db.insert(document))
        self.assertIn(document, self.db.all())

    def test_insert_invalid(self):
        with self.assertRaises(TypeError):
            self.db.insert(["not", "a", "dict"])

    def test_insert_many(self):
        documents = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        self.assertTrue(self.db.insert_many(documents))
        self.assertEqual(len(self.db.all()), len(documents))

    def test_insert_many_invalid(self):
        with self.assertRaises(TypeError):
            self.db.insert_many("not a list")

        with self.assertRaises(TypeError):
            self.db.insert_many([{ "valid": "dict" }, "not a dict"])

    def test_remove(self):
        self.db.insert({"name": "Alice", "age": 30})
        self.db.insert({"name": "Bob", "age": 25})
        removed = self.db.remove("name", "Alice")
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0]["name"], "Alice")
        self.assertNotIn({"name": "Alice", "age": 30}, self.db.all())

    def test_update(self):
        self.db.insert({"id": 1, "name": "Alice"})
        self.db.update("id", 1, {"age": 30})
        updated = self.db.search("id", 1)[0]
        self.assertIn("age", updated)
        self.assertEqual(updated["age"], 30)

    def test_purge(self):
        self.db.insert({"name": "Alice"})
        self.db.insert({"name": "Bob"})
        self.assertTrue(self.db.purge())
        self.assertEqual(len(self.db.all()), 0)

    def test_all(self):
        documents = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        self.db.insert_many(documents)
        self.assertEqual(self.db.all(), documents)

    def test_search(self):
        documents = [
            {"name": "Alice", "age": 30},
            {"name": "Alice", "age": 25}
        ]
        self.db.insert_many(documents)
        result = self.db.search("name", "Alice")
        self.assertEqual(len(result), 2)

    def test_find_any(self):
        documents = [
            {"tags": ["python", "coding"]},
            {"tags": ["cooking", "baking"]}
        ]
        self.db.insert_many(documents)
        result = self.db.find_any("tags", ["python", "baking"])
        self.assertEqual(len(result), 2)

    def test_find_all(self):
        documents = [
            {"tags": ["python", "coding", "testing"]},
            {"tags": ["coding", "testing"]}
        ]
        self.db.insert_many(documents)
        result = self.db.find_all("tags", ["coding", "testing"])
        self.assertEqual(len(result), 2)

if __name__ == "__main__":
    unittest.main()

