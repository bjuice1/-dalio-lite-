#!/bin/bash
# Dalio Lite - Quick Start Setup Script

set -e  # Exit on error

echo "=========================================="
echo "   DALIO LITE - QUICK START SETUP"
echo "=========================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo ""

# Check if we're in the right directory
if [ ! -f "dalio_lite.py" ]; then
    echo "❌ Error: Must run this from the dalio-lite directory"
    echo "   cd dalio-lite && ./quick_start.sh"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Setup .env if not exists
if [ ! -f ".env" ]; then
    echo "📝 Setting up .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  NEXT STEP: Edit .env and add your Alpaca API keys"
    echo "   1. Get keys from: https://alpaca.markets (Paper Trading section)"
    echo "   2. Open .env in a text editor"
    echo "   3. Paste your keys"
    echo ""
    echo "   Then run: python3 dalio_lite.py --dry-run"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Create necessary directories
mkdir -p logs state reports
echo "✓ Created directories: logs, state, reports"
echo ""

# Test if Alpaca keys are set
if grep -q "PKxxxxxx" .env 2>/dev/null; then
    echo "⚠️  WARNING: Alpaca keys not set in .env"
    echo "   Please edit .env and add your real keys"
    echo ""
else
    echo "✓ Alpaca keys detected in .env"
    echo ""
    echo "🚀 Ready to run! Try:"
    echo "   python3 dalio_lite.py --dry-run"
    echo ""
fi

echo "=========================================="
echo "📚 Next steps:"
echo "1. Get Alpaca paper trading keys: https://alpaca.markets"
echo "2. Edit .env and paste your keys"
echo "3. Fund your paper account: $17,000"
echo "4. Run: python3 dalio_lite.py --dry-run"
echo "5. Read README.md for full guide"
echo "=========================================="
