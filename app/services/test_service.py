fake_users_db = [
    {"id": 1, "name": "Jose Enrique", "email": "jose@example.com"},
    {"id": 2, "name": "María Pérez", "email": "maria@example.com"},
    {"id": 3, "name": "Juan Pérez", "email": "juan@example.com"},
]
def get_all_users():
    return fake_users_db

def get_user_by_id(user_id: int):
    user = next((u for u in fake_users_db if u["id"] == user_id), None)
    return user
