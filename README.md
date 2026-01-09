# Meeting Room Booking API

A comprehensive REST API for managing meeting room bookings built with FastAPI, PostgreSQL, and Docker. This system provides complete functionality for room management, booking scheduling, availability checking, and conflict prevention.

## 🏢 Overview

The Meeting Room Booking API is designed to help organizations manage their meeting rooms efficiently. It provides a robust backend system for:

- **Room Management**: Create, update, and manage meeting rooms with capacity and operating hours
- **Booking Management**: Schedule, modify, and cancel meeting room bookings
- **Availability Checking**: Real-time room availability validation with conflict detection
- **Search & Filtering**: Find available rooms and search bookings by various criteria
- **Schedule Viewing**: View room schedules by date

## ✨ Key Features

### Room Management
- Create rooms with capacity, location, and operating hours
- Update room information and status
- Soft-delete rooms (deactivation) with booking validation
- Filter active/inactive rooms
- Set custom operating hours per room

### Booking Management
- Create bookings with organizer and participant details
- Real-time availability checking during booking creation
- Prevent double-bookings and time conflicts
- Update bookings with automatic conflict detection
- Cancel bookings with reason tracking
- View booking schedules by date

### Smart Availability System
- Check if a room is available for a specific time slot
- Validate against operating hours
- Detect booking conflicts
- Find all available rooms for a given time period
- Filter by minimum capacity requirements

### Search & Filtering
- Get upcoming bookings (next N days)
- Get today's bookings
- Get bookings by organizer email
- Search bookings by title, organizer name, or description
- Filter by date range, room, and cancellation status

## 🚀 Technology Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0.23
- **Server**: Uvicorn 0.24.0
- **Containerization**: Docker & Docker Compose
- **Python**: 3.11

## 📋 Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local development)
- PostgreSQL (if running without Docker)

## 🛠️ Installation & Setup

### Option 1: Docker (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd meeting-booking-api
```

2. **Create environment file**
```bash
# Create .env file in the project root
cat > .env << EOF
# API Configuration
API_CONTAINER=meeting-api
API_IMAGE=meeting-api:latest
API_PORT=8000

# Database Configuration
DB_CONTAINER_NAME=meeting-db
DB_HOST=db
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=your_secure_password
DB_NAME=meeting_room

# Debug Mode
DEBUG=false
EOF
```

3. **Build and start services**
```bash
docker-compose up -d
```

4. **Verify the services are running**
```bash
docker-compose ps
```

The API will be available at:
- API: http://localhost:8000
- API Documentation (Swagger): http://localhost:8000/docs
- API Documentation (ReDoc): http://localhost:8000/redoc

### Option 2: Local Development

1. **Clone and navigate to the project**
```bash
git clone <repository-url>
cd meeting-booking-api
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_USERNAME=postgres
export DB_PASSWORD=your_password
export DB_NAME=meeting_room
export DEBUG=true
```

5. **Initialize database**
```bash
# Create tables and sample data
python create_tables.py sample

# Or just create tables
python create_tables.py create
```

6. **Run the application**
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Database Management

The `create_tables.py` script provides several commands for database management:

```bash
# Create database tables
python create_tables.py create

# Create tables with sample data (recommended for testing)
python create_tables.py sample

# Drop all tables (requires confirmation)
python create_tables.py drop

# Reset database (drop and recreate)
python create_tables.py reset

# Docker initialization (used by Docker container)
python create_tables.py docker-init
```

### Sample Data

When using the `sample` or `docker-init` command, the following data is created:

**Rooms:**
1. ห้องประชุมใหญ่ (Large Meeting Room) - Capacity: 20, Location: Floor 2 Building A
2. ห้องประชุมเล็ก 1 (Small Meeting Room 1) - Capacity: 6, Location: Floor 3 Building A
3. ห้องประชุมเล็ก 2 (Small Meeting Room 2) - Capacity: 8, Location: Floor 3 Building A

**Sample Bookings:**
- Daily Scrum Meeting (tomorrow 9:00-10:00)
- Frontend Developer Interview (tomorrow 14:00-15:30)

## 🔌 API Endpoints

### Root Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message and API info |
| GET | `/health` | Health check endpoint |

### Room Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/rooms/` | Create a new room |
| GET | `/api/v1/rooms/` | List all rooms |
| GET | `/api/v1/rooms/{room_id}` | Get room details |
| PUT | `/api/v1/rooms/{room_id}` | Update room |
| DELETE | `/api/v1/rooms/{room_id}` | Delete/deactivate room |
| GET | `/api/v1/rooms/{room_id}/availability` | Check room availability |
| GET | `/api/v1/rooms/available/` | Find available rooms |
| GET | `/api/v1/rooms/{room_id}/schedule` | Get room schedule |

### Booking Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/bookings/` | Create a booking |
| GET | `/api/v1/bookings/` | List bookings (with filters) |
| GET | `/api/v1/bookings/{booking_id}` | Get booking details |
| PUT | `/api/v1/bookings/{booking_id}` | Update booking |
| DELETE | `/api/v1/bookings/{booking_id}` | Cancel booking |
| GET | `/api/v1/bookings/upcoming/` | Get upcoming bookings |
| GET | `/api/v1/bookings/today/` | Get today's bookings |
| GET | `/api/v1/bookings/my/` | Get user's bookings |
| GET | `/api/v1/bookings/search/` | Search bookings |

## 📝 API Usage Examples

### Create a Room

