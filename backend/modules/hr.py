# HR Module - Employee Management, Incidents, Reviews, Feedback
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import os

router = APIRouter(prefix="/api/hr", tags=["HR"])

# Get database
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

# ==================== MODELS ====================

class IncidentReport(BaseModel):
    incident_id: str = Field(default_factory=lambda: f"inc_{uuid.uuid4().hex[:10]}")
    employee_id: str
    site_id: Optional[str] = None
    type: str  # safety, conduct, attendance, injury, property, other
    severity: str = "medium"  # low, medium, high, critical
    title: str
    description: str
    date_occurred: datetime
    witnesses: List[str] = []
    action_taken: str = ""
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    status: str = "open"  # open, investigating, resolved, closed
    reported_by: str
    attachments: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None

class PerformanceReview(BaseModel):
    review_id: str = Field(default_factory=lambda: f"rev_{uuid.uuid4().hex[:10]}")
    employee_id: str
    reviewer_id: str
    review_period_start: datetime
    review_period_end: datetime
    type: str = "annual"  # annual, quarterly, probationary, promotion
    ratings: Dict = {}  # {category: score}
    overall_rating: Optional[float] = None
    strengths: List[str] = []
    areas_for_improvement: List[str] = []
    goals: List[Dict] = []  # [{goal, target_date, status}]
    comments: str = ""
    employee_comments: str = ""
    status: str = "draft"  # draft, pending_review, completed, acknowledged
    scheduled_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EmployeeFeedback(BaseModel):
    feedback_id: str = Field(default_factory=lambda: f"fb_{uuid.uuid4().hex[:10]}")
    employee_id: Optional[str] = None  # None for anonymous
    anonymous: bool = False
    category: str  # workplace, management, benefits, safety, suggestion, other
    subject: str
    message: str
    rating: Optional[int] = None  # 1-5 satisfaction rating
    status: str = "new"  # new, reviewed, in_progress, resolved
    response: Optional[str] = None
    responded_by: Optional[str] = None
    responded_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HRTicket(BaseModel):
    ticket_id: str = Field(default_factory=lambda: f"tkt_{uuid.uuid4().hex[:10]}")
    employee_id: str
    category: str  # payroll, benefits, time_off, policy, complaint, other
    subject: str
    description: str
    priority: str = "normal"  # low, normal, high, urgent
    status: str = "open"  # open, in_progress, pending_info, resolved, closed
    assigned_to: Optional[str] = None
    messages: List[Dict] = []
    resolution: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None

class EmployeeDocument(BaseModel):
    document_id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:10]}")
    employee_id: str
    type: str  # id, w4, i9, contract, certification, policy_ack, other
    name: str
    file_url: Optional[str] = None
    expiration_date: Optional[datetime] = None
    status: str = "active"  # active, expired, pending
    uploaded_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== REQUEST MODELS ====================

class CreateIncidentRequest(BaseModel):
    employee_id: str
    site_id: Optional[str] = None
    type: str
    severity: str = "medium"
    title: str
    description: str
    date_occurred: str
    witnesses: List[str] = []
    action_taken: str = ""

class CreateReviewRequest(BaseModel):
    employee_id: str
    review_period_start: str
    review_period_end: str
    type: str = "annual"
    scheduled_date: Optional[str] = None

class CreateFeedbackRequest(BaseModel):
    anonymous: bool = False
    category: str
    subject: str
    message: str
    rating: Optional[int] = None

class CreateTicketRequest(BaseModel):
    category: str
    subject: str
    description: str
    priority: str = "normal"

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

# ==================== INCIDENT ENDPOINTS ====================

@router.get("/incidents")
async def list_incidents(request: Request, status: Optional[str] = None, employee_id: Optional[str] = None):
    """List incident reports"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {}
    if user.get("role") == "employee":
        query["employee_id"] = user["user_id"]
    elif employee_id:
        query["employee_id"] = employee_id
    if status:
        query["status"] = status
    
    incidents = await db.incidents.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    for inc in incidents:
        emp = await db.users.find_one({"user_id": inc["employee_id"]}, {"_id": 0, "name": 1})
        inc["employee_name"] = emp.get("name") if emp else "Unknown"
    
    return incidents

@router.post("/incidents")
async def create_incident(request: Request, data: CreateIncidentRequest):
    """Create incident report"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    incident = IncidentReport(
        employee_id=data.employee_id,
        site_id=data.site_id,
        type=data.type,
        severity=data.severity,
        title=data.title,
        description=data.description,
        date_occurred=datetime.fromisoformat(data.date_occurred.replace('Z', '+00:00')),
        witnesses=data.witnesses,
        action_taken=data.action_taken,
        reported_by=user["user_id"]
    )
    
    await db.incidents.insert_one(incident.model_dump())
    return incident.model_dump()

