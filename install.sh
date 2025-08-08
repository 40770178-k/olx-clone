#!/bin/bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "✅ Virtual environment ready and packages installed."
