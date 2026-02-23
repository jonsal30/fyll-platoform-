from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response, BackgroundTasks
from fastapi.responses import RedirectResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import math
import io
import csv
import base64
import warnings

# Google Sheets imports
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Google Sheets OAuth config
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_SHEETS_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_SHEETS_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_SHEETS_REDIRECT_URI', '')
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]

# Create the main app
app = FastAPI(title="Site Commander - Time Clock API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class UserRole(BaseModel):
    role: str = "employee"  # employee, manager, admin

class User(BaseModel):
    user_id: str = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:12]}")
    email: str
    name: str
    picture: Optional[str] = None
    role: str = "employee"
    numeric_id: Optional[str] = None
    assigned_sites: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WorkSite(BaseModel):
    site_id: str = Field(default_factory=lambda: f"site_{uuid.uuid4().hex[:8]}")
    name: str
    address: str
    latitude: float
    longitude: float
    radius_meters: int = 200
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TimeEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: f"entry_{uuid.uuid4().hex[:12]}")
    user_id: str
    site_id: str
    clock_in: datetime
    clock_out: Optional[datetime] = None
    lunch_start: Optional[datetime] = None
    lunch_end: Optional[datetime] = None
    clock_in_photo: Optional[str] = None
    clock_out_photo: Optional[str] = None
    clock_in_location: Optional[Dict[str, float]] = None
    clock_out_location: Optional[Dict[str, float]] = None
    location_verified: bool = False
    total_hours: Optional[float] = None
    status: str = "active"  # active, completed, pending_approval, approved, rejected
    notes: Optional[str] = None

class Timesheet(BaseModel):
    timesheet_id: str = Field(default_factory=lambda: f"ts_{uuid.uuid4().hex[:10]}")
    user_id: str
    site_id: str
    week_start: datetime
    week_end: datetime
    entries: List[str] = []
    total_hours: float = 0
    status: str = "pending"  # pending, submitted, approved, rejected
    manager_id: Optional[str] = None
    approval_token: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Notification(BaseModel):
    notification_id: str = Field(default_factory=lambda: f"notif_{uuid.uuid4().hex[:10]}")
    user_id: str
    title: str
    message: str
    type: str  # approval_request, approval_result, system
    link: Optional[str] = None
    read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== REQUEST/RESPONSE MODELS ====================

class ClockInRequest(BaseModel):
    site_id: str
    photo: Optional[str] = None  # Base64 encoded
    latitude: float
    longitude: float

class ClockOutRequest(BaseModel):
    entry_id: str
    photo: Optional[str] = None
    latitude: float
    longitude: float

class LunchRequest(BaseModel):
    entry_id: str
    action: str  # start or end

class ApprovalRequest(BaseModel):
    timesheet_id: str
    action: str  # approve or reject
    notes: Optional[str] = None
    corrections: Optional[Dict[str, Any]] = None

class CreateSiteRequest(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    radius_meters: int = 200

class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    assigned_sites: Optional[List[str]] = None
    numeric_id: Optional[str] = None

class NumericLoginRequest(BaseModel):
    numeric_id: str

# ==================== HELPER FUNCTIONS ====================

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula (returns meters)"""
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

async def verify_location(site_id: str, latitude: float, longitude: float) -> tuple[bool, float]:
    """Verify if location is within site's geo-fence"""
    site = await db.work_sites.find_one({"site_id": site_id}, {"_id": 0})
    if not site:
        return False, 0
    
    distance = calculate_distance(site["latitude"], site["longitude"], latitude, longitude)
    is_within = distance <= site["radius_meters"]
    return is_within, distance

def calculate_hours(clock_in: datetime, clock_out: datetime, lunch_start: Optional[datetime], lunch_end: Optional[datetime]) -> float:
    """Calculate total worked hours excluding lunch"""
    total = (clock_out - clock_in).total_seconds() / 3600
    if lunch_start and lunch_end:
        lunch_duration = (lunch_end - lunch_start).total_seconds() / 3600
        total -= lunch_duration
    return round(total, 2)

async def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from session token"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        return None
    
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        return None
    
    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    return user

async def create_notification(user_id: str, title: str, message: str, notif_type: str, link: Optional[str] = None):
    """Create a notification for a user"""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notif_type,
        link=link
    )
    await db.notifications.insert_one(notification.model_dump())

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    """Exchange session_id for session_token (Emergent OAuth)"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Call Emergent Auth to get user data
    async with httpx.AsyncClient() as client:
        auth_response = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        
        if auth_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        user_data = auth_response.json()
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data["email"]}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        # Update user info
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": user_data["name"], "picture": user_data.get("picture")}}
        )
    else:
        # Create new user
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        new_user = User(
            user_id=user_id,
            email=user_data["email"],
            name=user_data["name"],
            picture=user_data.get("picture"),
            role="employee"
        )
        await db.users.insert_one(new_user.model_dump())
    
    # Create session
    session_token = f"st_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7*24*60*60
    )
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user

@api_router.post("/auth/numeric-login")
async def numeric_login(request: NumericLoginRequest, response: Response):
    """Login with numeric ID"""
    user = await db.users.find_one({"numeric_id": request.numeric_id}, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="Employee ID not found")
    
    # Create session
    session_token = f"st_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user["user_id"],
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7*24*60*60
    )
    
    return user

@api_router.get("/auth/me")
async def get_me(request: Request):
    """Get current authenticated user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout and clear session"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out"}

