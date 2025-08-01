#!/usr/bin/env python3
"""
Main entry point for the Design Comparison Tool
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app import app

if __name__ == '__main__':
    # Starting Design Comparison Tool
    app.run(debug=True, host='0.0.0.0', port=5000) 