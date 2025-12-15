#!/bin/bash
#
# Installation script for MaSIF-neosurf using EasyBuild on HPC
# Configured for: /nemo/stp/chemicalbiology/home/shared/easybuild
#

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# EasyBuild paths
EASYBUILD_ROOT="/nemo/stp/chemicalbiology/home/shared/easybuild"
EASYBUILD_SOFTWARE="${EASYBUILD_ROOT}/software"
EASYBUILD_MODULES="${EASYBUILD_ROOT}/modules"
EASYBUILD_SOURCES="${EASYBUILD_ROOT}/sources"
EASYBUILD_BUILD="${EASYBUILD_ROOT}/build"
EASYBUILD_EBFILES="${EASYBUILD_ROOT}/ebfiles_repo"

# Application details
APP_NAME="MaSIF-neosurf"
VERSION="1.0"
SIF_FILE="masif-neosurf.sif"

# Installation paths
INSTALL_DIR="${EASYBUILD_SOFTWARE}/${APP_NAME}/${VERSION}"
MODULE_DIR="${EASYBUILD_MODULES}/all/${APP_NAME}"

echo ""
echo "=========================================="
echo "  MaSIF-neosurf EasyBuild Installation"
echo "=========================================="
echo ""
echo "EasyBuild root:     $EASYBUILD_ROOT"
echo "Installation dir:   $INSTALL_DIR"
echo "Module dir:         $MODULE_DIR"
echo "Version:            $VERSION"
echo ""

# Check if .sif file exists
print_step "Checking for Singularity image..."
if [ ! -f "$SIF_FILE" ]; then
    print_error "Singularity image file '$SIF_FILE' not found in current directory!"
    print_info "Please build the image first using:"
    echo "    sudo singularity build masif-neosurf.sif masif-neosurf.def"
    exit 1
fi
print_info "Found: $SIF_FILE"

# Check if singularity is available
print_step "Checking for Singularity..."
if ! command -v singularity &> /dev/null; then
    print_warn "Singularity command not found. Attempting to load module..."
    if command -v module &> /dev/null; then
        module load Singularity/3.11.3 2>/dev/null || print_warn "Could not load Singularity/3.11.3 module"
    fi
fi

if command -v singularity &> /dev/null; then
    SINGULARITY_VERSION=$(singularity --version)
    print_info "Singularity version: $SINGULARITY_VERSION"
else
    print_warn "Singularity not available, but continuing (will be loaded as module dependency)"
fi

# Check write permissions
print_step "Checking permissions..."
if [ ! -w "$EASYBUILD_ROOT" ]; then
    print_error "No write permission to $EASYBUILD_ROOT"
    print_info "You may need to run this script with appropriate permissions or contact your HPC admin."
    exit 1
fi
print_info "Write permissions OK"

# Confirm installation
echo ""
read -p "Proceed with installation? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Installation cancelled."
    exit 0
fi

# Create installation directory
print_step "Creating installation directory..."
mkdir -p "$INSTALL_DIR/bin"
print_info "Created: $INSTALL_DIR"

# Copy .sif file
print_step "Installing Singularity image..."
cp "$SIF_FILE" "$INSTALL_DIR/"
chmod 755 "$INSTALL_DIR/$SIF_FILE"
SIF_SIZE=$(du -h "$INSTALL_DIR/$SIF_FILE" | cut -f1)
print_info "Installed: $SIF_FILE ($SIF_SIZE)"

# Create wrapper scripts
print_step "Creating wrapper scripts..."

# Shell wrapper
cat > "$INSTALL_DIR/bin/masif-neosurf-shell" << 'EOF'
#!/bin/bash
# MaSIF-neosurf interactive shell wrapper
MASIF_SIF="$(dirname $(dirname $(readlink -f $0)))/masif-neosurf.sif"

# Default bind paths
BIND_PATHS="$PWD:/home"

# Add common HPC paths if they exist
[ -d "/nemo" ] && BIND_PATHS="$BIND_PATHS,/nemo"
[ -d "/scratch" ] && BIND_PATHS="$BIND_PATHS,/scratch"

singularity shell --bind "$BIND_PATHS" "$MASIF_SIF" "$@"
EOF
chmod +x "$INSTALL_DIR/bin/masif-neosurf-shell"

# Exec wrapper
cat > "$INSTALL_DIR/bin/masif-neosurf-exec" << 'EOF'
#!/bin/bash
# MaSIF-neosurf command execution wrapper
MASIF_SIF="$(dirname $(dirname $(readlink -f $0)))/masif-neosurf.sif"

# Default bind paths
BIND_PATHS="$PWD:/home"

