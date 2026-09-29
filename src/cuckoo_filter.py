import hashlib
import random

class CuckooFilter:
    def __init__(
        self,
        capacity=8,
        bucket_size=2,
        fingerprint_bits=12,
        max_kicks=100
    ):
        """
        Initialize a Cuckoo Filter.

        capacity: Number of buckets.
        bucket_size: Slots in each bucket.
        fingerprint_bits: Fingerprint length.
        max_kicks: Maximum eviction attempts.
        """

        # Capacity must be a positive power of two.
        if capacity < 2 or capacity & (capacity - 1):
            raise ValueError(
                "Capacity must be a power of two >= 2"
            )

        if bucket_size < 1 or fingerprint_bits < 1:
            raise ValueError("Invalid filter parameters")

        if max_kicks < 1:
            raise ValueError("max_kicks must be positive")

        self.capacity = capacity
        self.bucket_size = bucket_size
        self.fingerprint_bits = fingerprint_bits
        self.max_kicks = max_kicks

        # Create empty buckets.
        self.buckets = [
            [] for _ in range(capacity)
        ]

        self.size = 0

    def _fingerprint(self, username):
        data = username.encode("utf-8")

        hash_value = hashlib.blake2b(
            data,
            digest_size=8
        ).digest()

        number = int.from_bytes(hash_value, "big")

        return number % (
            2 ** self.fingerprint_bits - 1
        ) + 1
    
    def _get_indices(self, username, fingerprint):
        """
        Calculate two candidate buckets.
        """
        # First bucket: hash the original username.
        data = username.encode("utf-8")

        hash_value = hashlib.blake2b(
            data,
            digest_size=8,
            person=b"cf-index"
        ).digest()

        i1 = int.from_bytes(hash_value, "big") % self.capacity

        # Calculate an offset using the fingerprint.
        i2 = self._alternate_index(i1, fingerprint)
        return i1, i2

    
    def contains(self, username):
        # Generate the fingerprint.
        fingerprint = self._fingerprint(username)

        # Get two candidate buckets.
        i1, i2 = self._get_indices(
            username, fingerprint
        )

        if fingerprint in self.buckets[i1] or fingerprint in self.buckets[i2]:
            return True

        return False

    def _alternate_index(self, index, fingerprint):
        """
        Calculate the alternative bucket index
        from the current index and fingerprint.
        """

        fp_data = str(fingerprint).encode("utf-8")

        fp_hash = hashlib.blake2b(
            fp_data,
            digest_size=8,
            person=b"cf-alt"
        ).digest()

        offset = (
            int.from_bytes(fp_hash, "big")
            % self.capacity
        ) | 1

        return index ^ offset

    def insert(self, username):
        fingerprint = self._fingerprint(username)
        i1, i2 = self._get_indices(username, fingerprint)

        # Step 1: If the first bucket has space,
        # insert the fingerprint.
        if len(self.buckets[i1]) < self.bucket_size:
            self.buckets[i1].append(fingerprint)
            self.size += 1
            return True

        # Step 2: Otherwise, try the second bucket.
        if len(self.buckets[i2]) < self.bucket_size:
            self.buckets[i2].append(fingerprint)
            self.size += 1
            return True

        # Save the original state for rollback.
        old_buckets = [
            bucket.copy()
            for bucket in self.buckets
        ]

        # Randomly choose the first bucket.
        current_index = random.choice([i1, i2])

        # The fingerprint waiting to be inserted.
        current_fp = fingerprint

        # TODO:
        # Repeat up to self.max_kicks times.
        # 1. Select a random slot.
        # 2. Swap current_fp with the stored fingerprint.
        # 3. Calculate the evicted fingerprint's
        #    alternative bucket.
        # 4. Insert it if there is space.
        for _ in range(self.max_kicks):
            # Step 1: Select a random slot.
            slot_index = random.randint(
                0, self.bucket_size - 1
            )

            # Step 2: Swap current_fp with the stored fingerprint.
            evicted_fp = self.buckets[current_index][slot_index]
            self.buckets[current_index][slot_index] = current_fp

            # Step 3: Calculate the evicted fingerprint's alternative bucket.
            alt_index = self._alternate_index(current_index, evicted_fp)

            # Step 4: Insert it if there is space.
            if len(self.buckets[alt_index]) < self.bucket_size:
                self.buckets[alt_index].append(evicted_fp)
                self.size += 1
                return True

            # Prepare for the next iteration.
            current_fp = evicted_fp
            current_index = alt_index

        # If all attempts fail, restore old_buckets.
        self.buckets = old_buckets

        return False


if __name__ == "__main__":
    
    print("\nTest 1: Basic insertion")

    cf = CuckooFilter(
        capacity=16,
        bucket_size=2
    )

    usernames = [
        "alice", "bob", "cisco",
        "david", "emma"
    ]

    for username in usernames:
        assert cf.insert(username)

    for username in usernames:
        assert cf.contains(username)

    assert cf.size == 5

    print("Basic insertion test passed!")


    print("\nTest 2: Alternative bucket")

    fp = cf._fingerprint("alice")
    i1, i2 = cf._get_indices("alice", fp)

    assert cf._alternate_index(i1, fp) == i2
    assert cf._alternate_index(i2, fp) == i1

    print("Alternative bucket test passed!")

    
    print("\nTest 3: Eviction and rollback")

    random.seed(42)

    cf = CuckooFilter(
        capacity=8,
        bucket_size=2,
        max_kicks=100
    )

    successful = []
    failed = []

    for i in range(30):
        username = f"user{i}"

        if cf.insert(username):
            successful.append(username)
        else:
            failed.append(username)

        # Every previously successful insertion
        # must remain searchable.
        for name in successful:
            assert cf.contains(name), (
                f"Lost username: {name}"
            )

    assert cf.size == len(successful)
    assert cf.size <= 16
    assert len(failed) > 0

    for bucket in cf.buckets:
        assert len(bucket) <= cf.bucket_size

    print("Successful insertions:", len(successful))
    print("Failed insertions:", len(failed))
    print("Eviction and rollback test passed!")


    from pathlib import Path

    print("\nTest 4: Large dataset")

    data_path = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "usernames_1000.txt"
    )

    with open(data_path, "r", encoding="utf-8") as f:
        usernames = [
            line.strip()
            for line in f
            if line.strip()
        ]

    cf = CuckooFilter(
        capacity=512,
        bucket_size=4,
        fingerprint_bits=12
    )

    successful = []

    # Insert 1,000 usernames.
    for username in usernames:
        if cf.insert(username):
            successful.append(username)

    # Count false negatives.
    false_negatives = 0

    for username in successful:
        if not cf.contains(username):
            false_negatives += 1

    # Query 1,000 usernames that were not inserted.
    rng = random.Random(2026)

    negative_queries = [
        f"missing_{rng.getrandbits(64):016x}_{i}"
        for i in range(10000)
    ]

    false_positives = 0

    for username in negative_queries:
        if cf.contains(username):
            false_positives += 1

    print("Total usernames:", len(usernames))
    print("Successful insertions:", len(successful))
    print("False negatives:", false_negatives)
    print("Negative queries:", len(negative_queries))
    print("False positives:", false_positives)
    print(
        "False positive rate:",
        f"{false_positives / len(negative_queries):.4%}"
    )

