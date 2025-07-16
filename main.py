from typing import List, Dict
from datetime import datetime
import streamlit as st
import asyncio
import uuid

from graph import graph


# Page configuration
st.set_page_config(
    page_title="Travel Planner Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling - minimal now that we're using Streamlit's chat components
st.markdown("""
<style>
    .stChatMessage {
        margin-bottom: 1rem;
    }
    .stChatMessage .content {
        padding: 0.5rem;
    }
    .stChatMessage .timestamp {
        font-size: 0.8rem;
        color: #888;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_thread_id():
    return str(uuid.uuid4())

thread_id = get_thread_id()

# Initialize session state for chat history and user context
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "processing_message" not in st.session_state:
    st.session_state.processing_message = None

# Function to handle user input
def handle_user_message(user_input: str):
    # Add user message to chat history immediately
    timestamp = datetime.now().strftime("%I:%M %p")
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input,
        "timestamp": timestamp
    })
    
    # Set the message for processing in the next rerun
    st.session_state.processing_message = user_input

# Function to invoke the agent graph to interact with the Travel Planning Agent
async def invoke_agent_graph(user_input: str):
    """
    Run the agent with streaming text for the user_input prompt,
    while maintaining the entire conversation in `st.session_state.messages`.
    """
    initial_state = {
        "messages": [],
        "user_input": user_input,
        "contact_information": {}
    }
    
    async for chunk in graph.astream(initial_state, stream_mode="custom"):
        yield chunk

async def main():
    # Sidebar
    with st.sidebar:
        st.title("Appointment Scheduler")
        
        if st.button("Start New Conversation"):
            st.session_state.chat_history = []
            st.session_state.thread_id = str(uuid.uuid4())
            st.success("New conversation started!")

    # Main chat interface
    st.title("📅 Appointment Scheduler")
    st.caption("Tell me about your appointment needs and I'll help schedule it!")

    # Display chat messages
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            with st.chat_message("user", avatar=f"https://api.dicebear.com/7.x/avataaars/svg?seed={st.session_state.thread_id}"):
                st.markdown(message["content"])
                st.caption(message["timestamp"])
        else:
            with st.chat_message("assistant", avatar="https://api.dicebear.com/7.x/bottts/svg?seed=travel-agent"):
                st.markdown(message["content"])
                st.caption(message["timestamp"])

    # User input
    user_input = st.chat_input("Tell me about your appointment...")
    if user_input:
        handle_user_message(user_input)
        st.rerun()

    # Process message if needed
    if st.session_state.processing_message:
        user_input = st.session_state.processing_message
        st.session_state.processing_message = None
        
        # Process the message asynchronously
        with st.spinner("Thinking..."):
            try:
                # Prepare input for the agent using chat history
                if len(st.session_state.chat_history) > 1:
                    # Convert chat history to input list format for the agent
                    input_list = []
                    for msg in st.session_state.chat_history:
                        input_list.append({"role": msg["role"], "content": msg["content"]})
                else:
                    # First message
                    input_list = user_input

                # Display assistant response in chat message container
                response_content = ""
                
                # Create a chat message container using Streamlit's built-in component
                with st.chat_message("assistant", avatar="https://api.dicebear.com/7.x/bottts/svg?seed=travel-agent"):
                    message_placeholder = st.empty()
                    
                    # Run the async generator to fetch responses
                    async for chunk in invoke_agent_graph(user_input):
                        response_content += chunk
                        # Update only the text content
                        message_placeholder.markdown(response_content)
                
                # Add assistant response to chat history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_content,
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })
                
            except Exception as e:
                raise Exception(e)
                error_message = f"Sorry, I encountered an error: {str(e)}"
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": error_message,
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })
            
            # Force a rerun to display the AI response
            # st.rerun()

    # Footer
    st.divider()
    st.caption("Powered by Pydantic AI and LangGraph")

if __name__ == "__main__":
    asyncio.run(main())
