# Deployment Scripts

Utility scripts for deployment and testing.

## Scripts

### preprocess_pdb.sh

Main preprocessing wrapper script that handles:
- PDB file preprocessing
- Chain extraction
- Ligand processing (optional)
- Output organization

**Usage:**
```bash
./preprocess_pdb.sh input.pdb CHAIN_ID [-l LIGAND_ID] [-s ligand.sdf] [-o output_dir]
```

**Examples:**
```bash
# Basic preprocessing
./preprocess_pdb.sh 1a7x.pdb 1A7X_A

# With ligand
./preprocess_pdb.sh 1a7x.pdb 1A7X_A -l FKA_B -s 1a7x_C_FKA.sdf

# Custom output directory
./preprocess_pdb.sh 1a7x.pdb 1A7X_A -o /path/to/output
```

### test_email.sh

Tests email notification functionality on HPC.

**Usage:**
```bash
./test_email.sh your.email@crick.ac.uk
```

This script:
- Tests the HPC mail command
- Sends a test email
- Verifies email delivery

**Troubleshooting:**
If emails aren't working, see `../../docs/EMAIL_TROUBLESHOOTING.md`

## Integration

These scripts are used by:
- The web interface (`ui/app.py`)
- SLURM job submissions
- Manual command-line usage
- Automated testing

## Customization

Edit scripts to:
- Change default parameters
- Modify output formats
- Add custom preprocessing steps
- Adjust email templates
