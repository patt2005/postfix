# Email to TikTok Developer Support

**To:** developers@tiktok.com, tiktokfordevelopers@tiktok.com
**Subject:** URGENT: Approved App Still Showing as Unaudited - Unable to Post Public Videos

---

Dear TikTok Developer Support Team,

We are experiencing a critical production issue where our approved TikTok application is still being treated as unaudited by your API, preventing our users from posting public videos.

## Issue Summary

Despite our app being **officially approved on August 7, 2024**, we continue to receive the `unaudited_client_can_only_post_to_private_accounts` error when attempting to post videos with public privacy settings.

## Timeline of Events

1. **August 7, 2024**: Received approval email stating "Your app has been approved"
2. **August 7-14, 2024**: Updated our application with new Client Key and Client Secret from the approved app
3. **Current**: Still receiving unaudited app errors on all API calls

## Technical Details

### App Information
- **App Name:** Postify
- **Client Key:** awdkixsp0iao2bnk
- **Platform:** Production (Google Cloud Run)
- **API Version:** v2
- **OAuth Flow:** Authorization Code with PKCE

### Error Response
```json
{
    "error": {
        "code": "unaudited_client_can_only_post_to_private_accounts",
        "log_id": "20250814220001E01CA387ADDA7D0D21CE",
        "message": "Unaudited clients can only post videos with privacy_level set to SELF_ONLY"
    }
}
```

### API Request Details
- **Endpoint:** `https://open.tiktokapis.com/v2/post/publish/video/init/`
- **Headers:** 
  - Authorization: Bearer [valid_access_token]
  - Content-Type: application/json
- **Request Body:**
```json
{
    "post_info": {
        "title": "Video Title",
        "privacy_level": "PUBLIC_TO_EVERYONE"
    },
    "source_info": {
        "source": "FILE_UPLOAD",
        "video_size": 1234567,
        "chunk_size": 10485760,
        "total_chunk_count": 1
    }
}
```

## Steps We Have Taken

### 1. Updated Credentials
- ✅ Replaced old Client Key with new approved app Client Key
- ✅ Replaced old Client Secret with new approved app Client Secret
- ✅ Verified credentials are correctly loaded from environment variables

### 2. Token Management
- ✅ Revoked all existing access tokens
- ✅ Re-authenticated all users to obtain fresh tokens with new credentials
- ✅ Implemented automatic token refresh mechanism
- ✅ Verified tokens include correct scopes: `user.info.basic,video.publish`

### 3. Code Verification
- ✅ Confirmed using correct API endpoints
- ✅ Verified PKCE implementation is correct
- ✅ Ensured all API calls use HTTPS
- ✅ Added comprehensive error logging

### 4. Testing Performed
- ✅ Tested with multiple user accounts
- ✅ Tried different privacy levels (PUBLIC_TO_EVERYONE fails, SELF_ONLY works)
- ✅ Verified user info endpoint works correctly
- ✅ Confirmed video upload process completes successfully

## Critical Business Impact

This issue is severely impacting our production users:
- **Users affected:** All users attempting to post public videos
- **Business impact:** Users cannot use the core functionality they signed up for
- **User complaints:** Multiple support tickets about inability to post publicly

## Questions Requiring Immediate Clarification

1. **Is there a propagation delay?** How long after approval before the API recognizes the app as audited?

2. **Are we missing a step?** Is there an additional activation or configuration step required after approval that isn't documented?

3. **Is there a cache issue?** Do TikTok's API servers cache app audit status? If so, how can we force a refresh?

4. **Token generation timing?** Do access tokens generated before app approval remain "unaudited" even after app approval? 

5. **API endpoint verification?** Is there an API endpoint we can call to verify our app's current audit status?

## Requested Actions

We urgently request the following assistance:

1. **Verify our app status** - Please confirm our app (Client Key: awdkixsp0iao2bnk) shows as approved in your system

2. **Manual intervention** - If there's a sync issue, please manually update our app's status in the API gateway

3. **Provide timeline** - If there's a known propagation delay, please provide an estimated timeline for resolution

4. **Debug assistance** - If possible, please check the specific log ID provided above to see why our app is being flagged as unaudited

## Additional Context

- We followed all integration guidelines from the official documentation
- Our implementation passed your review process
- We have implemented all required security measures (PKCE, secure token storage, HTTPS)
- This is blocking a production deployment with active users

## Contact Information

For urgent follow-up:
- **Technical Contact:** [Your Name]
- **Email:** [Your Email]
- **Company:** Postify
- **Timezone:** [Your Timezone]

We are available for a technical call if that would expedite resolution.

## Attachments Available Upon Request

We can provide:
- Screenshot of approval email (August 7)
- Full API request/response logs
- Video demonstrating the issue
- Current app configuration from Developer Portal

**This is a critical production issue affecting all our users. We urgently need your assistance to resolve this as our app has been approved but is non-functional for public posting.**

Thank you for your immediate attention to this matter.

Best regards,
[Your Name]
[Your Title]
Postify

---

**Reference Numbers:**
- App Approval Date: August 7, 2024
- Client Key: awdkixsp0iao2bnk
- Example Log ID: 20250814220001E01CA387ADDA7D0D21CE