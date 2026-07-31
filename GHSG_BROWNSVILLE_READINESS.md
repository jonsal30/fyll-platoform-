# GH Service Group Brownsville Deployment Readiness

This branch converts the existing Garza Group workforce platform into a GH Service Group employee portal while preserving the functioning time-clock, geofence, photo, lunch, timesheet, approval, ATS, and administration modules.

## Changes in this branch

- GH Service Group branding on employee login, navigation, API metadata, and employee documentation
- Removed the external GGRS logo dependency from employee-facing screens
- Employee login now requires both Employee ID and a private PIN
- PINs are stored only as bcrypt hashes
- Admins can set or reset PINs from the Users panel
- PIN hashes are excluded from user-list and user-update API responses
- CORS no longer defaults to a wildcard origin
- Employees can see and use only explicitly assigned sites
- Production defaults to enforced geofencing and pre-provisioned accounts
- Brownsville-specific employee instructions and ABM check-in reference added
- Render deployment blueprint and environment templates added

## Production prerequisites

1. Create a production MongoDB database and set `MONGO_URL` and `DB_NAME`.
2. Deploy the backend and set `CORS_ORIGINS` to the exact employee portal URL.
3. Deploy the frontend and set `REACT_APP_BACKEND_URL` to the backend origin without `/api`.
4. Configure the precise paid-work geofence before employees clock time.
5. Create or import current GHSG employees; assign unique IDs, private PINs, roles, and sites.
6. Test one employee, one manager, and one administrator account end to end.
7. Validate camera and location permissions on iPhone Safari and Android Chrome.
8. Confirm the payroll export format against the current GHSG submission sheet.
9. Publish the employee guide and support escalation path.
10. Back up the database and define retention rules for employee photos and GPS records.

## Critical Brownsville location decision

The known address `109 N Browne Ave, Brownsville, TX` is the ABM badging/check-in location. It should not automatically become the time-clock geofence. The administrator must enter the actual location where paid time begins and ends, with verified latitude, longitude, and radius.

## Existing user migration

Existing users on the inherited database do not have PIN hashes. An administrator must open each current GHSG user in **Admin → Users**, assign the Brownsville site, set a private 4–12 digit PIN, and save before that user can sign in.

Do not reuse the same PIN for the full workforce. Do not use SSN digits, birth dates, or payroll account numbers.

## Smoke test

- Invalid Employee ID/PIN returns a generic authentication error.
- Valid employee can sign in.
- Employee sees only assigned/active sites.
- GPS outside the configured radius is flagged.
- Clock-in records photo, coordinates, timestamp, user, and site.
- Lunch start/end cannot be duplicated.
- Clock-out calculates hours after lunch.
- Employee can review and submit the week.
- Manager can approve or reject.
- Payroll CSV totals match the approved records.
- Signing out invalidates the session.

## Known remaining integration work

- The optional Google sign-in flow still uses Emergent Auth and should be replaced or disabled before treating it as GHSG-owned identity infrastructure.
- Google Sheets requires GHSG OAuth credentials.
- Email notifications require a configured provider.
- A formal privacy/retention policy is required for camera and GPS data.
- Brownsville employee roster and exact paid-work coordinates are not stored in this public repository.
