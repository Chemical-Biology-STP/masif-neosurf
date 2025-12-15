#!/usr/bin/env python3
"""Find the wrapper scripts"""

import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

HPC_CONFIG = {
    'hostname': os.environ.get('HPC_HOST'),
    'username': os.environ.get('HPC_USER'),
    'key_filename': os.environ.get('HPC_SSH_KEY'),
    'port': int(os.environ.get('HPC_PORT', '22')),
    'easybuild_prefix': os.environ.get('HPC_EASYBUILD_PREFIX')
}

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    hostname=HPC_CONFIG['hostname'],
    username=HPC_CONFIG['username'],
    key_filename=HPC_CONFIG['key_filename'],
    port=HPC_CONFIG['port']
)

cmd = f"""
echo "=== Looking for MaSIF-neosurf installation ==="
find {HPC_CONFIG['easybuild_prefix']}/software -name "*MaSIF*" -type d 2>/dev/null
echo ""
echo "=== Looking for wrapper scripts ==="
find {HPC_CONFIG['easybuild_prefix']}/software -name "masif-*" 2>/dev/null
echo ""
echo "=== Check bin directory ==="
ls -la {HPC_CONFIG['easybuild_prefix']}/software/MaSIF-neosurf/1.0/bin/ 2>/dev/null
"""

print("Finding wrapper scripts...")
print("=" * 60)
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8')
error = stderr.read().decode('utf-8')

print(output)
if error:
    print("\nStderr:")
    print(error)

client.close()
