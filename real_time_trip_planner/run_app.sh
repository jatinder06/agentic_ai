#!/bin/bash
# run_app.sh - Script to run the Travel Planning Application

# Change to the src directory
cd "$(dirname "$0")/src"

# Run the Streamlit application
echo "Starting Travel Planning Application..."
echo "Running from directory: $(pwd)"

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "Streamlit not found. Please install requirements:"
    echo "pip install -r ../requirements.txt"
    exit 1
fi

# Run the application
streamlit run app.py
