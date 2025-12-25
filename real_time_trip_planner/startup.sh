#!/bin/bash
# startup.sh - Cloud deployment startup script

# Set the port from environment variable (required for cloud platforms)
export PORT=${PORT:-8501}

# Start the Streamlit application
streamlit run src/app.py \
    --server.port $PORT \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false
