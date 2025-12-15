#!/usr/bin/env python3
"""Test module loading on HPC"""

import os
from pathlib import Path
import paramiko
from dotenv import load_dotenv

load_dotenv()

HPC_CONFIG = {
    'hostname': os.environ.get('HPC_HOST'),
    'username': os.environ.get('HPC_USER'),
    'key_filename': os.environ.get('HPC_SSH_KEY'),
    'port': int(os.environ.get('HPC_PORT', '22')),
    'module_init': os.environ.get('HPC_MODULE_INIT', '/etc/profile.d/modules.sh'),
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

# Test different ways to load the module
tests = [
    ("Test 1: Direct module load", "module load MaSIF-neosurf/1.0 && which masif-preprocess"),
    ("Test 2: With module init", f"source {HPC_CONFIG['module_init']} && module load MaSIF-neosurf/1.0 && which masif-preprocess"),
    ("Test 3: With EasyBuild setup", f"""
export EASYBUILD_PREFIX={HPC_CONFIG['easybuild_prefix']}
export MODULEPATH=$EASYBUILD_PREFIX/modules/all:$MODULEPATH
module load MaSIF-neosurf/1.0 && which masif-preprocess
"""),
    ("Test 4: Full setup", f"""
source {HPC_CONFIG['module_init']}
export EASYBUILD_PREFIX={HPC_CONFIG['easybuild_prefix']}
export MODULEPATH=$EASYBUILD_PREFIX/modules/all:$MODULEPATH
module load MaSIF-neosurf/1.0 && which masif-preprocess
"""),
    ("Test 5: Check .bashrc", "cat ~/.bashrc | grep -i module"),
]

for test_name, cmd in tests:
    print(f"\n{test_name}")
    print("=" * 60)
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if output:
        print(f"Output: {output}")
    if error:
        print(f"Error: {error}")

client.close()
