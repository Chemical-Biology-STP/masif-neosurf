# Docker Container Auto-Management

## Overview

The Flask app now automatically manages the PyMOL VDI Docker container, checking its status on startup and starting it if needed. This eliminates the need for manual container management in most cases.

## Features

### 1. Automatic Startup Check

When the Flask app starts, it automatically:

1. **Checks Docker availability**
   - Verifies Docker is installed and accessible
   - Disables PyMOL if Docker is not available

2. **Checks container status**
   - Looks for PyMOL VDI container
   - Determines if it's running, stopped, or missing

3. **Starts container if needed**
   - Automatically starts stopped containers
   - Creates and starts missing containers
   - Uses docker-compose for proper configuration

### 2. Startup Output

The app provides clear feedback during startup:

**When container is running:**
```
============================================================
Checking PyMOL VDI Container Status
============================================================
Container status: running
✓ PyMOL VDI container is already running
============================================================
```

**When container needs to be started:**
```
============================================================
Checking PyMOL VDI Container Status
============================================================
Container status: stopped
⚠️  PyMOL VDI container exists but is stopped
   Attempting to start...
✓ PyMOL VDI container started successfully
============================================================
```

**When Docker is not available:**
```
============================================================
Checking PyMOL VDI Container Status
============================================================
⚠️  Docker is not available on this system
   PyMOL visualization will not work
============================================================
```

## Implementation

### Functions Added

**`check_docker_available()`**
- Checks if Docker command is available
- Returns: `bool`

**`check_pymol_container_status()`**
- Checks container status using `docker ps`
- Returns: `'running'`, `'stopped'`, `'not_found'`, or `'error'`

**`start_pymol_container()`**
- Starts container using `docker-compose up -d pymol-vdi`
- Returns: `(success: bool, message: str)`

**`ensure_pymol_container_running()`**
- Main orchestration function
- Called during Flask app initialization
- Handles all startup logic

### API Endpoints

**`GET /api/pymol-health`**
- Check current container status
- Available to all logged-in users
- Returns status and diagnostic information

**`POST /api/pymol-start`** (Admin only)
- Manually start the container
- Useful for troubleshooting
- Returns success/error message

## Usage

### Normal Operation

Simply start the Flask app as usual:

```bash
cd ui
pixi run python app.py
```

The app will automatically handle the PyMOL container.

### Manual Container Control

You can still manually control the container if needed:

```bash
# Start container
docker-compose up -d pymol-vdi

# Stop container
docker-compose stop pymol-vdi

# Restart container
docker-compose restart pymol-vdi

# View logs
docker-compose logs -f pymol-vdi

# Check status
docker ps | grep pymol
```

### Health Check

Check container status via API:

```bash
curl -X GET http://localhost:5000/api/pymol-health \
  -H "Cookie: session=your_session_cookie"
```

Response:
```json
{
  "enabled": true,
  "status": "running",
  "message": "PyMOL VDI container is running",
  "url": "http://localhost:6080",
  "can_start": false
}
```

### Manual Start (Admin)

Start container via API (admin only):

```bash
curl -X POST http://localhost:5000/api/pymol-start \
  -H "Cookie: session=your_admin_session_cookie"
```

## Configuration

The auto-management respects your configuration in `.env`:

```bash
# Enable/disable PyMOL
PYMOL_VDI_ENABLED=true

# Container URL
PYMOL_VDI_URL=http://localhost:6080

# Shared volume path
PYMOL_SHARED_VOLUME=./pymol-shared

# Session timeout
PYMOL_SESSION_TIMEOUT=3600
```

If `PYMOL_VDI_ENABLED=false`, the auto-management is skipped.

## Troubleshooting

### Container Won't Start

**Check Docker:**
```bash
docker --version
docker ps
```

**Check docker-compose:**
```bash
docker-compose --version
cd ui
docker-compose config
```

**Check logs:**
```bash
cd ui
docker-compose logs pymol-vdi
```

**Manual start:**
```bash
cd ui
docker-compose up -d pymol-vdi
```

### Permission Issues

If you get permission errors:

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then test
docker ps
```

### Container Exists but Won't Start

```bash
# Remove old container
docker-compose down pymol-vdi

# Recreate
docker-compose up -d pymol-vdi
```

### Port Already in Use

If port 6080 is already in use:

1. Find what's using it:
   ```bash
   sudo lsof -i :6080
   ```

2. Either stop that service or change the port in `docker-compose.yml`:
   ```yaml
   pymol-vdi:
     ports:
       - "6081:6080"  # Use different external port
   ```

3. Update `.env`:
   ```bash
   PYMOL_VDI_URL=http://localhost:6081
   ```

## Testing

Test the Docker management functions:

```bash
cd ui
python test_docker_management.py
```

Expected output:
```
============================================================
Docker Management Test
============================================================

1. Checking Docker availability...
   ✓ Docker is available
   Docker version 28.2.2, build e6534b4

2. Checking PyMOL container status...
   Status: running
   ✓ Container is running

3. Checking docker-compose.yml...
   ✓ Found: /path/to/ui/docker-compose.yml
   ✓ pymol-vdi service is defined

4. Checking shared volume...
   ✓ Found: /path/to/ui/pymol-shared
   Sessions: 0

============================================================
Test completed!
============================================================
```

## Benefits

1. **Convenience** - No need to manually start containers
2. **Reliability** - Container is always running when needed
3. **Error Prevention** - Clear feedback if something is wrong
4. **Debugging** - Health check API for troubleshooting
5. **Flexibility** - Manual control still available

## Limitations

1. **Requires Docker** - Won't work without Docker installed
2. **Requires docker-compose** - Uses docker-compose for container management
3. **Startup Delay** - May add 2-5 seconds to Flask startup time
4. **No Auto-Restart** - If container crashes, requires Flask restart or manual start

## Future Enhancements

1. **Container Health Monitoring** - Periodic health checks during runtime
2. **Auto-Restart** - Automatically restart crashed containers
3. **Resource Monitoring** - Track container CPU/memory usage
4. **Multiple Containers** - Support for load-balanced PyMOL instances
5. **Graceful Shutdown** - Stop container when Flask app stops

## Security Considerations

- Container start requires docker-compose access
- Admin-only API endpoint for manual start
- No exposure of Docker socket to users
- Container runs with limited privileges

## Performance Impact

- **Startup Time:** +2-5 seconds (one-time check)
- **Runtime:** No impact (check only on startup)
- **Resource Usage:** Minimal (subprocess calls only)

## Conclusion

The Docker auto-management feature makes PyMOL visualization more reliable and easier to use by eliminating manual container management. The Flask app now handles container lifecycle automatically while still providing manual control when needed.

---

**Related Documentation:**
- [PyMOL Integration Guide](PYMOL_INTEGRATION.md)
- [PyMOL User Guide](PYMOL_USER_GUIDE.md)
- [PyMOL Final Summary](PYMOL_FINAL_SUMMARY.md)
