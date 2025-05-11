#!/usr/bin/env python
"""
Database initialization script for Hotel Management Dashboard
This script creates all database tables and populates them with sample data.
"""

import os
import random
from datetime import datetime, timedelta
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, User, Log, LogRead, Message, Room, Guest, Booking, OccupancyData, RevenueData

# Get database URL from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully")

def generate_sample_data():
    """Generate and insert sample data"""
    # Check if data already exists
    if db.query(User).count() > 0:
        print("Sample data already exists")
        return
    
    # Create sample users
    users = [
        {
            "user_id": "user1",
            "name": "John Smith",
            "role": "Manager",
            "email": "john@hotel.com",
            "phone": "555-1234",
            "bio": "Hotel Manager with 10 years of experience in luxury hospitality.",
            "avatar": "https://ui-avatars.com/api/?name=John+Smith&background=random"
        },
        {
            "user_id": "user2",
            "name": "Jane Doe",
            "role": "Front Desk",
            "email": "jane@hotel.com",
            "phone": "555-2345",
            "bio": "Front desk specialist with exceptional customer service skills.",
            "avatar": "https://ui-avatars.com/api/?name=Jane+Doe&background=random"
        },
        {
            "user_id": "user3",
            "name": "Mark Williams",
            "role": "Housekeeping",
            "email": "mark@hotel.com",
            "phone": "555-3456",
            "bio": "Head of housekeeping with attention to detail.",
            "avatar": "https://ui-avatars.com/api/?name=Mark+Williams&background=random"
        },
        {
            "user_id": "user4",
            "name": "Sarah Johnson",
            "role": "Maintenance",
            "email": "sarah@hotel.com",
            "phone": "555-4567",
            "bio": "Maintenance supervisor with technical expertise.",
            "avatar": "https://ui-avatars.com/api/?name=Sarah+Johnson&background=random"
        },
        {
            "user_id": "user5",
            "name": "Alex Chen",
            "role": "Sales",
            "email": "alex@hotel.com",
            "phone": "555-5678",
            "bio": "Sales executive focusing on corporate clients.",
            "avatar": "https://ui-avatars.com/api/?name=Alex+Chen&background=random"
        }
    ]
    
    # Add users to database
    for user_data in users:
        user = User(**user_data)
        db.add(user)
    
    db.commit()
    print("Users created")
    
    # Get users from database for relationships
    users_dict = {user.user_id: user for user in db.query(User).all()}
    
    # Create sample logs
    logs = [
        {
            "log_id": "log1",
            "title": "Morning Shift Handover",
            "message": "All rooms on 3rd floor cleaned. Room 302 needs maintenance check for AC.",
            "author_id": users_dict["user3"].id,
            "timestamp": datetime.now() - timedelta(hours=2)
        },
        {
            "log_id": "log2",
            "title": "VIP Guest Arrival",
            "message": "Mr. Peterson (Diamond member) arriving at 3PM. Requires airport pickup and champagne in room.",
            "author_id": users_dict["user2"].id,
            "timestamp": datetime.now() - timedelta(hours=4)
        },
        {
            "log_id": "log3",
            "title": "Maintenance Alert",
            "message": "Pool heater not functioning properly. Technician scheduled for tomorrow morning.",
            "author_id": users_dict["user4"].id,
            "timestamp": datetime.now() - timedelta(hours=6)
        },
        {
            "log_id": "log4",
            "title": "Corporate Booking",
            "message": "Tech Solutions booked 15 rooms for next week's conference. Special rate applied.",
            "author_id": users_dict["user5"].id,
            "timestamp": datetime.now() - timedelta(days=1)
        },
        {
            "log_id": "log5",
            "title": "Staff Meeting Reminder",
            "message": "Monthly staff meeting tomorrow at 9AM in the conference room. Attendance mandatory.",
            "author_id": users_dict["user1"].id,
            "timestamp": datetime.now() - timedelta(days=1, hours=5)
        }
    ]
    
    # Add logs to database
    for log_data in logs:
        log = Log(**log_data)
        db.add(log)
    
    db.commit()
    print("Logs created")
    
    # Add some log read records
    logs = db.query(Log).all()
    for log in logs:
        # Randomly mark some logs as read by different users
        for user in random.sample(list(users_dict.values()), random.randint(1, 3)):
            log_read = LogRead(log_id=log.id, user_id=user.id)
            db.add(log_read)
    
    db.commit()
    print("Log reads created")
    
    # Create sample messages
    messages = [
        {
            "message_id": "msg1",
            "sender_id": users_dict["user1"].id,
            "recipient_id": users_dict["user2"].id,
            "content": "Please update the VIP list for weekend arrivals.",
            "timestamp": datetime.now() - timedelta(hours=1),
            "is_read": False
        },
        {
            "message_id": "msg2",
            "sender_id": users_dict["user2"].id,
            "recipient_id": users_dict["user1"].id,
            "content": "VIP list updated. We have 3 platinum members arriving on Saturday.",
            "timestamp": datetime.now() - timedelta(minutes=45),
            "is_read": True
        },
        {
            "message_id": "msg3",
            "sender_id": users_dict["user3"].id,
            "recipient_id": users_dict["user4"].id,
            "content": "Room 302 needs AC maintenance. Guest complained about noise.",
            "timestamp": datetime.now() - timedelta(hours=3),
            "is_read": False
        }
    ]
    
    # Add messages to database
    for message_data in messages:
        message = Message(**message_data)
        db.add(message)
    
    db.commit()
    print("Messages created")
    
    # Create sample rooms
    room_types = ["Standard", "Deluxe", "Suite", "Executive"]
    room_statuses = ["Vacant", "Occupied", "Dirty", "Maintenance", "Out of Order"]
    
    rooms = []
    for floor in range(1, 5):  # 4 floors
        for room in range(1, 11):  # 10 rooms per floor
            room_number = f"{floor}0{room}" if room < 10 else f"{floor}{room}"
            room_type = random.choice(room_types)
            status = random.choice(room_statuses)
            
            # Some rooms were cleaned recently
            last_cleaned = None
            if status in ["Vacant", "Occupied"]:
                last_cleaned = datetime.now() - timedelta(days=random.randint(0, 7))
            
            # Some rooms have maintenance due
            maintenance_due = random.random() < 0.2  # 20% chance
            
            rooms.append({
                "room_number": room_number,
                "room_type": room_type,
                "status": status,
                "last_cleaned": last_cleaned,
                "maintenance_due": maintenance_due
            })
    
    # Add rooms to database
    for room_data in rooms:
        room = Room(**room_data)
        db.add(room)
    
    db.commit()
    print("Rooms created")
    
    # Create sample guests
    first_names = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "William", "Elizabeth"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor"]
    loyalty_levels = ["Standard", "Silver", "Gold", "Platinum", "Diamond"]
    
    guests = []
    for i in range(20):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        full_name = f"{first_name} {last_name}"
        
        guests.append({
            "guest_id": f"guest{i+1}",
            "name": full_name,
            "email": f"{first_name.lower()}.{last_name.lower()}@example.com",
            "phone": f"555-{random.randint(1000, 9999)}",
            "address": f"{random.randint(100, 999)} Main St, Anytown, USA",
            "loyalty_level": random.choice(loyalty_levels)
        })
    
    # Add guests to database
    for guest_data in guests:
        guest = Guest(**guest_data)
        db.add(guest)
    
    db.commit()
    print("Guests created")
    
    # Create sample bookings
    booking_statuses = ["Confirmed", "Cancelled", "No-Show", "Checked-In", "Checked-Out"]
    payment_statuses = ["Pending", "Paid", "Refunded", "Declined"]
    
    # Get rooms and guests
    rooms = db.query(Room).all()
    guests = db.query(Guest).all()
    
    bookings = []
    for i in range(30):
        guest = random.choice(guests)
        room = random.choice(rooms)
        
        # Random dates in the past month or future month
        days_offset = random.randint(-30, 30)
        check_in_date = datetime.now() + timedelta(days=days_offset)
        length_of_stay = random.randint(1, 7)
        check_out_date = check_in_date + timedelta(days=length_of_stay)
        
        # Determine status based on dates
        booking_status = "Confirmed"
        if check_in_date < datetime.now() and check_out_date < datetime.now():
            booking_status = "Checked-Out"
        elif check_in_date < datetime.now() and check_out_date > datetime.now():
            booking_status = "Checked-In"
        elif random.random() < 0.1:  # 10% chance
            booking_status = random.choice(["Cancelled", "No-Show"])
        
        # Random amount for the stay
        base_price = {"Standard": 100, "Deluxe": 150, "Suite": 250, "Executive": 300}
        price_per_night = base_price.get(room.room_type, 100)
        total_amount = price_per_night * length_of_stay
        
        payment_status = "Paid" if booking_status in ["Checked-Out"] else random.choice(payment_statuses)
        
        bookings.append({
            "booking_id": f"book{i+1}",
            "guest_id": guest.id,
            "room_id": room.id,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "booking_status": booking_status,
            "payment_status": payment_status,
            "total_amount": total_amount,
            "created_at": datetime.now() - timedelta(days=random.randint(1, 60))
        })
    
    # Add bookings to database
    for booking_data in bookings:
        booking = Booking(**booking_data)
        db.add(booking)
    
    db.commit()
    print("Bookings created")
    
    # Create sample occupancy data for the past year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    current_date = start_date
    total_rooms = 40  # Total rooms in the hotel
    
    occupancy_data = []
    while current_date <= end_date:
        # Occupancy varies by day of week and season
        # Higher on weekends, summer, and holidays
        day_of_week = current_date.weekday()  # 0-6 (Monday to Sunday)
        month = current_date.month  # 1-12
        
        # Base occupancy rate (higher on weekends)
        base_rate = 0.65 if day_of_week < 5 else 0.80
        
        # Seasonal adjustment (higher in summer months)
        if 5 <= month <= 9:  # May to September
            seasonal_factor = 0.15
        elif month in [12, 1]:  # December, January (holidays)
            seasonal_factor = 0.10
        else:
            seasonal_factor = 0.0
        
        # Random factor for natural variation
        random_factor = random.uniform(-0.1, 0.1)
        
        # Calculate occupancy rate with constraints
        occupancy_rate = min(max(base_rate + seasonal_factor + random_factor, 0.3), 0.95)
        rooms_occupied = int(total_rooms * occupancy_rate)
        
        occupancy_data.append({
            "date": current_date,
            "rooms_occupied": rooms_occupied,
            "total_rooms": total_rooms,
            "occupancy_rate": occupancy_rate
        })
        
        current_date += timedelta(days=1)
    
    # Add occupancy data to database
    for data in occupancy_data:
        occ_data = OccupancyData(**data)
        db.add(occ_data)
    
    db.commit()
    print("Occupancy data created")
    
    # Create sample revenue data for the past year
    current_date = start_date
    revenue_data = []
    
    while current_date <= end_date:
        # Get occupancy for this date
        occupancy = next((o for o in occupancy_data if o["date"].date() == current_date.date()), None)
        
        if occupancy:
            rooms_occupied = occupancy["rooms_occupied"]
            
            # Calculate room revenue (varies by day of week and season)
            day_of_week = current_date.weekday()
            month = current_date.month
            
            # Base room rate (higher on weekends)
            base_room_rate = 120 if day_of_week < 5 else 150
            
            # Seasonal adjustment (higher in summer and holidays)
            if 5 <= month <= 9:  # May to September
                rate_factor = 1.2
            elif month in [12, 1]:  # December, January
                rate_factor = 1.3
            else:
                rate_factor = 1.0
            
            # Calculate room revenue
            room_revenue = rooms_occupied * base_room_rate * rate_factor
            
            # F&B revenue (typically 30-40% of room revenue)
            fb_factor = random.uniform(0.3, 0.4)
            fb_revenue = room_revenue * fb_factor
            
            # Other revenue (spa, activities, etc.) - typically 10-20% of room revenue
            other_factor = random.uniform(0.1, 0.2)
            other_revenue = room_revenue * other_factor
            
            # Calculate total revenue
            total_revenue = room_revenue + fb_revenue + other_revenue
            
            revenue_data.append({
                "date": current_date,
                "room_revenue": round(room_revenue, 2),
                "fb_revenue": round(fb_revenue, 2),
                "other_revenue": round(other_revenue, 2),
                "total_revenue": round(total_revenue, 2)
            })
        
        current_date += timedelta(days=1)
    
    # Add revenue data to database
    for data in revenue_data:
        rev_data = RevenueData(**data)
        db.add(rev_data)
    
    db.commit()
    print("Revenue data created")
    print("Sample data generation complete")

if __name__ == "__main__":
    # Create tables
    create_tables()
    
    # Generate sample data
    generate_sample_data()
    
    # Close the database session
    db.close()
    print("Database initialization complete")