# ==================== TIME CLOCK ENDPOINTS ====================

@api_router.post("/clock/in")
async def clock_in(request: Request, data: ClockInRequest):
    """Clock in to a site"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check for existing active entry
    active_entry = await db.time_entries.find_one({
        "user_id": user["user_id"],
        "status": "active"
    }, {"_id": 0})
    
    if active_entry:
        raise HTTPException(status_code=400, detail="Already clocked in. Please clock out first.")
    
    # Verify location
    location_verified, distance = await verify_location(data.site_id, data.latitude, data.longitude)
    
    # Create time entry
    entry = TimeEntry(
        user_id=user["user_id"],
        site_id=data.site_id,
        clock_in=datetime.now(timezone.utc),
        clock_in_photo=data.photo,
        clock_in_location={"latitude": data.latitude, "longitude": data.longitude},
        location_verified=location_verified,
        status="active"
    )
    
    await db.time_entries.insert_one(entry.model_dump())
    
    result = entry.model_dump()
    result["distance_from_site"] = round(distance, 1)
    return result

@api_router.post("/clock/out")
async def clock_out(request: Request, data: ClockOutRequest):
    """Clock out from current entry"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    entry = await db.time_entries.find_one({
        "entry_id": data.entry_id,
        "user_id": user["user_id"],
        "status": "active"
    }, {"_id": 0})
    
    if not entry:
        raise HTTPException(status_code=404, detail="Active time entry not found")
    
    # Verify location
    location_verified, distance = await verify_location(entry["site_id"], data.latitude, data.longitude)
    
    clock_out_time = datetime.now(timezone.utc)
    clock_in_time = datetime.fromisoformat(entry["clock_in"]) if isinstance(entry["clock_in"], str) else entry["clock_in"]
    
    lunch_start = None
    lunch_end = None
    if entry.get("lunch_start"):
        lunch_start = datetime.fromisoformat(entry["lunch_start"]) if isinstance(entry["lunch_start"], str) else entry["lunch_start"]
    if entry.get("lunch_end"):
        lunch_end = datetime.fromisoformat(entry["lunch_end"]) if isinstance(entry["lunch_end"], str) else entry["lunch_end"]
    
    total_hours = calculate_hours(clock_in_time, clock_out_time, lunch_start, lunch_end)
    
    await db.time_entries.update_one(
        {"entry_id": data.entry_id},
        {"$set": {
            "clock_out": clock_out_time.isoformat(),
            "clock_out_photo": data.photo,
            "clock_out_location": {"latitude": data.latitude, "longitude": data.longitude},
            "total_hours": total_hours,
            "status": "completed"
        }}
    )
    
    updated_entry = await db.time_entries.find_one({"entry_id": data.entry_id}, {"_id": 0})
    updated_entry["distance_from_site"] = round(distance, 1)
    return updated_entry

