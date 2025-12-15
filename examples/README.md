# Example Files

Example input files for testing MaSIF-neosurf preprocessing.

## Files

### 1a7x.pdb
Protein structure file (PDB format) for testing basic preprocessing.

**Source:** PDB ID 1A7X  
**Description:** Example protein structure

### 1a7x_C_FKA.sdf
Ligand structure file (SDF format) for testing ligand-based preprocessing.

**Ligand ID:** FKA  
**Chain:** C  
**Description:** Example small molecule ligand

## Usage Examples

### Basic Preprocessing (No Ligand)

```bash
masif-preprocess 1a7x.pdb 1A7X_A
```

### With Ligand

```bash
masif-preprocess 1a7x.pdb 1A7X_A -l FKA_B -s 1a7x_C_FKA.sdf
```

### Using the Web Interface

1. Navigate to the web interface
2. Upload `1a7x.pdb`
3. Enter Chain ID: `1A7X_A`
4. (Optional) Upload `1a7x_C_FKA.sdf` and enter Ligand ID: `FKA_B`
5. Submit job

### Using Deployment Scripts

```bash
cd deployment/scripts
./preprocess_pdb.sh ../../examples/1a7x.pdb 1A7X_A
```

## Expected Output

After preprocessing, you should see:
- `output/` - Surface meshes (.ply) and predictions (.npy)
- `data_preparation/` - Preprocessed structures
- `descriptors/` - Surface features
- `targets/` - Predicted binding sites (if ligand provided)

## Testing

These files are used for:
- Verifying installation
- Testing the web interface
- Validating SLURM job submission
- Benchmarking performance

## Adding Your Own Examples

To add more examples:
1. Place PDB files in this directory
2. Add corresponding SDF files for ligands (if applicable)
3. Update this README with descriptions
4. Test with the preprocessing pipeline
