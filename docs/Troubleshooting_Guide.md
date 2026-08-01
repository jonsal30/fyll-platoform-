# GHSG Time Clock - Troubleshooting Guide

## Common Issues and Solutions

---

## Login Problems

### "Employee ID not found"

**Cause:** The numeric ID hasn't been assigned to your account.

**Solution:**
1. Contact your site manager or admin
2. They will assign you a numeric ID in the admin panel
3. Try again with the assigned ID

### Google Sign-In Not Working

**Cause:** Your Google account isn't linked to an employee profile.

**Solution:**
1. Ask your admin to create your employee record first
2. Then sign in with Google - it will automatically link

### Session Expired

**Cause:** You haven't logged in for over 7 days.

**Solution:** Simply log in again with your Employee ID or Google.

---

## GPS Location Issues

### "Unable to get location. Please enable GPS."

**Solutions:**

**On iPhone:**
1. Go to Settings → Privacy & Security → Location Services
2. Turn ON Location Services
3. Scroll down and find your browser (Safari/Chrome)
4. Set to "While Using the App"
5. Refresh the page

**On Android:**
1. Go to Settings → Location
2. Turn ON location
3. Go to Settings → Apps → [Your Browser] → Permissions
4. Allow Location permission
5. Refresh the page

**Still not working?**
- Step outside for better GPS signal
- Wait 30 seconds and try again
- Restart your browser

### "Off-site" Warning When I'm At Work

**Causes:**
1. GPS accuracy is low (poor signal)
2. Site coordinates may be slightly off

**Solutions:**
1. Wait for GPS to get more accurate (watch the ±Xm number decrease)
2. Move to a spot with better signal (near windows)
3. Report to admin if consistently off-site at correct location

---

## Camera Issues

### Camera Not Opening

**Solutions:**

**On iPhone:**
1. Go to Settings → Safari (or Chrome) → Camera
2. Set to "Allow"
3. Refresh the page and try again

**On Android:**
1. Go to Settings → Apps → [Your Browser] → Permissions
2. Allow Camera permission
3. Refresh and try again

### Photo Too Dark/Blurry

**Solutions:**
1. Make sure you're in good lighting
2. Hold phone steady
3. Look directly at camera
4. Retake if needed

---

## Clock In/Out Problems

### "Already clocked in" Error

**Cause:** You have an active time entry that wasn't closed.

**Solution:**
1. Check if you're already clocked in (shows "On Duty")
2. Clock out first before clocking in again
3. If stuck, contact your manager

### "Clock In" Button Disabled

**Cause:** Missing requirements for clock-in.

**Check:**
1. ✅ GPS location acquired (green indicator)
2. ✅ Work site selected
3. ❌ If GPS shows error, fix location first

### Forgot to Clock Out

**What to do:**
1. Contact your manager immediately
2. They will note the actual clock-out time
3. They'll approve with correction noted
4. Don't wait until next shift!

---

## Timesheet Issues

### Can't Submit Timesheet

**Causes:**
1. You still have an active (not clocked out) entry
2. No completed entries for the week

**Solutions:**
1. Make sure you've clocked out from all shifts
2. Check that you have at least one complete entry

### Wrong Hours Showing

**What to do:**
1. Check each day's entries in Timesheet view
2. Note which entries are incorrect
3. Contact your manager with specifics
4. They can make corrections during approval

### Timesheet Rejected

**What to do:**
1. Read the manager's note explaining why
2. Correct the issue (re-clock missing entries, etc.)
3. Resubmit for approval

---

## Google Sheets Integration (Admin)

### 404 Error When Connecting

**Cause:** OAuth redirect URI not configured correctly.

**Solution:**
1. Go to Google Cloud Console → APIs & Services → Credentials
2. Edit your OAuth 2.0 Client ID
3. Add to **Authorized redirect URIs**:
   ```
   https://workforce-tracker-52.preview.emergentagent.com/api/oauth/sheets/callback
   ```
4. Add to **Authorized JavaScript origins**:
   ```
   https://workforce-tracker-52.preview.emergentagent.com
   ```
5. Save and wait 5 minutes
6. Clear browser cookies and try again

### "Access Denied" Error

**Cause:** Wrong Google account or missing permissions.

**Solution:**
1. Make sure you're signed into the correct Google account
2. The account needs permission to create/edit Sheets
3. Try in an incognito window to ensure clean login

### Sync Not Working

**Check:**
1. Is Google Sheets connected? (Green checkmark in Integrations)
2. Is the timesheet approved? (Only approved sheets sync)
3. Check browser console for error messages

---

## Mobile Display Issues

### Page Not Loading Properly

**Solutions:**
1. Clear browser cache and cookies
2. Force refresh: Pull down to refresh
3. Try a different browser (Chrome recommended)
4. Check internet connection

### Bottom Navigation Hidden

**Cause:** Screen too small or zoomed in.

**Solution:**
1. Make sure zoom is at 100%
2. Try rotating to landscape then back
3. Scroll down to see navigation

---

## Performance Issues

### App Running Slowly

**Solutions:**
1. Close other browser tabs
2. Clear browser cache
3. Restart browser
4. Check internet connection speed

### Data Not Updating

**Solutions:**
1. Pull down to refresh (mobile)
2. Click refresh button (desktop)
3. Log out and log back in
4. Clear cookies and cache

---

## Emergency Contacts

**Site Issues:** Contact your Site Manager

**Technical Issues:** Contact GHSG Admin

**Urgent Payroll Issues:** Contact GHSG Support immediately

---

## Reporting Bugs

If you encounter a bug:

1. Note exactly what you were doing
2. Screenshot any error messages
3. Note your device type (iPhone/Android) and browser
4. Report to your manager or admin

---

*"We may be small. But we build like we're here forever."*

© 2026 GH Service Group LLC
