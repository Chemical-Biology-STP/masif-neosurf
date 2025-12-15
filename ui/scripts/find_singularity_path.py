#!/usr/bin/env python3
"""Find where Singularity module is located"""

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

# Check what happens in an interactive login shell
cmd = """
echo "=== MODULEPATH in interactive shell ==="
echo $MODULEPATH
echo ""
echo "=== Find Singularity module files ==="
find /usr/share /opt /nemo -name "*Singularity*" -path "*/modules/*" 2>/dev/null | head -20
echo ""
echo "=== Check common module locations ==="
ls -la /usr/share/modulefiles/ 2>/dev/null | grep -i singularity
ls -la /etc/modulefiles/ 2>/dev/null | grep -i singularity
echo ""
echo "=== Where is singularity binary? ==="
which singularity 2>&1 || find /usr -name singularity -type f 2>/dev/null | head -5
"""

print("Finding Singularity location...")
print("=" * 60)
stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8')
error = stderr.read().decode('utf-8')

print(output)
if error:
    print("\nStderr:")
    print(error)

client.close()
