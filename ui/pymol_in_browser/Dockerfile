FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1
ENV VNC_RESOLUTION=1280x1024
ENV VNC_DEPTH=24

# Install PyMOL, VNC, and desktop environment
RUN apt-get update && apt-get install -y \
    pymol \
    x11vnc \
    xvfb \
    fluxbox \
    novnc \
    websockify \
    net-tools \
    tigervnc-common \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create VNC directory
RUN mkdir -p /root/.vnc

# Copy startup script
COPY startup.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/startup.sh

EXPOSE 5901 6080

CMD ["/usr/local/bin/startup.sh"]
