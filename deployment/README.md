# Deployment

This directory contains all deployment-related files for MaSIF-neosurf across different platforms and environments.

## Directory Structure

```
deployment/
├── easybuild/          # EasyBuild module files
├── singularity/        # Singularity container files
├── docker/             # Docker container files
└── scripts/            # Deployment and utility scripts
```

## Deployment Options

### 1. EasyBuild Module (Recommended for HPC)

EasyBuild provides a standardized way to install software on HPC clusters.

**Files:**
- `easybuild/MaSIF-neosurf-1.0.eb` - EasyBuild recipe
- `easybuild/install_masif_easybuild.sh` - Installation script
- `easybuild/install_masif_module.sh` - Module setup script

**Documentation:** See `../docs/EASYBUILD_INSTALLATION.md`

### 2. Singularity Container

Singularity is ideal for HPC environments where Docker is not available.

**Files:**
- `singularity/masif-neosurf.def` - Singularity definition file
- `singularity/masif-neosurf.sif` - Pre-built Singularity image (if available)

**Documentation:** See `../docs/SINGULARITY_USAGE.md`

### 3. Docker Container

Docker provides an isolated environment for development and testing.

**Files:**
- `docker/Dockerfile` - Docker image definition

**Usage:**
```bash
cd deployment/docker
docker build -t masif-neosurf:latest .
docker run -it masif-neosurf:latest
```

## Utility Scripts

Located in `scripts/`:

- `preprocess_pdb.sh` - Main preprocessing wrapper script
- `test_email.sh` - Test email notification functionality

## Quick Start

For HPC deployment with EasyBuild:
```bash
cd deployment/easybuild
bash install_masif_easybuild.sh
```

For Singularity:
```bash
cd deployment/singularity
singularity build masif-neosurf.sif masif-neosurf.def
```

## Support

For deployment issues, refer to:
- `../docs/HPC_USAGE_GUIDE.md` - General HPC usage
- `../docs/EMAIL_TROUBLESHOOTING.md` - Email notification issues
- `../docs/EMAIL_SOLUTION_SUMMARY.md` - Email setup solutions
