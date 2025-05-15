from models_db import User
from database import db_manager
from auth import hash_password
from models_db import Property, InviteCode
from datetime import datetime

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

    props = [
    ("BOKOH", "Holiday Inn Brookpark - Cleveland Airport", "SPARK"),
    ("CLELW", "Holiday Inn Express & Suites - Westlake", "SPARK"),
    ("CLEMF", "Holiday Inn - Mayfield", "SPARK")
]

invites = [
    ("SPARK-E", "E", "SPARK"),
    ("SPARK-F", "F", "SPARK"),
    ("SPARK-M", "M", "SPARK"),
    ("SPARK-A", "A", "SPARK")
]

def seed_codes():
    for code, name, company in props:
        if not db_manager.db.query(Property).filter_by(code=code).first():
            db_manager.db.add(Property(code=code, name=name, company=company))

    for code, role, company in invites:
        if not db_manager.db.query(InviteCode).filter_by(code=code).first():
            db_manager.db.add(InviteCode(code=code, role=role, company=company))

    db_manager.db.commit()

if __name__ == "__main__":
    seed_users()
    seed_codes()
