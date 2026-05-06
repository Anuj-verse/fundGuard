#!/usr/bin/env python3
"""
Script to generate the standardized 1M transaction evaluation dataset.

Requirements: 9.1
"""

import logging
import os
import sys
from pathlib import Path

# Add src to python path if running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from synthetic_generator.main import main

if __name__ == "__main__":
    # Override sys.argv to run evaluation mode
    sys.argv = [
        "synthetic_generator",
        "--mode", "evaluation",
        "--format", "parquet",
        "--output-dir", "data/evaluation_dataset"
    ]
    sys.exit(main())
