# Installing MaSIF-neosurf with EasyBuild

This guide explains how to install the MaSIF-neosurf Singularity container as an HPC module using EasyBuild.

## Prerequisites

- EasyBuild installed on your HPC system
- Singularity installed and available
- The `masif-neosurf.sif` file built from the definition file

## Installation Methods

### Method 1: Using Local .sif File (Recommended for HPC)

This method doesn't require creating a tarball or hosting files.

1. **Prepare the installation directory structure:**

```bash
# Create a temporary build directory
mkdir -p /tmp/masif-neosurf-build
cd /tmp/masif-neosurf-build

# Copy your .sif file here
cp /path/to/masif-neosurf.sif .
```

2. **Modify the EasyConfig to skip source download:**

Create a modified version `MaSIF-neosurf-1.0-local.eb`:

```python
easyblock = 'Binary'

name = 'MaSIF-neosurf'
version = '1.0'

homepage = 'https://github.com/LPDI-EPFL/masif-neosurf'
description = """
MaSIF-neosurf - Surface-based protein design for ternary complexes.
"""

toolchain = SYSTEM

# No sources - we'll copy manually
sources = []

# Installation commands
install_cmd = 'mkdir -p %(installdir)s && '
install_cmd += 'cp masif-neosurf.sif %(installdir)s/ && '
install_cmd += 'chmod 755 %(installdir)s/masif-neosurf.sif'

postinstallcmds = [
    'mkdir -p %(installdir)s/bin',
    
    'cat > %(installdir)s/bin/masif-neosurf-shell << "EOF"\n'
    '#!/bin/bash\n'
    'MASIF_SIF="%(installdir)s/masif-neosurf.sif"\n'
    'singularity shell --bind $PWD:/home "$MASIF_SIF" "$@"\n'
    'EOF',
    'chmod +x %(installdir)s/bin/masif-neosurf-shell',
    
    'cat > %(installdir)s/bin/masif-neosurf-exec << "EOF"\n'
    '#!/bin/bash\n'
    'MASIF_SIF="%(installdir)s/masif-neosurf.sif"\n'
    'singularity exec --bind $PWD:/home "$MASIF_SIF" "$@"\n'
    'EOF',
    'chmod +x %(installdir)s/bin/masif-neosurf-exec',
    
    'cat > %(installdir)s/bin/masif-preprocess << "EOF"\n'
    '#!/bin/bash\n'
    'MASIF_SIF="%(installdir)s/masif-neosurf.sif"\n'
    'singularity exec --bind $PWD:/home "$MASIF_SIF" /home/preprocess_pdb.sh "$@"\n'
    'EOF',
    'chmod +x %(installdir)s/bin/masif-preprocess',
]

modextravars = {
    'MASIF_NEOSURF_SIF': '%(installdir)s/masif-neosurf.sif',
    'MASIF_NEOSURF_HOME': '%(installdir)s',
}

modloadmsg = """
MaSIF-neosurf loaded. Use 'masif-neosurf-shell' for interactive mode
or 'masif-neosurf-exec <command>' to run commands.
"""

sanity_check_paths = {
    'files': ['masif-neosurf.sif', 'bin/masif-neosurf-shell'],
    'dirs': ['bin'],
}

moduleclass = 'bio'
```

3. **Build and install with EasyBuild:**

```bash
# From the directory containing the .sif file
eb MaSIF-neosurf-1.0-local.eb --robot

# Or if you need to specify the buildpath
eb MaSIF-neosurf-1.0-local.eb --robot --buildpath=/tmp/masif-neosurf-build
```

### Method 2: Using Tarball Source

1. **Create a tarball of the .sif file:**

```bash
tar czf masif-neosurf-1.0.tar.gz masif-neosurf.sif
```

2. **Calculate the SHA256 checksum:**

```bash
sha256sum masif-neosurf-1.0.tar.gz
```

3. **Update the EasyConfig:**

Edit `MaSIF-neosurf-1.0.eb` and:
- Add the checksum to the `checksums` field
- Either upload the tarball to a web server and add the URL to `source_urls`, or place it in EasyBuild's source directory

