
class BloomFilter:

    """
    Initialize the Bloom filter.
    Input: m (array size), k (number of hash positions).
    Output: None.
    """
    def __init__(self, m=10007, k=7):
        """
        Initialize a Bloom Filter.
        m: Number of bits.
        k: Number of hash functions.
        """
        if m < 2 or k < 1 or k > m:
            raise ValueError("Invalid Bloom Filter parameters")

        self.m = m
        self.k = k
        self.bits = [0] * m


    """
    Generate hash positions using double hashing.
    Input: username (string).
    Output: List of k bit positions.
    """

    def _hashes(self, username):
        """
        Generate k bit positions for a username.
        """
        h1 = 0
        h2 = 0
        for char in username:
            code = ord(char)

            h1 = (h1 * 31 + code) % self.m
            h2 = (h2 * 37 + code) % (self.m - 1)

        step = h2 + 1

        positions = []

        for i in range(self.k):
            position = (h1 + i * step) % self.m
            positions.append(position)

        return positions

    """
    Insert a username by setting its hash positions.
    Input: username (string).
    Output: None.
    """
    def add(self, username):
        positions = self._hashes(username)

        for position in positions:
            self.bits[position] = 1

    """
    Perform an approximate membership check.
    Input: username (string).
    Output: False if absent, otherwise possibly True.
    """
    def contains(self, username):
        positions = self._hashes(username)

        for position in positions:
            if self.bits[position] == 0:
                return False
        return True

if __name__ == "__main__":
    from pathlib import Path

    # Load the 1,000 usernames generated previously
    data_path = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "usernames_1000.txt"
    )

    with open(data_path, "r", encoding="utf-8") as f:
        usernames = [line.strip() for line in f if line.strip()]

    bloom = BloomFilter(m=10007, k=7)

    # Test A: Insert all usernames.
    for username in usernames:
        bloom.add(username)

    false_negatives = 0

    for username in usernames:
        if not bloom.contains(username):
            false_negatives += 1

    print("Inserted usernames:", len(usernames))
    print("False negatives:", false_negatives)

    assert false_negatives == 0

    # Test B: Query usernames that were never inserted
    negative_usernames = [
        f"other{i:08d}" for i in range(1000)
    ]

    false_positives = 0

    for username in negative_usernames:
        if bloom.contains(username):
            false_positives += 1

    fpr = false_positives / len(negative_usernames)

    print("Negative queries:", len(negative_usernames))
    print("False positives:", false_positives)
    print(f"False positive rate: {fpr:.2%}")

