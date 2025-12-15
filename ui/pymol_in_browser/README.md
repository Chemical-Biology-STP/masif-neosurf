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

Default password: `pymol123` (change in docker-compose.yml)

## Components

- `Dockerfile`: PyMOL + VNC server + noVNC
- `docker-compose.yml`: Service orchestration
- `nginx.conf`: Reverse proxy with auth
- `startup.sh`: Session initialization

## Security Notes

⚠️ **Production Requirements:**
- Change default VNC password
- Enable SSL/TLS (add certificates)
- Implement proper authentication (OAuth, LDAP, etc.)
- Add session isolation per user
- Enable audit logging
- Configure firewall rules
- Limit concurrent sessions

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