4. **Install with EasyBuild:**

```bash
eb MaSIF-neosurf-1.0.eb --robot
```

### Method 3: Direct Manual Installation (Simplest)

If you just want to make it available quickly without full EasyBuild integration:

1. **Create module directory:**

```bash
# Adjust paths according to your HPC setup
MODULE_ROOT=/path/to/modules
mkdir -p $MODULE_ROOT/MaSIF-neosurf
```

2. **Copy the .sif file:**

```bash
INSTALL_DIR=/path/to/software/MaSIF-neosurf/1.0
mkdir -p $INSTALL_DIR/bin
cp masif-neosurf.sif $INSTALL_DIR/
```

3. **Create wrapper scripts:**

```bash
# Shell wrapper
cat > $INSTALL_DIR/bin/masif-neosurf-shell << 'EOF'
#!/bin/bash
MASIF_SIF="$(dirname $(dirname $(readlink -f $0)))/masif-neosurf.sif"
singularity shell --bind $PWD:/home "$MASIF_SIF" "$@"
EOF
chmod +x $INSTALL_DIR/bin/masif-neosurf-shell

# Exec wrapper
cat > $INSTALL_DIR/bin/masif-neosurf-exec << 'EOF'
#!/bin/bash
MASIF_SIF="$(dirname $(dirname $(readlink -f $0)))/masif-neosurf.sif"
singularity exec --bind $PWD:/home "$MASIF_SIF" "$@"
EOF
chmod +x $INSTALL_DIR/bin/masif-neosurf-exec
```

4. **Create module file:**

```bash
cat > $MODULE_ROOT/MaSIF-neosurf/1.0 << EOF
#%Module1.0
proc ModulesHelp { } {
    puts stderr "MaSIF-neosurf 1.0 - Surface-based protein design"
}

module-whatis "MaSIF-neosurf Singularity container"

set root $INSTALL_DIR

prepend-path PATH \$root/bin
setenv MASIF_NEOSURF_SIF \$root/masif-neosurf.sif
setenv MASIF_NEOSURF_HOME \$root
EOF
```

## Using the Module

After installation, load and use the module:

```bash
# Load the module
module load MaSIF-neosurf/1.0

# Check available commands
module help MaSIF-neosurf/1.0

# Use the wrapper scripts
masif-neosurf-shell                    # Interactive shell
masif-neosurf-exec python3 --version   # Execute command

# Or use singularity directly
singularity exec --bind $PWD:/home $MASIF_NEOSURF_SIF <command>
```

## Example SLURM Job Script

```bash
#!/bin/bash
#SBATCH --job-name=masif-neosurf
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

# Load the module
module load MaSIF-neosurf/1.0

# Run preprocessing
masif-neosurf-exec ./preprocess_pdb.sh example/1a7x.pdb 1A7X_A -o output/

# Or for seed refinement
cd rosetta_scripts/seed_refine
masif-neosurf-exec python3 1-prepare.py -t ./1LRY_A.pdb -m BB2
masif-neosurf-exec bash 2-run.sh
```

## GPU Support

For GPU-enabled jobs, add the `--nv` flag:

```bash
#!/bin/bash
#SBATCH --gres=gpu:1

module load MaSIF-neosurf/1.0

singularity exec --nv --bind $PWD:/home $MASIF_NEOSURF_SIF python3 train_model.py
```

## Troubleshooting

### Module not found
Check your `MODULEPATH`:
```bash
echo $MODULEPATH
module use /path/to/your/modules
```

### Permission denied
Ensure the .sif file and wrapper scripts are executable:
```bash
chmod 755 $INSTALL_DIR/masif-neosurf.sif
chmod +x $INSTALL_DIR/bin/*
```

### Singularity not available
Load Singularity module first:
```bash
module load Singularity
module load MaSIF-neosurf/1.0
```

## Updating the Module

To update to a new version:

1. Build new .sif file with updated version number
2. Create new EasyConfig with updated version
3. Install with EasyBuild
4. Users can switch versions with `module load MaSIF-neosurf/<version>`