@api_router.post("/clock/lunch")
async def manage_lunch(request: Request, data: LunchRequest):
    """Start or end lunch break"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    entry = await db.time_entries.find_one({
        "entry_id": data.entry_id,
        "user_id": user["user_id"],
        "status": "active"
    }, {"_id": 0})
    
    if not entry:
        raise HTTPException(status_code=404, detail="Active time entry not found")
    
    now = datetime.now(timezone.utc).isoformat()
    
    if data.action == "start":
        if entry.get("lunch_start"):
            raise HTTPException(status_code=400, detail="Lunch already started")
        await db.time_entries.update_one(
            {"entry_id": data.entry_id},
            {"$set": {"lunch_start": now}}
        )
    elif data.action == "end":
        if not entry.get("lunch_start"):
            raise HTTPException(status_code=400, detail="Lunch not started")
        if entry.get("lunch_end"):
            raise HTTPException(status_code=400, detail="Lunch already ended")
        await db.time_entries.update_one(
            {"entry_id": data.entry_id},
            {"$set": {"lunch_end": now}}
        )
    
    return await db.time_entries.find_one({"entry_id": data.entry_id}, {"_id": 0})

@api_router.get("/clock/status")
async def get_clock_status(request: Request):
    """Get current clock status for user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    active_entry = await db.time_entries.find_one({
        "user_id": user["user_id"],
        "status": "active"
    }, {"_id": 0})
    
    if active_entry:
        site = await db.work_sites.find_one({"site_id": active_entry["site_id"]}, {"_id": 0})
        return {
            "is_clocked_in": True,
            "entry": active_entry,
            "site": site
        }
    
    return {"is_clocked_in": False, "entry": None, "site": None}

# ==================== TIME ENTRIES ENDPOINTS ====================

