import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import time

# Configure Streamlit page
st.set_page_config(
  page_title="AI Assistant Chatbot",
  page_icon="🤖",
  layout="wide"
)

# Flask backend URL
FLASK_URL = "http://localhost:5001"

def send_message_to_backend(message, username="default_user", mode="function_calling", model="gemini-2.0-flash", messages=None):
  """Send message to Flask backend"""
  try:
    # Include session messages if provided
    request_data = {
      "message": message, 
      "username": username, 
      "mode": mode, 
      "model": model
    }
    
    if messages is not None:
      request_data["messages"] = messages
    
    response = requests.post(
      f"{FLASK_URL}/chat",
      json=request_data,
      timeout=30
    )
    return response.json()
  except requests.exceptions.RequestException as e:
    return {"error": f"Failed to connect to backend: {str(e)}"}

def get_users():
  """Get all users from backend"""
  try:
    response = requests.get(f"{FLASK_URL}/users")
    return response.json()
  except requests.exceptions.RequestException as e:
    return {"error": f"Failed to get users: {str(e)}"}

def get_user_reminders(username="default_user"):
  """Get user reminders from backend"""
  try:
    response = requests.get(f"{FLASK_URL}/reminders/{username}")
    return response.json()
  except requests.exceptions.RequestException as e:
    return {"error": f"Failed to get reminders: {str(e)}"}

def get_home_devices(username="default_user"):
  """Get home devices for a specific user from backend"""
  try:
    response = requests.get(f"{FLASK_URL}/home_devices/{username}")
    return response.json()
  except requests.exceptions.RequestException as e:
    return {"error": f"Failed to get home devices: {str(e)}"}

def toggle_device(device_id):
  """Toggle a device on/off"""
  try:
    response = requests.post(f"{FLASK_URL}/home_devices/{device_id}/toggle")
    return response.json()
  except requests.exceptions.RequestException as e:
    return {"error": f"Failed to toggle device: {str(e)}"}

def complete_reminder(reminder_id):
  """Mark reminder as completed"""
  try:
    response = requests.post(f"{FLASK_URL}/reminders/{reminder_id}/complete")
    return response.json()
  except requests.exceptions.RequestException as e:
    return {"error": f"Failed to complete reminder: {str(e)}"}

def render_chat_input():
  """Render the chat input"""
  mode = st.session_state.current_mode
  model = st.session_state.current_model
  placeholder_text = "Ask me to create a reminder or chat with me!" if mode == "function_calling" else "Ask me to help with code generation or programming!"
  prompt = st.chat_input(placeholder_text)
  if prompt:
    # Add user message to chat history
    st.session_state.messages.append({
      "role": "user", 
      "content": prompt,
      "request_time": time.time(),
      "timing": None
    })
    
    # Display user message
    with st.chat_message("user"):
      st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
      with st.spinner("Thinking..."):
        response_data = send_message_to_backend(prompt, st.session_state.username, mode, model, st.session_state.messages)
        
        if "error" in response_data:
          st.error(response_data["error"])
          response_content = f"Sorry, I encountered an error: {response_data['error']}"
        else:
          response_content = response_data.get("response", "I'm sorry, I didn't understand that.")
          st.markdown(response_content)
          
          # Show function call information
          if response_data.get("function_called"):
            with st.expander(f"🔧 Function Called: {response_data['function_called']}"):
              st.json(response_data.get("function_result", {}))
    
    # Add assistant response to chat history
    st.session_state.messages.append({
      "role": "assistant", 
      "content": response_content,
      "function_called": response_data.get("function_called"),
      "function_result": response_data.get("function_result"),
      "code_generated": response_data.get("code_generated"),
      "timing": response_data.get("timing"),
      "request_time": time.time()
    })

