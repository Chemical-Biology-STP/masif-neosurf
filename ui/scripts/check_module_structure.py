#!/usr/bin/env python3
"""Check the module structure"""

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

cmd = f"""
echo "=== Module directory contents ==="
ls -la {HPC_CONFIG['easybuild_prefix']}/modules/all/MaSIF-neosurf/
echo ""
echo "=== Testing module load with full path ==="
export MODULEPATH={HPC_CONFIG['easybuild_prefix']}/modules/all:$MODULEPATH
module avail 2>&1 | grep -i masif
echo ""
echo "=== Try loading the module ==="
module load MaSIF-neosurf/1.0 2>&1
echo ""
echo "=== Check if masif-preprocess is available ==="
which masif-preprocess 2>&1
"""

stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8')
error = stderr.read().decode('utf-8')

print(output)
if error:
    print("\nStderr:")
    print(error)

client.close()
