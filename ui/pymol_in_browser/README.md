# Remote PyMOL Streaming (VDI Pattern)

Browser-based access to full PyMOL via VNC/noVNC streaming.

## Architecture

- PyMOL runs on server with GPU support (VirtualGL optional)
- VNC server provides desktop session
- noVNC gateway streams to browser
- Nginx reverse proxy with authentication

## Quick Start

```bash
# Build and start services
docker-compose up -d

# Access PyMOL in browser
open http://localhost:8080
```

**Note:** Runs without password by default for easier access. To enable password protection, uncomment `VNC_PASSWORD` in docker-compose.yml.

## Components

- `Dockerfile`: PyMOL + VNC server + noVNC
- `docker-compose.yml`: Service orchestration
- `nginx.conf`: Reverse proxy with auth
- `startup.sh`: Session initialization

## Security Notes

⚠️ **Production Requirements:**
- Enable VNC password (uncomment VNC_PASSWORD in docker-compose.yml)
- Enable SSL/TLS (add certificates)
- Implement proper authentication (OAuth, LDAP, etc.)
- Add session isolation per user
- Enable audit logging
- Configure firewall rules
- Limit concurrent sessions
- Use reverse proxy with authentication (nginx/traefik)

## GPU Support

For GPU acceleration, add to docker-compose.yml:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

Requires: nvidia-docker2, VirtualGL configuration
