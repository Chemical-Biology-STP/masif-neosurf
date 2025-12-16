#!/usr/bin/env python3
"""
Script to assign jobs without user_id to a specific user
"""

import json
import sys
from pathlib import Path

def assign_jobs_to_user(user_id, user_email):
    """Assign all jobs without user_id to the specified user"""
    
    outputs_dir = Path("ui/outputs")
    if not outputs_dir.exists():
        print(f"Error: {outputs_dir} not found")
        return
    
    # Find all metadata.json files
    metadata_files = list(outputs_dir.glob("*/metadata.json"))
    
    updated_count = 0
    skipped_count = 0
    
    for metadata_file in metadata_files:
        try:
            # Read metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Check if user_id is missing
            if 'user_id' not in metadata or not metadata['user_id']:
                # Add user_id
                metadata['user_id'] = user_id
                
                # Write back
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                job_name = metadata.get('job_name', 'unknown')
                print(f"✓ Updated: {job_name} ({metadata_file.parent.name})")
                updated_count += 1
            else:
                skipped_count += 1
                
        except Exception as e:
            print(f"✗ Error processing {metadata_file}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Updated: {updated_count} jobs")
    print(f"  Skipped: {skipped_count} jobs (already have user_id)")
    print(f"  Assigned to: {user_email} ({user_id})")
    print(f"{'='*60}")


if __name__ == "__main__":
    # User to assign jobs to
    USER_ID = "35c101c7-c766-49d1-93a7-2d058befca8d"
    USER_EMAIL = "yipy@crick.ac.uk"
    
    print(f"Assigning jobs without user_id to: {USER_EMAIL}")
    print(f"User ID: {USER_ID}")
    print(f"{'='*60}\n")
    
    assign_jobs_to_user(USER_ID, USER_EMAIL)