```bash
curl -X POST "http://localhost:8000/api/v1/rooms/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Conference Room A",
    "capacity": 12,
    "location": "Floor 4",
    "description": "Large conference room with projector",
    "start_time": "08:00:00",
    "end_time": "18:00:00"
  }'
```

### Check Room Availability

```bash
curl -X GET "http://localhost:8000/api/v1/rooms/1/availability?start_datetime=2026-01-10T09:00:00&end_datetime=2026-01-10T11:00:00"
```

### Find Available Rooms

```bash
curl -X GET "http://localhost:8000/api/v1/rooms/available/?start_datetime=2026-01-10T14:00:00&end_datetime=2026-01-10T16:00:00&min_capacity=6"
```

### Create a Booking

```bash
curl -X POST "http://localhost:8000/api/v1/bookings/" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": 1,
    "title": "Project Planning Meeting",
    "organizer_name": "John Doe",
    "organizer_email": "john@company.com",
    "participant_count": 8,
    "start_datetime": "2026-01-10T14:00:00",
    "end_datetime": "2026-01-10T16:00:00",
    "description": "Q1 project planning session"
  }'
```

### Get Room Schedule

```bash
curl -X GET "http://localhost:8000/api/v1/rooms/1/schedule?target_date=2026-01-10"
```

### Search Bookings

```bash
curl -X GET "http://localhost:8000/api/v1/bookings/search/?q=project"
```

### Get Upcoming Bookings

```bash
curl -X GET "http://localhost:8000/api/v1/bookings/upcoming/?days=7"
```

## 🗂️ Project Structure

```
meeting-booking-api/
├── app/
│   ├── config/
│   │   └── config.py           # Database configuration
│   ├── models/
│   │   └── booking.py          # SQLAlchemy models (Room, Booking)
│   ├── modules/
│   │   ├── booking/
│   │   │   └── booking.py      # Booking business logic
│   │   └── room/
│   │       └── room.py         # Room business logic
│   ├── main.py                 # FastAPI application entry point
│   └── router.py               # API route definitions
├── db/
│   └── postgresql/             # PostgreSQL data directory
├── logs/                       # Application logs
├── create_tables.py            # Database initialization script
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Docker image definition
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🧩 Data Models

### Room Model

```python
{
  "id": 1,
  "name": "Conference Room A",
  "capacity": 12,
  "location": "Floor 4",
  "description": "Large conference room with projector",
  "start_time": "08:00:00",
  "end_time": "18:00:00",
  "is_active": true,
  "created_at": "2026-01-08T10:00:00"
}
```

### Booking Model

```python
{
  "id": 1,
  "room_id": 1,
  "room_name": "Conference Room A",
  "title": "Project Planning Meeting",
  "organizer_name": "John Doe",
  "organizer_email": "john@company.com",
  "participant_count": 8,
  "start_datetime": "2026-01-10T14:00:00",
  "end_datetime": "2026-01-10T16:00:00",
  "description": "Q1 project planning session",
  "notes": "Bring project documents",
  "is_cancelled": false,
  "cancelled_at": null,
  "cancellation_reason": null,
  "created_at": "2026-01-08T10:00:00"
}
```

## 🔒 Business Rules & Validations

### Room Management
- Room names must be unique
- Capacity must be positive
- End time must be after start time
- Rooms with future bookings cannot be deleted (soft-deleted instead)

### Booking Management
- End datetime must be after start datetime
- Participant count must be positive and not exceed room capacity
- Email format validation for organizer
- Bookings must be within room operating hours
- Cannot double-book a room (automatic conflict detection)
- Cancelled bookings cannot be modified
- When updating booking times, availability is re-checked

### Availability Checking
- Validates room exists and is active
- Checks against room operating hours
- Detects overlapping bookings
- Provides detailed reasons for unavailability

## 🐳 Docker Configuration

### Services

- **api**: FastAPI application (Port 8000)
- **db**: PostgreSQL 15 database (Port 5432)

### Networks

- `meeting_network`: Bridge network for service communication

### Volumes

- `./:/app`: Application code (hot-reload enabled)
- `./db/postgresql:/var/lib/postgresql/data/`: Database persistence
- `./logs:/app/logs`: Application logs

### Environment Variables

Configure via `.env` file:

```env
# API Configuration
API_CONTAINER=meeting-api
API_IMAGE=meeting-api:latest
API_PORT=8000

# Database Configuration
DB_CONTAINER_NAME=meeting-db
DB_HOST=db
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=your_secure_password
DB_NAME=meeting_room

# Debug Mode
DEBUG=false
```

## 📱 Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
  - Interactive interface to test all endpoints
  - View request/response schemas
  - Try out API calls directly from the browser

- **ReDoc**: http://localhost:8000/redoc
  - Clean, three-panel design
  - Excellent for reading and understanding the API

## 🔧 Development

### Running Tests

```bash
# TODO: Add testing framework
```

### Database Migrations

The project uses SQLAlchemy with Alembic support. To modify database schema:

1. Update models in `app/models/booking.py`
2. Run the create_tables script to apply changes

### Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Document complex business logic

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View database logs
docker-compose logs db

# Restart services
docker-compose restart
```

### API Not Responding

```bash
# Check API logs
docker-compose logs api

# Rebuild and restart
docker-compose down
docker-compose up --build
```

### Port Already in Use

```bash
# Change port in .env file
API_PORT=8001

# Or stop the service using the port
lsof -ti:8000 | xargs kill -9
```

