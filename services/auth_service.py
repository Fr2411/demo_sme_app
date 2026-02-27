import pandas as pd

from config import USERS_FILE
from services.client_service import ensure_db_structure


def load_users():
    ensure_db_structure()
    return pd.read_csv(USERS_FILE)


def authenticate_user(client_id, username, password):
    users = load_users()
    match = users[
        (users["client_id"].astype(str) == str(client_id))
        & (users["username"] == username)
        & (users["password"] == password)
    ]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def authenticate_admin(username, password):
    users = load_users()
    match = users[
        (users["username"] == username)
        & (users["password"] == password)
        & (users["role"].astype(str).str.lower() == "superadmin")
    ]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def create_client_user(client_id: str, username: str, password: str, role: str = "owner") -> tuple[bool, str]:
    users = load_users()
    client_id = str(client_id).strip()
    username = str(username).strip()
    password = str(password).strip()

    if not client_id or not username or not password:
        return False, "Client ID, username, and password are required"

    duplicate = users[
        (users["client_id"].astype(str) == client_id)
        & (users["username"].astype(str) == username)
    ]
    if not duplicate.empty:
        return False, "User already exists for this client"

    users = pd.concat(
        [
            users,
            pd.DataFrame(
                [
                    {
                        "client_id": client_id,
                        "username": username,
                        "password": password,
                        "role": role,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    users.to_csv(USERS_FILE, index=False)
    return True, "Client login user created"


def check_login(client_id, username, password):
    return authenticate_user(client_id, username, password) is not None
