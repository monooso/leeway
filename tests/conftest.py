"""Shared test configuration."""

import os
import sys

# Allow importing from src/app/ without installing.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src", "app"))
