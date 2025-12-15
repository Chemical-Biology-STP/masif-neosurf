#!/usr/bin/env python3
"""Quick check if MaSIF-neosurf module loads correctly"""

import os
import sys
from pathlib import Path
import paramiko

def load_env():
    env_file = Path('.env')
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

load_env()

HPC_CONFIG = {
    'hostname': os.environ.get('HPC_HOST'),
    'username': os.environ.get('HPC_USER'),
    'key_filename': os.environ.get('HPC_SSH_KEY'),
    'port': int(os.environ.get('HPC_PORT', '22'))
}

print("Testing MaSIF-neosurf module loading...")
print()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    hostname=HPC_CONFIG['hostname'],
    username=HPC_CONFIG['username'],
    key_filename=HPC_CONFIG['key_filename'],
    port=HPC_CONFIG['port']
)

# Test loading the module and checking for commands
cmd = """
module load MaSIF-neosurf/1.0 2>&1
echo "---"
which masif-preprocess 2>&1
echo "---"
module list 2>&1
"""

stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
output = stdout.read().decode('utf-8')
error = stderr.read().decode('utf-8')

print("Output:")
print(output)
if error:
    print("\nStderr:")
    print(error)

if 'masif-preprocess' in output:
    print("\n✅ MaSIF-neosurf module loads successfully!")
    print("✅ masif-preprocess command is available!")
else:
    print("\n⚠️  Module might not be loading correctly")
    print("Please check if 'module load MaSIF-neosurf/1.0' works when you SSH manually")

client.close()
