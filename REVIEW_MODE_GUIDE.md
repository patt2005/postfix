# TikTok Review Mode Guide

## 🔒 What is Review Mode?

Review Mode is a safety feature that restricts your app to private posting only until TikTok approves your application for public content posting. This ensures compliance with TikTok's review requirements.

---

## 📋 Current Status: **IN REVIEW**

Your app is currently in review mode with the following restrictions:

### Active Restrictions:
- ✅ **Private Posts Only** - All videos post as "Only Me" (visible to poster only)
- ❌ **Public Posting Disabled** - Cannot post to "Public" or "Friends"
- ❌ **Commercial Content Disabled** - Brand/promotional disclosure unavailable
- ✅ **File Upload Only** - URL posting disabled during review
- ⚠️ **10 Posts/Day Limit** - Maximum test posts per day

---

## 🚀 How to Enable Public Posting

### Step 1: Complete TikTok Review

1. Submit your app for review in TikTok Developer Portal
2. Ensure all UX requirements are met (✅ Already implemented)
3. Wait for TikTok's approval email

### Step 2: Disable Review Mode

Once approved by TikTok, update the configuration:

1. Open `config.py`
2. Change line 11:
   ```python
   # BEFORE (Review Mode Active)
   REVIEW_MODE = True
   
   # AFTER (Approved - Public Posting Enabled)
   REVIEW_MODE = False
   ```

3. Optional: Set approval date (line 14):
   ```python
   REVIEW_APPROVED_DATE = datetime(2024, 12, 25)  # Your approval date
   ```

4. Restart your application

---

## 🎯 Review Mode Features

### Automatic Privacy Override
- Any privacy selection is automatically changed to "Only Me"
- Users are notified of the override
- Prevents accidental public posting during review

### Visual Indicators
- Orange warning banner on dashboard
- Lock icons on post buttons
- Disabled commercial content section
- Privacy dropdown shows restrictions

### API Protection
- `/api/post/video` endpoint forces SELF_ONLY privacy
- `/api/post/video/compliant` validates review restrictions
- Commercial content stripped from requests

---

## 📊 Testing During Review

### Recommended Testing Steps:

1. **Test Private Posting**
   ```bash
   # Create a test post (will be private)
   curl -X POST /api/post/video/compliant \
     -H "Content-Type: application/json" \
     -d '{"title": "Test", "privacy_level": "SELF_ONLY"}'
   ```

2. **Verify Privacy Override**
   - Try selecting "Public" in UI
   - Confirm it changes to "Only Me"
   - Check response for review_mode_override

3. **Check Review Status**
   ```bash
   curl /api/review/status
   ```

### What to Test:
- ✅ Video uploads work correctly
- ✅ Posts appear as private on TikTok
- ✅ Character limits enforced
- ✅ Interaction settings (comments, duet, stitch)
- ✅ User consent flow
- ✅ Status polling after post

---

## 🔍 Review Mode API Endpoints

### Check Status
```
GET /api/review/status
```

Response:
```json
{
  "status": {
    "in_review": true,
    "can_post_publicly": false,
    "allowed_privacy_levels": ["SELF_ONLY"]
  },
  "warning": {
    "type": "review_mode",
    "message": "App in Review Mode"
  }
}
```

### Post Video (Compliant)
```
POST /api/post/video/compliant
```

During review, this endpoint:
- Forces privacy to SELF_ONLY
- Disables commercial content
- Adds review warnings to response

---

## ⚠️ Important Notes

### DO NOT:
- ❌ Disable review mode before TikTok approval
- ❌ Attempt to bypass privacy restrictions
- ❌ Post test content from production accounts
- ❌ Submit for review with review mode disabled

### DO:
- ✅ Test thoroughly with private posts
- ✅ Verify all UX requirements work
- ✅ Keep review mode active until approved
- ✅ Document any issues for TikTok review team

---

## 📝 Submission Checklist

Before submitting to TikTok:

- [ ] Review mode is ACTIVE (REVIEW_MODE = True)
- [ ] All UX requirements implemented
- [ ] Creator info displays correctly
- [ ] Privacy selector works (forced to SELF_ONLY)
- [ ] Interaction toggles function properly
- [ ] Commercial content section shows (but disabled)
- [ ] User consent checkbox present
- [ ] Video preview works
- [ ] Status polling implemented
- [ ] Test posts work as private

---

## 🎉 After Approval

Once TikTok approves your app:

1. **Update Configuration**
   - Set `REVIEW_MODE = False`
   - Set `REVIEW_APPROVED_DATE`

2. **Remove Restrictions**
   - Public posting enabled
   - All privacy levels available
   - Commercial content enabled
   - URL posting enabled (if domain verified)

3. **Update UI**
   - Review banner hidden
   - Full privacy options shown
   - Commercial content active

4. **Celebrate!** 🎊
   - Your app can now post publicly
   - All features fully enabled
   - Ready for production use

---

## 📧 Support

If you have questions during review:
- Check TikTok Developer Portal for status
- Review error messages in logs
- Ensure all compliance requirements met
- Contact TikTok developer support if needed

---

**Current Configuration File:** `config.py`
**Review Mode Status:** `REVIEW_MODE = True` (Line 11)
**Last Updated:** December 2024