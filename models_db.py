from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from models_base import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String)
    role = Column(String)  # e.g., Admin, Manager, FrontDesk
    last_active = Column(DateTime, default=datetime.utcnow)
    avatar = Column(String)
    bio = Column(Text)
    email = Column(String)
    phone = Column(String)

class Property(Base):
    __tablename__ = 'properties'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)  # e.g. BOKOH, CLELW
    name = Column(String)
    company = Column(String)  # e.g. Spark Hotels

class InviteCode(Base):
    __tablename__ = 'invite_codes'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)  # e.g. SPARK-E
    role = Column(String)  # E, F, M, A
    company = Column(String)  # for validation (e.g., SPARK)

class MessageThread(Base):
    __tablename__ = "message_threads"
    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, nullable=False)
    subject = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class OccupancyData(Base):
    __tablename__ = "occupancy_data"
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    rooms_occupied = Column(Integer)
    total_rooms = Column(Integer)

class RevenueData(Base):
    __tablename__ = "revenue_data"
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    room_revenue = Column(Float)
    fnb_revenue = Column(Float)
    other_revenue = Column(Float)

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True)
    room_number = Column(String)
    room_type = Column(String)
    room_status = Column(String)  # e.g. 'Vacant', 'Occupied', etc.

class Guest(Base):
    __tablename__ = "guests"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    loyalty_status = Column(String)

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey('guests.id'))
    room_id = Column(Integer, ForeignKey('rooms.id'))
    check_in_date = Column(Date)
    check_out_date = Column(Date)
    booking_status = Column(String)  # e.g. 'Reserved', 'Checked-In', etc.
    nights = Column(Integer)
    total_price = Column(Float)

    guest = relationship("Guest")
    room = relationship("Room")

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)