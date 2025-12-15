#!/usr/bin/env python3
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

print('PyMOL Configuration:')
print(f'  Enabled: {os.environ.get("PYMOL_VDI_ENABLED")}')
print(f'  URL: {os.environ.get("PYMOL_VDI_URL")}')
print(f'  Shared Volume: {os.environ.get("PYMOL_SHARED_VOLUME")}')
print(f'  Timeout: {os.environ.get("PYMOL_SESSION_TIMEOUT")}')
print()

shared_vol = Path(os.environ.get("PYMOL_SHARED_VOLUME", "pymol-shared"))
print(f'Shared volume path: {shared_vol.absolute()}')
print(f'Exists: {shared_vol.exists()}')
print(f'Is directory: {shared_vol.is_dir()}')
