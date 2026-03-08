# ATS (Applicant Tracking System) Module
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import os

router = APIRouter(prefix="/api/ats", tags=["ATS"])

# Get database from environment
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

# ==================== MODELS ====================

class JobPosting(BaseModel):
    job_id: str = Field(default_factory=lambda: f"job_{uuid.uuid4().hex[:10]}")
    title: str
    department: str = ""
    location: str
    site_id: Optional[str] = None
    client_id: Optional[str] = None
    employment_type: str = "full_time"  # full_time, part_time, contract, temp
    shift: str = ""  # day, night, swing, rotating
    pay_rate_min: Optional[float] = None
    pay_rate_max: Optional[float] = None
    pay_type: str = "hourly"  # hourly, salary
    description: str
    requirements: List[str] = []
    benefits: List[str] = []
    positions_available: int = 1
    positions_filled: int = 0
    status: str = "draft"  # draft, open, paused, closed, filled
    posted_to: List[str] = []  # indeed, google, internal
    indeed_job_key: Optional[str] = None
    google_job_id: Optional[str] = None
    created_by: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Applicant(BaseModel):
    applicant_id: str = Field(default_factory=lambda: f"app_{uuid.uuid4().hex[:10]}")
    job_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    resume_url: Optional[str] = None
    source: str = "direct"  # direct, indeed, google, referral
    referral_source: Optional[str] = None
    stage: str = "new"  # new, screening, interview, offer, hired, rejected
    stage_history: List[Dict] = []
    notes: List[Dict] = []
    rating: Optional[int] = None  # 1-5 stars
    background_check_status: Optional[str] = None  # pending, passed, failed
    background_check_id: Optional[str] = None
    offer_sent: bool = False
    offer_accepted: bool = False
    start_date: Optional[datetime] = None
    assigned_recruiter: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OfferLetter(BaseModel):
    offer_id: str = Field(default_factory=lambda: f"offer_{uuid.uuid4().hex[:10]}")
    applicant_id: str
    job_id: str
    position_title: str
    start_date: datetime
    pay_rate: float
    pay_type: str = "hourly"
    schedule: str = ""
    location: str = ""
    manager_name: str = ""
    benefits_summary: str = ""
    status: str = "draft"  # draft, sent, viewed, accepted, declined, expired
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    signature_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OnboardingChecklist(BaseModel):
    checklist_id: str = Field(default_factory=lambda: f"onb_{uuid.uuid4().hex[:10]}")
    applicant_id: str
    employee_id: Optional[str] = None  # After conversion to employee
    items: List[Dict] = []  # [{name, completed, completed_at, required}]
    status: str = "pending"  # pending, in_progress, completed
    start_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== REQUEST MODELS ====================

class CreateJobRequest(BaseModel):
    title: str
    location: str
    site_id: Optional[str] = None
    client_id: Optional[str] = None
    department: str = ""
    employment_type: str = "full_time"
    shift: str = ""
    pay_rate_min: Optional[float] = None
    pay_rate_max: Optional[float] = None
    pay_type: str = "hourly"
    description: str
    requirements: List[str] = []
    benefits: List[str] = []
    positions_available: int = 1

class CreateApplicantRequest(BaseModel):
    job_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    source: str = "direct"
    referral_source: Optional[str] = None

class UpdateStageRequest(BaseModel):
    stage: str
    notes: Optional[str] = None

class CreateOfferRequest(BaseModel):
    applicant_id: str
    start_date: str
    pay_rate: float
    pay_type: str = "hourly"
    schedule: str = ""
    benefits_summary: str = ""

# ==================== HELPER FUNCTIONS ====================

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
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    return user

# Default onboarding items
DEFAULT_ONBOARDING_ITEMS = [
    {"name": "Complete I-9 Form", "required": True, "completed": False},
    {"name": "Complete W-4 Form", "required": True, "completed": False},
    {"name": "Submit Direct Deposit Information", "required": True, "completed": False},
    {"name": "Sign Employee Handbook Acknowledgment", "required": True, "completed": False},
    {"name": "Complete Background Check", "required": True, "completed": False},
    {"name": "Attend Orientation", "required": True, "completed": False},
    {"name": "Complete Safety Training", "required": True, "completed": False},
    {"name": "Receive Uniform/Equipment", "required": False, "completed": False},
    {"name": "Meet with Supervisor", "required": True, "completed": False},
    {"name": "Complete E-Verify", "required": True, "completed": False}
]

# ==================== JOB POSTING ENDPOINTS ====================

