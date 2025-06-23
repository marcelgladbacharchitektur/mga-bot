#!/bin/bash

# MGA Bot Setup Script
# This script sets up the bot for the first time

set -e

echo "🔧 MGA Bot Setup Script"
echo "======================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Functions
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Check Python version
print_info "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
print_status "Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_info "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
print_status "Dependencies installed"

# Check for .env file
if [ ! -f ".env" ]; then
    print_info "Creating .env file from template..."
    cp .env.example .env
    print_status ".env file created"
    print_error "Please edit .env file with your actual credentials!"
else
    print_status ".env file already exists"
fi

# Create logs directory
if [ ! -d "logs" ]; then
    mkdir -p logs
    print_status "Logs directory created"
fi

# Create project counter file if it doesn't exist
if [ ! -f "project_counter.json" ]; then
    echo '{"year": 25, "counter": 0, "last_number": "25-000"}' > project_counter.json
    print_status "Project counter file created"
fi

# Portal setup (if needed)
if [ -d "portal" ]; then
    print_info "Setting up portal..."
    cd portal
    
    # Check if npm is installed
    if command -v npm &> /dev/null; then
        npm install
        print_status "Portal dependencies installed"
        
        # Create portal .env if needed
        if [ ! -f ".env" ]; then
            cp .env.example .env
            print_status "Portal .env file created"
            print_error "Please edit portal/.env file with your credentials!"
        fi
    else
        print_error "npm not found. Please install Node.js to set up the portal."
    fi
    
    cd ..
fi

print_info ""
print_status "Setup completed!"
print_info ""
print_info "Next steps:"
print_info "1. Edit .env file with your credentials"
print_info "2. Place your Google service account JSON file at the specified path"
print_info "3. Run the bot with: python src/bot/telegram_agent_google.py"
print_info ""
print_info "For production deployment, use: ./deploy.sh"