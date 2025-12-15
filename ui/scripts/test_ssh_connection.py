#!/usr/bin/env python3
"""
Test SSH connection to HPC
Run this script to verify your SSH configuration before starting the web app
"""

import os
import sys
from pathlib import Path
import paramiko

# Load environment variables from .env file
def load_env():
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ Error: .env file not found!")
        print("Please create .env file from .env.example:")
        print("  cp .env.example .env")
        print("  nano .env")
        sys.exit(1)
    
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

load_env()

# Get HPC configuration
HPC_CONFIG = {
    'hostname': os.environ.get('HPC_HOST', ''),
    'username': os.environ.get('HPC_USER', ''),
    'key_filename': os.environ.get('HPC_SSH_KEY', ''),
    'remote_work_dir': os.environ.get('HPC_WORK_DIR', ''),
    'port': int(os.environ.get('HPC_PORT', '22'))
}

print("=" * 60)
print("MaSIF-neosurf HPC SSH Connection Test")
print("=" * 60)
print()

# Validate configuration
print("📋 Configuration:")
print(f"  Host:     {HPC_CONFIG['hostname']}")
print(f"  User:     {HPC_CONFIG['username']}")
print(f"  SSH Key:  {HPC_CONFIG['key_filename']}")
print(f"  Work Dir: {HPC_CONFIG['remote_work_dir']}")
print(f"  Port:     {HPC_CONFIG['port']}")
print()

# Check if required fields are set
missing = []
if not HPC_CONFIG['hostname'] or HPC_CONFIG['hostname'] == 'your-hpc-login-node.edu':
    missing.append('HPC_HOST')
if not HPC_CONFIG['username'] or HPC_CONFIG['username'] == 'your_username':
    missing.append('HPC_USER')
if not HPC_CONFIG['key_filename']:
    missing.append('HPC_SSH_KEY')
if not HPC_CONFIG['remote_work_dir'] or 'your_username' in HPC_CONFIG['remote_work_dir']:
    missing.append('HPC_WORK_DIR')

if missing:
    print(f"❌ Error: Please configure these variables in .env file:")
    for var in missing:
        print(f"   - {var}")
    sys.exit(1)

# Check if SSH key exists
key_path = Path(HPC_CONFIG['key_filename']).expanduser()
if not key_path.exists():
    print(f"❌ Error: SSH key not found at {key_path}")
    print("   Please check HPC_SSH_KEY path in .env file")
    sys.exit(1)

print("✅ Configuration looks good!")
print()

# Test SSH connection
print("🔌 Testing SSH connection...")
try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    client.connect(
        hostname=HPC_CONFIG['hostname'],
        username=HPC_CONFIG['username'],
        key_filename=str(key_path),
        port=HPC_CONFIG['port'],
        timeout=10
    )
    
    print("✅ SSH connection successful!")
    print()
    
    # Test basic command
    print("🧪 Testing remote command execution...")
    stdin, stdout, stderr = client.exec_command('hostname && whoami', timeout=10)
    output = stdout.read().decode('utf-8').strip()
    error = stderr.read().decode('utf-8').strip()
    
    if output:
        print(f"✅ Remote command successful!")
        print(f"   Output: {output}")
    if error:
        print(f"⚠️  Stderr: {error}")
    print()
    
    # Test SLURM commands
    print("🧪 Testing SLURM commands...")
    stdin, stdout, stderr = client.exec_command('which sbatch && which squeue', timeout=10)
    output = stdout.read().decode('utf-8').strip()
    
    if 'sbatch' in output and 'squeue' in output:
        print("✅ SLURM commands available!")
        print(f"   {output}")
    else:
        print("⚠️  Warning: SLURM commands not found in PATH")
        print("   Make sure SLURM is available on the login node")
    print()
    
    # Test module command
    print("🧪 Testing MaSIF-neosurf module...")
    stdin, stdout, stderr = client.exec_command('module avail MaSIF-neosurf 2>&1', timeout=10)
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    combined = output + error
    
    if 'MaSIF-neosurf' in combined:
        print("✅ MaSIF-neosurf module found!")
    else:
        print("⚠️  Warning: MaSIF-neosurf module not found")
        print("   Make sure the module is installed on HPC")
    print()
    
    # Test SFTP and directory creation
    print("🧪 Testing SFTP and directory creation...")
    sftp = client.open_sftp()
    
    # Try to create work directory
    try:
        sftp.stat(HPC_CONFIG['remote_work_dir'])
        print(f"✅ Work directory exists: {HPC_CONFIG['remote_work_dir']}")
    except FileNotFoundError:
        try:
            sftp.mkdir(HPC_CONFIG['remote_work_dir'])
            print(f"✅ Created work directory: {HPC_CONFIG['remote_work_dir']}")
        except Exception as e:
            print(f"⚠️  Could not create work directory: {e}")
            print(f"   You may need to create it manually: mkdir -p {HPC_CONFIG['remote_work_dir']}")
    
    sftp.close()
    client.close()
    
    print()
    print("=" * 60)
    print("✅ All tests passed! Your SSH connection is ready.")
    print("=" * 60)
    print()
    print("You can now start the web application:")
    print("  pixi run dev")
    print()
    
except paramiko.AuthenticationException:
    print("❌ Authentication failed!")
    print("   Please check:")
    print("   1. Your username is correct")
    print("   2. Your SSH key path is correct")
    print("   3. Your SSH key is authorized on the HPC")
    print("   4. Try: ssh-copy-id " + HPC_CONFIG['username'] + "@" + HPC_CONFIG['hostname'])
    sys.exit(1)
    
except paramiko.SSHException as e:
    print(f"❌ SSH error: {e}")
    print("   Please check your SSH configuration")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("   Please check:")
    print("   1. HPC hostname is correct and reachable")
    print("   2. Port is correct (usually 22)")
    print("   3. You can connect manually: ssh " + HPC_CONFIG['username'] + "@" + HPC_CONFIG['hostname'])
    sys.exit(1)
