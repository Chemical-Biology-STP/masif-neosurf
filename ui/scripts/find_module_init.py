#!/usr/bin/env python3
"""Find the correct module initialization script on HPC"""

import os
from pathlib import Path
import paramiko
from dotenv import load_dotenv

load_dotenv()

HPC_CONFIG = {
    'hostname': os.environ.get('HPC_HOST'),
    'username': os.environ.get('HPC_USER'),
    'key_filename': os.environ.get('HPC_SSH_KEY'),
    'port': int(os.environ.get('HPC_PORT', '22'))
}

print("Finding module initialization script on HPC...")
print()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    hostname=HPC_CONFIG['hostname'],
    username=HPC_CONFIG['username'],
    key_filename=HPC_CONFIG['key_filename'],
    port=HPC_CONFIG['port']
)

# Check common module init locations
cmd = """
echo "=== Checking common module init paths ==="
for path in /etc/profile.d/modules.sh \
            /usr/share/Modules/init/bash \
            /usr/share/modules/init/bash \
            /opt/modules/init/bash \
            /etc/profile.d/lmod.sh \
            $MODULESHOME/init/bash; do
    if [ -f "$path" ]; then
        echo "FOUND: $path"
    fi
done

echo ""
echo "=== MODULESHOME variable ==="
echo $MODULESHOME

echo ""
echo "=== Module command type ==="
type module 2>&1

echo ""
echo "=== Checking .bashrc for module init ==="
grep -i "module" ~/.bashrc 2>&1 | head -5

echo ""
echo "=== Testing module load in interactive shell ==="
bash -l -c "module load MaSIF-neosurf/1.0 && which masif-preprocess" 2>&1
"""

stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
output = stdout.read().decode('utf-8')
error = stderr.read().decode('utf-8')

print(output)
if error:
    print("Stderr:")
    print(error)

client.close()

print("\n" + "="*60)
print("Based on the output above, update HPC_MODULE_INIT in your .env file")
print("to the correct path, or use one of these alternatives:")
print("="*60)
