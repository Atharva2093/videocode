# Known Issues & Limitations

## Video-Related Issues

### 1. Large Playlist Delays
**Issue**: Downloading large playlists (50+ videos) can take a long time and may timeout.

**Workaround**: 
- Select specific videos instead of entire playlist
- Download in smaller batches (10-20 videos at a time)
- Use the batch download feature with selected videos

### 2. Region-Locked Videos
**Issue**: Some videos are restricted to specific countries and cannot be downloaded.

**Error Message**: `Video unavailable in your country`

**Workaround**:
- Use a VPN to access the video from an allowed region
- Configure proxy settings in the backend (Phase 10.2)

### 3. Age-Restricted Videos
**Issue**: Videos that require age verification may fail to download.

**Workaround**:
- Configure YouTube cookies in yt-dlp
- Use authentication headers

### 4. Live Streams
**Issue**: Live streams cannot be downloaded directly.

**Status**: Not supported - must wait for stream to end

## Format-Related Issues

### 1. Browser MP4/MKV Support
**Issue**: Some browsers don't support certain video formats.

| Format | Chrome | Firefox | Safari | Edge |
|--------|--------|---------|--------|------|
| MP4 | ✅ | ✅ | ✅ | ✅ |
| WebM | ✅ | ✅ | ❌ | ✅ |
| MKV | ❌ | ❌ | ❌ | ❌ |

**Workaround**: Always convert to MP4 for maximum compatibility.

### 2. High-Quality Audio Codecs
**Issue**: Some high-quality audio formats (OPUS, FLAC) may not be supported on all devices.

**Workaround**: Use MP3 or M4A for maximum compatibility.

### 3. 4K/8K Video Downloads
**Issue**: Very high resolution videos may be slow to download and process.

**Note**: FFmpeg processing time increases significantly with resolution.

## PWA-Related Issues

### 1. iOS Safari Limitations
**Issue**: iOS has limited PWA support:
- No background downloads
- No push notifications
- Limited offline storage

**Workaround**: Use Chrome on iOS for better PWA support (still limited).

### 2. Service Worker Cache Limits
**Issue**: Browser may limit cache storage.

**Note**: Large downloaded files are not cached by service worker.

### 3. Install Prompt
**Issue**: Install prompt may not appear in all browsers.

**Requirements**:
- HTTPS connection
- Valid manifest.json
- Service worker registered
- User engagement threshold met

## Backend Issues

### 1. Rate Limiting
**Limits**:
- 30 requests per minute per IP
- 3 downloads per minute per IP

**Error Response**:
```json
{
    "detail": "Too many requests. Please slow down.",
    "error_code": "RATE_LIMIT_EXCEEDED",
    "retry_after": 60
}
```

### 2. File Size Limits
**Current Limit**: 2GB maximum file size

**Error Response**:
```json
{
    "detail": "File size exceeds maximum allowed (2GB)",
    "error_code": "FILE_TOO_LARGE"
}
```

### 3. Duration Limits
**Current Limit**: 2-hour maximum video duration

**Workaround**: Split long videos into segments (not currently supported).

### 4. Concurrent Downloads
**Limit**: 3 concurrent downloads per server instance

**Note**: Additional downloads are queued automatically.

## Mobile-Specific Issues

### 1. iOS Download Location
**Issue**: iOS doesn't allow direct file system access.

**Behavior**: Files open in browser's viewer, user must save manually.

### 2. Android Chrome Downloads
**Issue**: Large files may fail to download on older Android versions.

**Workaround**: Use smaller file sizes or mobile-optimized presets.

### 3. Mobile Data Usage
**Warning**: Video downloads consume significant data. WiFi recommended.

## Known Bugs

### Currently Open
1. QR code may fail to generate for very long URLs
2. Progress bar may jump back during format conversion
3. Theme toggle may flicker on initial page load

### Recently Fixed
- ~~Search results don't clear when switching modes~~ (Fixed in Phase 7)
- ~~Settings not persisting after refresh~~ (Fixed in Phase 7)

## Reporting Issues

To report a new issue:

1. Check if it's listed above
2. Include:
   - Browser/OS version
   - Video URL (if applicable)
   - Error message
   - Steps to reproduce
3. Submit via GitHub Issues

## Performance Tips

1. **Use mobile presets** for faster downloads on slower connections
2. **Select specific quality** instead of "best" for faster processing
3. **Clear browser cache** if experiencing issues
4. **Use desktop browser** for large downloads
5. **Enable auto-download** in settings for seamless experience
