# Client Portal Module
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import os

router = APIRouter(prefix="/api/clients", tags=["Clients"])

# Get database
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

# ==================== MODELS ====================

class Client(BaseModel):
    client_id: str = Field(default_factory=lambda: f"client_{uuid.uuid4().hex[:10]}")
    company_name: str
    contact_name: str
    contact_email: str
    contact_phone: str
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    industry: str = ""
    billing_email: Optional[str] = None
    billing_address: Optional[str] = None
    payment_terms: str = "net_30"  # net_15, net_30, net_45, net_60
    markup_rate: float = 0.0  # Percentage markup on labor
    status: str = "active"  # active, inactive, prospect
    assigned_sites: List[str] = []
    notes: str = ""
    portal_access: bool = False
    portal_user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StaffingRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:10]}")
    client_id: str
    site_id: Optional[str] = None
    title: str
    description: str
    positions_needed: int = 1
    shift: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    pay_rate: Optional[float] = None
    requirements: List[str] = []
    status: str = "pending"  # pending, approved, in_progress, fulfilled, cancelled
    priority: str = "normal"  # low, normal, high, urgent
    assigned_recruiter: Optional[str] = None
    job_id: Optional[str] = None  # Linked job posting
    notes: List[Dict] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Invoice(BaseModel):
    invoice_id: str = Field(default_factory=lambda: f"inv_{uuid.uuid4().hex[:10]}")
    invoice_number: str = ""
    client_id: str
    period_start: datetime
    period_end: datetime
    line_items: List[Dict] = []  # [{description, quantity, rate, amount}]
    subtotal: float = 0
    tax_rate: float = 0
    tax_amount: float = 0
    total: float = 0
    status: str = "draft"  # draft, sent, viewed, paid, overdue
    due_date: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClientEngagement(BaseModel):
    engagement_id: str = Field(default_factory=lambda: f"eng_{uuid.uuid4().hex[:10]}")
    client_id: str
    type: str  # call, meeting, email, site_visit
    subject: str
    description: str
    date: datetime
    outcome: str = ""
    follow_up_date: Optional[datetime] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== REQUEST MODELS ====================

class CreateClientRequest(BaseModel):
    company_name: str
    contact_name: str
    contact_email: str
    contact_phone: str
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    industry: str = ""
    billing_email: Optional[str] = None
    payment_terms: str = "net_30"
    markup_rate: float = 0.0
    notes: str = ""

class CreateStaffingRequestModel(BaseModel):
    client_id: str
    site_id: Optional[str] = None
    title: str
    description: str
    positions_needed: int = 1
    shift: str = ""
    start_date: Optional[str] = None
    pay_rate: Optional[float] = None
    requirements: List[str] = []
    priority: str = "normal"

class CreateInvoiceRequest(BaseModel):
    client_id: str
    period_start: str
    period_end: str
    line_items: List[Dict]
    tax_rate: float = 0
    notes: str = ""

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

async def generate_invoice_number():
    """Generate sequential invoice number"""
    year = datetime.now().year
    count = await db.invoices.count_documents({"invoice_number": {"$regex": f"^INV-{year}"}})
    return f"INV-{year}-{str(count + 1).zfill(5)}"

# ==================== CLIENT ENDPOINTS ====================

