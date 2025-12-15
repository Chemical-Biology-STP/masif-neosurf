#!/usr/bin/env python3
"""Check what commands the module provides"""

import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

HPC_CONFIG = {
    'hostname': os.environ.get('HPC_HOST'),
    'username': os.environ.get('HPC_USER'),
    'key_filename': os.environ.get('HPC_SSH_KEY'),
    'port': int(os.environ.get('HPC_PORT', '22')),
    'module_init': os.environ.get('HPC_MODULE_INIT'),
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
source {HPC_CONFIG['module_init']}
export EASYBUILD_PREFIX={HPC_CONFIG['easybuild_prefix']}
export MODULEPATH=$EASYBUILD_PREFIX/modules/all:$MODULEPATH
module --ignore_cache load MaSIF-neosurf/1.0 2>&1
echo "=== Environment variables set by module ==="
env | grep -i masif
echo ""
echo "=== Check for wrapper commands ==="
which masif-neosurf-shell
which masif-neosurf-exec
which masif-preprocess
echo ""
echo "=== Module help ==="
module help MaSIF-neosurf/1.0 2>&1
"""

print("Checking module commands...")
print("=" * 60)
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8')
error = stderr.read().decode('utf-8')

print(output)
if error:
    print("\nStderr:")
    print(error)

client.close()
