from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Session
from models.booking import Booking, Room
from modules.room.room import check_room_availability


class BookingCreate(BaseModel):
    room_id: int
    title: str
    organizer_name: str
    organizer_email: Optional[str] = None
    participant_count: int = 1
    start_datetime: datetime
    end_datetime: datetime
    description: Optional[str] = None
    notes: Optional[str] = None

    @validator("end_datetime")
    def end_after_start(cls, v, values):
        if 'start_datetime' in values and v <= values['start_datetime']:
            raise ValueError('เวลาสิ้นสุดต้องหลังจากเวลาเริ่ม')
        return v

    @validator("participant_count")
    def positive_participant_count(cls, v):
        if v <= 0:
            raise ValueError('ผู้เข้าร่วมต้องมากกว่า 0')
        return v

    @validator("organizer_email")
    def email_valid(cls, v):
        if v and '@' not in v:
            raise ValueError('รูปแบบอีเมลไม่ถูกต้อง')
        return v


class BookingUpdate(BaseModel):  # แก้ไขการจอง
    title: Optional[str] = None
    organizer_name: Optional[str] = None
    organizer_email: Optional[str] = None
    participant_count: Optional[int] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    description: Optional[str] = None
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    id: int
    room_id: int
    room_name: str
    title: str
    organizer_name: str
    organizer_email: Optional[str]
    participant_count: int
    start_datetime: datetime
    end_datetime: datetime
    description: Optional[str]
    notes: Optional[str]
    is_cancelled: bool
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_booking(cls, booking):
        return cls(
            id=booking.id,
            room_id=booking.room_id,
            room_name=booking.room_rel.name if booking.room_rel else "",
            title=booking.title,
            organizer_name=booking.organizer_name,
            organizer_email=booking.organizer_email,
            participant_count=booking.participant_count,
            start_datetime=booking.start_datetime,
            end_datetime=booking.end_datetime,
            description=booking.description,
            notes=booking.notes,
            is_cancelled=booking.is_cancelled,
            cancelled_at=booking.cancelled_at,
            cancellation_reason=booking.cancellation_reason,  # updated
            created_at=booking.created_at,
        )


def create_booking(db: Session, booking: BookingCreate) -> Booking:  # สร้างการจอง
    # ตรวจสอบห้อง
    room = db.query(Room).filter(Room.id == booking.room_id).first()
    if not room:
        raise ValueError("ไม่พบห้องประชุม")

    if not room.is_active:
        raise ValueError("ห้องประชุมไม่พร้อมใช้งาน")

    # ตรวจสอบ capacity
    if booking.participant_count > room.capacity:
        raise ValueError(f"จำนวนผู้เข้าร่วม ({booking.participant_count}) เกินความจุห้อง ({room.capacity})")

    # ตรวจว่าห้องว่าไหม
    availability = check_room_availability(
        db, booking.room_id, booking.start_datetime, booking.end_datetime
    )

    if not availability.is_available:
        raise ValueError(f"ห้องไม่ว่าง: {availability.reason}")

    # สร้างการจอง
    db_booking = Booking(**booking.dict())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking


def get_bookings(  # ดึงรายการการจอง
        db: Session,
        skip: int = 0,
        limit: int = 100,
        room_id: Optional[int] = None,
        organizer_email: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_cancelled: bool = False
) -> List[Booking]:
    query = db.query(Booking)

    if not include_cancelled:
        query = query.filter(Booking.is_cancelled == False)

    if room_id:
        query = query.filter(Booking.room_id == room_id)

    if organizer_email:
        query = query.filter(Booking.organizer_email == organizer_email)

    if start_date:
        query = query.filter(Booking.start_datetime >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query = query.filter(Booking.start_datetime <= datetime.combine(end_date, datetime.max.time()))

    return query.order_by(Booking.start_datetime.desc()).offset(skip).limit(limit).all()


def get_booking(db: Session, booking_id: int) -> Optional[Booking]:  # get by id
    return db.query(Booking).filter(Booking.id == booking_id).first()


def update_booking(  # แก้ไขการจอง
        db: Session,
        booking_id: int,
        booking_update: BookingUpdate
) -> Optional[Booking]:
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        return None

    if booking.is_cancelled:
        raise ValueError("ไม่สามารถแก้ไขการจองที่ยกเลิกแล้ว")

    # ถ้ามีการเปลี่ยนเวลา ต้องเช็คว่าว่างก่อน
    update_data = booking_update.dict(exclude_unset=True)

    if 'start_datetime' in update_data or 'end_datetime' in update_data:
        new_start = update_data.get('start_datetime', booking.start_datetime)
        new_end = update_data.get('end_datetime', booking.end_datetime)

        availability = check_room_availability(
            db, booking.room_id, new_start, new_end, booking.id
        )

        if not availability.is_available:
            raise ValueError(f"ไม่สามารถเปลี่ยนเวลาได้: {availability.reason}")

    # ตรวจสอบ capacity
    if 'participant_count' in update_data:
        room = db.query(Room).filter(Room.id == booking.room_id).first()
        if update_data['participant_count'] > room.capacity:
            raise ValueError(f"จำนวนผู้เข้าร่วม ({update_data['participant_count']}) เกินความจุห้อง ({room.capacity})")

    for field, value in update_data.items():
        setattr(booking, field, value)

    db.commit()
    db.refresh(booking)
    return booking


def cancel_booking(  # ยกเลิกการจอง
        db: Session,
        booking_id: int,
        reason: Optional[str] = None
) -> Optional[Booking]:
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        return None

    if booking.is_cancelled:
        raise ValueError("ยกเลิกแล้ว")

    booking.is_cancelled = True
    booking.cancelled_at = datetime.utcnow()
    booking.cancellation_reason = reason  # updated

    db.commit()
    db.refresh(booking)
    return booking


def get_upcoming_bookings(db: Session, days: int = 7) -> List[Booking]:  # การจองล่วงหน้า/ที่กำลังจะถึง
    from datetime import timedelta

    start_time = datetime.utcnow()
    end_time = start_time + timedelta(days=days)

    return db.query(Booking).filter(
        Booking.start_datetime >= start_time,
        Booking.start_datetime <= end_time,
        Booking.is_cancelled == False
    ).order_by(Booking.start_datetime).all()


def get_today_bookings(db: Session) -> List[Booking]:  # การจองวันนี้
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())

    return db.query(Booking).filter(
        Booking.start_datetime >= start_of_day,
        Booking.start_datetime <= end_of_day,
        Booking.is_cancelled == False
    ).order_by(Booking.start_datetime).all()


def get_my_bookings(db: Session, organizer_email: str) -> List[Booking]:  # my การจอง
    return db.query(Booking).filter(
        Booking.organizer_email == organizer_email,
        Booking.is_cancelled == False
    ).order_by(Booking.start_datetime.desc()).all()


def search_bookings(db: Session, search_term: str) -> List[Booking]:  # ค้นหาการจอง
    search_pattern = f"%{search_term}%"
    return db.query(Booking).filter(
        (Booking.title.ilike(search_pattern)) |
        (Booking.organizer_name.ilike(search_pattern)) |
        (Booking.description.ilike(search_pattern))
    ).filter(Booking.is_cancelled == False).all()