@router.get("/")
async def list_clients(request: Request, status: Optional[str] = None):
    """List all clients"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {}
    if status:
        query["status"] = status
    
    clients = await db.clients.find(query, {"_id": 0}).sort("company_name", 1).to_list(500)
    
    # Add stats
    for c in clients:
        c["active_employees"] = await db.users.count_documents({
            "assigned_sites": {"$in": c.get("assigned_sites", [])}
        })
        c["open_requests"] = await db.staffing_requests.count_documents({
            "client_id": c["client_id"],
            "status": {"$in": ["pending", "in_progress"]}
        })
    
    return clients

@router.post("/")
async def create_client(request: Request, data: CreateClientRequest):
    """Create a new client"""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    client_obj = Client(**data.model_dump())
    await db.clients.insert_one(client_obj.model_dump())
    return client_obj.model_dump()

@router.get("/{client_id}")
async def get_client(client_id: str, request: Request):
    """Get client details"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    client_data = await db.clients.find_one({"client_id": client_id}, {"_id": 0})
    if not client_data:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get related data
    sites = await db.work_sites.find({"site_id": {"$in": client_data.get("assigned_sites", [])}}, {"_id": 0}).to_list(100)
    requests = await db.staffing_requests.find({"client_id": client_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    invoices = await db.invoices.find({"client_id": client_id}, {"_id": 0}).sort("created_at", -1).to_list(20)
    engagements = await db.client_engagements.find({"client_id": client_id}, {"_id": 0}).sort("date", -1).to_list(20)
    
    return {
        "client": client_data,
        "sites": sites,
        "staffing_requests": requests,
        "invoices": invoices,
        "engagements": engagements
    }

@router.put("/{client_id}")
async def update_client(client_id: str, request: Request, data: CreateClientRequest):
    """Update client"""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.clients.update_one({"client_id": client_id}, {"$set": data.model_dump()})
    return await db.clients.find_one({"client_id": client_id}, {"_id": 0})

# ==================== STAFFING REQUEST ENDPOINTS ====================

@router.get("/requests/all")
async def list_staffing_requests(request: Request, status: Optional[str] = None, client_id: Optional[str] = None):
    """List staffing requests"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {}
    if status:
        query["status"] = status
    if client_id:
        query["client_id"] = client_id
    
    requests = await db.staffing_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    for req in requests:
        client_data = await db.clients.find_one({"client_id": req["client_id"]}, {"_id": 0, "company_name": 1})
        req["client_name"] = client_data.get("company_name") if client_data else "Unknown"
    
    return requests

@router.post("/requests")
async def create_staffing_request(request: Request, data: CreateStaffingRequestModel):
    """Create staffing request"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    start_date = None
    if data.start_date:
        start_date = datetime.fromisoformat(data.start_date.replace('Z', '+00:00'))
    
    req = StaffingRequest(
        client_id=data.client_id,
        site_id=data.site_id,
        title=data.title,
        description=data.description,
        positions_needed=data.positions_needed,
        shift=data.shift,
        start_date=start_date,
        pay_rate=data.pay_rate,
        requirements=data.requirements,
        priority=data.priority
    )
    
    await db.staffing_requests.insert_one(req.model_dump())
    return req.model_dump()

@router.post("/requests/{request_id}/approve")
async def approve_staffing_request(request_id: str, request: Request):
    """Approve and create job posting from request"""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    req = await db.staffing_requests.find_one({"request_id": request_id}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Create job posting
    from modules.ats import JobPosting
    
    job = JobPosting(
        title=req["title"],
        location=req.get("site_id", "TBD"),
        site_id=req.get("site_id"),
        client_id=req["client_id"],
        description=req["description"],
        shift=req.get("shift", ""),
        pay_rate_min=req.get("pay_rate"),
        requirements=req.get("requirements", []),
        positions_available=req["positions_needed"],
        created_by=user["user_id"]
    )
    
    await db.job_postings.insert_one(job.model_dump())
    
    # Update request
    await db.staffing_requests.update_one(
        {"request_id": request_id},
        {"$set": {
            "status": "in_progress",
            "job_id": job.job_id,
            "assigned_recruiter": user["user_id"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Request approved, job posting created", "job_id": job.job_id}

# ==================== INVOICE ENDPOINTS ====================

@router.get("/invoices/all")
async def list_invoices(request: Request, client_id: Optional[str] = None, status: Optional[str] = None):
    """List invoices"""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = {}
    if client_id:
        query["client_id"] = client_id
    if status:
        query["status"] = status
    
    invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    for inv in invoices:
        client_data = await db.clients.find_one({"client_id": inv["client_id"]}, {"_id": 0, "company_name": 1})
        inv["client_name"] = client_data.get("company_name") if client_data else "Unknown"
    
    return invoices

@router.post("/invoices")
async def create_invoice(request: Request, data: CreateInvoiceRequest):
    """Create invoice"""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    client_data = await db.clients.find_one({"client_id": data.client_id}, {"_id": 0})
    if not client_data:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Calculate totals
    subtotal = sum(item.get("amount", 0) for item in data.line_items)
    tax_amount = subtotal * (data.tax_rate / 100)
    total = subtotal + tax_amount
    
    # Calculate due date based on payment terms
    period_end = datetime.fromisoformat(data.period_end.replace('Z', '+00:00'))
    payment_days = {"net_15": 15, "net_30": 30, "net_45": 45, "net_60": 60}
    due_date = period_end + timedelta(days=payment_days.get(client_data.get("payment_terms", "net_30"), 30))
    
    invoice = Invoice(
        invoice_number=await generate_invoice_number(),
        client_id=data.client_id,
        period_start=datetime.fromisoformat(data.period_start.replace('Z', '+00:00')),
        period_end=period_end,
        line_items=data.line_items,
        subtotal=subtotal,
        tax_rate=data.tax_rate,
        tax_amount=tax_amount,
        total=total,
        due_date=due_date,
        notes=data.notes
    )
    
    await db.invoices.insert_one(invoice.model_dump())
    return invoice.model_dump()

@router.post("/invoices/{invoice_id}/send")
async def send_invoice(invoice_id: str, request: Request):
    """Mark invoice as sent"""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"status": "sent", "sent_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Invoice marked as sent"}

@router.post("/invoices/{invoice_id}/paid")
async def mark_invoice_paid(invoice_id: str, request: Request):
    """Mark invoice as paid"""
    user = await get_current_user(request)
    if not user or user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Invoice marked as paid"}

# ==================== ENGAGEMENT ENDPOINTS ====================

@router.post("/{client_id}/engagements")
async def add_engagement(client_id: str, request: Request, type: str, subject: str, description: str, outcome: str = ""):
    """Add client engagement record"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    engagement = ClientEngagement(
        client_id=client_id,
        type=type,
        subject=subject,
        description=description,
        date=datetime.now(timezone.utc),
        outcome=outcome,
        created_by=user["user_id"]
    )
    
    await db.client_engagements.insert_one(engagement.model_dump())
    return engagement.model_dump()
