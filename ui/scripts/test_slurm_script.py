#!/usr/bin/env python3
"""Test what the SLURM script looks like"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

HPC_CONFIG = {
    'hostname': os.environ.get('HPC_HOST'),
    'username': os.environ.get('HPC_USER'),
    'key_filename': os.environ.get('HPC_SSH_KEY'),
    'remote_work_dir': os.environ.get('HPC_WORK_DIR'),
    'port': int(os.environ.get('HPC_PORT', '22')),
    'module_init': os.environ.get('HPC_MODULE_INIT', '/etc/profile.d/modules.sh'),
    'easybuild_prefix': os.environ.get('HPC_EASYBUILD_PREFIX', '')
}

job_name = "test_job"
remote_job_dir = "/test/dir"
cmd_parts = ["masif-preprocess", "test.pdb", "A"]

easybuild_setup = ""
if HPC_CONFIG['easybuild_prefix']:
    easybuild_setup = f"""
# EasyBuild configuration
export EASYBUILD_PREFIX={HPC_CONFIG['easybuild_prefix']}
export MODULEPATH=$EASYBUILD_PREFIX/modules/all:$MODULEPATH
"""

slurm_content = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --output={remote_job_dir}/slurm_%j.out
#SBATCH --error={remote_job_dir}/slurm_%j.err
#SBATCH --time=02:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=4

# Initialize module system
if [ -f {HPC_CONFIG['module_init']} ]; then
    source {HPC_CONFIG['module_init']}
fi
{easybuild_setup}
module load MaSIF-neosurf/1.0

echo "Starting MaSIF-neosurf preprocessing"
echo "Job directory: {remote_job_dir}"
echo "Command: {' '.join(cmd_parts)}"
echo "Started at: $(date)"

{' '.join(cmd_parts)}

echo "Completed at: $(date)"
"""

print("Generated SLURM script:")
print("=" * 60)
print(slurm_content)
print("=" * 60)
