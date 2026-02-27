import pandas as pd

from config import USERS_FILE


def load_users():
    return pd.read_csv(USERS_FILE)


def check_login(username, password):
    users = load_users()
    if username in users["username"].values:
        user_pass = users.loc[users["username"] == username, "password"].values[0]
        return password == user_pass
    return False
