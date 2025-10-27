#!/bin/bash

# Optum's HR Specialist - Setup Script

echo "🏢 Setting up Optum's HR Specialist Chatbot..."

# Check if .env file exists and has API key
if [ ! -f .env ] || ! grep -q "GOOGLE_API_KEY=" .env || grep -q "your_google_api_key_here" .env; then
  echo "❌ Please set your Google API key in the .env file"
  echo "   Get your API key from: https://makersuite.google.com/app/apikey"
  echo "   Update .env file with: GOOGLE_API_KEY=your_actual_api_key_here"
  exit 1
fi

# Check for Python installation
if ! command -v python3 &> /dev/null; then
  echo "❌ Python3 is not installed. Please install Python3 first."
  echo "   On macOS: brew install python3"
  echo "   On Ubuntu: sudo apt install python3 python3-pip"
  exit 1
fi

# Check for pip installation
if ! command -v pip3 &> /dev/null; then
  echo "❌ pip3 is not installed. Please install pip3 first."
  echo "   On macOS: python3 -m ensurepip --upgrade"
  echo "   On Ubuntu: sudo apt install python3-pip"
  exit 1
fi

echo "✅ Python3 and pip3 are available"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Verify installation
echo "🔍 Verifying installation..."
python -c "import streamlit, flask, google.genai; print('✅ All dependencies installed successfully')"

if [ $? -eq 0 ]; then
  echo ""
  echo "🎉 Setup completed successfully!"
  echo ""
  echo "To start the application, run:"
  echo "  ./start_app_debug.sh"
  echo ""
  echo "Or manually:"
  echo "  source venv/bin/activate"
  echo "  python app.py &"
  echo "  streamlit run streamlit_app.py"
else
  echo "❌ Setup failed. Please check the error messages above."
  exit 1
fi
