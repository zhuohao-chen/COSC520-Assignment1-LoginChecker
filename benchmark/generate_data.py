from pathlib import Path


def generate_usernames(n):
    """
    Generate n unique usernames.
    Input:
        n: Number of usernames to generate.
    Output:
        A list of unique username strings.
    """
    usernames = []

    for i in range(n):
        username = f"user{i:08d}"
        usernames.append(username)

    return usernames


def save_usernames(usernames, filename):
    """
    Save usernames to a text file, one username per line.
    """
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    file_path = data_dir / filename

    with open(file_path, "w", encoding="utf-8") as file:
        for username in usernames:
            file.write(username + "\n")

    return file_path


if __name__ == "__main__":
    usernames = generate_usernames(1000)
    path = save_usernames(usernames, "usernames_1000.txt")

    print(f"Generated {len(usernames)} usernames.")
    print(f"Saved to: {path}")
    print("First 5 usernames:", usernames[:5])