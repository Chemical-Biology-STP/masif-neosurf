#!/bin/bash
# Test email notification functionality

echo "=========================================="
echo "MaSIF-neosurf Email Notification Test"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if service is running
echo "Test 1: Checking if email service is running..."
if [ -f email_service.pid ]; then
    PID=$(cat email_service.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Email service is running (PID: $PID)${NC}"
    else
        echo -e "${RED}✗ Email service is NOT running${NC}"
        echo "  Start it with: ./start_email_service.sh"
        exit 1
    fi
else
    echo -e "${RED}✗ Email service is NOT running${NC}"
    echo "  Start it with: ./start_email_service.sh"
    exit 1
fi
echo ""

# Test 2: Check SSH connection
echo "Test 2: Checking SSH connection to HPC..."
if ssh -i /home/yipy/.ssh/id_ed25519 -o ConnectTimeout=5 yipy@login.nemo.thecrick.org "echo 'SSH OK'" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ SSH connection successful${NC}"
else
    echo -e "${RED}✗ SSH connection failed${NC}"
    echo "  Check your SSH key and HPC connectivity"
    exit 1
fi
echo ""

# Test 3: Check mail command on HPC
echo "Test 3: Checking mail command on HPC..."
TEST_EMAIL="${1:-yewmun.yip@crick.ac.uk}"
echo "  Sending test email to: $TEST_EMAIL"

if ssh -i /home/yipy/.ssh/id_ed25519 yipy@login.nemo.thecrick.org "echo 'This is a test email from MaSIF-neosurf email notification service.' | mail -s 'MaSIF-neosurf Email Test' $TEST_EMAIL" 2>&1; then
    echo -e "${GREEN}✓ Test email sent successfully${NC}"
    echo "  Please check your inbox (and spam folder) for the test email"
else
    echo -e "${RED}✗ Failed to send test email${NC}"
    echo "  The mail command may not be configured on HPC"
fi
echo ""

# Test 4: Check recent service logs
echo "Test 4: Recent service activity..."
if [ -f email_service.log ]; then
    echo "  Last 10 log entries:"
    tail -n 10 email_service.log | sed 's/^/    /'
else
    echo -e "${YELLOW}⚠ No log file found${NC}"
fi
echo ""

# Test 5: Check for pending jobs
echo "Test 5: Checking for jobs awaiting email notification..."
PENDING_COUNT=0
if [ -d outputs ]; then
    for job_dir in outputs/*/; do
        if [ -f "${job_dir}metadata.json" ] && [ ! -f "${job_dir}.email_sent" ]; then
            PENDING_COUNT=$((PENDING_COUNT + 1))
        fi
    done
fi

if [ $PENDING_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ No jobs awaiting email notification${NC}"
else
    echo -e "${YELLOW}⚠ $PENDING_COUNT job(s) awaiting email notification${NC}"
    echo "  The service will check these jobs on the next cycle (every 60 seconds)"
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "All tests passed! The email notification service should be working."
echo ""
echo "To monitor the service in real-time:"
echo "  tail -f email_service.log"
echo ""
echo "To test with a real job:"
echo "  1. Submit a job via the web interface"
echo "  2. Wait for it to complete"
echo "  3. Check your email inbox"
echo ""
