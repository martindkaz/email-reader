#!/bin/bash

# Setup script for LangGraph Email Agent

echo "=================================="
echo "Email Search Agent Setup"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements-agent.txt

echo ""
echo "=================================="
echo "Configuration Check"
echo "=================================="
echo ""

# Check .env file
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and fill in your credentials:"
    echo "  cp .env.example .env"
    echo "  # Then edit .env with your actual values"
    exit 1
fi

# Check for required env vars
missing_vars=()

if ! grep -q "TENANT_ID=" .env || grep -q "TENANT_ID=your-tenant-id-here" .env; then
    missing_vars+=("TENANT_ID")
fi

if ! grep -q "CLIENT_ID=" .env || grep -q "CLIENT_ID=your-client-id-here" .env; then
    missing_vars+=("CLIENT_ID")
fi

if ! grep -q "ANTHROPIC_API_KEY=" .env || grep -q "ANTHROPIC_API_KEY=your-anthropic-api-key-here" .env; then
    missing_vars+=("ANTHROPIC_API_KEY")
fi

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ Missing or incomplete configuration in .env file:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please update your .env file with the correct values."
    exit 1
fi

echo "✅ All required environment variables are configured"
echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "To run the agent:"
echo "  1. Activate the virtual environment: source .venv/bin/activate"
echo "  2. Run interactively: python run_agent.py"
echo "  3. Or run a single query: python run_agent.py 'Find emails about project updates'"
echo ""