@api_router.get("/entries")
async def get_entries(request: Request, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get time entries for current user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {"user_id": user["user_id"]}
    
    if start_date:
        query["clock_in"] = {"$gte": start_date}
    if end_date:
        if "clock_in" in query:
            query["clock_in"]["$lte"] = end_date
        else:
            query["clock_in"] = {"$lte": end_date}
    
    entries = await db.time_entries.find(query, {"_id": 0}).sort("clock_in", -1).to_list(1000)
    return entries

@api_router.get("/entries/today")
async def get_today_entries(request: Request):
    """Get today's entries for current user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    entries = await db.time_entries.find({
        "user_id": user["user_id"],
        "clock_in": {"$gte": today_start.isoformat()}
    }, {"_id": 0}).to_list(100)
    
    return entries

# ==================== TIMESHEET ENDPOINTS ====================

@api_router.get("/timesheets")
async def get_timesheets(request: Request, status: Optional[str] = None):
    """Get timesheets for current user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {"user_id": user["user_id"]}
    if status:
        query["status"] = status
    
    timesheets = await db.timesheets.find(query, {"_id": 0}).sort("week_start", -1).to_list(100)
    return timesheets

@api_router.post("/timesheets/submit")
async def submit_timesheet(request: Request, week_start: str, site_id: str):
    """Submit a timesheet for approval"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    week_start_dt = datetime.fromisoformat(week_start.replace('Z', '+00:00'))
    week_end_dt = week_start_dt + timedelta(days=7)
    
    # Get entries for the week
    entries = await db.time_entries.find({
        "user_id": user["user_id"],
        "site_id": site_id,
        "clock_in": {"$gte": week_start_dt.isoformat(), "$lt": week_end_dt.isoformat()},
        "status": "completed"
    }, {"_id": 0}).to_list(100)
    
    if not entries:
        raise HTTPException(status_code=400, detail="No completed entries found for this week")
    
    total_hours = sum(e.get("total_hours", 0) for e in entries)
    entry_ids = [e["entry_id"] for e in entries]
    
    # Create approval token
    approval_token = uuid.uuid4().hex
    
    timesheet = Timesheet(
        user_id=user["user_id"],
        site_id=site_id,
        week_start=week_start_dt,
        week_end=week_end_dt,
        entries=entry_ids,
        total_hours=total_hours,
        status="submitted",
        approval_token=approval_token
    )
    
    await db.timesheets.insert_one(timesheet.model_dump())
    
    # Notify managers
    site = await db.work_sites.find_one({"site_id": site_id}, {"_id": 0})
    managers = await db.users.find({"role": "manager", "assigned_sites": site_id}, {"_id": 0}).to_list(100)
    
    for manager in managers:
        await create_notification(
            user_id=manager["user_id"],
            title="Timesheet Submitted",
            message=f"{user['name']} submitted a timesheet for {site['name'] if site else 'Unknown Site'}",
            notif_type="approval_request",
            link=f"/approve/{timesheet.timesheet_id}?token={approval_token}"
        )
    
    return timesheet.model_dump()

@api_router.get("/timesheets/{timesheet_id}")
async def get_timesheet(timesheet_id: str, token: Optional[str] = None, request: Request = None):
    """Get a specific timesheet (with entries)"""
    timesheet = await db.timesheets.find_one({"timesheet_id": timesheet_id}, {"_id": 0})
    
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    # Check authorization
    user = await get_current_user(request) if request else None
    
    if not user and not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if token and timesheet.get("approval_token") != token:
        raise HTTPException(status_code=403, detail="Invalid approval token")
    
    # Get entries
    entries = await db.time_entries.find(
        {"entry_id": {"$in": timesheet.get("entries", [])}},
        {"_id": 0}
    ).to_list(100)
    
    # Get user info
    employee = await db.users.find_one({"user_id": timesheet["user_id"]}, {"_id": 0})
    site = await db.work_sites.find_one({"site_id": timesheet["site_id"]}, {"_id": 0})
    
    return {
        "timesheet": timesheet,
        "entries": entries,
        "employee": employee,
        "site": site
    }

@api_router.post("/timesheets/{timesheet_id}/approve")
async def approve_timesheet(timesheet_id: str, data: ApprovalRequest, request: Request, token: Optional[str] = None):
    """Approve or reject a timesheet"""
    timesheet = await db.timesheets.find_one({"timesheet_id": timesheet_id}, {"_id": 0})
    
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    user = await get_current_user(request)
    
    # Verify authorization (manager or valid token)
    if user and user.get("role") not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if not user and token != timesheet.get("approval_token"):
        raise HTTPException(status_code=403, detail="Invalid token")
    
    new_status = "approved" if data.action == "approve" else "rejected"
    
    update_data = {
        "status": new_status,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "notes": data.notes
    }
    
    if user:
        update_data["manager_id"] = user["user_id"]
    
    # Apply corrections if any
    if data.corrections:
        for entry_id, correction in data.corrections.items():
            await db.time_entries.update_one(
                {"entry_id": entry_id},
                {"$set": correction}
            )
        # Recalculate total hours
        entries = await db.time_entries.find(
            {"entry_id": {"$in": timesheet.get("entries", [])}},
            {"_id": 0}
        ).to_list(100)
        update_data["total_hours"] = sum(e.get("total_hours", 0) for e in entries)
    
    await db.timesheets.update_one({"timesheet_id": timesheet_id}, {"$set": update_data})
    
    # Update entry statuses
    await db.time_entries.update_many(
        {"entry_id": {"$in": timesheet.get("entries", [])}},
        {"$set": {"status": new_status}}
    )
    
    # Notify employee
    await create_notification(
        user_id=timesheet["user_id"],
        title=f"Timesheet {new_status.capitalize()}",
        message=f"Your timesheet has been {new_status}" + (f": {data.notes}" if data.notes else ""),
        notif_type="approval_result"
    )
    
    return {"message": f"Timesheet {new_status}", "status": new_status}

# ==================== MANAGER ENDPOINTS ====================

@api_router.get("/manager/pending")
async def get_pending_timesheets(request: Request):
    """Get pending timesheets for manager"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.get("role") not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = {"status": "submitted"}
    
    # If manager (not admin), only show assigned sites
    if user.get("role") == "manager":
        query["site_id"] = {"$in": user.get("assigned_sites", [])}
    
    timesheets = await db.timesheets.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with user and site info
    result = []
    for ts in timesheets:
        employee = await db.users.find_one({"user_id": ts["user_id"]}, {"_id": 0})
        site = await db.work_sites.find_one({"site_id": ts["site_id"]}, {"_id": 0})
        result.append({
            **ts,
            "employee": employee,
            "site": site
        })
    
    return result

@api_router.get("/manager/team")
async def get_team_status(request: Request):
    """Get current status of team members"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.get("role") not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get employees at assigned sites
    query = {"role": "employee"}
    if user.get("role") == "manager":
        query["assigned_sites"] = {"$in": user.get("assigned_sites", [])}
    
    employees = await db.users.find(query, {"_id": 0}).to_list(100)
    
    result = []
    for emp in employees:
        active_entry = await db.time_entries.find_one({
            "user_id": emp["user_id"],
            "status": "active"
        }, {"_id": 0})
        
        result.append({
            "employee": emp,
            "is_clocked_in": active_entry is not None,
            "current_entry": active_entry
        })
    
    return result

# ==================== SITE ENDPOINTS ====================

@api_router.get("/sites")
async def get_sites(request: Request):
    """Get all work sites"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {"is_active": True}
    
    # Non-admin users only see assigned sites
    if user.get("role") not in ["admin"]:
        if user.get("assigned_sites"):
            query["site_id"] = {"$in": user.get("assigned_sites", [])}
    
    sites = await db.work_sites.find(query, {"_id": 0}).to_list(100)
    return sites

@api_router.post("/sites")
async def create_site(request: Request, data: CreateSiteRequest):
    """Create a new work site (admin only)"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    site = WorkSite(
        name=data.name,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude,
        radius_meters=data.radius_meters
    )
    
    await db.work_sites.insert_one(site.model_dump())
    return site.model_dump()

@api_router.put("/sites/{site_id}")
async def update_site(site_id: str, request: Request, data: CreateSiteRequest):
    """Update a work site"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.work_sites.update_one(
        {"site_id": site_id},
        {"$set": data.model_dump()}
    )
    
    return await db.work_sites.find_one({"site_id": site_id}, {"_id": 0})