# Add common HPC paths if they exist
[ -d "/nemo" ] && BIND_PATHS="$BIND_PATHS,/nemo"
[ -d "/scratch" ] && BIND_PATHS="$BIND_PATHS,/scratch"

singularity exec --bind "$BIND_PATHS" "$MASIF_SIF" "$@"
EOF
chmod +x "$INSTALL_DIR/bin/masif-neosurf-exec"

# Exec wrapper with GPU support
cat > "$INSTALL_DIR/bin/masif-neosurf-exec-gpu" << 'EOF'
#!/bin/bash
# MaSIF-neosurf command execution wrapper with GPU support
MASIF_SIF="$(dirname $(dirname $(readlink -f $0)))/masif-neosurf.sif"

# Default bind paths
BIND_PATHS="$PWD:/home"

# Add common HPC paths if they exist
[ -d "/nemo" ] && BIND_PATHS="$BIND_PATHS,/nemo"
[ -d "/scratch" ] && BIND_PATHS="$BIND_PATHS,/scratch"

singularity exec --nv --bind "$BIND_PATHS" "$MASIF_SIF" "$@"
EOF
chmod +x "$INSTALL_DIR/bin/masif-neosurf-exec-gpu"

# Preprocess wrapper
cat > "$INSTALL_DIR/bin/masif-preprocess" << 'EOF'
#!/bin/bash
# MaSIF-neosurf preprocessing wrapper
MASIF_SIF="$(dirname $(dirname $(readlink -f $0)))/masif-neosurf.sif"

# Default bind paths
BIND_PATHS="$PWD:/home"

# Add common HPC paths if they exist
[ -d "/nemo" ] && BIND_PATHS="$BIND_PATHS,/nemo"
[ -d "/scratch" ] && BIND_PATHS="$BIND_PATHS,/scratch"

singularity exec --bind "$BIND_PATHS" "$MASIF_SIF" /home/preprocess_pdb.sh "$@"
EOF
chmod +x "$INSTALL_DIR/bin/masif-preprocess"

print_info "Created wrapper scripts:"
print_info "  - masif-neosurf-shell"
print_info "  - masif-neosurf-exec"
print_info "  - masif-neosurf-exec-gpu"
print_info "  - masif-preprocess"

# Create module directory
print_step "Creating module file..."
mkdir -p "$MODULE_DIR"

# Create module file
cat > "$MODULE_DIR/$VERSION.lua" << EOF
-- MaSIF-neosurf module file
help([[
MaSIF-neosurf ${VERSION} - Surface-based protein design for ternary complexes

Description:
  MaSIF-neosurf is a computational strategy for the design of proteins that 
  target neosurfaces, i.e. surfaces arising from protein-ligand complexes.
  This module provides a Singularity container with all dependencies pre-installed.

Available commands:
  masif-neosurf-shell      - Start interactive shell in container
  masif-neosurf-exec       - Execute command in container
  masif-neosurf-exec-gpu   - Execute command with GPU support
  masif-preprocess         - Run preprocess_pdb.sh script

Examples:
  # Interactive shell
  masif-neosurf-shell

  # Execute command
  masif-neosurf-exec python3 --version

  # Preprocess PDB file
  masif-preprocess example/1a7x.pdb 1A7X_A -o output/

  # With ligand
  masif-preprocess example/1a7x.pdb 1A7X_A -l FKA_B -s example/1a7x_C_FKA.sdf -o output/

  # Direct singularity usage
  singularity exec --bind \$PWD:/home \$MASIF_NEOSURF_SIF <command>

  # GPU support
  masif-neosurf-exec-gpu python3 train_model.py

For more information:
  https://github.com/LPDI-EPFL/masif-neosurf
]])

whatis("Name: MaSIF-neosurf")
whatis("Version: ${VERSION}")
whatis("Category: bio, computational biology")
whatis("Description: Surface-based protein design for ternary complexes")
whatis("URL: https://github.com/LPDI-EPFL/masif-neosurf")

-- Load required dependencies
load("Singularity/3.11.3")

local root = "${INSTALL_DIR}"

prepend_path("PATH", pathJoin(root, "bin"))
setenv("MASIF_NEOSURF_SIF", pathJoin(root, "masif-neosurf.sif"))
setenv("MASIF_NEOSURF_HOME", root)
setenv("MASIF_NEOSURF_VERSION", "${VERSION}")

if (mode() == "load") then
    LmodMessage("")
    LmodMessage("MaSIF-neosurf ${VERSION} loaded.")
    LmodMessage("Singularity/3.11.3 loaded as dependency.")
    LmodMessage("Use 'module help ${APP_NAME}/${VERSION}' for usage information.")
    LmodMessage("")
end
EOF

print_info "Created module file: $MODULE_DIR/$VERSION.lua"

