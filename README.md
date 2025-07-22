# Postify

A Flask-based web application for automating TikTok content posting with OAuth authentication.

## Features

- TikTok OAuth 2.0 authentication (Login Kit)
- Secure session management
- User dashboard with TikTok account information
- Content posting functionality:
  - Post videos via URL (from verified domains)
  - Upload videos from computer (MP4, MOV, AVI, FLV, WMV)
  - Set privacy levels (Public, Friends, Private)
  - Configure video settings (disable duet, comments, stitch)
  - Real-time post status tracking
- Drag-and-drop file upload interface

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- TikTok Developer Account
- Registered TikTok App with Login Kit enabled

### 2. TikTok App Configuration

1. Go to [TikTok Developers Portal](https://developers.tiktok.com)
2. Create a new app or select existing one
3. Enable "Login Kit" product
4. Enable "Content Posting API" product with Direct Post configuration
5. Add redirect URI: `https://yourdomain.com/auth/tiktok/callback`
6. Request approval for `video.publish` scope
7. Note down your Client Key and Client Secret

### 3. Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd auto_poster_tt
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file from example:
```bash
cp .env.example .env
```

4. Update `.env` with your credentials:
```
TIKTOK_CLIENT_KEY=your_actual_client_key
TIKTOK_CLIENT_SECRET=your_actual_client_secret
TIKTOK_REDIRECT_URI=http://localhost:8080/auth/tiktok/callback
FLASK_SECRET_KEY=your_secure_secret_key
```

5. Run the application:
```bash
python app.py
```

6. Visit `http://localhost:8080` in your browser

## API Endpoints

### Authentication
- `/` - Landing page
- `/auth/tiktok` - Initiates TikTok OAuth flow
- `/auth/tiktok/callback` - OAuth callback handler
- `/logout` - Clear session and logout

### User Management
- `/dashboard` - User dashboard (requires authentication)
- `/api/user/info` - Get TikTok user information
- `/api/creator/info` - Get creator posting capabilities

### Content Posting
- `/api/post/video` - Initiate video post (URL or file upload)
- `/api/post/upload` - Upload video file to server
- `/api/post/upload/chunk` - Upload video chunk to TikTok
- `/api/post/status/<publish_id>` - Check post status

## Security Considerations

- CSRF protection using state parameter
- Secure session management
- Environment variables for sensitive data
- HTTPS required for production deployment

## Production Deployment

1. Set secure environment variables
2. Use HTTPS for all endpoints
3. Update redirect URI in TikTok app settings
4. Configure proper session storage (Redis recommended)

## Next Steps

- Implement token refresh mechanism
- Add content scheduling functionality
- Integrate TikTok Content Posting API
- Add database for storing scheduled posts
- Implement webhook handlers for post status updates