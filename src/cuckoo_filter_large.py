"""Cuckoo filter variant with an O(max_kicks) rollback log.
For large-scale experiments only. The original implementation in
src/cuckoo_filter.py remains unchanged, preserving earlier benchmark results.
"""

import random
from cuckoo_filter import CuckooFilter


class LargeCuckooFilter(CuckooFilter):
    """
    Insert a fingerprint using transaction-log rollback.
    Input: username (string).
    Output: True if inserted, otherwise False.
    """
    def insert(self, username):
        """Insert a username; return False and restore all changes on failure."""
        fingerprint = self._fingerprint(username)
        i1, i2 = self._get_indices(username, fingerprint)

        if len(self.buckets[i1]) < self.bucket_size:
            self.buckets[i1].append(fingerprint)
            self.size += 1
            return True

        if len(self.buckets[i2]) < self.bucket_size:
            self.buckets[i2].append(fingerprint)
            self.size += 1
            return True

        # Record each modified slot rather than copying all B buckets.
        changes = []
        current_index = random.choice((i1, i2))
        current_fp = fingerprint

        for _ in range(self.max_kicks):
            slot = random.randrange(self.bucket_size)
            evicted_fp = self.buckets[current_index][slot]
            changes.append((current_index, slot, evicted_fp))
            self.buckets[current_index][slot] = current_fp

            alternate = self._alternate_index(current_index, evicted_fp)
            if len(self.buckets[alternate]) < self.bucket_size:
                self.buckets[alternate].append(evicted_fp)
                self.size += 1
                return True

            current_fp = evicted_fp
            current_index = alternate

        # Undo modifications in reverse order, including repeated slot updates.
        for index, slot, old_fingerprint in reversed(changes):
            self.buckets[index][slot] = old_fingerprint
        return False
