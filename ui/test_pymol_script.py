#!/usr/bin/env python3
"""
Test PyMOL script generation
"""

from pathlib import Path
import tempfile
import shutil

def test_pymol_script_generation():
    """Test that the PyMOL script generates correct paths"""
    
    print("=" * 60)
    print("PyMOL Script Generation Test")
    print("=" * 60)
    
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create mock job directory
        job_dir = tmpdir / "data"
        job_dir.mkdir()
        
        # Create mock files
        (job_dir / "test.pdb").write_text("MOCK PDB")
        
        output_dir = job_dir / "output"
        output_dir.mkdir()
        (output_dir / "surface1.ply").write_text("MOCK PLY")
        (output_dir / "target_surface.ply").write_text("MOCK PLY")
        
        # Mock metadata
        metadata = {
            'job_name': 'test_job',
            'chain_id': 'A',
            'submitted_at': '2024-01-01',
            'pdb_file': 'test.pdb'
        }
        
        session_id = "user123_job456_1234567890"
        
        # Generate script (inline version for testing)
        def generate_pymol_script(session_id, job_dir, metadata):
            """Generate PyMOL script to load MaSIF results"""
            container_data_path = f"/data/{session_id}/data"
            
            script = f"""# MaSIF-neosurf Results Visualization
# Job: {metadata['job_name']}
# Chain: {metadata['chain_id']}
# Submitted: {metadata['submitted_at']}

print "="*60
print "Loading MaSIF-neosurf results..."
print "Job: {metadata['job_name']}"
print "="*60

# Set background and rendering
bg_color white
set antialias, 2
set ray_trace_mode, 1
set surface_quality, 2
set transparency, 0.3

"""
            
            # Find PDB file
            pdb_filename = metadata.get('pdb_file', '')
            pdb_file = job_dir / pdb_filename
            
            if pdb_file.exists():
                pdb_path = f"{container_data_path}/{pdb_filename}"
                script += f"# Load PDB structure\n"
                script += f"load {pdb_path}, protein\n"
                script += "color cyan, protein\n"
                script += "show cartoon, protein\n"
                script += "hide lines, protein\n"
                script += f"print 'Loaded protein structure: {pdb_filename}'\n\n"
            else:
                script += f"print 'Warning: PDB file not found: {pdb_filename}'\n\n"
            
            script += "# Load surface files (.ply)\n"
            
            # Find and load .ply files
            ply_files = sorted(job_dir.rglob('*.ply'))
            
            if ply_files:
                for i, ply_file in enumerate(ply_files):
                    # Get relative path from job_dir
                    rel_path = ply_file.relative_to(job_dir)
                    # Construct absolute path in container
                    ply_path = f"{container_data_path}/{rel_path}"
                    obj_name = ply_file.stem.replace('-', '_').replace('.', '_')
                    
                    script += f"load {ply_path}, {obj_name}\n"
                    
                    # Color surfaces based on type
                    if 'target' in ply_file.name.lower():
                        script += f"color red, {obj_name}\n"
                    elif 'ligand' in ply_file.name.lower():
                        script += f"color yellow, {obj_name}\n"
                    else:
                        script += f"color green, {obj_name}\n"
                
                script += f"print 'Loaded {len(ply_files)} surface files'\n\n"
            else:
                script += "print 'Warning: No .ply surface files found'\n\n"
            
            script += """# Adjust view
zoom
center

print "="*60
print "MaSIF-neosurf results loaded successfully!"
print "="*60
print ""
print "Mouse controls:"
print "  Rotate: Left-click and drag"
print "  Zoom: Scroll wheel"
print "  Pan: Right-click and drag"
print ""
"""
            
            return script
        
        script = generate_pymol_script(session_id, job_dir, metadata)
        
        print("\nGenerated PyMOL Script:")
        print("-" * 60)
        print(script)
        print("-" * 60)
        
        # Verify script contains correct paths
        expected_pdb_path = f"/data/{session_id}/data/test.pdb"
        expected_ply_path = f"/data/{session_id}/data/output/surface1.ply"
        
        print("\nVerification:")
        print(f"✓ Session ID: {session_id}")
        print(f"✓ Expected PDB path: {expected_pdb_path}")
        print(f"✓ Expected PLY path: {expected_ply_path}")
        
        if expected_pdb_path in script:
            print("✅ PDB path is correct")
        else:
            print("❌ PDB path is missing or incorrect")
            
        if expected_ply_path in script:
            print("✅ PLY path is correct")
        else:
            print("❌ PLY path is missing or incorrect")
            
        if "target_surface" in script:
            print("✅ Target surface detected")
        else:
            print("❌ Target surface not detected")
            
        if "color red" in script:
            print("✅ Target surface colored red")
        else:
            print("❌ Target surface color not set")
            
        # Check for helpful print statements
        if "Loading MaSIF-neosurf results" in script:
            print("✅ User-friendly messages included")
        else:
            print("❌ User-friendly messages missing")
        
        print("\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    test_pymol_script_generation()
