from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, time

from app.config.config import Base


class Room(Base):
    __tablename__ = 'room'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    capacity = Column(Integer)
    location = Column(String)
    description = Column(String)
    start_time = Column(Time)
    end_time = Column(Time)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    bookings = relationship("Booking", back_populates="room_rel")


class Booking(Base):
    __tablename__ = 'booking'

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey('room.id'), nullable=False)
    title = Column(String(300), nullable=False)
    organizer_name = Column(String(100), nullable=False)
    organizer_email = Column(String(100), nullable=False)
    participant_count = Column(Integer, nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    description = Column(Text)
    notes = Column(Text)
    is_cancelled = Column(Boolean, default=False)
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    room_rel = relationship("Room", back_populates="bookings")