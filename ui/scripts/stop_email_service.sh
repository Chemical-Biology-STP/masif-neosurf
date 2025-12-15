#!/bin/bash
# Stop the email notification service

cd "$(dirname "$0")"

if [ ! -f email_service.pid ]; then
    echo "Email notification service is not running (no PID file found)"
    exit 0
fi

PID=$(cat email_service.pid)

if ps -p $PID > /dev/null 2>&1; then
    echo "Stopping email notification service (PID: $PID)..."
    kill $PID
    
    # Wait for process to stop
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # Force kill if still running
    if ps -p $PID > /dev/null 2>&1; then
        echo "Force killing process..."
        kill -9 $PID
    fi
    
    rm email_service.pid
    echo "Email notification service stopped"
else
    echo "Process $PID is not running, removing stale PID file"
    rm email_service.pid
fi
