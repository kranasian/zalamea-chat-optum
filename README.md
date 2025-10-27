# Optum's HR Specialist Chatbot

A Streamlit chatbot application with Flask backend that connects to Google's Gemini API to provide HR assistance.

## Features

- 🤖 AI-powered HR specialist chatbot using Google Gemini Flash
- 💬 Real-time streaming responses
- 📊 Token usage, cost, and latency metrics
- 💡 Clickable example prompts
- 📝 Conversation history (last 5 messages)
- 🎨 Modern, responsive UI

## Setup Instructions

### 1. Setup the Application

Run the setup script to install dependencies and create a virtual environment:

```bash
./setup.sh
```

This script will:
- Check for Python3 and pip3 installation
- Create a virtual environment
- Install all required dependencies
- Verify the installation

### 2. Configure API Key

1. Get your Google API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Update the `.env` file with your API key:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

### 3. Run the Application

#### Quick Start (Recommended)
```bash
./start_app_debug.sh
```

This script will:
- Activate the virtual environment
- Start the Flask backend
- Verify Flask is running
- Start the Streamlit frontend
- Handle cleanup when stopped

#### Manual Start
If you prefer to start services manually:

```bash
# Activate virtual environment
source venv/bin/activate

# Start Flask backend (in background)
python app.py &

# Start Streamlit frontend
streamlit run streamlit_app.py
```

- Flask backend: `http://localhost:5001`
- Streamlit frontend: `http://localhost:8501`

## Usage

1. Open the Streamlit app in your browser
2. Click on any example prompt in the sidebar to get started
3. Type your HR-related questions in the chat input
4. View real-time streaming responses
5. Check usage metrics in the sidebar

## Example Prompts

The app includes pre-built prompts for common HR questions:
- Vacation and sick leave benefits
- Time off requests
- Performance review processes
- Personal information updates
- Employee assistance programs
- Workplace concerns reporting
- Remote work policies
- Pay stubs and tax documents
- Professional development opportunities
- Health insurance enrollment

## Technical Details

- **Backend**: Flask with CORS support
- **Frontend**: Streamlit with custom CSS styling
- **AI Model**: Google Gemini 1.5 Flash Latest (using google.genai API)
- **Streaming**: Server-sent events for real-time responses
- **Pricing**: Based on current Gemini Flash pricing ($0.075/1K input tokens, $0.30/1K output tokens)

## File Structure

```
zalamea-chat-optum/
├── app.py              # Flask backend
├── streamlit_app.py    # Streamlit frontend
├── requirements.txt    # Python dependencies
├── setup.sh           # Setup script (install dependencies)
├── start_app_debug.sh  # Debug start script
├── .env               # Environment variables (API key)
├── venv/              # Virtual environment (created by setup.sh)
└── README.md          # This file
```

## Notes

- The app maintains conversation context using the last 5 messages
- All responses are streamed in real-time for better user experience
- Usage metrics are displayed after each response
- The chatbot is specifically trained to act as Optum's HR Specialist
