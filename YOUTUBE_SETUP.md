# YouTube API Setup Guide

This guide will help you set up YouTube API access for uploading videos directly from the Postcard Video Creator.

## Prerequisites

1. **Install Required Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Google Account**
   - You need a Google account that has access to the YouTube channel you want to upload to

## Step 1: Create Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter a project name (e.g., "Postcard Video Uploader")
4. Click "Create"

## Step 2: Enable YouTube Data API v3

1. In your Google Cloud project, go to "APIs & Services" → "Library"
2. Search for "YouTube Data API v3"
3. Click on it and press "Enable"

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" (unless you have a Google Workspace account)
3. Fill in the required information:
   - **App name**: Postcard Video Creator
   - **User support email**: Your email
   - **Developer contact information**: Your email
4. Save and continue through the steps
5. Add your email to "Test users" if the app is in testing mode

## Step 4: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Choose "Desktop application"
4. Give it a name (e.g., "Postcard Video Creator")
5. Click "Create"
6. Download the JSON file
7. **Important**: Rename the downloaded file to `client_secrets.json`
8. Place `client_secrets.json` in the same folder as `postcard_video_creator.py`

## Step 5: Using the YouTube Upload Feature

1. Launch the Postcard Video Creator
2. Click "📺 Upload to YouTube" button
3. Click "Authenticate" - this will open your web browser
4. Sign in to your Google account and grant permissions
5. The app will show your available channels and allow you to select one
6. If you have multiple channels, choose your preferred channel from the dropdown
7. Click "Set as Default" to save your preferred channel for future uploads
8. Select videos to upload:
   - "Add Videos": Browse and select video files manually
   - "Add Current Part Videos": Add all videos from your current batch
9. Configure upload settings:
   - **Privacy**: Choose "unlisted" (default), "private", or "public"
   - **Playlist**: Select a playlist or "None"
   - **Title Template**: Use `{filename}` as placeholder for the video filename
   - **Description**: Enter a description for all videos
10. Click "Start Upload"

## Important Notes

### File Security
- Keep `client_secrets.json` secure and don't share it
- Add `client_secrets.json` and `youtube_token.pickle` to your `.gitignore` file
- The `youtube_token.pickle` file stores your authentication and will be created automatically

### Privacy Settings
- **Unlisted**: Videos are not publicly searchable but can be viewed with the link
- **Private**: Only you can view the videos
- **Public**: Videos are publicly visible and searchable

### Upload Limits
- YouTube has daily upload quotas
- Large files may take time to upload
- The app uploads videos one at a time with progress tracking

### Playlist Management
- **Channel-specific playlists**: Only playlists for the selected channel are shown
- **Auto-create new playlists**: Type a new playlist name and it will be created automatically
- **Existing playlists**: Select from dropdown of playlists that already exist for the channel
- Use "Refresh Playlists" to update the dropdown after creating playlists elsewhere
- The status label shows which channel's playlists are currently displayed
- New playlists are created as "Unlisted" by default
- Videos will be added to the selected/created playlist automatically

### Multi-Channel Support
- If you manage multiple YouTube channels, all will be shown in the Channel dropdown
- Channels are displayed with their name and custom URL (if available)
- Select your preferred channel from the dropdown before uploading
- Use "Set as Default" to save your preferred channel - it will be marked with [DEFAULT]
- Your default channel will be automatically selected when you authenticate
- Each channel has its own playlists and upload settings

## Troubleshooting

### "YouTube API libraries not available"
Run: `pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client`

### "client_secrets.json file not found"
Make sure the credentials file is named exactly `client_secrets.json` and is in the same folder as the main Python file.

### Authentication fails
1. Check that the OAuth consent screen is properly configured
2. Make sure your email is added to test users if the app is in testing mode
3. Try deleting `youtube_token.pickle` and re-authenticating

### Upload fails
1. Check your internet connection
2. Verify the video file is not corrupted
3. Check YouTube's supported file formats and size limits
4. Ensure you haven't exceeded daily quotas

## File Format Support

The YouTube uploader supports common video formats:
- MP4 (recommended)
- AVI
- MOV
- MKV
- WMV

For best results, use MP4 format which is what the Postcard Video Creator generates.
