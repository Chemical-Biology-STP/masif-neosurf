#!/bin/bash
#
# Installation script for MaSIF-neosurf Singularity container as HPC module
# This script installs the container and creates module files for easy loading
#

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Default values - MODIFY THESE FOR YOUR HPC ENVIRONMENT
DEFAULT_INSTALL_DIR="${HOME}/software/MaSIF-neosurf/1.0"
DEFAULT_MODULE_DIR="${HOME}/modules/MaSIF-neosurf"
SIF_FILE="masif-neosurf.sif"
VERSION="1.0"

# Parse command line arguments
INSTALL_DIR=""
MODULE_DIR=""
USE_EASYBUILD=false

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Install MaSIF-neosurf Singularity container as an HPC module.

OPTIONS:
    -i, --install-dir DIR    Installation directory (default: $DEFAULT_INSTALL_DIR)
    -m, --module-dir DIR     Module files directory (default: $DEFAULT_MODULE_DIR)
    -e, --easybuild          Use EasyBuild for installation
    -h, --help               Show this help message

EXAMPLES:
    # Basic installation with defaults
    $0

    # Custom installation directory
    $0 -i /opt/software/MaSIF-neosurf/1.0 -m /opt/modules/MaSIF-neosurf

    # Use EasyBuild
    $0 -e

REQUIREMENTS:
    - masif-neosurf.sif file in current directory
    - Singularity installed and available
    - Write permissions to installation and module directories

EOF
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        -m|--module-dir)
            MODULE_DIR="$2"
            shift 2
            ;;
        -e|--easybuild)
            USE_EASYBUILD=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Set defaults if not provided
INSTALL_DIR="${INSTALL_DIR:-$DEFAULT_INSTALL_DIR}"
MODULE_DIR="${MODULE_DIR:-$DEFAULT_MODULE_DIR}"

print_info "MaSIF-neosurf Installation Script"
echo "=================================="
echo ""
echo "Installation directory: $INSTALL_DIR"
echo "Module directory:       $MODULE_DIR"
echo "Use EasyBuild:          $USE_EASYBUILD"
echo ""

# Check if .sif file exists
if [ ! -f "$SIF_FILE" ]; then
    print_error "Singularity image file '$SIF_FILE' not found in current directory!"
    print_info "Please build the image first using: sudo singularity build masif-neosurf.sif masif-neosurf.def"
    exit 1
fi

# Check if singularity is available
if ! command -v singularity &> /dev/null; then
    print_warn "Singularity command not found. Make sure it's available on your HPC system."
    print_info "You may need to: module load Singularity"
fi

# Confirm installation
read -p "Proceed with installation? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Installation cancelled."
    exit 0
fi

# Installation using EasyBuild
if [ "$USE_EASYBUILD" = true ]; then
    print_info "Installing using EasyBuild..."
    
    if ! command -v eb &> /dev/null; then
        print_error "EasyBuild (eb) command not found!"
        print_info "Load EasyBuild module or install manually."
        exit 1
    fi
    
    # Check if EasyConfig exists
    if [ ! -f "MaSIF-neosurf-${VERSION}.eb" ]; then
        print_error "EasyConfig file 'MaSIF-neosurf-${VERSION}.eb' not found!"
        exit 1
    fi
    
    # Create tarball for EasyBuild
    print_info "Creating tarball..."
    tar czf "masif-neosurf-${VERSION}.tar.gz" "$SIF_FILE"
    
    # Calculate checksum
    CHECKSUM=$(sha256sum "masif-neosurf-${VERSION}.tar.gz" | awk '{print $1}')
    print_info "SHA256 checksum: $CHECKSUM"
    
    # Update EasyConfig with checksum
    sed -i "s/checksums = \[''\]/checksums = ['$CHECKSUM']/" "MaSIF-neosurf-${VERSION}.eb"
    
    # Install with EasyBuild
    print_info "Running EasyBuild..."
    eb "MaSIF-neosurf-${VERSION}.eb" --robot
    
    print_info "EasyBuild installation complete!"
    print_info "Load the module with: module load MaSIF-neosurf/${VERSION}"
    
else
    # Manual installation
    print_info "Installing manually..."
    
    # Create installation directory
    print_info "Creating installation directory: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/bin"
    
    # Copy .sif file
    print_info "Copying Singularity image..."
    cp "$SIF_FILE" "$INSTALL_DIR/"
    chmod 755 "$INSTALL_DIR/$SIF_FILE"
    
    # Create wrapper scripts
    print_info "Creating wrapper scripts..."
    
    # Shell wrapper
    cat > "$INSTALL_DIR/bin/masif-neosurf-shell" << 'EOF'
#!/bin/bash
MASIF_SIF="$(dirname $(dirname $(readlink -f $0)))/masif-neosurf.sif"
singularity shell --bind $PWD:/home "$MASIF_SIF" "$@"
EOF
    chmod +x "$INSTALL_DIR/bin/masif-neosurf-shell"
    
    # Exec wrapper
    cat > "$INSTALL_DIR/bin/masif-neosurf-exec" << 'EOF'
