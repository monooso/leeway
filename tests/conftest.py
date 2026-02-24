"""Shared test configuration."""

import os
import sys

# Allow importing from src/ without installing — keeps app as a proper package.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))
