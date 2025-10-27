import streamlit as st
import requests
import json
from datetime import datetime
import time

# Configure Streamlit page
st.set_page_config(
  page_title="Optum's HR Specialist",
  page_icon="🏢",
  layout="wide"
)

# Flask backend URL
FLASK_URL = "http://localhost:5001"

def send_message_to_backend(message, messages=None):
  """Send message to Flask backend"""
  try:
    # Include session messages if provided
    request_data = {
      "message": message,
      "messages": messages or []
    }
    
    response = requests.post(
      f"{FLASK_URL}/chat",
      json=request_data,
      stream=True,
      timeout=30
    )
    
    if response.status_code != 200:
      return {"error": f"Backend returned status {response.status_code}: {response.text}"}
    
    # Process streaming response
    full_response = ""
    metrics_data = {}
    
    for line in response.iter_lines():
      if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
          data_str = line_str[6:]  # Remove 'data: ' prefix
          
          if data_str == '[DONE]':
            break
          
          try:
            data = json.loads(data_str)
            
            if data.get('type') == 'content':
              full_response += data.get('content', '')
            elif data.get('type') == 'metrics':
              metrics_data = data
            elif data.get('type') == 'error':
              return {"error": data.get('error', 'Unknown error')}
              
          except json.JSONDecodeError:
            continue
    
    return {
      "response": full_response,
      "timing": metrics_data
    }
    
  except requests.exceptions.RequestException as e:
    return {"error": f"Failed to connect to backend: {str(e)}"}

def render_chat_input():
  """Render the chat input"""
  prompt = st.chat_input("Ask me anything about HR policies, benefits, or procedures!")
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
        response_data = send_message_to_backend(prompt, st.session_state.messages)
        
        if "error" in response_data:
          st.error(response_data["error"])
          response_content = f"Sorry, I encountered an error: {response_data['error']}"
        else:
          response_content = response_data.get("response", "I'm sorry, I didn't understand that.")
          st.markdown(response_content)
    
    # Add assistant response to chat history
    st.session_state.messages.append({
      "role": "assistant", 
      "content": response_content,
      "timing": response_data.get("timing"),
      "request_time": time.time()
    })

def main():
  
  # Initialize session state
  if "messages" not in st.session_state:
    st.session_state.messages = []
  
  # Header
  st.markdown("""
  <div style="text-align: center; padding: 1rem 0; background: linear-gradient(90deg, #1f4e79, #2d5a87); color: white; border-radius: 10px; margin-bottom: 2rem;">
    <h3>🏢 Optum's HR Specialist</h3>
  </div>
  """, unsafe_allow_html=True)
  
  # Render the chat interface
  render_chat_interface()
  
  # Chat input
  render_chat_input()


def render_chat_interface():
  """Render the chat interface"""
  
  # Display chat messages
  for message in st.session_state.messages:
    with st.chat_message(message["role"]):
      st.markdown(message["content"])
      
      # Show timing information if available
      if ("timing" in message and 
          message["timing"] is not None and
          "latency" in message["timing"]):
        with st.expander("⏱️ Performance Metrics"):
          timing = message["timing"]
          
          col1, col2, col3, col4 = st.columns(4)
          
          with col1:
            st.metric("Input Tokens", timing.get("input_tokens", 0))
          
          with col2:
            st.metric("Output Tokens", timing.get("output_tokens", 0))
          
          with col3:
            st.metric("Total Tokens", timing.get("total_tokens", 0))
          
          with col4:
            st.metric("Latency", f"{timing.get('latency', 0):.2f}s")

  # Example prompts
  st.markdown("---")
  st.markdown("#### 💡 HR Questions Ideas")
  col1, col2, col3, col4, col5 = st.columns(5)
  
  def process_example_prompt(prompt_text):
    """Process an example prompt by sending it to the backend"""
    
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
        response_data = send_message_to_backend(prompt_text, st.session_state.messages)
        
        if "error" in response_data:
          st.error(response_data["error"])
          response_content = f"Sorry, I encountered an error: {response_data['error']}"
        else:
          response_content = response_data.get("response", "I'm sorry, I didn't understand that.")
          st.markdown(response_content)
    
    # Add assistant response to chat history
    st.session_state.messages.append({
      "role": "assistant", 
      "content": response_content,
      "timing": response_data.get("timing"),
      "request_time": time.time()
    })
    
    st.rerun()
  
  with col1:
    if st.button("what do I need for a loan?"):
      process_example_prompt("what do I need for a loan?")
  
  with col2:
    if st.button("can I apply?"):
      process_example_prompt("can I apply?")
  
  with col3:
    if st.button("what's voluntary contributions"):
      process_example_prompt("what's voluntary contributions")
  
  with col4:
    if st.button("what if I resigned in 5 years?"):
      process_example_prompt("what if I resigned in 5 years?")
  
  with col5:
    if st.button("how long should I stay to get maximum benefit?"):
      process_example_prompt("how long should I stay to get maximum benefit?")

  # Additional example prompts row
  col1, col2, col3, col4, col5 = st.columns(5)

  with col1:
    if st.button("how much should I contribute so that I can leave in 15 years and have 1M pesos."):
      process_example_prompt("how much should I contribute so that I can leave in 15 years and have 1M pesos.")
  
  with col2:
    if st.button("Which document should I have if I can't pay?"):
      process_example_prompt("Which document should I have if I can't pay?")
  
  with col3:
    if st.button("what note?"):
      process_example_prompt("what note?")
  
  with col4:
    if st.button("how I see the deductions and the details?"):
      process_example_prompt("how I see the deductions and the details?")
  
  with col5:
    if st.button("How do I enroll in health insurance benefits?"):
      process_example_prompt("How do I enroll in health insurance benefits?")


if __name__ == "__main__":
  main()