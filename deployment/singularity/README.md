# Singularity Deployment

Singularity container files for MaSIF-neosurf.

## Files

- `masif-neosurf.def` - Singularity definition file (recipe)

**Note:** The `.sif` image file is not included in the repository due to its large size (>1GB). You need to build it locally.

## Building the Container

### From Definition File

```bash
# Build the container (requires root/sudo or --fakeroot)
sudo singularity build masif-neosurf.sif masif-neosurf.def

# Or with fakeroot (if available)
singularity build --fakeroot masif-neosurf.sif masif-neosurf.def
```

### From Docker Hub (if available)

```bash
singularity pull docker://your-registry/masif-neosurf:latest
```

## Usage

### Interactive Shell

```bash
singularity shell masif-neosurf.sif
```

### Run Command

```bash
singularity exec masif-neosurf.sif masif-preprocess input.pdb CHAIN_ID
```

### With Bind Mounts

```bash
# Mount current directory
singularity exec --bind $PWD:/data masif-neosurf.sif masif-preprocess /data/input.pdb CHAIN_ID

# Mount specific directories
singularity exec \
  --bind /path/to/input:/input \
  --bind /path/to/output:/output \
  masif-neosurf.sif masif-preprocess /input/file.pdb CHAIN_ID -o /output
```

## On HPC with SLURM

```bash
#!/bin/bash
#SBATCH --job-name=masif
#SBATCH --time=02:00:00
#SBATCH --mem=8G

module load Singularity

singularity exec masif-neosurf.sif masif-preprocess input.pdb CHAIN_ID
```

## Advantages

- ✅ No root access needed to run (only to build)
- ✅ Compatible with HPC environments
- ✅ Reproducible environment
- ✅ Easy to share and distribute
- ✅ Works with SLURM and other schedulers

## Documentation

See `../../docs/SINGULARITY_USAGE.md` for detailed usage guide.
