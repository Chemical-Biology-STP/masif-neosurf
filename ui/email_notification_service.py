#!/usr/bin/env python3
"""
Email Notification Service for MaSIF-neosurf
Checks for completed jobs and sends email notifications

Run this as a background service or cron job:
    python email_notification_service.py

Or as a systemd service for automatic startup
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime
import paramiko
from io import StringIO

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
OUTPUT_FOLDER = Path('outputs')
HPC_CONFIG = {
    'hostname': os.environ.get('HPC_HOST', 'login.nemo.thecrick.org'),
    'username': os.environ.get('HPC_USER', 'yipy'),
    'key_filename': os.environ.get('HPC_SSH_KEY', str(Path.home() / '.ssh' / 'id_ed25519')),
    'port': int(os.environ.get('HPC_PORT', '22')),
}

CHECK_INTERVAL = 60  # Check every 60 seconds


def get_ssh_client():
    """Create and return an SSH client connected to HPC"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(
            hostname=HPC_CONFIG['hostname'],
            username=HPC_CONFIG['username'],
            key_filename=HPC_CONFIG['key_filename'],
            port=HPC_CONFIG['port'],
            timeout=10
        )
        return client
    except Exception as e:
        raise Exception(f"Failed to connect to HPC: {str(e)}")


def send_email_via_hpc(to_email, subject, body):
    """Send email using HPC's mail system via SSH"""
    try:
        client = get_ssh_client()
        
        # Escape subject and body for shell
        escaped_subject = subject.replace('"', '\\"').replace('$', '\\$')
        escaped_body = body.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
        
        # Use printf to properly handle newlines
        cmd = f'printf "%s\\n" "{escaped_body}" | mail -s "{escaped_subject}" {to_email}'
        
        stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
        exit_code = stdout.channel.recv_exit_status()
        
        client.close()
        
        return exit_code == 0
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def check_job_status(job_id):
    """Check SLURM job status via SSH"""
    try:
        client = get_ssh_client()
        
        # Try squeue first (for running/pending jobs)
        stdin, stdout, stderr = client.exec_command(
            f"squeue -j {job_id} -h -o '%T'",
            timeout=10
        )
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8').strip()
        
        client.close()
        
        if exit_code == 0 and output:
            return output
        
        # Job not in queue, check sacct (for completed jobs)
        client = get_ssh_client()
        stdin, stdout, stderr = client.exec_command(
            f"sacct -j {job_id} -n -o State",
            timeout=10
        )
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8').strip()
        
        client.close()
        
        if exit_code == 0 and output:
            return output.split()[0]
        
        return 'UNKNOWN'
    except Exception as e:
        print(f"Error checking job status: {e}")
        return 'ERROR'


def process_job_notifications():
    """Check for completed jobs and send notifications"""
    print(f"[{datetime.now()}] Checking for completed jobs...")
    
    if not OUTPUT_FOLDER.exists():
        print(f"Output folder {OUTPUT_FOLDER} does not exist")
        return
    
    for job_dir in OUTPUT_FOLDER.iterdir():
        if not job_dir.is_dir():
            continue
        
        metadata_file = job_dir / 'metadata.json'
        email_sent_file = job_dir / '.email_sent'
        
        # Skip if email already sent or no metadata
        if email_sent_file.exists() or not metadata_file.exists():
            continue
        
        try:
            # Read job metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            job_id = metadata.get('job_id')
            job_name = metadata.get('job_name')
            job_uuid = metadata.get('job_uuid')
            user_email = metadata.get('user_email')
            
            if not all([job_id, job_name, job_uuid, user_email]):
                continue
            
            # Check job status
            status = check_job_status(job_id)
            
            # Only send email if job is completed or failed
            if status in ['COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT', 'NODE_FAIL']:
                print(f"Job {job_name} ({job_id}) is {status}, sending email to {user_email}")
                
                # Get web app URL from environment or use default
                web_app_url = os.environ.get('WEB_APP_URL', 'http://10.0.208.117:5000')
                
                if status == 'COMPLETED':
                    subject = f"MaSIF-neosurf Job Completed - {job_name}"
                    body = f"""Your MaSIF-neosurf preprocessing job has completed successfully!

Job Name: {job_name}
Job ID: {job_id}
Status: Completed

You can view and download your results at:
{web_app_url}/job/{job_uuid}

---
MaSIF-neosurf Web Interface"""
                else:
                    subject = f"MaSIF-neosurf Job Failed - {job_name}"
                    body = f"""Your MaSIF-neosurf preprocessing job has failed.

Job Name: {job_name}
Job ID: {job_id}
Status: {status}

If you need assistance, please contact the Chemical Biology STP's computational chemists:
- Yew Mun: yewmun.yip@crick.ac.uk
- Dani: daniella.hares@crick.ac.uk

Include your Job ID in your email for faster support.

---
MaSIF-neosurf Web Interface"""
                
                # Send email
                if send_email_via_hpc(user_email, subject, body):
                    # Mark email as sent
                    email_sent_file.touch()
                    print(f"✓ Email sent successfully for job {job_name}")
                else:
                    print(f"✗ Failed to send email for job {job_name}")
        
        except Exception as e:
            print(f"Error processing {job_dir.name}: {e}")


def main():
    """Main loop"""
    print("=" * 60)
    print("MaSIF-neosurf Email Notification Service")
    print("=" * 60)
    print(f"Output folder: {OUTPUT_FOLDER.absolute()}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print(f"HPC: {HPC_CONFIG['hostname']}")
    print("=" * 60)
    print()
    
    while True:
        try:
            process_job_notifications()
        except Exception as e:
            print(f"Error in main loop: {e}")
        
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
