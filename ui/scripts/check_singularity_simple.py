#!/usr/bin/env python3
"""Simple check for Singularity"""

import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

HPC_CONFIG = {
    'hostname': os.environ.get('HPC_HOST'),
    'username': os.environ.get('HPC_USER'),
    'key_filename': os.environ.get('HPC_SSH_KEY'),
    'port': int(os.environ.get('HPC_PORT', '22')),
}

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    hostname=HPC_CONFIG['hostname'],
    username=HPC_CONFIG['username'],
    key_filename=HPC_CONFIG['key_filename'],
    port=HPC_CONFIG['port']
)

# Simpler check
cmd = """
# Source bashrc to get your interactive environment
source ~/.bashrc 2>/dev/null
echo "=== MODULEPATH after sourcing bashrc ==="
echo $MODULEPATH
echo ""
echo "=== Try loading Singularity ==="
module load Singularity/3.11.3 2>&1
echo ""
echo "=== Where is singularity? ==="
which singularity
"""

print("Checking Singularity with bashrc...")
print("=" * 60)
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8')
error = stderr.read().decode('utf-8')

print(output)
if error:
    print("\nStderr:")
    print(error)

client.close()
