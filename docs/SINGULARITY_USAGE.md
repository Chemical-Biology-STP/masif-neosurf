# MaSIF-neosurf Singularity Usage Guide

This guide explains how to use MaSIF-neosurf with Singularity instead of Docker.

## Building the Singularity Image

Build the Singularity image from the definition file:

```bash
singularity build masif-neosurf.sif masif-neosurf.def
```

**Note:** Building requires root/sudo privileges or access to a system with `--fakeroot` support:

```bash
# With sudo
sudo singularity build masif-neosurf.sif masif-neosurf.def

# With fakeroot (if available)
singularity build --fakeroot masif-neosurf.sif masif-neosurf.def

# On HPC systems, you may need to build remotely
singularity build --remote masif-neosurf.sif masif-neosurf.def
```

## Running the Container

### Interactive Shell

Start an interactive shell session with your current directory mounted:

```bash
singularity shell --bind $PWD:/home masif-neosurf.sif
```

Inside the container, navigate to your mounted directory:

```bash
Singularity> cd /home
Singularity> ls
```

### Execute Commands Directly

Run commands without entering the container:

```bash
singularity exec --bind $PWD:/home masif-neosurf.sif <command>
```

## Example Workflows

### 1. Preprocess a PDB File

With ligand:
```bash
singularity exec --bind $PWD:/home masif-neosurf.sif \
    ./preprocess_pdb.sh example/1a7x.pdb 1A7X_A -l FKA_B -s example/1a7x_C_FKA.sdf -o example/output/
```

Without ligand:
```bash
singularity exec --bind $PWD:/home masif-neosurf.sif \
    ./preprocess_pdb.sh example/1a7x.pdb 1A7X_A -o example/output/
```

### 2. Seed Refinement Protocol

Navigate to the seed refinement directory and run the workflow:

```bash
# Step 1: Prepare input files
singularity exec --bind $PWD:/home masif-neosurf.sif \
    python3 rosetta_scripts/seed_refine/1-prepare.py -t ./1LRY_A.pdb -m BB2

# Step 2: Run seed refinement
singularity exec --bind $PWD:/home masif-neosurf.sif \
    bash rosetta_scripts/seed_refine/2-run.sh

# Step 3: Post-processing
singularity exec --bind $PWD:/home masif-neosurf.sif \
    bash rosetta_scripts/seed_refine/3-postprocess.sh S BB2
```

### 3. Running Seed Search

```bash
singularity exec --bind $PWD:/home masif-neosurf.sif \
    python3 masif_seed_search/scripts/your_search_script.py
```

## Binding Additional Directories

If you need to access files from multiple directories, use multiple `--bind` flags:

```bash
singularity exec \
    --bind $PWD:/home \
    --bind /path/to/data:/data \
    --bind /path/to/output:/output \
    masif-neosurf.sif <command>
```

## Environment Variables

The following environment variables are automatically set in the container:

- `MSMS_BIN=/usr/local/bin/msms`
- `APBS_BIN=/usr/local/bin/apbs`
- `MULTIVALUE_BIN=/usr/local/share/apbs/tools/bin/multivalue`
- `PDB2PQR_BIN=/usr/local/bin/pdb2pqr30`
- `REDUCE_HET_DICT=/install/reduce/reduce_wwPDB_het_dict.txt`

## GPU Support

If you need GPU support for TensorFlow operations:

```bash
singularity exec --nv --bind $PWD:/home masif-neosurf.sif <command>
```

The `--nv` flag enables NVIDIA GPU support.

## Differences from Docker

| Docker | Singularity |
|--------|-------------|
| `docker run -it -v $PWD:/home/$(basename $PWD) masif-neosurf` | `singularity shell --bind $PWD:/home masif-neosurf.sif` |
| `docker exec <container> <command>` | `singularity exec --bind $PWD:/home masif-neosurf.sif <command>` |
| Runs as root by default | Runs as your user by default |
| Requires daemon | No daemon required |

## Troubleshooting

### Permission Issues

Singularity runs as your user by default, so file permissions should match your host system. If you encounter permission issues:

1. Check that the mounted directories are readable/writable by your user
2. Ensure output directories exist before running commands

### Missing Dependencies

If you encounter missing dependencies, you may need to rebuild the image or install them in a writable overlay:

```bash
singularity build --sandbox masif-neosurf-sandbox masif-neosurf.def
singularity shell --writable masif-neosurf-sandbox
# Install additional packages
# Then convert back to .sif if needed
```

### HPC-Specific Considerations

On HPC systems:
- Use `--bind` to mount scratch directories for temporary files
- Consider using `--cleanenv` to avoid conflicts with host environment
- Check with your HPC documentation for Singularity-specific guidelines

```bash
singularity exec --cleanenv --bind $PWD:/home --bind /scratch/$USER:/scratch masif-neosurf.sif <command>
```
