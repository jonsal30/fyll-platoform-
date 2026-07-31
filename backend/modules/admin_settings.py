# Admin Settings & White-Label Module
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import os
import json

router = APIRouter(prefix="/api/admin", tags=["Admin Settings"])

# Get database
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

# ==================== MODELS ====================

class BrandingSettings(BaseModel):
    company_name: str = "GH Service Group"
    tagline: str = "Building people, not just payroll."
    logo_url: str = ""
    favicon_url: str = ""
    primary_color: str = "#4600FF"  # Keystone Indigo
    secondary_color: str = "#FF2E63"  # Vertex Magenta
    accent_color: str = "#101820"  # Foundation
    background_color: str = "#F5F5F5"  # Horizon
    font_heading: str = "Crimson Pro"
    font_body: str = "system-ui"
    custom_css: str = ""

class ModuleSettings(BaseModel):
    time_clock: bool = True
    ats_recruiting: bool = True
    client_portal: bool = True
    hr_management: bool = True
    payroll: bool = True
    executive_dashboard: bool = True

class IntegrationSettings(BaseModel):
    google_sheets_client_id: str = ""
    google_sheets_client_secret: str = ""
    google_sheets_redirect_uri: str = ""
    indeed_employer_id: str = ""
    indeed_api_key: str = ""
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = ""
    background_check_provider: str = ""  # checkr, sterling, goodhire
    background_check_api_key: str = ""

class SystemSettings(BaseModel):
    settings_id: str = "system_settings"
    branding: BrandingSettings = BrandingSettings()
    modules: ModuleSettings = ModuleSettings()
    integrations: IntegrationSettings = IntegrationSettings()
    geo_fence_radius_default: int = 200
    session_timeout_days: int = 7
    require_photo_clock_in: bool = True
    require_photo_clock_out: bool = True
    allow_off_site_clock_in: bool = True
    lunch_auto_deduct_minutes: int = 0
    overtime_threshold_daily: float = 8.0
    overtime_threshold_weekly: float = 40.0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: str = ""

# ==================== REQUEST MODELS ====================

class UpdateBrandingRequest(BaseModel):
    company_name: Optional[str] = None
    tagline: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_color: Optional[str] = None
    font_heading: Optional[str] = None
    font_body: Optional[str] = None
    custom_css: Optional[str] = None

class UpdateIntegrationsRequest(BaseModel):
    google_sheets_client_id: Optional[str] = None
    google_sheets_client_secret: Optional[str] = None
    google_sheets_redirect_uri: Optional[str] = None
    indeed_employer_id: Optional[str] = None
    indeed_api_key: Optional[str] = None
    sendgrid_api_key: Optional[str] = None
    sendgrid_from_email: Optional[str] = None
    background_check_provider: Optional[str] = None
    background_check_api_key: Optional[str] = None

class UpdateModulesRequest(BaseModel):
    time_clock: Optional[bool] = None
    ats_recruiting: Optional[bool] = None
    client_portal: Optional[bool] = None
    hr_management: Optional[bool] = None
    payroll: Optional[bool] = None
    executive_dashboard: Optional[bool] = None

# ==================== HELPER ====================

async def get_current_user(request: Request) -> Optional[dict]:
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
    
    return await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})

async def get_or_create_settings():
    """Get or create system settings"""
    settings = await db.system_settings.find_one({"settings_id": "system_settings"}, {"_id": 0})
    if not settings:
        default_settings = SystemSettings()
        await db.system_settings.insert_one(default_settings.model_dump())
        return default_settings.model_dump()
    return settings

# ==================== SETTINGS ENDPOINTS ====================

@router.get("/settings")
async def get_settings(request: Request):
    """Get all system settings"""
    user = await get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = await get_or_create_settings()
    return settings

@router.get("/settings/branding")
async def get_branding(request: Request = None):
    """Get branding settings (public for frontend theming)"""
    settings = await get_or_create_settings()
    return settings.get("branding", BrandingSettings().model_dump())

@router.put("/settings/branding")
async def update_branding(request: Request, data: UpdateBrandingRequest):
    """Update branding settings"""
    user = await get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = await get_or_create_settings()
    branding = settings.get("branding", {})
    
    for key, value in data.model_dump().items():
        if value is not None:
            branding[key] = value
    
    await db.system_settings.update_one(
        {"settings_id": "system_settings"},
        {"$set": {
            "branding": branding,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user["user_id"]
        }}
    )
    
    return {"message": "Branding updated", "branding": branding}

