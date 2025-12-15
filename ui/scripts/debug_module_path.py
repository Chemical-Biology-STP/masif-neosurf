#!/usr/bin/env python3
"""Debug module path"""

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

# Check what's in the EasyBuild modules directory
cmd = f"""
ls -la {HPC_CONFIG['easybuild_prefix']}/modules/all/ | head -20
echo "---"
find {HPC_CONFIG['easybuild_prefix']}/modules -name "*MaSIF*" -o -name "*masif*" 2>/dev/null
"""

print("Checking EasyBuild modules directory:")
print("=" * 60)
stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
output = stdout.read().decode('utf-8')
error = stderr.read().decode('utf-8')

print(output)
if error:
    print(f"Error: {error}")

client.close()
