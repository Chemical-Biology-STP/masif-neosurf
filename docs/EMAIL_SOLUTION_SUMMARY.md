# Email Notification Solution Summary

## Problem

Users were not receiving email notifications when their MaSIF-neosurf jobs completed.

**Root Cause:** SLURM compute nodes don't have access to the `mail` command, so the bash `send_notification()` function in the SLURM job scripts couldn't send emails.

## Solution

Created a **standalone email notification service** that runs on the login node (where `mail` works) and periodically checks for completed jobs.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Login Node                            │
│                                                              │
│  ┌──────────────────┐         ┌─────────────────────────┐  │
│  │   Flask Web App  │         │  Email Notification     │  │
│  │   (port 5000)    │         │  Service                │  │
│  │                  │         │                         │  │
│  │  - Submit jobs   │         │  - Checks job status    │  │
│  │  - View results  │         │  - Sends emails         │  │
│  │  - User auth     │         │  - Runs every 60s       │  │
│  └──────────────────┘         └─────────────────────────┘  │
│           │                              │                   │
│           │ SSH                          │ SSH               │
│           ↓                              ↓                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              HPC SLURM System                         │  │
│  │                                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │  │
│  │  │ Compute     │  │ Compute     │  │ Compute     │ │  │
│  │  │ Node 1      │  │ Node 2      │  │ Node 3      │ │  │
│  │  │             │  │             │  │             │ │  │
│  │  │ (no mail)   │  │ (no mail)   │  │ (no mail)   │ │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## How It Works

1. **User submits job** via Flask web app
2. **Job runs on compute node** (no email capability)
3. **Email service** (running on login node):
   - Checks `outputs/` directory every 60 seconds
   - For each job without `.email_sent` marker:
     - Connects to HPC via SSH
     - Checks SLURM job status
     - If completed/failed, sends email via `mail` command
     - Creates `.email_sent` marker
4. **User receives email** with link to results

## Files Created

### Core Service
- `ui/email_notification_service.py` - Main service (Python)

### Management Scripts
- `ui/start_email_service.sh` - Start service in background
- `ui/stop_email_service.sh` - Stop service
- `ui/check_email_service.sh` - Check service status
- `ui/test_email_notification.sh` - Test email functionality

### Configuration
- `ui/.env` - Added `WEB_APP_URL` setting
- `ui/masif-email-service.service` - Systemd service file (optional)

### Documentation
- `ui/EMAIL_SERVICE_README.md` - Complete service documentation
- `ui/DEPLOYMENT_CHECKLIST.md` - Step-by-step deployment guide
- `EMAIL_TROUBLESHOOTING.md` - Updated troubleshooting guide
- `EMAIL_SOLUTION_SUMMARY.md` - This file

## Quick Start

```bash
# 1. Start the email service
cd ui
./start_email_service.sh

# 2. Check it's running
./check_email_service.sh

# 3. Test email functionality
./test_email_notification.sh your.email@crick.ac.uk

# 4. Monitor logs
tail -f email_service.log
```

## Testing

1. Submit a test job via web interface
2. Wait for job to complete (check with `squeue -u yipy`)
3. Check service logs: `tail -f ui/email_service.log`
4. Check your email inbox (and spam folder)

## Email Templates

### Success Email
```
Subject: MaSIF-neosurf Job Completed - {job_name}

Your MaSIF-neosurf preprocessing job has completed successfully!

Job Name: {job_name}
Job ID: {job_id}
Status: Completed

You can view and download your results at:
http://10.0.208.117:5000/job/{job_uuid}
```

### Failure Email
```
Subject: MaSIF-neosurf Job Failed - {job_name}

Your MaSIF-neosurf preprocessing job has failed.

Job Name: {job_name}
Job ID: {job_id}
Status: {status}

If you need assistance, please contact the Chemical Biology STP's
computational chemists:
- Yew Mun: yewmun.yip@crick.ac.uk
- Dani: daniella.hares@crick.ac.uk
```

## Advantages

✅ **Works on compute nodes** - No mail command needed on compute nodes
✅ **Reliable** - Runs independently from SLURM jobs
✅ **No duplicates** - Uses `.email_sent` marker files
✅ **Automatic retry** - Checks every 60 seconds until email sent
✅ **Minimal resources** - Only SSH connections and file I/O
✅ **Easy to monitor** - Simple log file and status scripts
✅ **Easy to maintain** - Can restart without affecting running jobs

## Production Deployment

### Option 1: Manual (Simple)
Just start the service and ensure it's restarted after system reboots.

### Option 2: Systemd (Recommended)
Install as systemd service for automatic startup:
```bash
sudo cp ui/masif-email-service.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable masif-email-service
sudo systemctl start masif-email-service
```

### Option 3: Cron Monitoring
Add health check to crontab:
```bash
0 * * * * cd /path/to/masif-neosurf/ui && ./check_email_service.sh || ./start_email_service.sh
```

## Troubleshooting

### Service not running
```bash
cd ui
./start_email_service.sh
```

### Emails not arriving
1. Check service logs: `tail -f ui/email_service.log`
2. Test mail on HPC: `ssh yipy@login.nemo.thecrick.org "echo Test | mail -s Test your@email.com"`
3. Check spam folder
4. Verify job metadata has `user_email` field

### Service crashes
```bash
# View logs
cat ui/email_service.log

# Restart
cd ui
./stop_email_service.sh
./start_email_service.sh
```

## Next Steps

1. ✅ Start the email service
2. ✅ Test with a real job submission
3. ✅ Verify email delivery
4. ⬜ (Optional) Set up systemd service
5. ⬜ (Optional) Add cron monitoring

## Support

For issues or questions:
- Yew Mun: yewmun.yip@crick.ac.uk
- Dani: daniella.hares@crick.ac.uk
