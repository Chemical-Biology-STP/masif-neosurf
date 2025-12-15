#!/usr/bin/env python3
"""
Test Docker management functions
"""

import subprocess
from pathlib import Path


def check_docker_available():
    """Check if Docker is available on the system"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_pymol_container_status():
    """Check if PyMOL VDI container is running"""
    try:
        result = subprocess.run(
            ['docker', 'ps', '-a', '--filter', 'name=pymol', '--format', '{{.Names}}\t{{.Status}}'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return 'error'
        
        output = result.stdout.strip()
        if not output:
            return 'not_found'
        
        for line in output.split('\n'):
            if 'pymol' in line.lower():
                if 'up' in line.lower():
                    return 'running'
                else:
                    return 'stopped'
        
        return 'not_found'
        
    except Exception as e:
        print(f"Error: {e}")
        return 'error'


def main():
    print("=" * 60)
    print("Docker Management Test")
    print("=" * 60)
    
    # Test 1: Check Docker availability
    print("\n1. Checking Docker availability...")
    docker_available = check_docker_available()
    if docker_available:
        print("   ✓ Docker is available")
        
        # Get Docker version
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, 
                              text=True)
        print(f"   {result.stdout.strip()}")
    else:
        print("   ✗ Docker is not available")
        return
    
    # Test 2: Check container status
    print("\n2. Checking PyMOL container status...")
    status = check_pymol_container_status()
    print(f"   Status: {status}")
    
    if status == 'running':
        print("   ✓ Container is running")
        
        # Get container details
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=pymol', '--format', 
             'table {{.Names}}\t{{.Status}}\t{{.Ports}}'],
            capture_output=True,
            text=True
        )
        print("\n   Container details:")
        for line in result.stdout.strip().split('\n'):
            print(f"   {line}")
            
    elif status == 'stopped':
        print("   ⚠️  Container exists but is stopped")
        print("   You can start it with: docker-compose up -d pymol-vdi")
        
    elif status == 'not_found':
        print("   ⚠️  Container not found")
        print("   You can create it with: docker-compose up -d pymol-vdi")
        
    else:
        print("   ✗ Error checking status")
    
    # Test 3: Check docker-compose file
    print("\n3. Checking docker-compose.yml...")
    compose_file = Path(__file__).parent / 'docker-compose.yml'
    if compose_file.exists():
        print(f"   ✓ Found: {compose_file}")
        
        # Check if pymol-vdi service is defined
        content = compose_file.read_text()
        if 'pymol-vdi' in content:
            print("   ✓ pymol-vdi service is defined")
        else:
            print("   ✗ pymol-vdi service not found in docker-compose.yml")
    else:
        print(f"   ✗ Not found: {compose_file}")
    
    # Test 4: Check shared volume
    print("\n4. Checking shared volume...")
    shared_volume = Path(__file__).parent / 'pymol-shared'
    if shared_volume.exists():
        print(f"   ✓ Found: {shared_volume}")
        
        # Count sessions
        sessions = list(shared_volume.glob('*'))
        print(f"   Sessions: {len(sessions)}")
        if sessions:
            print("   Active sessions:")
            for session in sessions[:5]:  # Show first 5
                print(f"     - {session.name}")
            if len(sessions) > 5:
                print(f"     ... and {len(sessions) - 5} more")
    else:
        print(f"   ⚠️  Not found: {shared_volume}")
        print("   Will be created when PyMOL is first used")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
