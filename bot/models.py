from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum


Base = declarative_base()


class ServiceType(str, enum.Enum):
    HAIRCUT = "haircut"
    BEARD = "beard"
    COLORING = "coloring"
    STYLING = "styling"


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    bookings = relationship("Booking", back_populates="user")
    contest_entries = relationship("ContestEntry", back_populates="user")


class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    duration_minutes = Column(Integer, default=30)
    price = Column(Integer, default=0)
    service_type = Column(SQLEnum(ServiceType), default=ServiceType.HAIRCUT)
    is_active = Column(Integer, default=1)
    
    bookings = relationship("Booking", back_populates="service")


class TimeSlot(Base):
    __tablename__ = "time_slots"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    start_time = Column(String(5), nullable=False)
    end_time = Column(String(5), nullable=False)
    is_available = Column(Integer, default=1)
    max_bookings = Column(Integer, default=1)
    current_bookings = Column(Integer, default=0)
    
    service = relationship("Service")
    bookings = relationship("Booking", back_populates="time_slot")


class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    time_slot_id = Column(Integer, ForeignKey("time_slots.id"), nullable=False)
    client_name = Column(String(100), nullable=False)
    client_phone = Column(String(20), nullable=False)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    time_slot = relationship("TimeSlot", back_populates="bookings")


class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=True)
    is_superadmin = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ContestEntry(Base):
    __tablename__ = "contest_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    answer = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")