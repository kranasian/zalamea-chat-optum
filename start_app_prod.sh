#!/bin/bash

# Optum's HR Specialist - Production Start Script

echo "🏢 Starting Optum's HR Specialist Chatbot (Production Mode)..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
  echo "❌ Virtual environment not found. Please run setup.sh first:"
  echo "  ./setup.sh"
  exit 1
fi

# Check if .env file exists and has API key
if [ ! -f .env ] || ! grep -q "GOOGLE_API_KEY=" .env || grep -q "your_google_api_key_here" .env; then
  echo "❌ Please set your Google API key in the .env file"
  echo "   Get your API key from: https://makersuite.google.com/app/apikey"
  echo "   Update .env file with: GOOGLE_API_KEY=your_actual_api_key_here"
  exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import streamlit, flask, google.genai" 2>/dev/null; then
  echo "❌ Dependencies not found. Please run setup.sh first:"
  echo "  ./setup.sh"
  exit 1
fi

echo "✅ All dependencies verified"

# Kill any existing processes on ports 6000 and 9382
echo "🔍 Checking for existing processes on ports 6000 and 9382..."

# Kill processes on port 6000 (Flask)
if lsof -ti:6000 > /dev/null 2>&1; then
  echo "⚠️ Killing existing process on port 6000..."
  lsof -ti:6000 | xargs kill -9 2>/dev/null
  sleep 1
fi

# Kill processes on port 9382 (Streamlit)
if lsof -ti:9382 > /dev/null 2>&1; then
  echo "⚠️ Killing existing process on port 9382..."
  lsof -ti:9382 | xargs kill -9 2>/dev/null
  sleep 1
fi

echo "✅ Ports cleared"

# Start Flask backend in background
echo "🚀 Starting Flask backend..."
python app.py &
FLASK_PID=$!

# Wait for Flask to start
echo "⏳ Waiting for Flask to start..."
sleep 3

# Check if Flask is running
if ! curl -s http://localhost:6000/health > /dev/null; then
  echo "❌ Flask backend failed to start. Check the error messages above."
  kill $FLASK_PID 2>/dev/null
  exit 1
fi

echo "✅ Flask backend is running on http://localhost:6000"

# Start Streamlit frontend
echo "🌐 Starting Streamlit frontend..."
echo "   Flask backend: http://localhost:6000"
echo "   Streamlit app: http://0.0.0.0:9382"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Start Streamlit with production configuration
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 9382

# Cleanup: kill Flask when Streamlit stops
echo ""
echo "🛑 Stopping services..."

# Kill Flask process
if [ ! -z "$FLASK_PID" ]; then
  kill $FLASK_PID 2>/dev/null
fi

# Kill any remaining processes on ports 6000 and 9382
if lsof -ti:6000 > /dev/null 2>&1; then
  echo "⚠️ Killing remaining process on port 6000..."
  lsof -ti:6000 | xargs kill -9 2>/dev/null
fi

if lsof -ti:9382 > /dev/null 2>&1; then
  echo "⚠️ Killing remaining process on port 9382..."
  lsof -ti:9382 | xargs kill -9 2>/dev/null
fi

echo "✅ Services stopped"
