# Garza Group HR Platform - PRD

## Company Mission
"Building people, not just payroll. Developing leaders, not just filling shifts. Strengthening communities, one person at a time."

## Platform Overview
Complete HR Management Platform for GGRSLLC - a people-first staffing company serving janitorial, custodial, facilities & industrial roles across ABM, Walmart, XAI, LG, Boeing, and other clients.

## Modules Implemented

### 1. Time Clock (Complete)
- Clock in/out with photo verification
- GPS geo-fencing (200m radius)
- Lunch break tracking
- Timesheet submission and approval
- Manager approval workflow
- CSV export for payroll

### 2. ATS - Applicant Tracking System (Complete)
- Job posting creation and management
- Applicant pipeline (New → Screening → Interview → Offer → Hired)
- Stage tracking with history
- Offer letter creation
- Onboarding checklists
- Pipeline statistics and conversion rates

### 3. Client Portal (Backend Complete)
- Client management with contacts
- Staffing requests workflow
- Invoice generation and tracking
- Engagement logging
- Site assignments

### 4. HR Management (Backend Complete)
- Incident reporting
- Performance reviews
- Employee feedback system
- HR ticketing system
- Employee profiles and documents

### 5. Admin Settings (Backend Complete)
- White-label branding configuration
- Module toggle (enable/disable features)
- Integration settings (Google Sheets, Indeed, SendGrid)
- Time clock configuration
- Executive dashboard KPIs

## Data Seeded
- 34 employees from roster with unique numeric IDs (1001-1034)
- 11 work sites with real addresses and coordinates
- Managers and admin accounts

## API Endpoints

### Time Clock
- POST /api/clock/in, /api/clock/out, /api/clock/lunch
- GET /api/clock/status, /api/entries, /api/timesheets
- POST /api/timesheets/submit, /api/timesheets/{id}/approve

### ATS
- GET/POST /api/ats/jobs, /api/ats/applicants
- POST /api/ats/jobs/{id}/publish
- POST /api/ats/applicants/{id}/stage
- POST /api/ats/offers
- GET /api/ats/pipeline/stats

### Clients
- GET/POST /api/clients
- POST /api/clients/requests
- POST /api/clients/invoices

### HR
- GET/POST /api/hr/incidents, /api/hr/reviews, /api/hr/feedback
- GET/POST /api/hr/tickets
- GET /api/hr/employees/{id}/profile

### Admin
- GET/PUT /api/admin/settings
- PUT /api/admin/settings/branding
- PUT /api/admin/settings/integrations
- GET /api/admin/dashboard/executive

## Frontend Pages
- /login - Employee ID + Google Sign-In
- /dashboard - Clock in/out interface
- /timesheet - Weekly timesheet view
- /manager - Approval dashboard
- /recruiting - ATS with jobs and applicants
- /admin - Sites, Users, Integrations management

## Next Steps (P1)
1. Build Client Portal frontend pages
2. Build HR Management frontend pages
3. Add Executive Dashboard with charts
4. Indeed API integration for job posting
5. SendGrid for email notifications

