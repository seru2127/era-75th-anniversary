#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Run the app
python -m uvicorn app:app --host 0.0.0.0 --port 