#!/bin/bash
MASIF_SIF="$(dirname $(dirname $(readlink -f $0)))/masif-neosurf.sif"
singularity exec --bind $PWD:/home "$MASIF_SIF" "$@"
EOF
    chmod +x "$INSTALL_DIR/bin/masif-neosurf-exec"
    
    # Preprocess wrapper
    cat > "$INSTALL_DIR/bin/masif-preprocess" << 'EOF'
#!/bin/bash
MASIF_SIF="$(dirname $(dirname $(readlink -f $0)))/masif-neosurf.sif"
singularity exec --bind $PWD:/home "$MASIF_SIF" /home/preprocess_pdb.sh "$@"
EOF
    chmod +x "$INSTALL_DIR/bin/masif-preprocess"
    
    # Create module directory
    print_info "Creating module directory: $MODULE_DIR"
    mkdir -p "$MODULE_DIR"
    
    # Create module file
    print_info "Creating module file..."
    cat > "$MODULE_DIR/$VERSION" << EOF
#%Module1.0
##
## MaSIF-neosurf module file
##
proc ModulesHelp { } {
    puts stderr "MaSIF-neosurf ${VERSION} - Surface-based protein design for ternary complexes"
    puts stderr ""
    puts stderr "Available commands:"
    puts stderr "  masif-neosurf-shell    - Start interactive shell in container"
    puts stderr "  masif-neosurf-exec     - Execute command in container"
    puts stderr "  masif-preprocess       - Run preprocess_pdb.sh script"
    puts stderr ""
    puts stderr "Examples:"
    puts stderr "  masif-neosurf-shell"
    puts stderr "  masif-neosurf-exec python3 --version"
    puts stderr "  masif-preprocess example/1a7x.pdb 1A7X_A -o output/"
}

module-whatis "MaSIF-neosurf ${VERSION} - Singularity container for protein design"

set root ${INSTALL_DIR}

prepend-path PATH \$root/bin
setenv MASIF_NEOSURF_SIF \$root/masif-neosurf.sif
setenv MASIF_NEOSURF_HOME \$root
setenv MASIF_NEOSURF_VERSION ${VERSION}

if { [module-info mode load] } {
    puts stderr ""
    puts stderr "MaSIF-neosurf ${VERSION} loaded."
    puts stderr "Use 'module help MaSIF-neosurf/${VERSION}' for usage information."
    puts stderr ""
}
EOF
    
    print_info "Installation complete!"
    echo ""
    print_info "To use the module, add the module directory to your MODULEPATH:"
    echo "    module use $MODULE_DIR/.."
    echo "    module load MaSIF-neosurf/${VERSION}"
    echo ""
    print_info "Or add this to your ~/.bashrc:"
    echo "    export MODULEPATH=\$MODULEPATH:$MODULE_DIR/.."
    echo ""
fi

# Create a quick test script
print_info "Creating test script..."
cat > "test_masif_module.sh" << EOF
#!/bin/bash
# Test script for MaSIF-neosurf module

echo "Testing MaSIF-neosurf module installation..."
echo ""

# Load module
echo "Loading module..."
module use $MODULE_DIR/..
module load MaSIF-neosurf/${VERSION}

# Check environment variables
echo "Checking environment variables..."
echo "MASIF_NEOSURF_SIF: \$MASIF_NEOSURF_SIF"
echo "MASIF_NEOSURF_HOME: \$MASIF_NEOSURF_HOME"
echo ""

# Test commands
echo "Testing wrapper scripts..."
which masif-neosurf-shell
which masif-neosurf-exec
which masif-preprocess
echo ""

# Test singularity exec
echo "Testing Singularity execution..."
masif-neosurf-exec python3 --version
echo ""

echo "Test complete! Module is working correctly."
EOF
chmod +x "test_masif_module.sh"

print_info "Test script created: test_masif_module.sh"
echo ""

# Summary
echo "=================================="
print_info "Installation Summary"
echo "=================================="
echo ""
echo "Installation directory: $INSTALL_DIR"
echo "Module file location:   $MODULE_DIR/$VERSION"
echo ""
echo "Next steps:"
echo "  1. Add module directory to MODULEPATH:"
echo "     module use $MODULE_DIR/.."
echo ""
echo "  2. Load the module:"
echo "     module load MaSIF-neosurf/${VERSION}"
echo ""
echo "  3. Test the installation:"
echo "     ./test_masif_module.sh"
echo ""
echo "  4. Use the module:"
echo "     masif-neosurf-shell                    # Interactive shell"
echo "     masif-neosurf-exec <command>           # Execute command"
echo "     masif-preprocess <pdb> <chain> -o out/ # Preprocess PDB"
echo ""
print_info "Installation successful!"
