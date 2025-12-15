# Email Notification Service

## Overview

The email notification service monitors completed SLURM jobs and sends email notifications to users. This service runs independently from the Flask web app and checks job status periodically.

## Why a Separate Service?

SLURM compute nodes don't have access to the `mail` command, so we can't send emails directly from the SLURM job scripts. Instead, this service runs on the login node (where `mail` works) and periodically checks for completed jobs.

## Quick Start

### 1. Start the Service

```bash
cd ui
./start_email_service.sh
```

This will start the service in the background and create:
- `email_service.pid` - Process ID file
- `email_service.log` - Service logs

### 2. Check Service Status

```bash
./check_email_service.sh
```

This shows whether the service is running and displays recent log entries.

### 3. Stop the Service

```bash
./stop_email_service.sh
```

### 4. View Logs

```bash
tail -f email_service.log
```

## How It Works

1. **Periodic Checks**: Every 60 seconds, the service scans the `outputs/` directory for job metadata
2. **Status Check**: For each job without a `.email_sent` marker, it checks the SLURM job status via SSH
3. **Email Notification**: If the job is completed/failed, it sends an email via the HPC's `mail` command
4. **Marker File**: Creates `.email_sent` file to prevent duplicate emails

## Configuration

The service uses the same `.env` file as the Flask app:

```bash
# Required settings
HPC_HOST=login.nemo.thecrick.org
HPC_USER=yipy
HPC_SSH_KEY=/home/yipy/.ssh/id_ed25519
WEB_APP_URL=http://10.0.208.117:5000

# Optional
CHECK_INTERVAL=60  # seconds (hardcoded in script)
```

## Systemd Service (Optional)

For automatic startup on system boot:

### 1. Install the Service

```bash
# Copy service file to systemd directory
sudo cp masif-email-service.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable masif-email-service

# Start service now
sudo systemctl start masif-email-service
```

### 2. Manage the Service

```bash
# Check status
sudo systemctl status masif-email-service

# View logs
sudo journalctl -u masif-email-service -f

# Restart service
sudo systemctl restart masif-email-service

# Stop service
sudo systemctl stop masif-email-service

# Disable service (don't start on boot)
sudo systemctl disable masif-email-service
```

## Troubleshooting

### Service Won't Start

1. Check if Python 3 is installed: `python3 --version`
2. Check if required packages are installed: `pip3 install paramiko python-dotenv`
3. Check if `.env` file exists and has correct settings
4. Check SSH key permissions: `chmod 600 /home/yipy/.ssh/id_ed25519`

### Emails Not Being Sent

1. **Check service is running**: `./check_email_service.sh`
2. **Check logs**: `tail -f email_service.log`
3. **Test mail command on HPC**:
   ```bash
   ssh yipy@login.nemo.thecrick.org
   echo "Test" | mail -s "Test" your.email@crick.ac.uk
   ```
4. **Check spam folder** - emails might be filtered
5. **Verify job metadata** - ensure `metadata.json` contains `user_email`

### Service Crashes

Check the logs for errors:
```bash
tail -n 100 email_service.log
```

Common issues:
- SSH connection timeout - check HPC connectivity
- Permission denied - check SSH key permissions
- Module not found - install required Python packages

## Email Templates

### Completed Job

```
Subject: MaSIF-neosurf Job Completed - {job_name}

Your MaSIF-neosurf preprocessing job has completed successfully!

Job Name: {job_name}
Job ID: {job_id}
Status: Completed

You can view and download your results at:
{web_app_url}/job/{job_uuid}

---
MaSIF-neosurf Web Interface
```

### Failed Job

```
Subject: MaSIF-neosurf Job Failed - {job_name}

Your MaSIF-neosurf preprocessing job has failed.

Job Name: {job_name}
Job ID: {job_id}
Status: {status}

If you need assistance, please contact the Chemical Biology STP's computational chemists:
- Yew Mun: yewmun.yip@crick.ac.uk
- Dani: daniella.hares@crick.ac.uk

Include your Job ID in your email for faster support.

---
MaSIF-neosurf Web Interface
```

## Performance

- **Check Interval**: 60 seconds (configurable in script)
- **Resource Usage**: Minimal - only SSH connections and file I/O
- **Scalability**: Can handle hundreds of jobs without issues

## Security

- Uses SSH key authentication (no passwords)
- Only reads job metadata and status
- Doesn't modify any files except `.email_sent` markers
- Runs with user permissions (not root)

## Maintenance

### Clean Up Old Jobs

The service doesn't delete old jobs. To clean up:

```bash
# Remove jobs older than 30 days
find outputs/ -type d -mtime +30 -exec rm -rf {} +
```

### Monitor Service Health

Add to cron for automatic monitoring:

```bash
# Check every hour and restart if needed
0 * * * * /home/yipy/GitHub/easybuild/software/masif-neosurf/ui/check_email_service.sh || /home/yipy/GitHub/easybuild/software/masif-neosurf/ui/start_email_service.sh
```

## Development

To modify the service:

1. Stop the service: `./stop_email_service.sh`
2. Edit `email_notification_service.py`
3. Test changes: `python3 email_notification_service.py`
4. Start service: `./start_email_service.sh`

## Support

For issues or questions, contact:
- Yew Mun: yewmun.yip@crick.ac.uk
- Dani: daniella.hares@crick.ac.uk
