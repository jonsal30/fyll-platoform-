# GH Service Group Brownsville Deployment Readiness

This branch converts the inherited workforce platform into a GH Service Group employee portal for Brownsville. It preserves timekeeping, lunch tracking, timesheets, approvals, reporting, ATS, MongoDB, and Google Sheets hooks while adding the Browne shuttle workflow.

## Employee workflow

1. **Check In for Shuttle at Browne** — attendance only; no paid time is created.
2. **Start Work** — creates the paid time entry and captures a verification photo and GPS.
3. **Start Lunch** — pauses paid work time.
4. **Return from Lunch** — resumes paid work time.
5. **End Work** — completes the paid time entry and captures a verification photo and GPS.
6. **Check Out at Browne** — attendance-only return confirmation.

The API rejects out-of-order events. Employees may end work without a lunch when no lunch was taken. The work/lunch/end actions remain linked to the payroll time-entry record.

## Browne attendance location

- Address: 109 N Browne Ave, Brownsville, TX 78521
- Latitude: `25.917616`
- Longitude: `-97.389920`
- Initial radius: `400` meters

The first five completed attendance days collect GPS evidence without blocking an employee. Starting after day five, Browne shuttle check-in and return check-out must fall within the configured radius.

Paid-work geofence enforcement is initially disabled with `GEOFENCE_ENFORCED=false`. Review the first-five-day work-start/work-end evidence, configure the verified SpaceX/Shawmut worksite center and radius in **Admin → Sites**, then set `GEOFENCE_ENFORCED=true`.

## Identity and employee provisioning

- Employee sign-in requires Employee ID plus a private 4–12 digit PIN.
- PINs are stored only as bcrypt hashes and are excluded from all login, profile, and user-list responses.
- Legacy Emergent Google sign-in is disabled by default.
- Self-registration is disabled.
- Administrators can add employees and assign roles, IDs, PINs, and sites from **Admin → Users**.

### First administrator

For an empty production database, enter these as private deployment settings:

- `BOOTSTRAP_ADMIN_NAME`
- `BOOTSTRAP_ADMIN_ID`
- `BOOTSTRAP_ADMIN_PIN` — 6–12 digits

The application creates the first administrator only when no administrator exists. After the first successful admin sign-in, remove `BOOTSTRAP_ADMIN_PIN` from the hosting settings. Do not reuse a banking PIN, SSN digits, birth date, or one shared workforce PIN.

## Render deployment

The repository includes `render.yaml` for two services:

- `ghsg-workforce-api` — FastAPI backend
- `ghsg-employee-portal` — React static frontend

Required private values during Blueprint setup:

- `MONGO_URL`
- `CORS_ORIGINS` — exact frontend origin
- `REACT_APP_BACKEND_URL` — backend origin without `/api`
- Bootstrap administrator values above

Google Sheets OAuth values may remain blank for the initial rollout. Configure them only when GHSG is ready to connect Sheets.

## Production smoke test

- Invalid Employee ID/PIN returns a generic authentication error.
- Bootstrap administrator can sign in.
- Administrator can create a Brownsville work site and an employee.
- Employee sees only assigned active sites.
- Browne shuttle check-in records coordinates, accuracy, distance, timestamp, and attendance-only status.
- Start Work creates a paid time entry with photo and GPS.
- Lunch Out and Lunch In update the same paid entry.
- End Work completes the entry and calculates paid hours after lunch.
- Browne return check-out completes the attendance session without changing payroll time.
- Employee can review and submit the week.
- Manager can approve or reject.
- Payroll CSV totals match approved records.
- iPhone Safari and Android Chrome grant precise location and camera access.
- Signing out invalidates the session.

## Operational decisions still owned by GHSG

- Confirm the travel-time policy with Laurie and Will.
- Review the first five workdays before enabling the paid-work geofence.
- Define GPS/photo retention and manager correction procedures.
- Import or create the current Brownsville roster privately.
- Confirm the payroll export against the current GHSG submission sheet.

## Validation

- Python source compilation passes.
- Modified React source parses successfully.
- GitHub Actions validates backend dependencies/compilation and the production frontend build.
