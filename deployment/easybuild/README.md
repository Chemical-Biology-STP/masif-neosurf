# EasyBuild Deployment

EasyBuild files for installing MaSIF-neosurf as an HPC module.

## Files

- `MaSIF-neosurf-1.0.eb` - EasyBuild recipe defining dependencies and installation
- `install_masif_easybuild.sh` - Automated installation script
- `install_masif_module.sh` - Module configuration script

## Installation

### Prerequisites

- EasyBuild installed on your HPC cluster
- Access to install modules (or appropriate EASYBUILD_PREFIX)

### Quick Install

```bash
bash install_masif_easybuild.sh
```

This will:
1. Set up EasyBuild environment
2. Install all dependencies
3. Build MaSIF-neosurf module
4. Configure module paths

### Manual Installation

```bash
# Load EasyBuild
module load EasyBuild

# Install MaSIF-neosurf
eb MaSIF-neosurf-1.0.eb --robot

# Load the module
module load MaSIF-neosurf/1.0
```

## Usage

After installation:

```bash
module load MaSIF-neosurf/1.0
masif-preprocess input.pdb CHAIN_ID
```

## Customization

Edit `MaSIF-neosurf-1.0.eb` to:
- Change version numbers
- Modify dependencies
- Adjust installation paths
- Add custom configurations

## Documentation

See `../../docs/EASYBUILD_INSTALLATION.md` for detailed installation guide.
