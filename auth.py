import bcrypt
from database import db_manager
from models_db import User

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

# Authenticate user
def authenticate(username, password):
    user = db_manager.db.query(User).filter_by(username=username).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None