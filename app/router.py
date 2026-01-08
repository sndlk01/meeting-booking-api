from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
import traceback

from config.config import get_db

# Import functions
from modules.room.room import (
    RoomCreate, RoomUpdate, RoomResponse, RoomAvailability,
    create_room, get_rooms, get_room, update_room, delete_room,
    check_room_availability, find_available_rooms, get_room_schedule
)

from modules.booking.booking import (
    BookingCreate, BookingUpdate, BookingResponse,
    create_booking, get_bookings, get_booking, update_booking,
    cancel_booking, get_upcoming_bookings, get_today_bookings,
    get_my_bookings, search_bookings
)

router = APIRouter()


# สร้างห้อง
@router.post("/rooms/", response_model=RoomResponse, tags=["Rooms"])
def create_room_endpoint(room: RoomCreate, db: Session = Depends(get_db)):
    try:
        return create_room(db, room)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rooms/", response_model=List[RoomResponse], tags=["Rooms"])
def get_rooms_endpoint(
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        db: Session = Depends(get_db)
):
    return get_rooms(db, skip=skip, limit=limit, active_only=active_only)


@router.get("/rooms/{room_id}", response_model=RoomResponse, tags=["Rooms"])
def get_room_endpoint(room_id: int, db: Session = Depends(get_db)):
    room = get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="ไม่พบห้องประชุม")
    return room


@router.put("/rooms/{room_id}", response_model=RoomResponse, tags=["Rooms"])
def update_room_endpoint(room_id: int, room_update: RoomUpdate, db: Session = Depends(get_db)):
    try:
        room = update_room(db, room_id, room_update)
        if not room:
            raise HTTPException(status_code=404, detail="ไม่พบห้องประชุม")
        return room
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/rooms/{room_id}", tags=["Rooms"])
def delete_room_endpoint(room_id: int, db: Session = Depends(get_db)):
    try:
        success = delete_room(db, room_id)
        if not success:
            raise HTTPException(status_code=404, detail="ไม่พบห้องประชุม")
        return {"message": "ลบห้องเรียบร้อยแล้ว"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# เช็คว่าห้องว่างไหม
@router.get("/rooms/{room_id}/availability", response_model=RoomAvailability, tags=["Rooms"])
def check_availability_endpoint(
        room_id: int,
        start_datetime: datetime,
        end_datetime: datetime,
        db: Session = Depends(get_db)
):
    return check_room_availability(db, room_id, start_datetime, end_datetime)


# หาห้องที่ว่าง
@router.get("/rooms/available/", response_model=List[RoomResponse], tags=["Rooms"])
def find_available_rooms_endpoint(
        start_datetime: datetime,
        end_datetime: datetime,
        min_capacity: Optional[int] = None,
        db: Session = Depends(get_db)
):
    return find_available_rooms(db, start_datetime, end_datetime, min_capacity)


# ค้นหาตารางการจองตามตาราง#
@router.get("/rooms/{room_id}/schedule", tags=["Rooms"])
def get_room_schedule_endpoint(
        room_id: int,
        target_date: date,
        db: Session = Depends(get_db)
):
    bookings = get_room_schedule(db, room_id, target_date)
    # Convert to BookingResponse format
    return [BookingResponse.from_booking(booking) for booking in bookings]


@router.post("/bookings/", response_model=BookingResponse, tags=["Bookings"])
def create_booking_endpoint(booking: BookingCreate, db: Session = Depends(get_db)):
    try:
        db_booking = create_booking(db, booking)
        return BookingResponse.from_booking(db_booking)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bookings/", response_model=List[BookingResponse], tags=["Bookings"])
def get_bookings_endpoint(
        skip: int = 0,
        limit: int = 100,
        room_id: Optional[int] = None,
        organizer_email: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_cancelled: bool = False,
        db: Session = Depends(get_db)
):
    bookings = get_bookings(
        db, skip=skip, limit=limit, room_id=room_id,
        organizer_email=organizer_email, start_date=start_date,
        end_date=end_date, include_cancelled=include_cancelled
    )
    return [BookingResponse.from_booking(booking) for booking in bookings]


@router.get("/bookings/{booking_id}", response_model=BookingResponse, tags=["Bookings"])
def get_booking_endpoint(booking_id: int, db: Session = Depends(get_db)):
    booking = get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="ไม่พบการจอง")
    return BookingResponse.from_booking(booking)


# แก้ไขการจอง
@router.put("/bookings/{booking_id}", response_model=BookingResponse, tags=["Bookings"])
def update_booking_endpoint(
        booking_id: int,
        booking_update: BookingUpdate,
        db: Session = Depends(get_db)
):
    try:
        booking = update_booking(db, booking_id, booking_update)
        if not booking:
            raise HTTPException(status_code=404, detail="ไม่พบการจอง")
        return BookingResponse.from_booking(booking)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/bookings/{booking_id}", tags=["Bookings"])
def cancel_booking_endpoint(
        booking_id: int,
        reason: Optional[str] = None,
        db: Session = Depends(get_db)
):
    try:
        booking = cancel_booking(db, booking_id, reason)
        if not booking:
            raise HTTPException(status_code=404, detail="ไม่พบการจอง")
        return {"message": "ยกเลิกการจองแล้ว", "booking_id": booking.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# การจองล่วงหน้า/ที่กำลังจะถึง
@router.get("/bookings/upcoming/", response_model=List[BookingResponse], tags=["Bookings"])
def get_upcoming_bookings_endpoint(days: int = 7, db: Session = Depends(get_db)):
    bookings = get_upcoming_bookings(db, days)
    return [BookingResponse.from_booking(booking) for booking in bookings]


# today booking
@router.get("/bookings/today/", response_model=List[BookingResponse], tags=["Bookings"])
def get_today_bookings_endpoint(db: Session = Depends(get_db)):
    bookings = get_today_bookings(db)
    return [BookingResponse.from_booking(booking) for booking in bookings]


# get my booking
@router.get("/bookings/my/", response_model=List[BookingResponse], tags=["Bookings"])
def get_my_bookings_endpoint(organizer_email: str, db: Session = Depends(get_db)):
    bookings = get_my_bookings(db, organizer_email)
    return [BookingResponse.from_booking(booking) for booking in bookings]


# ค้นหากาารจอง
@router.get("/bookings/search/", response_model=List[BookingResponse], tags=["Bookings"])
def search_bookings_endpoint(q: str, db: Session = Depends(get_db)):
    bookings = search_bookings(db, q)
    return [BookingResponse.from_booking(booking) for booking in bookings]
