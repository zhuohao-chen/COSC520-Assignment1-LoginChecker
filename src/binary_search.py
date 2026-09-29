def binary_search(usernames, target):
    """
    Check whether target exists in a sorted list using binary search.

    Input:
        usernames: A sorted list of username strings.
        target: The username to search for.

    Output:
        True if target exists, otherwise False.
    """

    low = 0
    high = len(usernames) - 1

    while low <= high:
        mid = (low + high) // 2
        middle_username = usernames[mid]

        if middle_username == target:
            return True

        if target < middle_username:
            high = mid - 1
        else:
            low = mid + 1
        
    return False


if __name__ == "__main__":
    usernames = [
        "alice",
        "bob",
        "cisco",
        "david",
        "emma"
    ]

    print(binary_search(usernames, "cisco"))
    print(binary_search(usernames, "zoe"))