def main():
  
  # Initialize session state
  if "messages" not in st.session_state:
    st.session_state.messages = []
  if "username" not in st.session_state:
    st.session_state.username = "EmptyUser"  # Default to first seeded user
  if "current_mode" not in st.session_state:
    st.session_state.current_mode = "function_calling"
  if "current_model" not in st.session_state:
    st.session_state.current_model = "gemini-2.0-flash"
  
  # AI Mode selection
  col1, col2 = st.columns([1, 1])
  
  with col1:
    ai_mode_options = [
      "Code Gen: Gemini Flash Lite Latest [Proposed/Fastest]",
      "Function Calling: Gemini 2.5 Flash [FC 2.0: Slow]",
      "Function Calling: Gemini 2.0 Flash [FC 1.0: Slow]",
      "Function Calling: Gemini 2.5 Flash Lite [FC 2.0: Fast]",
      "Function Calling: Gemini 2.0 Flash Lite [FC 1.0: Fast]", 
      "Code Gen: Gemini Flash Latest [Fast]",
      "Code Gen: Gemini 2.5 Flash Lite [Fastest]",
      "Code Gen: Gemini 2.5 Flash [Fast]", 
      "Code Gen: Gemini Flash Latest (Thinking) [Quality, Sometimes Slow]",
      "Code Gen: Gemini Flash Lite Latest (Thinking) [Quality, Normal]",
    ]
    
    selected_mode = st.selectbox(
      "AI Mode",
      options=ai_mode_options,
      index=0,
      help="Choose the AI mode and model for your conversation"
    )
    
    # Parse the selected mode and model
    if selected_mode.startswith("Function Calling"):
      st.session_state.current_mode = "function_calling"
      if "2.0 Flash Lite" in selected_mode:
        st.session_state.current_model = "gemini-2.0-flash-lite"
      elif "2.0 Flash" in selected_mode:
        st.session_state.current_model = "gemini-2.0-flash"
      elif "2.5 Flash" in selected_mode:
        st.session_state.current_model = "gemini-flash-latest"
      elif "2.5 Flash Lite" in selected_mode:
        st.session_state.current_model = "gemini-flash-lite-latest"
    else:  # Code Gen
      st.session_state.current_mode = "code_gen"
      if "2.5 Flash Lite" in selected_mode:
        st.session_state.current_model = "gemini-2.5-flash-lite"
      elif "2.5 Flash" in selected_mode:
        st.session_state.current_model = "gemini-2.5-flash"
      elif "Flash Latest" in selected_mode:
        st.session_state.current_model = "gemini-flash-latest"
      elif "Flash Lite Latest" in selected_mode:
        st.session_state.current_model = "gemini-flash-lite-latest"
      elif "Flash Latest (Thinking)" in selected_mode:
        st.session_state.current_model = "gemini-flash-latest-thinking"
      elif "Flash Lite Latest (Thinking)" in selected_mode:
        st.session_state.current_model = "gemini-flash-lite-latest-thinking"

  
  # Render the chat interface
  render_chat_interface()
  
  # Chat input
  render_chat_input()

