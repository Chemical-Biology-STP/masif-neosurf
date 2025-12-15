# PyMOL VDI Integration

This document describes how to set up and use the PyMOL in-browser visualization feature for MaSIF-neosurf results.

## Overview

The PyMOL VDI (Virtual Desktop Infrastructure) integration allows users to visualize their MaSIF-neosurf results directly in the browser without installing any software. It uses:

- **PyMOL** running in a Docker container
- **VNC server** for remote desktop access
- **noVNC** for browser-based VNC client
- **Nginx** reverse proxy with security
- **Xvfb** for virtual display
- **Fluxbox** for window management

## Architecture

```
User Browser
    ↓
Flask Web UI (Port 5000)
    ↓
PyMOL VDI Container (Port 6080)
    ├── VNC Server
    ├── noVNC Web Client
    ├── PyMOL Application
    └── Shared Volume (/pymol-shared)
         └── Session Data
              ├── PDB files
              ├── PLY surface files
              └── PyMOL scripts
```

## Setup

### 1. Prerequisites

- Docker and Docker Compose installed
- PyMOL VDI Docker image built or available
- Sufficient disk space for session data

### 2. Automatic Container Management

**NEW:** The Flask app now automatically checks and starts the PyMOL VDI container on startup!

When you start the Flask app, it will:
1. Check if Docker is available
2. Check if the PyMOL VDI container is running
3. Automatically start the container if it's stopped
4. Create the container if it doesn't exist

**Startup Output:**
```
============================================================
Checking PyMOL VDI Container Status
============================================================
Container status: running
✓ PyMOL VDI container is already running
============================================================
```

If the container is stopped, you'll see:
```
⚠️  PyMOL VDI container exists but is stopped
   Attempting to start...
✓ PyMOL VDI container started successfully
```

**Manual Control:**
You can still manually control the container:
```bash
# Start
docker-compose up -d pymol-vdi

# Stop
docker-compose stop pymol-vdi

# Restart
docker-compose restart pymol-vdi

# View logs
docker-compose logs pymol-vdi
```

### 3. Configuration

Edit `ui/.env`:

```bash
# Enable PyMOL visualization
PYMOL_VDI_ENABLED=true

# PyMOL VDI URL (internal Docker network)
PYMOL_VDI_URL=http://pymol-vdi:6080

# Shared volume path
PYMOL_SHARED_VOLUME=/pymol-shared

# Session timeout in seconds (default: 1 hour)
PYMOL_SESSION_TIMEOUT=3600
```

### 3. Docker Compose Deployment

```bash
cd ui
docker-compose up -d
```

This will start:
- MaSIF web interface on port 5000
- PyMOL VDI on port 6080

### 4. Standalone Deployment

If running services separately:

```bash
# Start PyMOL VDI
docker run -d \
  --name pymol-vdi \
  -p 6080:6080 \
  -v /path/to/pymol-shared:/data:ro \
  your-pymol-vdi-image:latest

# Update .env
PYMOL_VDI_URL=http://localhost:6080
PYMOL_SHARED_VOLUME=/path/to/pymol-shared

# Start Flask app
python app.py
```

## Usage

### For Users

1. **Submit a job** through the web interface
2. **Wait for completion** - visualization is only available for completed jobs
3. **Click "Visualize in PyMOL"** on the job details page
4. **Wait for session preparation** - files are downloaded from HPC and prepared
5. **Interact with PyMOL** in the embedded viewer:
   - Rotate: Left-click and drag
   - Zoom: Scroll wheel
   - Pan: Right-click and drag
   - Type commands in PyMOL console for advanced features

### Session Management

- Each user gets an isolated session
- Sessions auto-expire after the configured timeout
- Sessions are automatically cleaned up when:
  - User clicks "Close Viewer"
  - User navigates away from the page
  - Session timeout is reached

### What Gets Loaded

The PyMOL script automatically loads:

1. **PDB structure** - Original protein structure (if available)
2. **Surface files (.ply)** - MaSIF-neosurf generated surfaces
   - Target surfaces (colored red)
   - Ligand surfaces (colored yellow)
   - Other surfaces (colored green)

## PyMOL Script

The auto-generated script (`load_results.pml`) includes:

```python
# Set up nice rendering
bg_color white
set antialias, 2
set surface_quality, 2
set transparency, 0.3

# Load structures
load protein.pdb, protein
load surface.ply, surface

# Color and style
color cyan, protein
show cartoon, protein
color red, surface

# Optimize view
zoom
center
```

## Security Considerations

### Session Isolation

- Each session has a unique ID: `{user_id}_{job_uuid}_{timestamp}`
- Users can only access their own sessions
- Admins can access all sessions

### File Access

- Job files are copied to session directory (not symlinked)
- PyMOL container has read-only access to shared volume
- Sessions are in isolated directories

### Cleanup

- Automatic cleanup on session close
- Periodic cleanup of expired sessions (recommended cron job)
- Manual cleanup via admin interface

## Troubleshooting

### PyMOL doesn't load

**Check if PyMOL VDI is enabled:**
```bash
grep PYMOL_VDI_ENABLED .env
```

**Check if PyMOL VDI container is running:**
```bash
docker ps | grep pymol-vdi
```

