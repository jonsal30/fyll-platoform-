# Garza Group Recruiting Services (GGRSLLC) - Time Clock PRD

## Company Mission
"Building people, not just payroll. Developing leaders, not just filling shifts. Strengthening communities, one person at a time."

GGRSLLC staffs janitorial, custodial, facilities & industrial roles across multiple U.S. clients & sites (ABM, Walmart, XAI, LG, Boeing, etc.) - serving first-generation workers, low-income earners, immigrants, and people who've been told they're "just labor" when really they're quiet leaders in the making.

## Original Problem Statement
Create a comprehensive web app time clock solution that tracks employee work hours, lunch breaks, and uses geo-fencing to ensure employees are on-site. Include a photo verification feature for authentication. Offer both numeric ID and Google Sign-In options for user convenience. Design the system so that on-site managers can approve time sheets daily or weekly, which are then forwarded to the main office. Ensure that employees and managers can reconcile time sheets weekly, with all data securely logged and managed in Google Sheets. Prioritize security, accuracy, and a streamlined user experience. For a multi-site workforce.

## User Choices & Brand Guidelines
- Simple webcam photo capture on clock-in/out
- Google Sheets API for data sync (credentials provided)
- 11 real work sites with 200m geo-fencing radius
- Emergent-managed Google Auth
- In-app notifications + CSV export as backup

### Brand Colors (ATS Recruiting Palette)
- Keystone Indigo: #4600FF (primary, hero, buttons)
- Foundation Blue-Black: #101820 (text, nav, UI)
- Vertex Magenta: #FF2E63 (energy, CTAs, accents)
- Horizon White: #F5F5F5 (backgrounds, cards)

### Typography
- Headlines: Crimson Pro (serif, XCharter-like warmth)
- Body/UI: System Sans (clarity, offline support)

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
