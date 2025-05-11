from models_db import User
from database import db_manager
from auth import hash_password

def seed_users():
    if not db_manager.db.query(User).filter_by(username="rdesai").first():
        user = User(
            username="rdesai",
            name="Rishikesh Desai",
            hashed_password=hash_password("admin123"),
            role="Developer"
        )
        db_manager.db.add(user)
        db_manager.db.commit()

if __name__ == "__main__":
    seed_users()