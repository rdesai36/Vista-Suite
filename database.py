import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv

from models_base import Base  # or wherever your Base is
from models_db import User, OccupancyData, RevenueData, Room, Guest, Booking

class DatabaseManager:
    def __init__(self):
        load_dotenv()

        db_url = os.getenv("DATABASE_URL", "sqlite:///vista.db")
        self.engine = create_engine(db_url, echo=False, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.db = scoped_session(self.session_factory)

        def update_room_status(self, room_id, new_status):
            room = self.db.query(Room).get(room_id)
            if room:
                room.room_status = new_status
                self.db.commit()
                return True
            return False

        def check_in_booking(self, booking_id):
            booking = self.db.query(Booking).get(booking_id)
            if booking and booking.booking_status == "Reserved":
                booking.booking_status = "Checked-In"
                self.db.commit()
                return True
            return False

        def check_out_booking(self, booking_id):
            booking = self.db.query(Booking).get(booking_id)
            if booking and booking.booking_status == "Checked-In":
                booking.booking_status = "Checked-Out"
                self.db.commit()
                return True
            return False

    def get_session(self):
        return self.db()

def get_db_manager():
    return db_manager

db_manager = DatabaseManager()
