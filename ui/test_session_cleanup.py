#!/usr/bin/env python3
"""
Test script for PyMOL session cleanup functionality
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_cleanup_simulation():
    """Simulate session cleanup behavior"""
    
    print("=" * 60)
    print("PyMOL Session Cleanup Test")
    print("=" * 60)
    
    # Simulate shared volume
    test_dir = Path("test_pymol_shared")
    test_dir.mkdir(exist_ok=True)
    
    user_id = "test_user_123"
    job_uuid = "abc123"
    
    # Create multiple session directories (simulating relaunches)
    sessions = []
    for i in range(3):
        timestamp = int(time.time()) - (i * 100)  # Different timestamps
        session_id = f"{user_id}_{job_uuid}_{timestamp}"
        session_dir = test_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Create a dummy file
        (session_dir / "test.txt").write_text(f"Session {i}")
        sessions.append(session_dir)
        print(f"✓ Created session: {session_id}")
    
    print(f"\nTotal sessions created: {len(sessions)}")
    print(f"Sessions in directory: {len(list(test_dir.glob('*')))}")
    
    # Simulate cleanup (what the app does)
    print("\n" + "-" * 60)
    print("Simulating cleanup_old_sessions()...")
    print("-" * 60)
    
    pattern = f"{user_id}_{job_uuid}_*"
    print(f"Pattern: {pattern}")
    
    cleaned = 0
    for session_dir in test_dir.glob(pattern):
        if session_dir.is_dir():
            print(f"  Cleaning up: {session_dir.name}")
            import shutil
            shutil.rmtree(session_dir)
            cleaned += 1
    
    print(f"\n✓ Cleaned up {cleaned} old sessions")
    
    # Create new session
    new_timestamp = int(time.time())
    new_session_id = f"{user_id}_{job_uuid}_{new_timestamp}"
    new_session_dir = test_dir / new_session_id
    new_session_dir.mkdir(exist_ok=True)
    (new_session_dir / "test.txt").write_text("New session")
    
    print(f"✓ Created new session: {new_session_id}")
    
    # Verify only new session exists
    remaining = list(test_dir.glob(pattern))
    print(f"\nSessions remaining: {len(remaining)}")
    for session in remaining:
        print(f"  - {session.name}")
    
    # Cleanup test directory
    import shutil
    shutil.rmtree(test_dir)
    print(f"\n✓ Test directory cleaned up")
    
    print("\n" + "=" * 60)
    if len(remaining) == 1:
        print("✅ TEST PASSED: Only new session remains")
    else:
        print("❌ TEST FAILED: Multiple sessions found")
    print("=" * 60)


def test_pattern_matching():
    """Test that pattern matching works correctly"""
    
    print("\n" + "=" * 60)
    print("Pattern Matching Test")
    print("=" * 60)
    
    test_dir = Path("test_pymol_shared")
    test_dir.mkdir(exist_ok=True)
    
    # Create sessions for different users and jobs
    test_cases = [
        ("user1", "job1", True),   # Should match
        ("user1", "job1", True),   # Should match
        ("user1", "job2", False),  # Different job
        ("user2", "job1", False),  # Different user
        ("user1", "job1", True),   # Should match
    ]
    
    counter = 0
    for user_id, job_uuid, should_match in test_cases:
        timestamp = int(time.time()) + counter
        session_id = f"{user_id}_{job_uuid}_{timestamp}"
        session_dir = test_dir / session_id
        session_dir.mkdir(exist_ok=True)
        counter += 1
    
    print(f"Created {len(test_cases)} test sessions")
    
    # Test cleanup for user1, job1
    target_user = "user1"
    target_job = "job1"
    pattern = f"{target_user}_{target_job}_*"
    
    print(f"\nCleaning up pattern: {pattern}")
    
    matched = list(test_dir.glob(pattern))
    print(f"Matched sessions: {len(matched)}")
    
    expected_matches = sum(1 for _, _, should_match in test_cases if should_match)
    
    for session_dir in matched:
        print(f"  - {session_dir.name}")
        import shutil
        shutil.rmtree(session_dir)
    
    remaining = list(test_dir.glob("*"))
    print(f"\nRemaining sessions: {len(remaining)}")
    for session_dir in remaining:
        print(f"  - {session_dir.name}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)
    
    print("\n" + "=" * 60)
    if len(matched) == expected_matches:
        print(f"✅ TEST PASSED: Matched {len(matched)} sessions (expected {expected_matches})")
    else:
        print(f"❌ TEST FAILED: Matched {len(matched)} sessions (expected {expected_matches})")
    print("=" * 60)


if __name__ == "__main__":
    test_cleanup_simulation()
    test_pattern_matching()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
