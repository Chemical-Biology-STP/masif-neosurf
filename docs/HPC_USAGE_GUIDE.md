# MaSIF-neosurf HPC Usage Guide

Quick reference for using MaSIF-neosurf on your HPC system.

## Installation

```bash
# 1. Build the Singularity image (on a system with sudo)
sudo singularity build masif-neosurf.sif masif-neosurf.def

# 2. Transfer to HPC and run installation script
scp masif-neosurf.sif your-hpc:/path/to/working/dir/
ssh your-hpc
cd /path/to/working/dir/
chmod +x install_masif_easybuild.sh
./install_masif_easybuild.sh
```

## Loading the Module

```bash
# Load MaSIF-neosurf (Singularity/3.11.3 loads automatically)
module load MaSIF-neosurf/1.0

# Check what's loaded
module list

# View help
module help MaSIF-neosurf/1.0
```

## Available Commands

After loading the module, you have access to:

| Command | Description |
|---------|-------------|
| `masif-neosurf-shell` | Interactive shell in container |
| `masif-neosurf-exec` | Execute command in container |
| `masif-neosurf-exec-gpu` | Execute with GPU support |
| `masif-preprocess` | Run preprocessing script |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `$MASIF_NEOSURF_SIF` | Path to Singularity image |
| `$MASIF_NEOSURF_HOME` | Installation directory |
| `$MASIF_NEOSURF_VERSION` | Version number |

## Interactive Usage

```bash
# Start interactive session
srun --pty --cpus-per-task=4 --mem=16G bash

# Load module
module load MaSIF-neosurf/1.0

# Enter container shell
masif-neosurf-shell

# Inside container, you can run any command
Singularity> python3 --version
Singularity> cd /home
Singularity> ls
```

## Batch Job Examples

### Basic Preprocessing Job

```bash
#!/bin/bash
#SBATCH --job-name=masif-preprocess
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=masif_%j.out
#SBATCH --error=masif_%j.err

# Load module (Singularity/3.11.3 loaded automatically)
module load MaSIF-neosurf/1.0

# Preprocess PDB file
masif-preprocess example/1a7x.pdb 1A7X_A -o output/

# With ligand
masif-preprocess example/1a7x.pdb 1A7X_A \
    -l FKA_B \
    -s example/1a7x_C_FKA.sdf \
    -o output/
```

### Seed Refinement Job

```bash
#!/bin/bash
#SBATCH --job-name=masif-refine
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --output=refine_%j.out
#SBATCH --error=refine_%j.err

module load MaSIF-neosurf/1.0

cd rosetta_scripts/seed_refine

# Step 1: Prepare
masif-neosurf-exec python3 1-prepare.py -t ./1LRY_A.pdb -m BB2

# Step 2: Run refinement
masif-neosurf-exec bash 2-run.sh

# Step 3: Post-process
masif-neosurf-exec bash 3-postprocess.sh S BB2
```

### GPU Job

```bash
#!/bin/bash
#SBATCH --job-name=masif-gpu
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu
#SBATCH --output=masif_gpu_%j.out
#SBATCH --error=masif_gpu_%j.err

module load MaSIF-neosurf/1.0

# Run with GPU support
masif-neosurf-exec-gpu python3 train_model.py
```

### Array Job for Multiple PDBs

```bash
#!/bin/bash
#SBATCH --job-name=masif-array
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --array=1-10
#SBATCH --output=masif_%A_%a.out
#SBATCH --error=masif_%A_%a.err

module load MaSIF-neosurf/1.0

# List of PDB files
PDB_LIST=(
    "1a7x.pdb 1A7X_A"
    "2xyz.pdb 2XYZ_B"
    # ... add more
)

# Get current PDB from array
PDB_INFO=(${PDB_LIST[$SLURM_ARRAY_TASK_ID-1]})
PDB_FILE=${PDB_INFO[0]}
CHAIN=${PDB_INFO[1]}

# Process
masif-preprocess $PDB_FILE $CHAIN -o output_${SLURM_ARRAY_TASK_ID}/
```

## Direct Singularity Usage

If you need more control, use Singularity directly:

```bash
module load MaSIF-neosurf/1.0

# Basic execution
singularity exec --bind $PWD:/home $MASIF_NEOSURF_SIF python3 script.py

# With additional bind paths
singularity exec \
    --bind $PWD:/home \
    --bind /nemo:/nemo \
    --bind /scratch/$USER:/scratch \
    $MASIF_NEOSURF_SIF python3 script.py

# With GPU
singularity exec --nv --bind $PWD:/home $MASIF_NEOSURF_SIF python3 script.py
```

## File Paths and Binding

The container automatically binds:
- Current directory (`$PWD`) to `/home` inside container
- `/nemo` (if exists)
- `/scratch` (if exists)

When working inside the container, your files are accessible at `/home`:

```bash
# On HPC
cd /nemo/stp/chemicalbiology/home/users/yourname/project

# Inside container
masif-neosurf-shell
Singularity> cd /home  # This is your project directory
Singularity> ls        # See your files
```

## Troubleshooting

### Module not found
```bash
# Check module path
module avail MaSIF

# If not found, check installation
ls /nemo/stp/chemicalbiology/home/shared/easybuild/modules/all/MaSIF-neosurf/
```

### Singularity not found
```bash
# Singularity should load automatically, but if not:
module load Singularity/3.11.3
module load MaSIF-neosurf/1.0
```

### Permission denied
```bash
# Check file permissions
ls -la $MASIF_NEOSURF_SIF

# Should be readable by all users
chmod 755 $MASIF_NEOSURF_SIF
```

### Out of memory
```bash
# Increase memory in SLURM script
#SBATCH --mem=64G

# Or use a larger node
#SBATCH --partition=highmem
```

### Bind path errors
```bash
# Explicitly specify bind paths
singularity exec --bind /path/to/data:/data $MASIF_NEOSURF_SIF command
```

## Performance Tips

1. **Use local scratch for temporary files**
   ```bash
   export TMPDIR=/scratch/$USER/tmp_$SLURM_JOB_ID
   mkdir -p $TMPDIR
   ```

2. **Parallel processing**
   ```bash
   #SBATCH --cpus-per-task=16
   # Use all cores in your scripts
   ```

3. **GPU acceleration**
   ```bash
   #SBATCH --gres=gpu:1
   masif-neosurf-exec-gpu python3 script.py
   ```

4. **Array jobs for multiple structures**
   - More efficient than submitting individual jobs
   - Better resource utilization

## Getting Help

```bash
# Module help
module help MaSIF-neosurf/1.0

# View documentation
cat $MASIF_NEOSURF_HOME/README.txt

# SLURM templates
ls $MASIF_NEOSURF_HOME/*.sh

# GitHub repository
# https://github.com/LPDI-EPFL/masif-neosurf
```

## Unloading

```bash
# Unload module
module unload MaSIF-neosurf/1.0

# This also unloads Singularity/3.11.3 if no other modules need it
```

## Version Management

```bash
# Check available versions
module avail MaSIF-neosurf

# Load specific version
module load MaSIF-neosurf/1.0

# Switch versions
module swap MaSIF-neosurf/1.0 MaSIF-neosurf/2.0
```
