"""
NexusOps SDK - Test Configuration

Add SDK parent directory to Python path for testing.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sdk_dir = Path(__file__).parent.parent
if str(sdk_dir) not in sys.path:
    sys.path.insert(0, str(sdk_dir))