## White-Label Configuration
- Company name, logo, tagline
- Color palette (Keystone #4600FF, Vertex #FF2E63, Foundation #101820, Horizon #F5F5F5)
- Font configuration
- Module visibility toggles

## User Personas

### Employee
- Needs quick clock-in/out on mobile device
- Uses numeric ID or Google Sign-In
- Views their own timesheets
- Submits weekly timesheets for approval

### Manager
- Approves team timesheets
- Views team status (who's clocked in)
- Can access via approval links in emails/notifications
- Edits and corrects time entries

### Admin
- Manages work sites (add/edit/delete)
- Manages user roles and site assignments
- Configures Google Sheets integration
- Exports data as CSV

## Core Requirements (Static)

### Authentication
- [x] Google Sign-In via Emergent Auth
- [x] Numeric ID login for quick access
- [x] Session management with secure cookies

### Time Tracking
- [x] Clock-in with photo capture
- [x] Clock-out with photo capture
- [x] Lunch break start/end tracking
- [x] Geo-fencing verification (200m radius)
- [x] Real-time elapsed time display

### Timesheet Management
- [x] Weekly timesheet view
- [x] Submit for approval workflow
- [x] Manager approval/rejection
- [x] Approval via shareable links (token-based)

### Data Management
- [x] Google Sheets sync integration
- [x] CSV export functionality
- [x] MongoDB data storage

### Admin Features
- [x] Work site CRUD (with geo-coordinates)
- [x] User role management
- [x] Site assignment per user

## What's Been Implemented (Jan 2026)

### Rebrand Complete
- Garza Group logo integration
- ATS Recruiting color palette (Keystone Indigo, Vertex Magenta, Foundation, Horizon)
- Company taglines throughout ("Building people, not just payroll")
- Professional serif + sans typography

### Database Seeded with Real Data
**11 Work Sites:**
1. LG - Holland (1 LG Way, Holland, MI 49423)
2. XAi - Colossus (3231 Riverport Road, Memphis, TN 38109)
3. XAi - Duke (2875 Stanton Rd, Memphis, TN 38109)
4. XAi - Tulane (5420 Tulane Rd, Memphis, TN 38109)
5. Walmart - Olive Branch (9200 Alexander Rd, Olive Branch, MS 38654)
6. ABM - Boeing (325 James S. McDonnell Blvd, Hazelwood, MO 63042)
7. 6040 Telephone (Houston, TX)
8. 7411 Mesa (Houston, TX)
9. RPM (Iowa Colony, TX)
10. Skyline (Dallas, TX)
11. GGRS HQ (8811 Park Place Blvd, Houston, TX)

**Sample Employees:**
- Khi Anderson (ID: 1001) - XAi Tulane
- Rodney Jones (ID: 1002) - XAi Duke/Tulane
- Kristie Lewis (ID: 1003) - XAi Tulane
- Terrance Rooks (ID: 1004) - XAi Tulane
- Adriana Hernandez (ID: 1005) - LG Holland
- Roberto De La Paz (ID: 1006) - LG Holland
- Jasmine Dorris (ID: 1007) - XAi Colossus
- Cedric Doss (ID: 1008) - XAi Colossus
- Site Manager (ID: 2001) - All Memphis/Holland sites
- Admin User (ID: 1234) - All sites

### Backend (FastAPI)
- Complete REST API with /api prefix
- User authentication (Emergent OAuth + Numeric ID)
- Time entries CRUD
- Timesheet submission and approval workflow
- Work sites management
- Notifications system
- Google Sheets OAuth integration
- CSV export endpoint

### Frontend (React + Shadcn UI)
- Dark industrial "Site Commander" design theme
- Mobile-first responsive layout
- Login page with dual auth options
- Employee Dashboard with:
  - Clock-in/out functionality
  - Photo capture via webcam
  - GPS location verification
  - Lunch break management
  - Real-time timer
- Timesheet page with week navigation
- Manager Dashboard with:
  - Pending approvals list
  - Team status view
  - Quick approve/reject actions
- Approval Page (accessible via links)
- Admin Panel with:
  - Sites management tab
  - Users management tab
  - Integrations tab (Google Sheets)

## Prioritized Backlog

### P0 (Critical) - DONE
- [x] Authentication system
- [x] Clock-in/out flow
- [x] Photo capture
- [x] Geo-fencing verification
- [x] Timesheet submission
- [x] Manager approval

### P1 (Important) - Partially Done
- [x] Google Sheets sync (needs user credentials)
- [x] CSV export
- [ ] Email notifications (SendGrid - needs API key)
- [ ] Push notifications (browser)

### P2 (Nice to Have)
- [ ] Offline mode support
- [ ] Biometric authentication
- [ ] Shift scheduling
- [ ] Overtime calculations
- [ ] Report generation dashboard
- [ ] Multi-language support

## Technical Architecture

### Stack
- Frontend: React 19, Tailwind CSS, Shadcn UI, Lucide Icons
- Backend: FastAPI, Motor (async MongoDB)
- Database: MongoDB
- Auth: Emergent Google OAuth
- Integrations: Google Sheets API

### Key Endpoints
- POST /api/auth/session - Exchange OAuth token
- POST /api/auth/numeric-login - Numeric ID login
- GET /api/auth/me - Get current user
- POST /api/clock/in - Clock in
- POST /api/clock/out - Clock out
- POST /api/clock/lunch - Lunch start/end
- GET /api/clock/status - Current clock status
- GET/POST /api/sites - Work sites
- GET/POST /api/timesheets - Timesheet management
- POST /api/timesheets/{id}/approve - Approve/reject
- GET /api/export/csv - Export data

## Next Tasks

1. Add more work sites (9 more to reach 10)
2. Create test employee accounts
3. Test full workflow: clock-in → lunch → clock-out → submit → approve
4. Configure Google Sheets sync with actual credentials
5. Add SendGrid for email notifications (optional)
