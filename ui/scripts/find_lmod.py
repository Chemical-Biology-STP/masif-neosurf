#!/usr/bin/env python3
"""Find Lmod initialization"""

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

cmd = """
echo "=== Looking for Lmod ==="
which lmod 2>&1
echo ""
echo "=== Looking for module init scripts ==="
ls -la /etc/profile.d/*mod* 2>&1
echo ""
ls -la /usr/share/lmod/*/init/bash 2>&1
echo ""
echo "=== Check common locations ==="
ls -la /usr/share/Modules/init/bash 2>&1
ls -la /opt/ohpc/admin/lmod/lmod/init/bash 2>&1
echo ""
echo "=== What does your .bashrc source? ==="
grep -i "module\|lmod" ~/.bashrc 2>&1
"""

stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8')
error = stderr.read().decode('utf-8')

print(output)

client.close()