**Check PyMOL VDI logs:**
```bash
docker logs pymol-vdi
```

### Files not appearing

**Verify files were downloaded from HPC:**
```bash
ls -la outputs/job_name_uuid/
```

**Check shared volume permissions:**
```bash
ls -la /pymol-shared/
```

**Check session directory:**
```bash
ls -la /pymol-shared/{session_id}/data/
```

### Session expired immediately

**Check timeout configuration:**
```bash
grep PYMOL_SESSION_TIMEOUT .env
```

**Increase timeout if needed:**
```bash
PYMOL_SESSION_TIMEOUT=7200  # 2 hours
```

### Clipboard paste not working in VNC

This is a known limitation of browser-based VNC clients. **Workarounds:**

1. **Use the Copy Command button** on the web interface, then:
   - Try `Ctrl+Shift+V` in the PyMOL console
   - Try right-click → Paste in the PyMOL console
   
2. **Type manually with Tab autocomplete:**
   - Type `@/data/` in PyMOL console
   - Press `Tab` to see available sessions
   - Select your session folder
   - Type `/load_results.pml` and press Enter

3. **Use noVNC clipboard feature:**
   - Click the clipboard icon in the noVNC sidebar (left side of viewer)
   - Paste the command into the noVNC clipboard panel
   - The text will be sent to the VNC session

4. **Configure browser clipboard permissions:**
   - Some browsers require explicit clipboard permissions
   - Check browser settings for clipboard access

### Performance issues

**Reduce surface quality in PyMOL:**
```python
set surface_quality, 0
```

**Limit concurrent sessions:**
- Implement rate limiting per user
- Set maximum concurrent sessions

**Increase container resources:**
```yaml
pymol-vdi:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
```

## Maintenance

### Cleanup Old Sessions

Create a cron job to clean up expired sessions:

```bash
#!/bin/bash
# cleanup-pymol-sessions.sh

SHARED_VOLUME="/pymol-shared"
CURRENT_TIME=$(date +%s)

for session_dir in "$SHARED_VOLUME"/*; do
    if [ -f "$session_dir/session.json" ]; then
        expires_at=$(jq -r '.expires_at' "$session_dir/session.json")
        if [ "$CURRENT_TIME" -gt "$expires_at" ]; then
            echo "Cleaning up expired session: $(basename $session_dir)"
            rm -rf "$session_dir"
        fi
    fi
done
```

Add to crontab:
```bash
# Run every hour
0 * * * * /path/to/cleanup-pymol-sessions.sh
```

### Monitor Usage

Track PyMOL session usage:

```bash
# Count active sessions
ls -1 /pymol-shared/ | wc -l

# Check disk usage
du -sh /pymol-shared/

# List sessions by user
for dir in /pymol-shared/*; do
    jq -r '.user_id' "$dir/session.json" 2>/dev/null
done | sort | uniq -c
```

## Advanced Configuration

### Custom PyMOL Startup

Modify `generate_pymol_script()` in `app.py` to customize:
- Color schemes
- Rendering settings
- Default views
- Custom selections

### Multiple PyMOL Instances

For high-traffic deployments, run multiple PyMOL VDI containers:

```yaml
services:
  pymol-vdi-1:
    image: your-pymol-vdi-image
    ports:
      - "6081:6080"
  
  pymol-vdi-2:
    image: your-pymol-vdi-image
    ports:
      - "6082:6080"
```

Implement load balancing in Flask app.

### Integration with Load Balancer

Use Nginx to load balance PyMOL sessions:

```nginx
upstream pymol_backend {
    least_conn;
    server pymol-vdi-1:6080;
    server pymol-vdi-2:6080;
}

location /pymol/ {
    proxy_pass http://pymol_backend/;
}
```

## API Reference

### Check PyMOL Health

```
GET /api/pymol-health
```

**Response:**
```json
{
    "enabled": true,
    "status": "running",
    "message": "PyMOL VDI container is running",
    "url": "http://localhost:6080",
    "can_start": false
}
```

**Status values:**
- `running` - Container is up and running
- `stopped` - Container exists but is stopped
- `not_found` - Container doesn't exist
- `disabled` - PyMOL is disabled in config
- `error` - Error checking status

### Start PyMOL Container (Admin Only)

```
POST /api/pymol-start
```

**Response:**
```json
{
    "success": true,
    "message": "PyMOL VDI container started successfully"
}
```

### Prepare PyMOL Session

```
GET /api/prepare-pymol-session/<job_uuid>
```

**Response:**
```json
{
    "success": true,
    "pymol_url": "http://pymol-vdi:6080/vnc.html?autoconnect=true&resize=scale",
    "session_id": "user123_job456_1234567890",
    "script_path": "/data/user123_job456_1234567890/load_results.pml",
    "expires_in": 3600
}
```

### Cleanup PyMOL Session

```
POST /api/cleanup-pymol-session/<session_id>
```

**Response:**
```json
{
    "success": true,
    "message": "Session cleaned up successfully"
}
```

## Support

For issues or questions:
- Check the troubleshooting section above
- Review Flask app logs: `tail -f logs/app.log`
- Review PyMOL VDI logs: `docker logs pymol-vdi`
- Contact: yewmun.yip@crick.ac.uk