@api_router.delete("/sites/{site_id}")
async def delete_site(site_id: str, request: Request):
    """Deactivate a work site"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.work_sites.update_one({"site_id": site_id}, {"$set": {"is_active": False}})
    return {"message": "Site deactivated"}

# ==================== USER MANAGEMENT ENDPOINTS ====================

@api_router.get("/users")
async def get_users(request: Request):
    """Get all users (admin/manager)"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.get("role") not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    return users

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, request: Request, data: UpdateUserRequest):
    """Update user role/sites"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    await db.users.update_one({"user_id": user_id}, {"$set": update_data})
    return await db.users.find_one({"user_id": user_id}, {"_id": 0})

# ==================== NOTIFICATION ENDPOINTS ====================

@api_router.get("/notifications")
async def get_notifications(request: Request):
    """Get notifications for current user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    notifications = await db.notifications.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return notifications

@api_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, request: Request):
    """Mark notification as read"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    await db.notifications.update_one(
        {"notification_id": notification_id, "user_id": user["user_id"]},
        {"$set": {"read": True}}
    )
    return {"message": "Marked as read"}

@api_router.get("/notifications/unread-count")
async def get_unread_count(request: Request):
    """Get unread notification count"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    count = await db.notifications.count_documents({
        "user_id": user["user_id"],
        "read": False
    })
    
    return {"count": count}

# ==================== EXPORT ENDPOINTS ====================

@api_router.get("/export/csv")
async def export_csv(request: Request, start_date: str, end_date: str, site_id: Optional[str] = None):
    """Export time entries as CSV"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {}
    
    if user.get("role") == "employee":
        query["user_id"] = user["user_id"]
    elif site_id:
        query["site_id"] = site_id
    
    query["clock_in"] = {"$gte": start_date, "$lte": end_date}
    
    entries = await db.time_entries.find(query, {"_id": 0}).to_list(10000)
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Entry ID", "User ID", "Site ID", "Clock In", "Clock Out",
        "Lunch Start", "Lunch End", "Total Hours", "Location Verified", "Status"
    ])
    
    for entry in entries:
        writer.writerow([
            entry.get("entry_id"),
            entry.get("user_id"),
            entry.get("site_id"),
            entry.get("clock_in"),
            entry.get("clock_out"),
            entry.get("lunch_start"),
            entry.get("lunch_end"),
            entry.get("total_hours"),
            entry.get("location_verified"),
            entry.get("status")
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=timesheet_{start_date}_{end_date}.csv"}
    )

# ==================== GOOGLE SHEETS OAUTH ENDPOINTS ====================

@api_router.get("/oauth/sheets/login")
async def sheets_oauth_login(request: Request):
    """Initiate Google Sheets OAuth"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Google Sheets not configured")
    
    flow = Flow.from_client_config({
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }, scopes=GOOGLE_SCOPES, redirect_uri=GOOGLE_REDIRECT_URI)
    
    url, state = flow.authorization_url(access_type='offline', prompt='consent')
    
    # Save state
    await db.oauth_states.insert_one({
        "state": state,
        "user_id": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    })
    
    return {"auth_url": url}

