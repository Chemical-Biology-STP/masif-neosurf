# PyMOL VDI Docker Image - Build Instructions

## Overview

This directory contains the Docker build files for creating the PyMOL VDI (Virtual Desktop Infrastructure) container image used by the MaSIF-neosurf web interface.

## Prerequisites

- Docker installed (version 20.10 or later)
- Docker Compose installed (version 1.29 or later)
- At least 2GB free disk space
- Internet connection for downloading base images

## Quick Build

### Option 1: Using docker-compose (Recommended)

```bash
cd ui/pymol_in_browser
docker-compose build
```

This will create the image: `pymol_in_browser_pymol-vnc:latest`

### Option 2: Using docker build directly

```bash
cd ui/pymol_in_browser
docker build -t pymol_in_browser_pymol-vnc:latest .
```

## Testing the Image

After building, test the image locally:

```bash
cd ui/pymol_in_browser
docker-compose up -d
```

Then open your browser to:
- **noVNC Interface:** http://localhost:6080 (no password required)
- **Direct VNC:** vnc://localhost:5901 (no password required)
- **Nginx Proxy:** http://localhost:8080

To stop the test:
```bash
docker-compose down
```

## Using with MaSIF Web Interface

Once built, the image will be automatically used by the main application:

```bash
cd ui
docker-compose up -d
```

The main `ui/docker-compose.yml` references this image as `pymol_in_browser_pymol-vnc:latest`.

## Build Configuration

### Environment Variables

Edit `.env` or set in docker-compose.yml:

- `VNC_PASSWORD` - Password for VNC access (default: none/passwordless)
- `VNC_RESOLUTION` - Screen resolution (default: `1280x1024`)
- `VNC_DEPTH` - Color depth (default: `24`)

**Note:** By default, VNC runs without a password for easier access. To enable password protection, uncomment the `VNC_PASSWORD` line in docker-compose.yml.

### GPU Support (Optional)

For GPU-accelerated rendering, uncomment the GPU section in `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

**Requirements:**
- NVIDIA GPU
- nvidia-docker2 installed
- NVIDIA Container Toolkit configured

## Image Contents

The built image includes:

- **Base:** Ubuntu 22.04
- **PyMOL:** Latest version from conda-forge
- **VNC Server:** TigerVNC
- **noVNC:** Browser-based VNC client
- **Window Manager:** Fluxbox (lightweight)
- **Display Server:** Xvfb (virtual framebuffer)

## Customization

### Adding Python Packages

Edit `Dockerfile` and add to the conda install line:

```dockerfile
RUN conda install -c conda-forge pymol-open-source numpy scipy your-package
```

### Changing PyMOL Version

Specify version in `Dockerfile`:

```dockerfile
RUN conda install -c conda-forge pymol-open-source=2.5.0
```

### Custom Startup Scripts

Edit `startup.sh` to add initialization commands that run when the container starts.

## Troubleshooting

### Build Fails

**Check Docker version:**
```bash
docker --version
docker-compose --version
```

**Clean build (no cache):**
```bash
docker-compose build --no-cache
```

**Check disk space:**
```bash
df -h
```

### Image Too Large

The image is approximately 1.5-2GB. To reduce size:

1. Use multi-stage builds
2. Clean conda cache in Dockerfile
3. Remove unnecessary packages

### VNC Connection Issues

**Test VNC server:**
```bash
docker-compose up
docker-compose logs pymol-vnc
```

**Check ports:**
```bash
docker ps
netstat -tulpn | grep 6080
```

## Security Notes

⚠️ **For Production Use:**

1. **Enable VNC password (recommended for production):**
   ```yaml
   environment:
     - VNC_PASSWORD=your-secure-password
   ```
   By default, VNC runs without password for easier development/testing.

2. **Enable SSL/TLS:**
   - Add certificates to nginx.conf
   - Uncomment HTTPS port in docker-compose.yml

3. **Implement authentication:**
   - Add OAuth/LDAP to nginx
   - Use session tokens

4. **Network isolation:**
   - Use Docker networks
   - Configure firewall rules

5. **Resource limits:**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
   ```

## Updating the Image

To update PyMOL or dependencies:

1. Edit `Dockerfile`
2. Rebuild:
   ```bash
   docker-compose build --no-cache
   ```
3. Test the new image
4. Update main application:
   ```bash
   cd ../
   docker-compose restart pymol-vdi
   ```

## Distribution

### Saving Image

To share the image without rebuilding:

```bash
docker save pymol_in_browser_pymol-vnc:latest | gzip > pymol-vdi.tar.gz
```

### Loading Image

On another machine:

```bash
gunzip -c pymol-vdi.tar.gz | docker load
```

### Pushing to Registry

To use a container registry:

```bash
# Tag for registry
docker tag pymol_in_browser_pymol-vnc:latest your-registry/pymol-vdi:latest

# Push
docker push your-registry/pymol-vdi:latest

# Update docker-compose.yml to use registry image
```

## Performance Optimization

### Build Time

- Use Docker BuildKit:
  ```bash
  DOCKER_BUILDKIT=1 docker-compose build
  ```

### Runtime Performance

- Allocate more resources in docker-compose.yml
- Use SSD for Docker storage
- Enable GPU support if available
- Increase shared memory:
  ```yaml
  shm_size: '2gb'
  ```

## Support

For issues or questions:
- Check logs: `docker-compose logs pymol-vnc`
- Review Dockerfile for build errors
- Test with minimal configuration first
- Contact: yewmun.yip@crick.ac.uk

## Related Documentation

- [PyMOL Integration Guide](../docs/PYMOL_INTEGRATION.md)
- [Docker Auto-Management](../docs/DOCKER_AUTO_MANAGEMENT.md)
- [Main README](../README.md)
