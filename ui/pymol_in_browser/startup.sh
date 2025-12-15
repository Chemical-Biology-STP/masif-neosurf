#!/bin/bash
set -e

# Start Xvfb
Xvfb $DISPLAY -screen 0 ${VNC_RESOLUTION}x${VNC_DEPTH} &
sleep 2

# Start window manager
fluxbox &
sleep 1

# Set VNC password and start VNC server
if [ -n "$VNC_PASSWORD" ]; then
    mkdir -p /root/.vnc
    x11vnc -storepasswd "$VNC_PASSWORD" /root/.vnc/passwd
    x11vnc -display $DISPLAY -forever -shared -rfbauth /root/.vnc/passwd -rfbport 5900 &
else
    x11vnc -display $DISPLAY -forever -shared -nopw -rfbport 5900 &
fi
sleep 2

# Start noVNC with websockify
websockify --web=/usr/share/novnc 6080 localhost:5900 &
sleep 2

# Start PyMOL
DISPLAY=$DISPLAY pymol &

# Keep container running
wait
