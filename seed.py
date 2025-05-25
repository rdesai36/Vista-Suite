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