@api_router.get("/oauth/sheets/callback")
async def sheets_oauth_callback(code: str, state: str):
    """Handle Google Sheets OAuth callback"""
    # Verify state
    state_doc = await db.oauth_states.find_one({"state": state}, {"_id": 0})
    if not state_doc:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    await db.oauth_states.delete_one({"state": state})
    
    flow = Flow.from_client_config({
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }, scopes=GOOGLE_SCOPES, redirect_uri=GOOGLE_REDIRECT_URI)
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        flow.fetch_token(code=code)
    
    creds = flow.credentials
    
    # Save tokens
    await db.google_tokens.update_one(
        {"user_id": state_doc["user_id"]},
        {"$set": {
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "expires_at": creds.expiry.isoformat() if creds.expiry else None,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "token_uri": "https://oauth2.googleapis.com/token",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return RedirectResponse("/admin?sheets=connected")

@api_router.post("/sheets/sync")
async def sync_to_sheets(request: Request, timesheet_id: str):
    """Sync a timesheet to Google Sheets"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get token
    token_doc = await db.google_tokens.find_one({}, {"_id": 0})
    if not token_doc:
        raise HTTPException(status_code=400, detail="Google Sheets not connected")
    
    # Get timesheet data
    timesheet = await db.timesheets.find_one({"timesheet_id": timesheet_id}, {"_id": 0})
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    
    entries = await db.time_entries.find(
        {"entry_id": {"$in": timesheet.get("entries", [])}},
        {"_id": 0}
    ).to_list(100)
    
    employee = await db.users.find_one({"user_id": timesheet["user_id"]}, {"_id": 0})
    site = await db.work_sites.find_one({"site_id": timesheet["site_id"]}, {"_id": 0})
    
    # Build credentials
    creds = Credentials(
        token=token_doc["access_token"],
        refresh_token=token_doc.get("refresh_token"),
        token_uri=token_doc.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_doc.get("client_id"),
        client_secret=token_doc.get("client_secret")
    )
    
    # Refresh if needed
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        await db.google_tokens.update_one(
            {"user_id": token_doc["user_id"]},
            {"$set": {"access_token": creds.token}}
        )
    
    service = build('sheets', 'v4', credentials=creds)
    
    # Get or create spreadsheet ID from settings
    settings = await db.settings.find_one({"key": "google_sheets"}, {"_id": 0})
    spreadsheet_id = settings.get("spreadsheet_id") if settings else None
    
    if not spreadsheet_id:
        # Create new spreadsheet
        spreadsheet = service.spreadsheets().create(body={
            "properties": {"title": "Site Commander Timesheets"}
        }).execute()
        spreadsheet_id = spreadsheet["spreadsheetId"]
        await db.settings.update_one(
            {"key": "google_sheets"},
            {"$set": {"spreadsheet_id": spreadsheet_id}},
            upsert=True
        )
    
    # Prepare data
    values = [
        ["Timesheet ID", timesheet_id],
        ["Employee", employee.get("name", "Unknown")],
        ["Site", site.get("name", "Unknown") if site else "Unknown"],
        ["Week", f"{timesheet.get('week_start', '')} to {timesheet.get('week_end', '')}"],
        ["Total Hours", timesheet.get("total_hours", 0)],
        ["Status", timesheet.get("status", "")],
        [],
        ["Date", "Clock In", "Clock Out", "Lunch Start", "Lunch End", "Hours", "Verified"]
    ]
    
    for entry in entries:
        values.append([
            entry.get("clock_in", "")[:10] if entry.get("clock_in") else "",
            entry.get("clock_in", "")[11:19] if entry.get("clock_in") else "",
            entry.get("clock_out", "")[11:19] if entry.get("clock_out") else "",
            entry.get("lunch_start", "")[11:19] if entry.get("lunch_start") else "",
            entry.get("lunch_end", "")[11:19] if entry.get("lunch_end") else "",
            entry.get("total_hours", 0),
            "Yes" if entry.get("location_verified") else "No"
        ])
    
    # Append to sheet
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="Sheet1!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": values}
    ).execute()
    
    return {"message": "Synced to Google Sheets", "spreadsheet_id": spreadsheet_id}

@api_router.get("/sheets/status")
async def get_sheets_status(request: Request):
    """Check Google Sheets connection status"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token_doc = await db.google_tokens.find_one({}, {"_id": 0})
    settings = await db.settings.find_one({"key": "google_sheets"}, {"_id": 0})
    
    return {
        "connected": token_doc is not None,
        "spreadsheet_id": settings.get("spreadsheet_id") if settings else None
    }

# ==================== ROOT ENDPOINT ====================

@api_router.get("/")
async def root():
    return {"message": "Site Commander API", "version": "1.0.0"}

# Include the router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
