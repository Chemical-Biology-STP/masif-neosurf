# PyMOL Integration Fixes

## Issues Fixed

### 1. Duplicate Session Directories ✅

**Problem:** When relaunching PyMOL for the same job, duplicate directories were created in the shared volume.

**Solution:** 
- Implemented `cleanup_old_sessions()` function that removes old session directories before creating new ones
- Pattern matching: `{user_id}_{job_uuid}_*` ensures only sessions for the same user and job are cleaned up
- Called automatically before creating a new session in `prepare_pymol_session()`

**Code Location:** `ui/app.py` lines 1259-1275

### 2. Clipboard Paste Not Working ⚠️ (Workarounds Provided)

**Problem:** Users cannot paste the PyMOL command into the VNC session using standard clipboard operations.

**Root Cause:** Browser-based VNC clients have limited clipboard integration due to browser security restrictions.

**Solutions Implemented:**

#### A. Improved Copy Button
- Enhanced copy-to-clipboard functionality with fallback methods
- Better visual feedback when command is copied
- Works with modern browsers using Clipboard API

#### B. Multiple Loading Methods Documented
The UI now provides clear instructions for 3 methods:

1. **Copy & Paste (Recommended)**
   - Copy command button
   - Try `Ctrl+Shift+V` or right-click → Paste
   - Clear visual instructions

2. **Manual Typing with Autocomplete**
   - Type `@/data/` then press Tab
   - Select session folder from autocomplete
   - Type `/load_results.pml`

3. **noVNC Clipboard Panel** (documented in help)
   - Use the clipboard icon in noVNC sidebar
   - Paste into noVNC clipboard panel
   - Text is sent to VNC session

#### C. Enhanced UI/UX
- Redesigned instruction panel with better visual hierarchy
- Color-coded sections (blue for primary method, gray for alternative)
- Added keyboard shortcuts with visual `<kbd>` tags
- Included tips for different paste methods

**Code Locations:**
- `ui/templates/job_details.html` - Updated instructions and copy function
- `ui/docs/PYMOL_INTEGRATION.md` - Troubleshooting section

## Testing Checklist

- [x] Code syntax validation (no errors)
- [ ] Test session creation
- [ ] Test duplicate session cleanup
- [ ] Test copy command button
- [ ] Test PyMOL script loading
- [ ] Test session expiry timer
- [ ] Test session cleanup on close

## User Experience Improvements

1. **Better Instructions**
   - Step-by-step numbered instructions
   - Visual keyboard shortcuts
   - Multiple methods provided
   - Tips and warnings clearly marked

2. **Session Management**
   - Automatic cleanup of old sessions
   - Clear session ID display
   - Expiry countdown timer
   - Warning about session lifecycle

3. **Visual Feedback**
   - Copy button changes to "✓ Copied!" with green background
   - Loading modal during session preparation
   - Clear status messages

## Known Limitations

1. **Clipboard Integration**
   - Browser security restrictions limit clipboard access in iframes
   - VNC clipboard synchronization is not perfect
   - Users may need to use alternative methods

2. **Session Persistence**
   - Sessions expire after timeout
   - Relaunching creates a new session (old one is cleaned up)
   - Files are copied (not symlinked) which uses more disk space

## Future Enhancements

1. **Auto-load Script**
   - Investigate PyMOL startup script options
   - Pre-load results without user interaction
   - Requires PyMOL VDI container configuration

2. **Clipboard Proxy**
   - Implement server-side clipboard proxy
   - Sync clipboard between browser and VNC
   - Requires additional infrastructure

3. **Session Pooling**
   - Pre-warm PyMOL sessions for faster loading
   - Reuse sessions instead of creating new ones
   - Implement session queue management

4. **Cron Job for Cleanup**
   - Automated cleanup of expired sessions
   - Disk space monitoring
   - Usage statistics collection

## Documentation Updates

- ✅ Updated `ui/docs/PYMOL_INTEGRATION.md` with troubleshooting section
- ✅ Added clipboard workarounds
- ✅ Documented session cleanup behavior
- ✅ Created this fixes summary document

## Contact

For questions or issues:
- Email: yewmun.yip@crick.ac.uk
- Check logs: `ui/logs/app.log`
- Check PyMOL container: `docker logs ui_pymol-vdi_1`
