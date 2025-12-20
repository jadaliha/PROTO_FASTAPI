#!/bin/bash

# Setup script for Todo App
# Single source of truth: protos/todo.proto

set -e

echo "🔧 Setting up Todo App..."

mkdir -p protos templates/partials static

echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

echo ""
echo "🔄 Generating Python protobuf from todo.proto..."
python3 -m grpc_tools.protoc \
  -I./protos \
  --python_out=./protos \
  --pyi_out=./protos \
  ./protos/todo.proto

echo "  ✅ protos/todo_pb2.py"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📐 Architecture:"
echo "   protos/todo.proto (SOURCE OF TRUTH)"
echo "   ├── protos/todo_pb2.py  (Python backend)"
echo "   └── static/app.js       (JS loads .proto at runtime via protobuf.js)"
echo ""
echo "To run: python main.py"
echo "Visit:  http://localhost:8080"
