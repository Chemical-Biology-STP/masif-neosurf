# MaSIF-neosurf Deployment Checklist

## Prerequisites

- [x] Flask app configured and running
- [x] HPC SSH access configured
- [x] `.env` file with correct settings
- [ ] Email notification service started

## Email Notification Setup

### 1. Install Required Packages

```bash
pip3 install paramiko python-dotenv
```

Or if using pixi:
```bash
pixi add paramiko python-dotenv
```

### 2. Verify Configuration

Check `ui/.env` has these settings:
```bash
HPC_HOST=login.nemo.thecrick.org
HPC_USER=yipy
HPC_SSH_KEY=/home/yipy/.ssh/id_ed25519
WEB_APP_URL=http://10.0.208.117:5000
```

### 3. Test SSH Connection

```bash
ssh -i /home/yipy/.ssh/id_ed25519 yipy@login.nemo.thecrick.org
```

Should connect without password prompt.

### 4. Test Mail Command on HPC

```bash
ssh yipy@login.nemo.thecrick.org
echo "Test email" | mail -s "Test Subject" your.email@crick.ac.uk
```

Check your inbox (and spam folder).

### 5. Start Email Service

```bash
cd ui
./start_email_service.sh
```

Expected output:
```
Starting email notification service...
Email notification service started (PID: 12345)
Logs: ui/email_service.log
```

### 6. Verify Service is Running

```bash
./check_email_service.sh
```

Expected output:
```
✅ Email notification service is running (PID: 12345)

Recent log entries:
====================
[2025-12-14 18:30:00] Checking for completed jobs...
```

### 7. Monitor Logs

```bash
tail -f email_service.log
```

You should see periodic checks every 60 seconds.

## Testing Email Notifications

### 1. Submit a Test Job

Use the web interface to submit a simple job (e.g., example_basic).

### 2. Wait for Job to Complete

Check job status in the web interface or via:
```bash
ssh yipy@login.nemo.thecrick.org
squeue -u yipy
```

### 3. Check Service Logs

```bash
cd ui
tail -f email_service.log
```

You should see:
```
Job example_basic_20251214_183000 (12345678) is COMPLETED, sending email to user@crick.ac.uk
✓ Email sent successfully for job example_basic_20251214_183000
```

### 4. Check Your Email

Look for email with subject: "MaSIF-neosurf Job Completed - example_basic_..."

If not in inbox, check spam folder.

## Troubleshooting

### Service Won't Start

```bash
# Check Python version
python3 --version

# Check if packages are installed
python3 -c "import paramiko, dotenv; print('OK')"

# Check SSH key permissions
ls -la /home/yipy/.ssh/id_ed25519
chmod 600 /home/yipy/.ssh/id_ed25519
```

### Emails Not Arriving

1. **Check service is running:**
   ```bash
   ./check_email_service.sh
   ```

2. **Check logs for errors:**
   ```bash
   tail -n 50 email_service.log
   ```

3. **Test mail command manually:**
   ```bash
   ssh yipy@login.nemo.thecrick.org
   echo "Test" | mail -s "Test" your.email@crick.ac.uk
   ```

4. **Check spam folder**

5. **Verify job metadata has user_email:**
   ```bash
   cat outputs/YOUR_JOB_DIR/metadata.json | grep user_email
   ```

### Service Crashes

```bash
# View full logs
cat email_service.log

# Restart service
./stop_email_service.sh
./start_email_service.sh
```

## Production Deployment

### Option 1: Keep Service Running Manually

Just ensure the service is started after system reboots:
```bash
cd /home/yipy/GitHub/easybuild/software/masif-neosurf/ui
./start_email_service.sh
```

### Option 2: Systemd Service (Recommended)

For automatic startup on boot:

```bash
# Install service
sudo cp masif-email-service.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable masif-email-service
sudo systemctl start masif-email-service

# Check status
sudo systemctl status masif-email-service

# View logs
sudo journalctl -u masif-email-service -f
```

## Maintenance

### View Service Status

```bash
cd ui
./check_email_service.sh
```

### Restart Service

```bash
cd ui
./stop_email_service.sh
./start_email_service.sh
```

### Clean Up Old Jobs

```bash
# Remove jobs older than 30 days
find outputs/ -type d -mtime +30 -exec rm -rf {} +
```

### Monitor Service Health (Cron)

Add to crontab for automatic monitoring:
```bash
crontab -e
```

Add line:
```
0 * * * * cd /home/yipy/GitHub/easybuild/software/masif-neosurf/ui && ./check_email_service.sh || ./start_email_service.sh
```

This checks every hour and restarts if needed.

## Files Created

- ✅ `ui/email_notification_service.py` - Main service script
- ✅ `ui/start_email_service.sh` - Start service
- ✅ `ui/stop_email_service.sh` - Stop service
- ✅ `ui/check_email_service.sh` - Check service status
- ✅ `ui/masif-email-service.service` - Systemd service file
- ✅ `ui/EMAIL_SERVICE_README.md` - Complete documentation
- ✅ `ui/DEPLOYMENT_CHECKLIST.md` - This file
- ✅ `EMAIL_TROUBLESHOOTING.md` - Updated troubleshooting guide

## Next Steps

1. [ ] Start the email service: `cd ui && ./start_email_service.sh`
2. [ ] Submit a test job via web interface
3. [ ] Wait for job to complete
4. [ ] Check email inbox for notification
5. [ ] (Optional) Set up systemd service for automatic startup
6. [ ] (Optional) Add cron job for health monitoring

## Support

For issues or questions, contact:
- Yew Mun: yewmun.yip@crick.ac.uk
- Dani: daniella.hares@crick.ac.uk
