# GGRS Time Clock - Admin Handbook

## Administrator Guide

"Strengthening communities, one person at a time."

As an admin, you manage the entire time clock system including sites, users, integrations, and reporting.

---

## Admin Panel Overview

Access: Log in → **Admin** in navigation

Three main tabs:
1. **Sites** - Manage work locations
2. **Users** - Manage employees and roles
3. **Integrations** - Google Sheets connection

---

## Managing Work Sites

### Adding a New Site

1. Go to **Admin** → **Sites** tab
2. Click **"+ Add Site"**
3. Fill in:
   - **Site Name**: e.g., "XAi - Colossus"
   - **Address**: Full street address
   - **Latitude/Longitude**: GPS coordinates
   - **Radius**: Geo-fence distance (default 200m)
4. Click **Save**

### Finding GPS Coordinates

1. Go to Google Maps
2. Search for the address
3. Right-click on the exact location
4. Click to copy coordinates
5. Format: Latitude, Longitude (e.g., 35.0456, -90.0833)

### Editing a Site

1. Click the **pencil icon** on the site card
2. Update any fields
3. Click **Save**

### Deactivating a Site

1. Click the **trash icon** on the site card
2. Confirm deactivation
3. Site becomes inactive (not deleted for records)

---

## Managing Users

### Viewing All Users

1. Go to **Admin** → **Users** tab
2. See table with all employees, managers, and admins

### Editing a User

1. Click the **pencil icon** next to the user
2. Update:
   - **Role**: employee, manager, or admin
   - **Numeric ID**: For quick login (e.g., 1001)
   - **Assigned Sites**: Which sites they can clock into/manage
3. Click **Save**

### Role Permissions

| Role | Clock In/Out | View Own Timesheet | Approve Timesheets | Manage Sites | Manage Users |
|------|-------------|-------------------|-------------------|--------------|--------------|
| Employee | ✅ | ✅ | ❌ | ❌ | ❌ |
| Manager | ✅ | ✅ | ✅ (assigned sites) | ❌ | ❌ |
| Admin | ✅ | ✅ | ✅ (all sites) | ✅ | ✅ |

### Assigning Numeric IDs

1. IDs should be unique 4-digit numbers
2. Start from 1001 for employees
3. Use 2001+ for managers
4. Keep a master list for reference

---

## Google Sheets Integration

### Setting Up Google Sheets Sync

**Prerequisites:**
- Google Cloud Console project
- OAuth 2.0 credentials configured

**Steps:**
1. Go to **Admin** → **Integrations** tab
2. Click **"Connect Google Sheets"**
3. Sign in with the company Google account
4. Authorize the app to access Sheets
5. A new spreadsheet will be created automatically

**Redirect URI for Google Console:**
```
https://workforce-tracker-52.preview.emergentagent.com/api/oauth/sheets/callback
```

### Troubleshooting 404 Error

If you get a 404 error when connecting:

1. **Check the Redirect URI** in Google Cloud Console:
   - Go to APIs & Services → Credentials
   - Click your OAuth 2.0 Client ID
   - Ensure **Authorized redirect URIs** includes:
     ```
     https://workforce-tracker-52.preview.emergentagent.com/api/oauth/sheets/callback
     ```

2. **Check JavaScript Origins**:
   - Add: `https://workforce-tracker-52.preview.emergentagent.com`

3. **Wait 5 minutes** after making changes (Google caches)

4. **Clear browser cookies** and try again

### Syncing Timesheets

Once connected:
1. Approved timesheets can be synced to Google Sheets
2. Data includes all entry details and totals
3. Use for payroll reconciliation

---

## Payroll Reports

### Weekly Payroll Export

1. Use the API endpoint or Reports section
2. Export format: Last Name, First Name (A-Z sorted)
3. Ready for direct deposit upload

### Report Endpoints

- `/api/reports/payroll?week_start=YYYY-MM-DD` - Payroll summary
- `/api/reports/site-weekly/{site_id}?week_start=YYYY-MM-DD` - Site detail
- `/api/reports/audit-trail?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Compliance audit
- `/api/reports/export/payroll-csv` - CSV download
- `/api/reports/export/audit-csv` - Audit CSV download

---

## Audit Trail & Compliance

### What's Tracked

- Employee submission timestamp
- Manager approval timestamp
- Manager name
- Approval notes
- All lunch breaks taken
- Location verification status
- Photo verification status

### Accessing Audit Records

1. Use the audit trail API endpoint
2. Export as CSV for compliance records
3. Store according to labor law requirements

---

## Employee Login Methods

### Numeric ID Login
- Each employee gets a unique 4-digit ID
- Fast login without email/password
- Admin assigns IDs in user management

### Google Sign-In
- Employees can use their personal Gmail
- First login links their Google account to their profile
- Admin must create the employee record first

### Linking Google Account to Existing Employee

1. Create employee record with name and numeric ID
2. Employee signs in with Google
3. System automatically links if name matches
4. Or admin manually links via user edit

---

## Backup Procedures

### CSV Export (Always Available)

Even without Google Sheets:
1. Export timesheet data as CSV
2. Export payroll summaries
3. Export audit trails
4. Import into any spreadsheet software

### Database Backups

MongoDB data is the source of truth. Regular backups recommended.

---

## Security Best Practices

✅ Regularly review user roles
✅ Remove access for terminated employees
✅ Audit manager approvals monthly
✅ Keep Google Sheets credentials secure
✅ Use strong passwords for admin accounts

---

## Support

For technical issues: Contact Emergent support
For business questions: Contact GGRS HQ

---

*"We may be small. But we build like we're here forever."*

© 2026 Garza Group Recruiting Services, LLC
