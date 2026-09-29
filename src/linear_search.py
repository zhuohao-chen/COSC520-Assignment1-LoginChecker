def linear_search(usernames, target):
    """
    Check whether target exists in usernames using linear search.

    Input:
        usernames: A list of username strings.
        target: The username to search for.

    Output:
        True if target exists, otherwise False.
    """

    for i in usernames:
        if i == target:
            return True
    return False

if __name__ == "__main__":
    usernames = [
        "alice",
        "bob",
        "cisco",
        "david",
        "emma"
    ]

    print(linear_search(usernames, "cisco"))
    print(linear_search(usernames, "zoe"))