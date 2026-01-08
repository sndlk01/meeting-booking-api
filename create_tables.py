import os
import sys
from datetime import datetime, time, timedelta
from dotenv import load_dotenv

load_dotenv()

sys.path.append('/app')
sys.path.append('/app/app')

if os.getenv("DB_HOST"):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from models.booking import Base, Room, Booking

    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_USERNAME = os.getenv("DB_USERNAME")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")

    print(f" Environment variables loaded:")
    print(f"   DB_HOST: {DB_HOST}")
    print(f"   DB_PORT: {DB_PORT}")
    print(f"   DB_NAME: {DB_NAME}")
    print(f"   DB_USERNAME: {DB_USERNAME}")

    DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    print(f"🐳 Docker mode - Connecting to: {DB_HOST}:{DB_PORT}")
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    try:
        from app.config.config import engine, SessionLocal
        from app.models.booking import Base, Room, Booking

        print("Local mode - Using config.config")
    except ImportError as e:
        print(f"Error importing config: {e}")
        print("Make sure you're running from the project root directory")
        sys.exit(1)


def wait_for_database():
    import time
    from sqlalchemy.exc import OperationalError

    max_retries = 30
    retry_count = 0

    while retry_count < max_retries:
        try:
            connection = engine.connect()
            connection.close()
            print("Database connection successful!")
            return True
        except OperationalError:
            retry_count += 1
            print(f"Waiting for database... (attempt {retry_count}/{max_retries})")
            time.sleep(2)

    print("Failed to connect to database")
    return False


def ensure_cancellation_reason_column():
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('booking')]
    if 'cancellation_reason' not in columns:
        print("Adding missing 'cancellation_reason' column to 'booking' table...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE booking ADD COLUMN cancellation_reason TEXT;"))
        print("Column 'cancellation_reason' added.")


def create_tables():
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        ensure_cancellation_reason_column()
        print("Database tables created successfully!")
        return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False


def drop_tables():
    try:
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("All tables dropped!")
        return True
    except Exception as e:
        print(f"Error dropping tables: {e}")
        return False


def reset_database():
    try:
        print("Resetting database...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        ensure_cancellation_reason_column()
        print("Database reset successfully!")
        return True
    except Exception as e:
        print(f"Error resetting database: {e}")
        return False


def create_sample_data():
    db = SessionLocal()

    try:
        print("Creating sample data...")

        existing_rooms = db.query(Room).count()
        if existing_rooms > 0:
            print(f"Found {existing_rooms} existing rooms, skipping sample data")
            return True

        rooms = [
            Room(
                name="ห้องประชุมใหญ่",
                capacity=20,
                location="ชั้น 2 อาคาร A",
                description="ห้องประชุมหลักสำหรับการประชุมใหญ่ พร้อมโปรเจกเตอร์และระบบเสียง",
                start_time=time(8, 0),
                end_time=time(18, 0)
            ),
            Room(
                name="ห้องประชุมเล็ก 1",
                capacity=6,
                location="ชั้น 3 อาคาร A",
                description="ห้องประชุมขนาดเล็กสำหรับทีมงาน พร้อมกระดานไวท์บอร์ด",
                start_time=time(8, 0),
                end_time=time(18, 0)
            ),
            Room(
                name="ห้องประชุมเล็ก 2",
                capacity=8,
                location="ชั้น 3 อาคาร A",
                description="ห้องประชุมขนาดเล็กสำหรับการประชุมแผนก",
                start_time=time(8, 0),
                end_time=time(18, 0)
            )
        ]

        for room in rooms:
            db.add(room)

        db.commit()
        print(f"Created {len(rooms)} rooms")

        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        day_after = now + timedelta(days=2)

        bookings = [
            Booking(
                room_id=1,
                title="Daily Scrum Meeting",
                organizer_name="เอ็มม่า วัดท่าไม้",
                organizer_email="emma@company.com",
                participant_count=8,
                start_datetime=tomorrow.replace(hour=9, minute=0, second=0, microsecond=0),
                end_datetime=tomorrow.replace(hour=10, minute=0, second=0, microsecond=0),
                description="ประชุมติดตามงานประจำวันของทีม Development"
            ),
            Booking(
                room_id=2,
                title="สัมภาษณ์งาน - Frontend Developer",
                organizer_name="น้องแจน แจนแจน",
                organizer_email="jan@company.com",
                participant_count=3,
                start_datetime=tomorrow.replace(hour=14, minute=0, second=0, microsecond=0),
                end_datetime=tomorrow.replace(hour=15, minute=30, second=0, microsecond=0),
                description="สัมภาษณ์ผู้สมัครตำแหน่ง Frontend Developer"
            )
        ]

        for booking in bookings:
            db.add(booking)

        db.commit()
        print(f"Created {len(bookings)} sample bookings")

        print("\nSample Data Summary:")
        print("=" * 50)
        print("Rooms:")
        for i, room in enumerate(rooms, 1):
            print(f"  {i}. {room.name} (ความจุ: {room.capacity} คน) - {room.location}")

        print("\nBookings:")
        for i, booking in enumerate(bookings, 1):
            print(f"  {i}. {booking.title} - {booking.start_datetime.strftime('%d/%m/%Y %H:%M')}")
        print("=" * 50)

        return True

    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "docker-init":
            if wait_for_database():
                success = create_tables() and create_sample_data()
            else:
                success = False
        elif command == "create":
            success = create_tables()
        elif command == "drop":
            confirm = input("ต้องการลบตารางทั้งหมดใช่ไหม? (yes/no): ")
            if confirm.lower() == "yes":
                success = drop_tables()
            else:
                print("ยกเลิกการทำงาน")
                sys.exit(0)
        elif command == "reset":
            confirm = input("ต้องการรีเซ็ตฐานข้อมูลใช่ไหม? ข้อมูลทั้งหมดจะหายไป! (yes/no): ")
            if confirm.lower() == "yes":
                success = reset_database()
            else:
                print("ยกเลิกการทำงาน")
                sys.exit(0)
        elif command == "sample":
            success = create_tables() and create_sample_data()
        else:
            print("คำสั่งไม่ถูกต้อง")
            sys.exit(1)

        if success:
            print("ดำเนินการเสร็จสิ้น!")
        else:
            print("💥กิดข้อผิดพลาด!")
            sys.exit(1)
    else:
        print("\nคำสั่งที่ใช้ได้:")
        print("  create      - สร้างตาราง")
        print("  drop        - ลบตารางทั้งหมด")
        print("  reset       - ลบและสร้างตารางใหม่")
        print("  sample      - สร้างตารางพร้อมข้อมูลตัวอย่าง")
        print("  docker-init - สำหรับ Docker (รอ DB + สร้างตาราง + ข้อมูลตัวอย่าง)")