@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str, request: Request):
    """Get incident details"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    incident = await db.incidents.find_one({"incident_id": incident_id}, {"_id": 0})
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    employee = await db.users.find_one({"user_id": incident["employee_id"]}, {"_id": 0})
    reporter = await db.users.find_one({"user_id": incident["reported_by"]}, {"_id": 0})
    
    return {
        "incident": incident,
        "employee": employee,
        "reporter": reporter
    }

@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str, request: Request, resolution: str):
    """Resolve incident"""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.incidents.update_one(
        {"incident_id": incident_id},
        {"$set": {
            "status": "resolved",
            "action_taken": resolution,
            "resolved_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Incident resolved"}

# ==================== REVIEW ENDPOINTS ====================

@router.get("/reviews")
async def list_reviews(request: Request, employee_id: Optional[str] = None, status: Optional[str] = None):
    """List performance reviews"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {}
    if user.get("role") == "employee":
        query["employee_id"] = user["user_id"]
    elif employee_id:
        query["employee_id"] = employee_id
    if status:
        query["status"] = status
    
    reviews = await db.reviews.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    for rev in reviews:
        emp = await db.users.find_one({"user_id": rev["employee_id"]}, {"_id": 0, "name": 1})
        rev["employee_name"] = emp.get("name") if emp else "Unknown"
    
    return reviews

@router.post("/reviews")
async def create_review(request: Request, data: CreateReviewRequest):
    """Create performance review"""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    scheduled = None
    if data.scheduled_date:
        scheduled = datetime.fromisoformat(data.scheduled_date.replace('Z', '+00:00'))
    
    review = PerformanceReview(
        employee_id=data.employee_id,
        reviewer_id=user["user_id"],
        review_period_start=datetime.fromisoformat(data.review_period_start.replace('Z', '+00:00')),
        review_period_end=datetime.fromisoformat(data.review_period_end.replace('Z', '+00:00')),
        type=data.type,
        scheduled_date=scheduled
    )
    
    await db.reviews.insert_one(review.model_dump())
    return review.model_dump()

@router.put("/reviews/{review_id}")
async def update_review(review_id: str, request: Request, ratings: Dict = None, 
                        strengths: List[str] = None, areas_for_improvement: List[str] = None,
                        goals: List[Dict] = None, comments: str = None, overall_rating: float = None):
    """Update review ratings and comments"""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {}
    if ratings is not None:
        update_data["ratings"] = ratings
    if strengths is not None:
        update_data["strengths"] = strengths
    if areas_for_improvement is not None:
        update_data["areas_for_improvement"] = areas_for_improvement
    if goals is not None:
        update_data["goals"] = goals
    if comments is not None:
        update_data["comments"] = comments
    if overall_rating is not None:
        update_data["overall_rating"] = overall_rating
    
    await db.reviews.update_one({"review_id": review_id}, {"$set": update_data})
    return await db.reviews.find_one({"review_id": review_id}, {"_id": 0})