def render_chat_interface():
  """Render the chat interface"""
  mode = st.session_state.current_mode
  
  # Sidebar for user settings and reminders (available for all modes)
  with st.sidebar:
    st.header("Set Context")
    
    # User dropdown
    users_data = get_users()
    if "users" in users_data:
      users = users_data["users"]
      if users:
        user_options = [user["username"] for user in users]
        selected_user = st.selectbox(
          "Select User",
          options=user_options,
          index=user_options.index(st.session_state.username) if st.session_state.username in user_options else 0,
          help="Choose a user to view their reminders and create new ones"
        )
        st.session_state.username = selected_user
      else:
        st.error("No users found")
    else:
      st.error("Failed to load users")
    
    st.header("Your Reminders")
    if st.button("🔄 Refresh Reminders"):
      st.rerun()
    
    # Display reminders
    reminders_data = get_user_reminders(st.session_state.username)
    if "reminders" in reminders_data:
      reminders = reminders_data["reminders"]
      if reminders:
        # Prepare data for table
        table_data = []
        for reminder in reminders:
          # Format datetime to remove seconds
          reminder_time = datetime.fromisoformat(reminder['reminder_time'].replace('Z', '+00:00'))
          formatted_time = reminder_time.strftime("%Y-%m-%d %H:%M")
          
          table_data.append({
            "Reminder Title": reminder['title'],
            "Trigger Time": f"{formatted_time}"
          })
        
        # Display as table
        st.dataframe(
          table_data,
          use_container_width=True,
          hide_index=True
        )
      else:
        st.info("No reminders yet. Try asking me to create one!")
    else:
      st.error("Failed to load reminders")
    
    # Home Devices Section
    st.header("🏠 Home Devices")
    if st.button("🔄 Refresh Devices"):
      st.rerun()
    
    # Get home devices data for the selected user
    devices_data = get_home_devices(st.session_state.username)
    if "devices" in devices_data:
      devices = devices_data["devices"]
      if devices:
        # Group devices by room
        rooms = {}
        for device in devices:
          room_name = device['room_name']
          if room_name not in rooms:
            rooms[room_name] = []
          rooms[room_name].append(device)
        
        # Display devices by room
        for room_name, room_devices in rooms.items():
          st.subheader(f"🏠 {room_name}")
          
          # Create columns for devices in this room
          cols = st.columns(min(len(room_devices), 3))  # Max 4 devices per row
          
          for i, device in enumerate(room_devices):
            with cols[i % 3]:
              # Determine icon and color based on device type and status
              if device['device_type'] == 'light':
                icon = "💡" if device['is_on'] else "✖️"
                color = "#FFD700" if device['is_on'] else "#808080"  # Gold if on, gray if off
                
                # Create clickable device card with styling
                button_clicked = st.button(
                  f"{icon} {device['name']}",
                  key=f"device_{device['device_id']}",
                  help=f"Click to toggle {device['name']} {'OFF' if device['is_on'] else 'ON'}",
                  use_container_width=True
                )
                if device['is_on']:
                  st.markdown(f"""
                    <div style="display: flex; justify-content: center; align-items: center; padding-bottom: 15px;">
                      <span style="font-size: 12px; text-align: center;">🔆 <b>{device['brightness']}%</b></span>
                      <span style="padding-left: 10px; font-size: 12px; text-align: center;">🎨 <b>{device['color_name'] or 'N/A'}</b></span>
                    </div>
                    """, unsafe_allow_html=True)
                
                if button_clicked:
                  # Toggle the device
                  result = toggle_device(device['device_id'])
                  if result.get('success'):
                    st.success(f"Toggled {device['name']} {'OFF' if device['is_on'] else 'ON'}")
                    st.rerun()
                  else:
                    st.error(f"Failed to toggle {device['name']}: {result.get('error', 'Unknown error')}")
              
              else:  # thermostat
                icon = "🌡️" if device['is_on'] else "✖️"
                color = "#FF6B6B" if device['is_on'] else "#808080"  # Red if on, gray if off
                
                # Create clickable device card with styling
                button_clicked = st.button(
                  f"{icon} {device['name']}",
                  key=f"device_{device['device_id']}",
                  help=f"Click to toggle {device['name']} {'OFF' if device['is_on'] else 'ON'}",
                  use_container_width=True
                )
                if device['is_on']:
                  st.markdown(f"""
                    <div style="display: flex; justify-content: center; align-items: center; padding-bottom: 15px;">
                      <span style="font-size: 12px;">🌡️ <b>{device['target_temperature']}°C</b></span>
                    </div>
                    """, unsafe_allow_html=True)
                
                if button_clicked:
                  # Toggle the device
                  result = toggle_device(device['device_id'])
                  if result.get('success'):
                    st.success(f"Toggled {device['name']} {'OFF' if device['is_on'] else 'ON'}")
                    st.rerun()
                  else:
                    st.error(f"Failed to toggle {device['name']}: {result.get('error', 'Unknown error')}")
          
          # Add some spacing between rooms
          st.markdown("<br>", unsafe_allow_html=True)
      
      else:
        st.info("No home devices found. Try running the user seeder to create some devices!")
    else:
      st.error("Failed to load home devices")
    
    
    st.markdown("""
    <div style="font-size: 10px; line-height: 1.8em; color: #aaa;">
      <p><b>Disclaimer:</b> I only did the bare minimum on the prompts, so don't use it as a barrometer for comparing quality between approaches.</p>
    </div>
    """, unsafe_allow_html=True)

  
  # Performance summary
  if st.session_state.messages:
    assistant_messages = [msg for msg in st.session_state.messages if msg["role"] == "assistant" and "timing" in msg and msg["timing"] is not None]
    if assistant_messages:
      latest_timing = assistant_messages[-1]["timing"]
      
      # Check if timing data has the required keys
      if (latest_timing and 
          "backend_processing_start" in latest_timing and 
          "request_received" in latest_timing and
          "total_processing_time" in latest_timing and
          "end_to_end_latency" in latest_timing):
        
        # Create performance summary
        with st.expander("📊 Latest Performance Summary", expanded=False):
          col1, col2, col3, col4, col5 = st.columns(5)
          
          with col1:
            backend_start = (latest_timing["backend_processing_start"] - latest_timing["request_received"]) * 1000
            st.metric("Backend Start", f"{backend_start:.1f}ms")
          
          with col2:
            processing_time = latest_timing["total_processing_time"]
            st.metric("Processing Time", f"{processing_time:.1f}ms")
          
          with col3:
            e2e_latency = latest_timing["end_to_end_latency"]
            st.metric("End-to-End", f"{e2e_latency:.1f}ms")
          
          with col4:
            if latest_timing.get("gemini_api_calls"):
              total_gemini_time = sum(call["duration_ms"] for call in latest_timing["gemini_api_calls"])
              st.metric("Gemini API", f"{total_gemini_time:.1f}ms")
            else:
              st.metric("Gemini API", "")

          with col5:
            if latest_timing.get("execution_time"):
              total_execution_time = sum(call["duration_ms"] for call in latest_timing["execution_time"])
              st.metric("Execution Time", f"{total_execution_time:.1f}ms")
            else:
              st.metric("Execution Time", "")

  # Display chat messages
  for message in st.session_state.messages:
    with st.chat_message(message["role"]):
      st.markdown(message["content"])
      
      # Show function call results if available
      if "function_called" in message and message["function_called"]:
        with st.expander(f"🔧 Function Called: {message['function_called']}"):
          st.json(message.get("function_result", {}))
      
      # Show generated code if available (for code generation mode)
      if "code_generated" in message and message["code_generated"]:
        with st.expander("💻 Generated Code"):
          st.code(message["code_generated"], language="python")
      
      # Show timing information if available
      if ("timing" in message and 
          message["timing"] is not None and
          "backend_processing_start" in message["timing"] and
          "request_received" in message["timing"] and
          "total_processing_time" in message["timing"] and
          "end_to_end_latency" in message["timing"]):
        with st.expander("⏱️ Performance Metrics"):
          timing = message["timing"]
          
          # Calculate backend processing start latency
          backend_start_latency = (timing["backend_processing_start"] - timing["request_received"]) * 1000
          
          col1, col2, col3 = st.columns(3)
          
          with col1:
            st.metric(
              label="Backend Processing Start",
              value=f"{backend_start_latency:.1f}ms",
              help="Time from request received until backend starts processing"
            )
          
          with col2:
            st.metric(
              label="Total Processing Time",
              value=f"{timing['total_processing_time']:.1f}ms",
              help="Time spent in backend processing"
            )
          
          with col3:
            st.metric(
              label="End-to-End Latency",
              value=f"{timing['end_to_end_latency']:.1f}ms",
              help="Total time from request to response"
            )


          col4, col5 = st.columns(2)
          
          with col4:
            if timing.get("gemini_api_calls"):
              total_gemini_time = sum(call["duration_ms"] for call in timing["gemini_api_calls"])
              st.metric("Gemini API", f"{total_gemini_time:.1f}ms")
            else:
              st.metric("Gemini API", "")      
        
            # Show Gemini API call details if available
            if timing.get("gemini_api_calls") and len(timing["gemini_api_calls"]) > 1:
              st.subheader("🤖 Gemini API Calls")
              for i, call in enumerate(timing["gemini_api_calls"]):
                st.metric(
                  label=f"API Call #{call['call_number']}",
                  value=f"{call['duration_ms']:.1f}ms",
                  help=f"Duration of Gemini API call #{call['call_number']}"
                )
          
          with col5:
            if timing.get("execution_time"):
              total_execution_time = sum(call["duration_ms"] for call in timing["execution_time"])
              st.metric("Execution Time", f"{total_execution_time:.1f}ms")
            else:
              st.metric("Execution Time", "")
          
            # Show execution time details if available
            if timing.get("execution_time") and len(timing["execution_time"]) > 1:
              st.subheader("🔧 Execution Time")
              for i, call in enumerate(timing["execution_time"]):
                st.metric(
                  label=f"Execution #{call['call_number']}",
                  value=f"{call['duration_ms']:.1f}ms",
                  help=f"Duration of execution #{call['call_number']}"
                )
  
  
  # Example prompts
  st.markdown("---")
  st.markdown("#### 💡 Reminders Ideas")
  col1, col2, col3, col4, col5 = st.columns(5)
  
  def process_example_prompt(prompt_text):
    """Process an example prompt by sending it to the backend"""
    mode = st.session_state.current_mode
    model = st.session_state.current_model
    
    # Add user message to chat history
    st.session_state.messages.append({
      "role": "user", 
      "content": prompt_text,
      "request_time": time.time(),
      "timing": None
    })
    
    # Display user message
    with st.chat_message("user"):
      st.markdown(prompt_text)
    
    # Get AI response
    with st.chat_message("assistant"):
      with st.spinner("Thinking..."):
        response_data = send_message_to_backend(prompt_text, st.session_state.username, mode, model, st.session_state.messages)
        
        if "error" in response_data:
          st.error(response_data["error"])
          response_content = f"Sorry, I encountered an error: {response_data['error']}"
        else:
          response_content = response_data.get("response", "I'm sorry, I didn't understand that.")
          st.markdown(response_content)
          
          # Show function call information
          if response_data.get("function_called"):
            with st.expander(f"🔧 Function Called: {response_data['function_called']}"):
              st.json(response_data.get("function_result", {}))
    
    # Add assistant response to chat history
    st.session_state.messages.append({
      "role": "assistant", 
      "content": response_content,
      "function_called": response_data.get("function_called"),
      "function_result": response_data.get("function_result"),
      "code_generated": response_data.get("code_generated"),
      "timing": response_data.get("timing"),
      "request_time": time.time()
    })
    
    st.rerun()
  
  with col1:
    if st.button("FT: Create a reminder at 5pm to bring the dog to the vet"):
      process_example_prompt("Create a reminder at 5pm to bring the dog to the vet")
  
  with col2:
    if st.button("notify me to pop the trash at 4pm tomorrow"):
      process_example_prompt("notify me to pop the trash at 4pm tomorrow")
  
  with col3:
    if st.button("when should I go to the vet?"):
      process_example_prompt("when should I go to the vet?")
  
  with col4:
    if st.button("How many reminders do I have tomorrow?"):
      process_example_prompt("How many reminders do I have tomorrow?")
  
  with col5:
    if st.button("the trash reminder needs to be done 2 days later at 7pm"):
      process_example_prompt("the trash reminder needs to be done 2 days later at 7pm")


  st.markdown("#### 💡 Home Devices Ideas  (only turn on/off, what is on/off implemented for now)")
  col1, col2, col3, col4, col5 = st.columns(5)

  with col1:
    if st.button("turn on all lights but the lamps must be off"):
      process_example_prompt("turn on all lights but the lamps must be off")
  
  with col2:
    if st.button("if any lights are on, remind me to turn them off in 3 hours"):
      process_example_prompt("if any lights are on, remind me to turn them off in 3 hours")

if __name__ == "__main__":
  main()