@router.get("/jobs")
async def list_jobs(request: Request, status: Optional[str] = None, client_id: Optional[str] = None):
    """List all job postings"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {}
    if status:
        query["status"] = status
    if client_id:
        query["client_id"] = client_id
    
    jobs = await db.job_postings.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Enrich with applicant counts
    for job in jobs:
        job["applicant_count"] = await db.applicants.count_documents({"job_id": job["job_id"]})
        job["new_applicants"] = await db.applicants.count_documents({"job_id": job["job_id"], "stage": "new"})
    
    return jobs

@router.post("/jobs")
async def create_job(request: Request, data: CreateJobRequest):
    """Create a new job posting"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    job = JobPosting(
        title=data.title,
        location=data.location,
        site_id=data.site_id,
        client_id=data.client_id,
        department=data.department,
        employment_type=data.employment_type,
        shift=data.shift,
        pay_rate_min=data.pay_rate_min,
        pay_rate_max=data.pay_rate_max,
        pay_type=data.pay_type,
        description=data.description,
        requirements=data.requirements,
        benefits=data.benefits,
        positions_available=data.positions_available,
        created_by=user["user_id"]
    )
    
    await db.job_postings.insert_one(job.model_dump())
    return job.model_dump()

@router.get("/jobs/{job_id}")
async def get_job(job_id: str, request: Request):
    """Get job posting details"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    job = await db.job_postings.find_one({"job_id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get applicants
    applicants = await db.applicants.find({"job_id": job_id}, {"_id": 0}).to_list(500)
    
    # Get client info if applicable
    client = None
    if job.get("client_id"):
        client = await db.clients.find_one({"client_id": job["client_id"]}, {"_id": 0})
    
    return {
        "job": job,
        "applicants": applicants,
        "client": client,
        "stats": {
            "total_applicants": len(applicants),
            "by_stage": {
                "new": len([a for a in applicants if a["stage"] == "new"]),
                "screening": len([a for a in applicants if a["stage"] == "screening"]),
                "interview": len([a for a in applicants if a["stage"] == "interview"]),
                "offer": len([a for a in applicants if a["stage"] == "offer"]),
                "hired": len([a for a in applicants if a["stage"] == "hired"]),
                "rejected": len([a for a in applicants if a["stage"] == "rejected"])
            }
        }
    }

@router.put("/jobs/{job_id}")
async def update_job(job_id: str, request: Request, data: CreateJobRequest):
    """Update a job posting"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.job_postings.update_one({"job_id": job_id}, {"$set": update_data})
    return await db.job_postings.find_one({"job_id": job_id}, {"_id": 0})

