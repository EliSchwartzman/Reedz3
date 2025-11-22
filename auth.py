import bcrypt
import supabase_db
from models import User

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def authenticate(username: str, password: str):
    user = supabase_db.get_user_by_username(username)
    if user and check_password(password, user.password):
        return user
    return None

def is_admin(user: User) -> bool:
    return user.role == 'Admin'

def can_place_prediction(user: User) -> bool:
    return user.role in ['Admin', 'Member']

def can_manage_bets(user: User) -> bool:
    return is_admin(user)

def reset_password(email: str, new_password: str) -> bool:
    user = supabase_db.get_user_by_email(email)
    if user:
        hashed = hash_password(new_password)
        return supabase_db.update_user_password(user.user_id, hashed)
    return False
