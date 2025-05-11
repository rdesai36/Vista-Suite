from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from models_base import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String)
    role = Column(String)  # e.g., Admin, Manager, FrontDesk

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
