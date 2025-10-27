#!/bin/bash

# Optum's HR Specialist - Debug Start Script

echo "🏢 Starting Optum's HR Specialist Chatbot (Debug Mode)..."

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

# Kill any existing processes on ports 5000 and 8501
echo "🔍 Checking for existing processes on ports 5000 and 8501..."

# Kill processes on port 5001 (Flask)
if lsof -ti:5001 > /dev/null 2>&1; then
  echo "⚠️ Killing existing process on port 5001..."
  lsof -ti:5001 | xargs kill -9 2>/dev/null
  sleep 1
fi

# Kill processes on port 8501 (Streamlit)
if lsof -ti:8501 > /dev/null 2>&1; then
  echo "⚠️ Killing existing process on port 8501..."
  lsof -ti:8501 | xargs kill -9 2>/dev/null
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
if ! curl -s http://localhost:5001/health > /dev/null; then
  echo "❌ Flask backend failed to start. Check the error messages above."
  kill $FLASK_PID 2>/dev/null
  exit 1
fi

echo "✅ Flask backend is running on http://localhost:5001"

# Start Streamlit frontend
echo "🌐 Starting Streamlit frontend..."
echo "   Flask backend: http://localhost:5001"
echo "   Streamlit app: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Start Streamlit
streamlit run streamlit_app.py

# Cleanup: kill Flask when Streamlit stops
echo ""
echo "🛑 Stopping services..."

# Kill Flask process
if [ ! -z "$FLASK_PID" ]; then
  kill $FLASK_PID 2>/dev/null
fi

# Kill any remaining processes on ports 5001 and 8501
if lsof -ti:5001 > /dev/null 2>&1; then
  echo "⚠️ Killing remaining process on port 5001..."
  lsof -ti:5001 | xargs kill -9 2>/dev/null
fi

if lsof -ti:8501 > /dev/null 2>&1; then
  echo "⚠️ Killing remaining process on port 8501..."
  lsof -ti:8501 | xargs kill -9 2>/dev/null
fi

echo "✅ Services stopped"
