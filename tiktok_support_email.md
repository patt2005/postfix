# Email to TikTok Developer Support

**To:** tiktokfordevelopers@tiktok.com
**Subject:** Re: [Support Request] App Review Process - Persistent Unaudited App Error Despite Approval

---

Hello TikTok For Developers Team,

Thank you for approving our application on August 7th. However, we are experiencing a critical issue that is preventing us from using the approved app functionality.

## Issue Description

Despite receiving approval confirmation for our app, we are still encountering the "unaudited_client_can_only_post_to_private_accounts" error when attempting to post videos with public privacy settings.

## App Details

- **App Name:** Postify
- **Client Key:** awdkixsp0iao2bnk
- **Approval Date:** August 7, 2024
- **Error Code:** `unaudited_client_can_only_post_to_private_accounts`
- **API Endpoint:** `/v2/post/publish/video/init/`

## Steps We've Taken

1. **Verified App Approval Status:** We received confirmation email on Aug 7 stating "Your app has been approved"
2. **Updated Credentials:** We've updated both the Client Key and Client Secret in our application
3. **Re-authenticated Users:** We've implemented a re-authentication flow to obtain fresh access tokens
4. **Token Refresh:** We've attempted refreshing existing tokens using the refresh_token grant type
5. **Verified Scopes:** Confirmed we're requesting `user.info.basic,video.publish` scopes

## Current Behavior

When making API calls to post videos:
- **Expected:** Videos should post with PUBLIC_TO_EVERYONE privacy level
- **Actual:** API returns error code `unaudited_client_can_only_post_to_private_accounts`

## API Response Example

```json
{
    "error": {
        "code": "unaudited_client_can_only_post_to_private_accounts",
        "log_id": "20250814220001E01CA387ADDA7D0D21CE",
        "message": "Please review our integration guidelines..."
    }
}
```

## Questions

1. Is there a propagation delay after app approval before the API recognizes the approved status?
2. Do existing access tokens need to be completely revoked and regenerated (not just refreshed) after app approval?
3. Is there a specific API endpoint to verify our app's current audit status?
4. Are there additional steps required to activate public posting capabilities after approval?

## Request

We urgently need assistance to resolve this issue as our users cannot utilize the public posting functionality despite our app being approved. Please advise on:

1. How to verify our app's approved status via API
2. The correct process to enable public posting after approval
3. Any additional configuration required on the TikTok Developer Portal

We have production users waiting to use this functionality, and any expedited assistance would be greatly appreciated.

## Additional Information

- **Redirect URI:** https://postify-164860087792.europe-west1.run.app/auth/tiktok/callback
- **Environment:** Production (Google Cloud Run)
- **OAuth Flow:** Authorization Code with PKCE
- **Token Storage:** Server-side with refresh capability

Please let us know if you need any additional information, API logs, or access to debug this issue.

Thank you for your prompt attention to this matter.

Best regards,
[Your Name]
[Your Company]
[Contact Information]

---

**Attachments:**
- Screenshot of approval email (Aug 7)
- API error response logs
- Current app configuration screenshot from Developer Portal