@router.post("/jobs/{job_id}/publish")
async def publish_job(job_id: str, request: Request, platforms: List[str] = ["internal"]):
    """Publish job to platforms (internal, indeed, google)"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    job = await db.job_postings.find_one({"job_id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    posted_to = job.get("posted_to", [])
    
    # TODO: Integrate with Indeed API when credentials provided
    # TODO: Integrate with Google Jobs API
    
    for platform in platforms:
        if platform not in posted_to:
            posted_to.append(platform)
    
    await db.job_postings.update_one(
        {"job_id": job_id},
        {"$set": {
            "status": "open",
            "posted_to": posted_to,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": f"Job published to {', '.join(platforms)}", "posted_to": posted_to}

@router.post("/jobs/{job_id}/close")
async def close_job(job_id: str, request: Request, reason: str = "filled"):
    """Close a job posting"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    status = "filled" if reason == "filled" else "closed"
    
    await db.job_postings.update_one(
        {"job_id": job_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Job {status}"}

# ==================== APPLICANT ENDPOINTS ====================

@router.get("/applicants")
async def list_applicants(request: Request, job_id: Optional[str] = None, stage: Optional[str] = None):
    """List all applicants"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {}
    if job_id:
        query["job_id"] = job_id
    if stage:
        query["stage"] = stage
    
    applicants = await db.applicants.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Enrich with job info
    for app in applicants:
        job = await db.job_postings.find_one({"job_id": app["job_id"]}, {"_id": 0, "title": 1, "location": 1})
        app["job_title"] = job.get("title") if job else "Unknown"
        app["job_location"] = job.get("location") if job else ""
    
    return applicants

@router.post("/applicants")
async def create_applicant(request: Request, data: CreateApplicantRequest):
    """Create a new applicant (can be called publicly for job applications)"""
    # Check if job exists and is open
    job = await db.job_postings.find_one({"job_id": data.job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("status") != "open":
        raise HTTPException(status_code=400, detail="Job is not accepting applications")
    
    # Check for duplicate application
    existing = await db.applicants.find_one({
        "job_id": data.job_id,
        "email": data.email
    }, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Application already submitted for this position")
    
    applicant = Applicant(
        job_id=data.job_id,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        address=data.address,
        city=data.city,
        state=data.state,
        zip_code=data.zip_code,
        source=data.source,
        referral_source=data.referral_source,
        stage_history=[{
            "stage": "new",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "by": "system"
        }]
    )
    
    await db.applicants.insert_one(applicant.model_dump())
    return applicant.model_dump()

@router.get("/applicants/{applicant_id}")
async def get_applicant(applicant_id: str, request: Request):
    """Get applicant details"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    applicant = await db.applicants.find_one({"applicant_id": applicant_id}, {"_id": 0})
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    
    # Get job info
    job = await db.job_postings.find_one({"job_id": applicant["job_id"]}, {"_id": 0})
    
    # Get offer if any
    offer = await db.offer_letters.find_one({"applicant_id": applicant_id}, {"_id": 0})
    
    # Get onboarding checklist if any
    checklist = await db.onboarding_checklists.find_one({"applicant_id": applicant_id}, {"_id": 0})
    
    return {
        "applicant": applicant,
        "job": job,
        "offer": offer,
        "onboarding": checklist
    }

@router.post("/applicants/{applicant_id}/stage")
async def update_applicant_stage(applicant_id: str, request: Request, data: UpdateStageRequest):
    """Update applicant stage"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    applicant = await db.applicants.find_one({"applicant_id": applicant_id}, {"_id": 0})
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    
    stage_entry = {
        "stage": data.stage,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "by": user["user_id"],
        "by_name": user.get("name"),
        "notes": data.notes
    }
    
    update_data = {
        "stage": data.stage,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.applicants.update_one(
        {"applicant_id": applicant_id},
        {
            "$set": update_data,
            "$push": {"stage_history": stage_entry}
        }
    )
    
    # If hired, create onboarding checklist
    if data.stage == "hired":
        checklist = OnboardingChecklist(
            applicant_id=applicant_id,
            items=DEFAULT_ONBOARDING_ITEMS.copy(),
            status="pending"
        )
        await db.onboarding_checklists.insert_one(checklist.model_dump())
    
    return {"message": f"Stage updated to {data.stage}"}

@router.post("/applicants/{applicant_id}/notes")
async def add_applicant_note(applicant_id: str, request: Request, note: str):
    """Add a note to applicant"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    note_entry = {
        "note": note,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "by": user["user_id"],
        "by_name": user.get("name")
    }
    
    await db.applicants.update_one(
        {"applicant_id": applicant_id},
        {"$push": {"notes": note_entry}}
    )
    
    return {"message": "Note added"}

@router.post("/applicants/{applicant_id}/rating")
async def rate_applicant(applicant_id: str, request: Request, rating: int):
    """Rate an applicant (1-5 stars)"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    
    await db.applicants.update_one(
        {"applicant_id": applicant_id},
        {"$set": {"rating": rating, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Rating set to {rating}"}

# ==================== OFFER LETTER ENDPOINTS ====================

@router.post("/offers")
async def create_offer(request: Request, data: CreateOfferRequest):
    """Create an offer letter"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    applicant = await db.applicants.find_one({"applicant_id": data.applicant_id}, {"_id": 0})
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    
    job = await db.job_postings.find_one({"job_id": applicant["job_id"]}, {"_id": 0})
    
    # Get site/location info
    location = job.get("location", "") if job else ""
    if job and job.get("site_id"):
        site = await db.work_sites.find_one({"site_id": job["site_id"]}, {"_id": 0})
        if site:
            location = f"{site.get('name')} - {site.get('address', '')}"
    
    offer = OfferLetter(
        applicant_id=data.applicant_id,
        job_id=applicant["job_id"],
        position_title=job.get("title", "Position") if job else "Position",
        start_date=datetime.fromisoformat(data.start_date.replace('Z', '+00:00')),
        pay_rate=data.pay_rate,
        pay_type=data.pay_type,
        schedule=data.schedule,
        location=location,
        manager_name=user.get("name", ""),
        benefits_summary=data.benefits_summary
    )
    
    await db.offer_letters.insert_one(offer.model_dump())
    
    # Update applicant stage to offer
    await db.applicants.update_one(
        {"applicant_id": data.applicant_id},
        {
            "$set": {"stage": "offer", "offer_sent": False, "updated_at": datetime.now(timezone.utc).isoformat()},
            "$push": {"stage_history": {
                "stage": "offer",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "by": user["user_id"],
                "notes": "Offer letter created"
            }}
        }
    )
    
    return offer.model_dump()

@router.post("/offers/{offer_id}/send")
async def send_offer(offer_id: str, request: Request):
    """Mark offer as sent (email integration pending)"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    offer = await db.offer_letters.find_one({"offer_id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    await db.offer_letters.update_one(
        {"offer_id": offer_id},
        {"$set": {"status": "sent", "sent_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await db.applicants.update_one(
        {"applicant_id": offer["applicant_id"]},
        {"$set": {"offer_sent": True}}
    )
    
    # TODO: Send actual email when email service configured
    
    return {"message": "Offer marked as sent"}

@router.get("/offers/{offer_id}")
async def get_offer(offer_id: str, request: Request):
    """Get offer letter details"""
    offer = await db.offer_letters.find_one({"offer_id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    applicant = await db.applicants.find_one({"applicant_id": offer["applicant_id"]}, {"_id": 0})
    
    return {
        "offer": offer,
        "applicant": applicant
    }

@router.post("/offers/{offer_id}/respond")
async def respond_to_offer(offer_id: str, accepted: bool, signature: Optional[str] = None):
    """Applicant responds to offer (public endpoint with token)"""
    offer = await db.offer_letters.find_one({"offer_id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    status = "accepted" if accepted else "declined"
    
    update_data = {
        "status": status,
        "responded_at": datetime.now(timezone.utc).isoformat()
    }
    if signature:
        update_data["signature_url"] = signature
    
    await db.offer_letters.update_one({"offer_id": offer_id}, {"$set": update_data})
    
    # Update applicant
    if accepted:
        await db.applicants.update_one(
            {"applicant_id": offer["applicant_id"]},
            {
                "$set": {
                    "offer_accepted": True,
                    "start_date": offer.get("start_date"),
                    "stage": "hired",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                "$push": {"stage_history": {
                    "stage": "hired",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "by": "applicant",
                    "notes": "Offer accepted"
                }}
            }
        )
        
        # Create onboarding checklist
        checklist = OnboardingChecklist(
            applicant_id=offer["applicant_id"],
            items=DEFAULT_ONBOARDING_ITEMS.copy(),
            status="pending",
            start_date=offer.get("start_date")
        )
        await db.onboarding_checklists.insert_one(checklist.model_dump())
    
    return {"message": f"Offer {status}"}

# ==================== ONBOARDING ENDPOINTS ====================

@router.get("/onboarding/{applicant_id}")
async def get_onboarding(applicant_id: str, request: Request):
    """Get onboarding checklist"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    checklist = await db.onboarding_checklists.find_one({"applicant_id": applicant_id}, {"_id": 0})
    if not checklist:
        raise HTTPException(status_code=404, detail="Onboarding checklist not found")
    
    applicant = await db.applicants.find_one({"applicant_id": applicant_id}, {"_id": 0})
    
    return {
        "checklist": checklist,
        "applicant": applicant
    }

@router.post("/onboarding/{checklist_id}/item")
async def update_onboarding_item(checklist_id: str, request: Request, item_name: str, completed: bool):
    """Update an onboarding item"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    checklist = await db.onboarding_checklists.find_one({"checklist_id": checklist_id}, {"_id": 0})
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    # Update the specific item
    items = checklist.get("items", [])
    for item in items:
        if item["name"] == item_name:
            item["completed"] = completed
            if completed:
                item["completed_at"] = datetime.now(timezone.utc).isoformat()
                item["completed_by"] = user["user_id"]
            break
    
    # Check if all required items are complete
    all_required_complete = all(
        item.get("completed", False) 
        for item in items 
        if item.get("required", False)
    )
    
    status = "completed" if all_required_complete else "in_progress"
    
    update_data = {"items": items, "status": status}
    if status == "completed":
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.onboarding_checklists.update_one(
        {"checklist_id": checklist_id},
        {"$set": update_data}
    )
    
    return {"message": f"Item '{item_name}' updated", "status": status}

# ==================== PIPELINE STATS ====================

@router.get("/pipeline/stats")
async def get_pipeline_stats(request: Request):
    """Get ATS pipeline statistics"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Job stats
    total_jobs = await db.job_postings.count_documents({})
    open_jobs = await db.job_postings.count_documents({"status": "open"})
    
    # Applicant stats
    total_applicants = await db.applicants.count_documents({})
    new_applicants = await db.applicants.count_documents({"stage": "new"})
    in_screening = await db.applicants.count_documents({"stage": "screening"})
    in_interview = await db.applicants.count_documents({"stage": "interview"})
    offers_pending = await db.applicants.count_documents({"stage": "offer"})
    hired = await db.applicants.count_documents({"stage": "hired"})
    
    # Recent activity (last 7 days)
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    new_this_week = await db.applicants.count_documents({"created_at": {"$gte": week_ago}})
    hired_this_week = await db.applicants.count_documents({
        "stage": "hired",
        "updated_at": {"$gte": week_ago}
    })
    
    return {
        "jobs": {
            "total": total_jobs,
            "open": open_jobs,
            "closed": total_jobs - open_jobs
        },
        "pipeline": {
            "new": new_applicants,
            "screening": in_screening,
            "interview": in_interview,
            "offer": offers_pending,
            "hired": hired,
            "total": total_applicants
        },
        "this_week": {
            "new_applicants": new_this_week,
            "hired": hired_this_week
        },
        "conversion_rate": round((hired / total_applicants * 100) if total_applicants > 0 else 0, 1)
    }
