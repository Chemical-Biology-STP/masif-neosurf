# Email Notification Troubleshooting

## Problem
Users are not receiving email notifications when jobs complete.

## Root Cause ✅ IDENTIFIED

**SLURM compute nodes don't have access to the `mail` command**, so emails cannot be sent directly from job scripts running on compute nodes.

## Solution ✅ IMPLEMENTED

We've created a **standalone email notification service** (`ui/email_notification_service.py`) that:
1. Runs on the login node (where `mail` command works)
2. Periodically checks for completed jobs via SSH
3. Sends email notifications when jobs finish

## Quick Start

### Start the Email Service

```bash
cd ui
./start_email_service.sh
```

### Check Service Status

```bash
cd ui
./check_email_service.sh
```

### View Logs

```bash
cd ui
tail -f email_service.log
```

### Stop the Service

```bash
cd ui
./stop_email_service.sh
```

## Testing Email Functionality

### Test 1: Mail Command on Login Node

```bash
# SSH to HPC login node
ssh yipy@login.nemo.thecrick.org

# Test mail command
echo "Test message from login node" | mail -s "Test Email" your.email@crick.ac.uk
```

✅ **This should work** - login node has mail access

### Test 2: Mail Command on Compute Node

```bash
# Submit a test job
srun --pty bash
echo "Test from compute node" | mail -s "Test" your.email@crick.ac.uk
```

❌ **This will fail** - compute nodes don't have mail access

## How the Email Service Works

1. **Service runs on login node** (where you start the Flask app)
2. **Every 60 seconds**, it checks the `outputs/` directory for jobs
3. **For each job** without a `.email_sent` marker:
   - Connects to HPC via SSH
   - Checks SLURM job status (`squeue` or `sacct`)
   - If job is completed/failed, sends email via `mail` command
   - Creates `.email_sent` marker to prevent duplicates

## Troubleshooting

### Service Not Running

**Check:**
```bash
cd ui
./check_email_service.sh
```

**Start if needed:**
```bash
cd ui
./start_email_service.sh
```

### Emails Still Not Arriving

1. **Check service logs:**
   ```bash
   cd ui
   tail -f email_service.log
   ```

2. **Look for errors:**
   - SSH connection failures
   - Mail command errors
   - Permission issues

3. **Test mail manually on HPC:**
   ```bash
   ssh yipy@login.nemo.thecrick.org
   echo "Test" | mail -s "Test Subject" your.email@crick.ac.uk
   ```

4. **Check spam folder** - HPC emails might be filtered

5. **Verify job metadata:**
   ```bash
   cd outputs/YOUR_JOB_DIR
   cat metadata.json
   ```
   Ensure `user_email` field exists

### Service Crashes

**View recent logs:**
```bash
cd ui
tail -n 100 email_service.log
```

**Common issues:**
- SSH timeout - check HPC connectivity
- Missing Python packages - install `paramiko` and `python-dotenv`
- SSH key permissions - run `chmod 600 /home/yipy/.ssh/id_ed25519`

## Alternative: Systemd Service (Optional)

For automatic startup on system boot, see `ui/EMAIL_SERVICE_README.md` for systemd setup instructions.

## Removing Old Email Functions from SLURM Scripts

The SLURM scripts in `app.py` still have `send_notification()` bash functions that won't work on compute nodes. These can be safely removed since the email service handles notifications.

**To remove (optional):**
1. Edit `ui/app.py`
2. Search for `send_notification()` function in SLURM script templates
3. Remove the function and the trap line
4. Restart Flask app

**Note:** Keeping them doesn't hurt - they just won't work on compute nodes.

## Documentation

See `ui/EMAIL_SERVICE_README.md` for complete documentation including:
- Detailed setup instructions
- Systemd service configuration
- Performance and security notes
- Maintenance tips

## Support

For issues or questions, contact:
- Yew Mun: yewmun.yip@crick.ac.uk
- Dani: daniella.hares@crick.ac.uk