@router.post("/reviews/{review_id}/complete")
async def complete_review(review_id: str, request: Request):
    """Mark review as completed"""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.reviews.update_one(
        {"review_id": review_id},
        {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Review completed"}

@router.post("/reviews/{review_id}/acknowledge")
async def acknowledge_review(review_id: str, request: Request, employee_comments: str = ""):
    """Employee acknowledges review"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    review = await db.reviews.find_one({"review_id": review_id}, {"_id": 0})
    if not review or review["employee_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.reviews.update_one(
        {"review_id": review_id},
        {"$set": {
            "status": "acknowledged",
            "employee_comments": employee_comments,
            "acknowledged_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Review acknowledged"}

# ==================== FEEDBACK ENDPOINTS ====================

@router.get("/feedback")
async def list_feedback(request: Request, status: Optional[str] = None, category: Optional[str] = None):
    """List employee feedback"""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = {}
    if status:
        query["status"] = status
    if category:
        query["category"] = category
    
    feedback = await db.feedback.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return feedback

@router.post("/feedback")
async def submit_feedback(request: Request, data: CreateFeedbackRequest):
    """Submit employee feedback"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    feedback = EmployeeFeedback(
        employee_id=None if data.anonymous else user["user_id"],
        anonymous=data.anonymous,
        category=data.category,
        subject=data.subject,
        message=data.message,
        rating=data.rating
    )
    
    await db.feedback.insert_one(feedback.model_dump())
    return {"message": "Feedback submitted", "feedback_id": feedback.feedback_id}

@router.post("/feedback/{feedback_id}/respond")
async def respond_to_feedback(feedback_id: str, request: Request, response: str):
    """Respond to feedback"""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.feedback.update_one(
        {"feedback_id": feedback_id},
        {"$set": {
            "status": "resolved",
            "response": response,
            "responded_by": user["user_id"],
            "responded_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Response recorded"}

# ==================== HR TICKET ENDPOINTS ====================

@router.get("/tickets")
async def list_tickets(request: Request, status: Optional[str] = None):
    """List HR tickets"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {}
    if user.get("role") == "employee":
        query["employee_id"] = user["user_id"]
    if status:
        query["status"] = status
    
    tickets = await db.hr_tickets.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    for tkt in tickets:
        emp = await db.users.find_one({"user_id": tkt["employee_id"]}, {"_id": 0, "name": 1})
        tkt["employee_name"] = emp.get("name") if emp else "Unknown"
    
    return tickets

@router.post("/tickets")
async def create_ticket(request: Request, data: CreateTicketRequest):
    """Create HR ticket"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    ticket = HRTicket(
        employee_id=user["user_id"],
        category=data.category,
        subject=data.subject,
        description=data.description,
        priority=data.priority,
        messages=[{
            "from": user["user_id"],
            "from_name": user.get("name"),
            "message": data.description,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]
    )
    
    await db.hr_tickets.insert_one(ticket.model_dump())
    return ticket.model_dump()

@router.post("/tickets/{ticket_id}/message")
async def add_ticket_message(ticket_id: str, request: Request, message: str):
    """Add message to ticket"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    msg = {
        "from": user["user_id"],
        "from_name": user.get("name"),
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.hr_tickets.update_one(
        {"ticket_id": ticket_id},
        {"$push": {"messages": msg}, "$set": {"status": "in_progress"}}
    )
    return {"message": "Message added"}

@router.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(ticket_id: str, request: Request, resolution: str):
    """Resolve HR ticket"""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.hr_tickets.update_one(
        {"ticket_id": ticket_id},
        {"$set": {
            "status": "resolved",
            "resolution": resolution,
            "resolved_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Ticket resolved"}

# ==================== EMPLOYEE PROFILE ENDPOINTS ====================

@router.get("/employees/{employee_id}/profile")
async def get_employee_profile(employee_id: str, request: Request):
    """Get complete employee profile"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Only admin/manager can view other profiles
    if user.get("role") == "employee" and user["user_id"] != employee_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    employee = await db.users.find_one({"user_id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get related data
    documents = await db.employee_documents.find({"employee_id": employee_id}, {"_id": 0}).to_list(50)
    incidents = await db.incidents.find({"employee_id": employee_id}, {"_id": 0}).to_list(20)
    reviews = await db.reviews.find({"employee_id": employee_id}, {"_id": 0}).sort("created_at", -1).to_list(10)
    tickets = await db.hr_tickets.find({"employee_id": employee_id}, {"_id": 0}).to_list(20)
    
    # Get time summary (last 30 days)
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    time_entries = await db.time_entries.find({
        "user_id": employee_id,
        "clock_in": {"$gte": thirty_days_ago}
    }, {"_id": 0}).to_list(100)
    
    total_hours = sum(e.get("total_hours", 0) or 0 for e in time_entries)
    
    return {
        "employee": employee,
        "documents": documents,
        "incidents": incidents,
        "reviews": reviews,
        "tickets": tickets,
        "time_summary": {
            "last_30_days_hours": round(total_hours, 2),
            "entries_count": len(time_entries)
        }
    }

@router.get("/dashboard/stats")
async def get_hr_dashboard_stats(request: Request):
    """Get HR dashboard statistics"""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Employee counts
    total_employees = await db.users.count_documents({"role": "employee"})
    
    # Open incidents
    open_incidents = await db.incidents.count_documents({"status": {"$in": ["open", "investigating"]}})
    
    # Pending reviews
    pending_reviews = await db.reviews.count_documents({"status": {"$in": ["draft", "pending_review"]}})
    
    # Open tickets
    open_tickets = await db.hr_tickets.count_documents({"status": {"$in": ["open", "in_progress"]}})
    
    # New feedback
    new_feedback = await db.feedback.count_documents({"status": "new"})
    
    # Recent hires (last 30 days)
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    new_hires = await db.applicants.count_documents({
        "stage": "hired",
        "updated_at": {"$gte": thirty_days_ago}
    })
    
    return {
        "employees": {
            "total": total_employees,
            "new_hires_30d": new_hires
        },
        "incidents": {
            "open": open_incidents
        },
        "reviews": {
            "pending": pending_reviews
        },
        "tickets": {
            "open": open_tickets
        },
        "feedback": {
            "new": new_feedback
        }
    }
