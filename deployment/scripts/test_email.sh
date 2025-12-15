#!/bin/bash
# Test script to check if email works on HPC

# Replace with your email
YOUR_EMAIL="your.email@crick.ac.uk"

echo "Testing email functionality on HPC..."
echo "Sending test email to: $YOUR_EMAIL"

# Test 1: Simple mail command
echo "Test email from HPC" | mail -s "Test Email from MaSIF-neosurf" $YOUR_EMAIL

if [ $? -eq 0 ]; then
    echo "✓ Mail command executed successfully"
else
    echo "✗ Mail command failed with exit code: $?"
fi

# Test 2: Check if mail command exists
if command -v mail &> /dev/null; then
    echo "✓ 'mail' command is available"
    which mail
else
    echo "✗ 'mail' command not found"
fi

# Test 3: Check alternative mail commands
if command -v sendmail &> /dev/null; then
    echo "✓ 'sendmail' is available"
    which sendmail
fi

if command -v mailx &> /dev/null; then
    echo "✓ 'mailx' is available"
    which mailx
fi

echo ""
echo "Please check your email inbox for the test message."
echo "If you don't receive it, the HPC mail system may not be configured."
