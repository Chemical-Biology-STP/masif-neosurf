#!/usr/bin/env python3
"""Find the actual module file location"""

import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

HPC_CONFIG = {
    'hostname': os.environ.get('HPC_HOST'),
    'username': os.environ.get('HPC_USER'),
    'key_filename': os.environ.get('HPC_SSH_KEY'),
    'port': int(os.environ.get('HPC_PORT', '22')),
    'easybuild_prefix': os.environ.get('HPC_EASYBUILD_PREFIX', '')
}

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    hostname=HPC_CONFIG['hostname'],
    username=HPC_CONFIG['username'],
    key_filename=HPC_CONFIG['key_filename'],
    port=HPC_CONFIG['port']
)

# Find the module file
cmd = f"""
echo "=== Looking for MaSIF-neosurf module file ==="
find {HPC_CONFIG['easybuild_prefix']}/modules -name "*MaSIF*" -o -name "*masif*" 2>/dev/null
echo ""
echo "=== Checking module directories ==="
ls -la {HPC_CONFIG['easybuild_prefix']}/modules/all/ 2>/dev/null | grep -i masif
echo ""
echo "=== What's in your interactive shell? ==="
echo "Run this manually: ssh {HPC_CONFIG['username']}@{HPC_CONFIG['hostname']}"
echo "Then run: module avail MaSIF"
echo "Then run: echo \\$MODULEPATH"
"""

stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8')
error = stderr.read().decode('utf-8')

print(output)
if error:
    print("Errors:")
    print(error)

client.close()
