#!/usr/bin/env python3
"""
Run script for the Travel Planning Application

This script sets up the correct Python path and runs the Streamlit app
from the src directory structure.
"""
import sys
import os
from pathlib import Path

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Change to src directory
os.chdir(src_dir)

if __name__ == "__main__":
    # Import and run the app
    try:
        import streamlit as st
        from app import TravelPlanningApp

        # Run with streamlit
        import subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])

    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all required packages are installed:")
        print("pip install streamlit langchain langgraph google-generativeai reportlab")
    except Exception as e:
        print(f"Error running application: {e}")
