#!/bin/bash
set -e

echo "Unified State Machine - Setup"
echo "───────────────────────────────"

python3 -m pip install -q -r requirements.txt
python3 -m grpc_tools.protoc -I./protos --python_out=./protos --pyi_out=./protos ./protos/app.proto
touch protos/__init__.py

echo "✓ Done! Run: python3 server.py"
echo "  Open: http://localhost:8000"
