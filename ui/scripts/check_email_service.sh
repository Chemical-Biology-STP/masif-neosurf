#!/bin/bash
# Check the status of the email notification service

cd "$(dirname "$0")"

if [ ! -f email_service.pid ]; then
    echo "❌ Email notification service is NOT running"
    exit 1
fi

PID=$(cat email_service.pid)

if ps -p $PID > /dev/null 2>&1; then
    echo "✅ Email notification service is running (PID: $PID)"
    echo ""
    echo "Recent log entries:"
    echo "===================="
    tail -n 20 email_service.log
    exit 0
else
    echo "❌ Email notification service is NOT running (stale PID file)"
    rm email_service.pid
    exit 1
fi
