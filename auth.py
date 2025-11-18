import bcrypt
from models import User, Role
import supabase_db


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def login(username: str, password: str) -> User:
    user = supabase_db.get_user_by_username(username)
    if user and verify_password(password, user.password_hash):
        return user
    return None


def is_admin(user: User) -> bool:
    return user.role == Role.ADMIN


def require_admin(user: User):
    if not is_admin(user):
        raise PermissionError("Admin privileges required.")


def require_member_or_admin(user: User):
    if not (user and (user.role == Role.ADMIN or user.role == Role.MEMBER)):
        raise PermissionError("Member or Admin privileges required.")
