#!/bin/bash
# Start the email notification service in the background

cd "$(dirname "$0")"

# Check if service is already running
if [ -f email_service.pid ]; then
    PID=$(cat email_service.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Email notification service is already running (PID: $PID)"
        exit 0
    else
        echo "Removing stale PID file"
        rm email_service.pid
    fi
fi

# Start the service
echo "Starting email notification service..."
nohup pixi run python email_notification_service.py > email_service.log 2>&1 &
PID=$!

# Save PID
echo $PID > email_service.pid

echo "Email notification service started (PID: $PID)"
echo "Logs: ui/email_service.log"
echo ""
echo "To stop the service, run: ./stop_email_service.sh"
echo "To view logs, run: tail -f email_service.log"
