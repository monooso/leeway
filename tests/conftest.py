"""Shared test configuration."""

import os
import sys

# Add src/ to the import path so tests can import modules directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