@router.put("/settings/integrations")
async def update_integrations(request: Request, data: UpdateIntegrationsRequest):
    """Update integration settings"""
    user = await get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = await get_or_create_settings()
    integrations = settings.get("integrations", {})
    
    for key, value in data.model_dump().items():
        if value is not None:
            integrations[key] = value
    
    # Also update environment-based settings for Google Sheets
    if data.google_sheets_client_id is not None or data.google_sheets_client_secret is not None:
        # Store in separate collection for the OAuth flow to access
        await db.integration_credentials.update_one(
            {"integration": "google_sheets"},
            {"$set": {
                "client_id": integrations.get("google_sheets_client_id", ""),
                "client_secret": integrations.get("google_sheets_client_secret", ""),
                "redirect_uri": integrations.get("google_sheets_redirect_uri", ""),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
    
    await db.system_settings.update_one(
        {"settings_id": "system_settings"},
        {"$set": {
            "integrations": integrations,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user["user_id"]
        }}
    )
    
    return {"message": "Integrations updated"}

@router.put("/settings/modules")
async def update_modules(request: Request, data: UpdateModulesRequest):
    """Update module visibility settings"""
    user = await get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = await get_or_create_settings()
    modules = settings.get("modules", {})
    
    for key, value in data.model_dump().items():
        if value is not None:
            modules[key] = value
    
    await db.system_settings.update_one(
        {"settings_id": "system_settings"},
        {"$set": {
            "modules": modules,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user["user_id"]
        }}
    )
    
    return {"message": "Modules updated", "modules": modules}

@router.put("/settings/time-clock")
async def update_time_clock_settings(request: Request, 
                                      geo_fence_radius_default: Optional[int] = None,
                                      require_photo_clock_in: Optional[bool] = None,
                                      require_photo_clock_out: Optional[bool] = None,
                                      allow_off_site_clock_in: Optional[bool] = None,
                                      lunch_auto_deduct_minutes: Optional[int] = None,
                                      overtime_threshold_daily: Optional[float] = None,
                                      overtime_threshold_weekly: Optional[float] = None):
    """Update time clock specific settings"""
    user = await get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {}
    if geo_fence_radius_default is not None:
        update_data["geo_fence_radius_default"] = geo_fence_radius_default
    if require_photo_clock_in is not None:
        update_data["require_photo_clock_in"] = require_photo_clock_in
    if require_photo_clock_out is not None:
        update_data["require_photo_clock_out"] = require_photo_clock_out
    if allow_off_site_clock_in is not None:
        update_data["allow_off_site_clock_in"] = allow_off_site_clock_in
    if lunch_auto_deduct_minutes is not None:
        update_data["lunch_auto_deduct_minutes"] = lunch_auto_deduct_minutes
    if overtime_threshold_daily is not None:
        update_data["overtime_threshold_daily"] = overtime_threshold_daily
    if overtime_threshold_weekly is not None:
        update_data["overtime_threshold_weekly"] = overtime_threshold_weekly
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = user["user_id"]
    
    await db.system_settings.update_one(
        {"settings_id": "system_settings"},
        {"$set": update_data}
    )
    
    return {"message": "Time clock settings updated"}

# ==================== EXECUTIVE DASHBOARD ENDPOINTS ====================

@router.get("/dashboard/executive")
async def get_executive_dashboard(request: Request):
    """Get executive dashboard KPIs"""
    user = await get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from datetime import timedelta
    
    now = datetime.now(timezone.utc)
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    
    # Staffing Metrics
    total_employees = await db.users.count_documents({"role": "employee"})
    active_today = await db.time_entries.count_documents({
        "clock_in": {"$gte": now.replace(hour=0, minute=0, second=0).isoformat()}
    })
    
    # Recruiting Metrics
    open_positions = await db.job_postings.count_documents({"status": "open"})
    total_applicants = await db.applicants.count_documents({})
    hired_this_month = await db.applicants.count_documents({
        "stage": "hired",
        "updated_at": {"$gte": thirty_days_ago}
    })
    new_applicants_week = await db.applicants.count_documents({
        "created_at": {"$gte": seven_days_ago}
    })
    
    # Calculate fill rate
    filled_positions = await db.job_postings.count_documents({"status": "filled"})
    total_positions = await db.job_postings.count_documents({})
    fill_rate = round((filled_positions / total_positions * 100) if total_positions > 0 else 0, 1)
    
    # Time to fill (average days from job post to hire)
    # This would require more complex aggregation - simplified for now
    
    # Client Metrics
    total_clients = await db.clients.count_documents({"status": "active"})
    open_requests = await db.staffing_requests.count_documents({"status": {"$in": ["pending", "in_progress"]}})
    
    # Revenue Metrics (from invoices)
    pipeline = [
        {"$match": {"status": "paid", "paid_at": {"$gte": thirty_days_ago}}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}}}
    ]
    revenue_result = await db.invoices.aggregate(pipeline).to_list(1)
    revenue_30d = revenue_result[0]["total"] if revenue_result else 0
    
    pending_invoices = await db.invoices.count_documents({"status": {"$in": ["sent", "viewed"]}})
    pending_amount_pipeline = [
        {"$match": {"status": {"$in": ["sent", "viewed"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}}}
    ]
    pending_result = await db.invoices.aggregate(pending_amount_pipeline).to_list(1)
    pending_amount = pending_result[0]["total"] if pending_result else 0
    
    # HR Metrics
    open_incidents = await db.incidents.count_documents({"status": {"$in": ["open", "investigating"]}})
    open_tickets = await db.hr_tickets.count_documents({"status": {"$in": ["open", "in_progress"]}})
    
    # Hours worked
    hours_pipeline = [
        {"$match": {"clock_in": {"$gte": thirty_days_ago}}},
        {"$group": {"_id": None, "total": {"$sum": "$total_hours"}}}
    ]
    hours_result = await db.time_entries.aggregate(hours_pipeline).to_list(1)
    total_hours_30d = round(hours_result[0]["total"], 1) if hours_result else 0
    
    return {
        "staffing": {
            "total_employees": total_employees,
            "active_today": active_today,
            "total_hours_30d": total_hours_30d
        },
        "recruiting": {
            "open_positions": open_positions,
            "total_applicants": total_applicants,
            "hired_this_month": hired_this_month,
            "new_applicants_week": new_applicants_week,
            "fill_rate_percent": fill_rate
        },
        "clients": {
            "total_active": total_clients,
            "open_requests": open_requests
        },
        "financials": {
            "revenue_30d": revenue_30d,
            "pending_invoices": pending_invoices,
            "pending_amount": pending_amount
        },
        "hr": {
            "open_incidents": open_incidents,
            "open_tickets": open_tickets
        },
        "kpis": {
            "fill_rate": fill_rate,
            "employees_per_client": round(total_employees / total_clients, 1) if total_clients > 0 else 0,
            "avg_hours_per_employee": round(total_hours_30d / total_employees, 1) if total_employees > 0 else 0
        }
    }

@router.get("/dashboard/trends")
async def get_dashboard_trends(request: Request, days: int = 30):
    """Get trend data for charts"""
    user = await get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from datetime import timedelta
    
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    
    # Daily hours trend
    hours_by_day = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        pipeline = [
            {"$match": {"clock_in": {"$gte": day_start.isoformat(), "$lt": day_end.isoformat()}}},
            {"$group": {"_id": None, "total": {"$sum": "$total_hours"}}}
        ]
        result = await db.time_entries.aggregate(pipeline).to_list(1)
        hours_by_day.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "hours": round(result[0]["total"], 1) if result else 0
        })
    
    # Weekly applicants trend
    applicants_by_week = []
    for i in range(4):  # Last 4 weeks
        week_start = now - timedelta(days=now.weekday() + 7 * (3 - i))
        week_end = week_start + timedelta(days=7)
        count = await db.applicants.count_documents({
            "created_at": {"$gte": week_start.isoformat(), "$lt": week_end.isoformat()}
        })
        applicants_by_week.append({
            "week": week_start.strftime("%m/%d"),
            "count": count
        })
    
    return {
        "hours_trend": hours_by_day,
        "applicants_trend": applicants_by_week
    }
