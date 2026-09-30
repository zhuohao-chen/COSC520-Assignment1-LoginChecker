
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from linear_search import linear_search
from binary_search import binary_search
from hash_table import HashTable
from bloom_filter import BloomFilter
from cuckoo_filter import CuckooFilter


class TestAlgorithms(unittest.TestCase):

    def test_linear_search(self):
        users = ["alice", "bob", "cisco"]
        self.assertTrue(linear_search(users, "bob"))
        self.assertFalse(linear_search(users, "david"))
        self.assertFalse(linear_search([], "alice"))

    def test_binary_search(self):
        users = ["alice", "bob", "cisco"]
        self.assertTrue(binary_search(users, "bob"))
        self.assertFalse(binary_search(users, "david"))
        self.assertFalse(binary_search([], "alice"))

    def test_hash_table(self):
        table = HashTable(capacity=2)
        users = [f"user{i}" for i in range(20)]

        for user in users:
            table.insert(user)

        for user in users:
            self.assertTrue(table.contains(user))

        self.assertFalse(table.contains("missing"))
        self.assertEqual(table.size, len(users))
        self.assertGreater(table.capacity, 2)

        table.insert("user0")
        self.assertEqual(table.size, len(users))

    def test_bloom_filter(self):
        bf = BloomFilter(m=10007, k=7)
        users = ["alice", "bob", "cisco"]

        self.assertFalse(bf.contains("alice"))

        for user in users:
            bf.add(user)

        for user in users:
            self.assertTrue(bf.contains(user))

    def test_cuckoo_filter(self):
        cf = CuckooFilter(
            capacity=64,
            bucket_size=4,
            fingerprint_bits=12
        )
        users = ["alice", "bob", "cisco", "david"]

        for user in users:
            self.assertTrue(cf.insert(user))

        for user in users:
            self.assertTrue(cf.contains(user))

        self.assertEqual(cf.size, len(users))


if __name__ == "__main__":
    unittest.main()
