from distutils.command.install import value

from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime, time
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.booking import Room, Booking


class RoomCreate(BaseModel):
    name: str
    capacity: int
    location: str
    description: str
    start_time: time
    end_time: time

    def capacity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('capacity must be positive')
        return v

    def endtime_after_start_time(cls, v):
        if 'start_time' in value and v <= value['start_time']:
            raise ValueError('start time must be after start time')
        return v


class RoomUpdate(BaseModel):  # edit room
    name: Optional[str] = None
    capacity: Optional[int] = None
    location: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_active: Optional[bool] = None


class RoomResponse(BaseModel):
    id: int
    name: str
    capacity: int
    location: Optional[str]
    description: Optional[str]
    start_time: time
    end_time: time
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RoomAvailability(BaseModel):  # check ว่าห้องว่างไหม
    room_id: int
    room_name: str
    start_datetime: datetime
    end_datetime: datetime
    is_available: bool
    reason: Optional[str] = None


# funtion
def create_room(db: Session, room: RoomCreate) -> Room:
    existing = db.query(Room).filter(Room.name == room.name).first()
    if existing:
        raise ValueError(f"ห้อง '{room.name}' มีอยู่แล้ว")

    db_room = Room(**room.dict())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


def get_rooms(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
) -> List[Room]:
    query = db.query(Room)  # ดึงรายการห้อง

    if active_only:
        query = query.filter(Room.is_active == True)

    return query.offset(skip).limit(limit).all()


def get_room(db: Session, room_id: int) -> Optional[Room]:  # ดึงตาม id
    return db.query(Room).filter(Room.id == room_id).first()


def update_room(db: Session, room_id: int, room_update: RoomUpdate) -> Optional[Room]:  # แก้ไขข้อมูลห้อง
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        return None
    if room_update.name and room_update.name != db_room.name:
        existing = db.query(Room).filter(Room.name == room_update.name).first()
        if existing:
            raise ValueError(f"ห้อง '{room_update.name}' มีอยู่แล้ว")

    update_data = room_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_room, field, value)

    db.commit()  # commit to db
    db.refresh(db_room)
    return db_room


def delete_room(db: Session, room_id: int) -> bool:  # ลบห้อง
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        return False

    future_bookings = db.query(Booking).filter(  # check การจองล่วงหน้า
        and_(
            Booking.room_id == room_id,
            Booking.start_datetime > datetime.utcnow(),
            Booking.is_cancelled == False
        )
    ).count()

    if future_bookings > 0:
        raise ValueError(f"ไม่สามารถลบห้องได้ มีการจอง {future_bookings} อยู่")

    db_room.is_active = False
    db.commit()
    return True


def check_room_availability(  # check ว่าห้องว่างไหม
        db: Session,
        room_id: int,
        start_datetime: datetime,
        end_datetime: datetime,
        exclude_booking_id: Optional[int] = None
) -> RoomAvailability:
    room = db.query(Room).filter(Room.id == room_id).first()

    result = RoomAvailability(
        room_id=room_id,
        room_name=room.name if room else "ไม่พบห้อง",
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        is_available=False,
        reason=None
    )

    if not room:
        result.reason = "ไม่พบห้องประชุม"
        return result

    if not room.is_active:
        result.reason = "ห้องไม่พร้อมใช้งาน"
        return result

    start_time = start_datetime.time()
    end_time = end_datetime.time()

    if start_time < room.start_time or end_time > room.end_time:
        result.reason = f"นอกเวลาทำการ ({room.start_time.strftime('%H:%M')} - {room.end_time.strftime('%H:%M')})"
        return result

    query = db.query(Booking).filter(
        and_(
            Booking.room_id == room_id,
            Booking.is_cancelled == False,
            # ตรวจสอบการจองทับ
            Booking.start_datetime < end_datetime,
            Booking.end_datetime > start_datetime
        )
    )

    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)

    conflicting_booking = query.first()

    if conflicting_booking:
        result.reason = f"มีการจองแล้ว: {conflicting_booking.title} ({conflicting_booking.start_datetime.strftime('%H:%M')}-{conflicting_booking.end_datetime.strftime('%H:%M')})"
        return result

    result.is_available = True
    return result


def find_available_rooms(  #หาห่องว่าง
        db: Session,
        start_datetime: datetime,
        end_datetime: datetime,
        min_capacity: Optional[int] = None
) -> List[Room]:
    query = db.query(Room).filter(Room.is_active == True)

    if min_capacity:
        query = query.filter(Room.capacity >= min_capacity)

    rooms = query.all()
    available_rooms = []

    for room in rooms:
        availability = check_room_availability(db, room.id, start_datetime, end_datetime)
        if availability.is_available:
            available_rooms.append(room)

    return available_rooms


def get_room_schedule(db: Session, room_id: int, date: datetime.date) -> List[Booking]: #ดูการจองห้อง
    start_of_day = datetime.combine(date, datetime.min.time())
    end_of_day = datetime.combine(date, datetime.max.time())

    return db.query(Booking).filter(
        and_(
            Booking.room_id == room_id,
            Booking.start_datetime >= start_of_day,
            Booking.start_datetime <= end_of_day,
            Booking.is_cancelled == False
        )
    ).order_by(Booking.start_datetime).all()