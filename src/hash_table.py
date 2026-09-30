

class HashTable:
    def __init__(self, capacity=10):
        """
        Initialize the hash table.
        Input: capacity (initial number of buckets).
        Output: None.
        """
        self.capacity = capacity
        self.buckets = [[] for _ in range(capacity)]
        self.size = 0
        self.max_load_factor = 0.75



    def _hash(self, username):
        """
        Calculate a bucket index using polynomial hashing.
        Input: username (string).
        Output: Bucket index (integer).
        """

        hash_value = 0

        for char in username:
            # 每轮循环中，hash_value 乘以 31这个质数，然后加上当前字符的 ASCII 值，
            # 这样可以避免abc和cba出现在一个桶中会出现很多collision，乘以个质数可以显著减少这样的情况，
            # 31是一个常用的质数，能够在一定程度上减少哈希冲突，这样子字符位置也会影响在哈希表的位置
            # Multiply by 31 to make character order affect the hash value.
            hash_value = hash_value*31 + ord(char)

        return hash_value % self.capacity



    def insert(self, username):
        """
        Insert a username if it does not already exist.
        Input: username (string).
        Output: None.
        """
        index = self._hash(username)
        bucket = self.buckets[index]
        for name in bucket:
            if username == name:
                return
        bucket.append(username)
        self.size += 1

        if self.size / self.capacity > self.max_load_factor:
            self._resize()



    def contains(self, username):
        """
        Check whether a username exists in the hash table.
        Input: username (string).
        Output: True if found, otherwise False.
        """
        index = self._hash(username)
        bucket = self.buckets[index]

        for user in bucket:
            if user == username:
                return True
        return False



    def _resize(self):
        """
        Double the capacity and rehash existing usernames.
        Input: None.
        Output: None.
        """
        old_buckets = self.buckets
        self.capacity *= 2
        self.buckets = [[] for _ in range(self.capacity)]
        self.size = 0
        for bucket in old_buckets:
            for username in bucket:
                self.insert(username)




if __name__ == "__main__":
    table = HashTable(capacity=4)

    usernames = [
        "alice",
        "bob",
        "cisco",
        "david",
        "emma",
        "frank"
    ]

    for username in usernames:
        table.insert(username)
        print(
            f"Inserted: {username}, "
            f"Size: {table.size}, "
            f"Capacity: {table.capacity}"
        )

    for username in usernames:
        assert table.contains(username)
    assert not table.contains("zoe")
    old_size = table.size
    table.insert("alice")
    assert table.size == old_size

    print("All tests passed!")