# Copy EasyConfig to ebfiles_repo for documentation
print_step "Archiving EasyConfig..."
mkdir -p "$EASYBUILD_EBFILES/${APP_NAME}"
if [ -f "MaSIF-neosurf-${VERSION}.eb" ]; then
    cp "MaSIF-neosurf-${VERSION}.eb" "$EASYBUILD_EBFILES/${APP_NAME}/"
    print_info "Copied EasyConfig to: $EASYBUILD_EBFILES/${APP_NAME}/"
fi

# Create usage documentation
print_step "Creating documentation..."
cat > "$INSTALL_DIR/README.txt" << EOF
MaSIF-neosurf ${VERSION}
========================

Installation Date: $(date)
Installation Path: $INSTALL_DIR
Module Path: $MODULE_DIR/$VERSION.lua

LOADING THE MODULE
------------------
module load ${APP_NAME}/${VERSION}

Note: Singularity/3.11.3 will be automatically loaded as a dependency.

AVAILABLE COMMANDS
------------------
masif-neosurf-shell      - Interactive shell
masif-neosurf-exec       - Execute commands
masif-neosurf-exec-gpu   - Execute with GPU support
masif-preprocess         - Preprocess PDB files

ENVIRONMENT VARIABLES
---------------------
MASIF_NEOSURF_SIF        - Path to Singularity image
MASIF_NEOSURF_HOME       - Installation directory
MASIF_NEOSURF_VERSION    - Version number

EXAMPLES
--------
# Load module
module load ${APP_NAME}/${VERSION}

# Interactive shell
masif-neosurf-shell

# Execute command
masif-neosurf-exec python3 --version

# Preprocess PDB
masif-preprocess example/1a7x.pdb 1A7X_A -o output/

# SLURM job example
#!/bin/bash
#SBATCH --job-name=masif
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

module load ${APP_NAME}/${VERSION}
masif-preprocess input.pdb CHAIN_A -o results/

SUPPORT
-------
GitHub: https://github.com/LPDI-EPFL/masif-neosurf
EOF

print_info "Created: $INSTALL_DIR/README.txt"

# Create SLURM job template
cat > "$INSTALL_DIR/slurm_template.sh" << 'EOF'
#!/bin/bash
#SBATCH --job-name=masif-neosurf
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=masif_%j.out
#SBATCH --error=masif_%j.err

# Load MaSIF-neosurf module (Singularity/3.11.3 loaded automatically)
module load MaSIF-neosurf/1.0

# Set working directory
cd $SLURM_SUBMIT_DIR

# Example: Preprocess PDB file
masif-preprocess example/1a7x.pdb 1A7X_A -o output/

# Example: Run seed refinement
# cd rosetta_scripts/seed_refine
# masif-neosurf-exec python3 1-prepare.py -t ./1LRY_A.pdb -m BB2
# masif-neosurf-exec bash 2-run.sh

echo "Job completed!"
EOF

# Create GPU SLURM job template
cat > "$INSTALL_DIR/slurm_template_gpu.sh" << 'EOF'
#!/bin/bash
#SBATCH --job-name=masif-neosurf-gpu
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --output=masif_gpu_%j.out
#SBATCH --error=masif_gpu_%j.err

# Load MaSIF-neosurf module (Singularity/3.11.3 loaded automatically)
module load MaSIF-neosurf/1.0

# Set working directory
cd $SLURM_SUBMIT_DIR

# Example: Run with GPU support
masif-neosurf-exec-gpu python3 train_model.py

echo "GPU job completed!"
EOF

print_info "Created: $INSTALL_DIR/slurm_template.sh"
print_info "Created: $INSTALL_DIR/slurm_template_gpu.sh"

# Installation complete
echo ""
echo "=========================================="
print_info "Installation Complete!"
echo "=========================================="
echo ""
echo "Installation Summary:"
echo "  Software:     $INSTALL_DIR"
echo "  Module:       $MODULE_DIR/$VERSION.lua"
echo "  Size:         $SIF_SIZE"
echo ""
echo "To use MaSIF-neosurf:"
echo ""
echo "  1. Load the module:"
echo "     module load ${APP_NAME}/${VERSION}"
echo ""
echo "  2. View help:"
echo "     module help ${APP_NAME}/${VERSION}"
echo ""
echo "  3. Test the installation:"
echo "     masif-neosurf-exec python3 --version"
echo ""
echo "  4. Run preprocessing:"
echo "     masif-preprocess <pdb_file> <chain> -o <output_dir>"
echo ""
echo "Documentation:"
echo "  README:       $INSTALL_DIR/README.txt"
echo "  SLURM template: $INSTALL_DIR/slurm_template.sh"
echo ""
print_info "Module is ready to use!"
echo ""
