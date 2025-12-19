#!/bin/bash

# Setup script for Protobuf Todo App

echo "🔧 Setting up Todo App with Protobuf..."

# Create directory structure
echo "📁 Creating directories..."
mkdir -p protos
mkdir -p protos/generated
mkdir -p templates/partials
mkdir -p static

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Generate Python protobuf code
echo "🔨 Generating Python protobuf code..."
python3 -m grpc_tools.protoc \
  -I./protos \
  --python_out=./protos \
  ./protos/todo.proto

# Copy proto file to static for frontend
echo "📋 Copying proto file for frontend..."
cp protos/todo.proto static/todo.proto

echo "✅ Setup complete!"
echo ""
echo "To run the app:"
echo "  python main.py"
echo ""
echo "Then visit: http://localhost:8080"