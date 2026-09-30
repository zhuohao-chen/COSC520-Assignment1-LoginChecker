"""Place under tests/ and run with python -m unittest discover -s tests -v."""
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from cuckoo_filter_large import LargeCuckooFilter


class TestLargeCuckooFilter(unittest.TestCase):
    def test_insert_and_lookup(self):
        cf = LargeCuckooFilter(capacity=32, bucket_size=4)
        names = [f"user{i}" for i in range(80)]
        random.seed(2026)
        for name in names:
            self.assertTrue(cf.insert(name))
        self.assertEqual(cf.size, len(names))
        for name in names:
            self.assertTrue(cf.contains(name))

    def test_rollback_on_full_filter(self):
        cf = LargeCuckooFilter(capacity=2, bucket_size=1, max_kicks=3)
        self.assertTrue(cf.insert("alice"))
        self.assertTrue(cf.insert("bob"))
        original = [bucket.copy() for bucket in cf.buckets]
        original_size = cf.size
        random.seed(2026)
        self.assertFalse(cf.insert("charlie"))
        self.assertEqual(cf.size, original_size)
        self.assertEqual(cf.buckets, original)
        self.assertTrue(cf.contains("alice"))
        self.assertTrue(cf.contains("bob"))


if __name__ == "__main__":
    unittest.main()
