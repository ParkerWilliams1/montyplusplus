#!/bin/bash

echo "🚀 Setting up Competitive Coding Platform..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null
then
    echo "❌ Node.js is not installed. Please install Node.js first:"
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Install dependencies
echo ""
echo "📦 Installing Node.js dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create necessary directories
echo ""
echo "📁 Creating directory structure..."
mkdir -p public temp

# Make transpiler executable
chmod +x transpiler.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the server, run:"
echo "  npm start"
echo ""
echo "Then open your browser to:"
echo "  http://localhost:8000"
echo ""
echo "⚠️  Don't forget to replace transpiler.py with your actual C++ to Python transpiler!"
