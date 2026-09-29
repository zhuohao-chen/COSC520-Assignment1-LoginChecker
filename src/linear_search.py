def linear_search(usernames, target):
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