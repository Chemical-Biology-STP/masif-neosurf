#!/usr/bin/env python3
"""Find singularity binary directly"""

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
echo "=== Check if singularity is in system PATH ==="
ls -la /usr/bin/singularity 2>&1
ls -la /usr/local/bin/singularity 2>&1
echo ""
echo "=== Check common singularity locations ==="
ls -la /opt/singularity*/bin/singularity 2>&1
ls -la /usr/lib*/singularity/bin/singularity 2>&1
echo ""
echo "=== What does 'module show Singularity/3.11.3' say when you can load it? ==="
echo "Please run this manually: ssh and then 'module show Singularity/3.11.3'"
"""

print("Finding singularity binary...")
print("=" * 60)
stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
output = stdout.read().decode('utf-8')
error = stderr.read().decode('utf-8')

print(output)
if error:
    print("\nStderr:")
    print(error)

client.close()

print("\n" + "=" * 60)
print("RECOMMENDATION:")
print("Please SSH to your HPC and run:")
print("  module load Singularity/3.11.3")
print("  module show Singularity/3.11.3")
print("  which singularity")
print("\nThen share the output so we can see where singularity is located.")
