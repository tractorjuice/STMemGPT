# Importing required packages
import streamlit as st
import openai
import promptlayer
import uuid
import json
import glob
import os
import sys
import pickle
import readline
import interface  # for printing to terminal
import memgpt.agent as agent
import memgpt.system as system
import memgpt.utils as utils
import memgpt.presets as presets
import memgpt.constants as constants
import memgpt.personas.personas as personas
import memgpt.humans.humans as humans
from memgpt.persistence_manager import InMemoryStateManager, InMemoryStateManagerWithPreloadedArchivalMemory, InMemoryStateManagerWithFaiss

#MODEL = "gpt-3.5-turbo"
#MODEL = "gpt-3.5-turbo-0301"
#MODEL = "gpt-3.5-turbo-0613"
#MODEL = "gpt-3.5-turbo-1106"
MODEL = "gpt-3.5-turbo-16k"
#MODEL = "gpt-3.5-turbo-16k-0613"
#MODEL = "gpt-4"
#MODEL = "gpt-4-0613"
#MODEL = "gpt-4-0613"
#MODEL = "gpt-4-32k-0613"
#MODEL = "gpt-4-1106-preview"
#MODEL = "gpt-4-vision-preview"

MODE = "Archive"
#MODE = "Chat"
new_messages = []

if "heartbeat_request" not in st.session_state:
    st.session_state["heartbeat_request"] = None
    
if "function_failed" not in st.session_state:
    st.session_state["function_failed"] = False
    
if "token_warning" not in st.session_state:
    st.session_state["token_warning"] = False
    
if "memgpt_agent" not in st.session_state:
    st.session_state["memgpt_agent"] = False
    
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    
if "prompt" not in st.session_state:
    st.session_state["prompt"] = None

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append(   
        {
            "role": "user",
            "content": "Help?"
        })
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": """
            I'm here to help you learn about and create Wardley Maps. Here are some options for getting started:
            1. Learn: To learn about the components and concepts of a Wardley Map, type "Learn".
            2. Vocabulary: To get a list of common Wardley Map terms and their definitions, type "Vocabulary".
            3. Create: To create your own Wardley Map with step-by-step guidance, type "Create".
            
            Please introduce yourself and if you have any specific questions or need clarification on any aspect of Wardley Mapping, feel free to ask.
            """
        })

st.set_page_config(page_title="Map Mentor - Ultimate Wardley Map Assistant", layout="wide")
st.sidebar.title("Ultimate AI Assistant")
st.sidebar.title("Wardley Mapping Version")
st.sidebar.divider()
st.sidebar.markdown("Developed by Mark Craddock](https://twitter.com/mcraddock)", unsafe_allow_html=True)
st.sidebar.markdown("Current Version: 1.9.0")
#st.sidebar.write(st.session_state.session_id)
st.sidebar.divider()

# Check if the user has provided an API key, otherwise default to the secret
user_openai_api_key = st.sidebar.text_input("Enter your OpenAI API Key:", placeholder="sk-...", type="password")
  
def clean_and_parse_json(raw_json):
    # Remove newline characters and extra spaces
    cleaned_json = raw_json.replace("\n", "\\n")
    return json.loads(cleaned_json, strict=False)

def process_assistant_messages(new_messages):
    response = None  # Initialize the response variable
    for item in new_messages:
        if 'function_call' in item and 'arguments' in item['function_call']:
            try:
                message_args = json.loads(item['function_call']['arguments'], strict=False)
                if 'message' in message_args:
                    try:
                        # Try to clean and parse the message if it's a JSON string
                        response = clean_and_parse_json(message_args['message'])
                    except json.JSONDecodeError:
                        # If cleaning and parsing fail, use the message as is
                        response = message_args['message']
            except json.JSONDecodeError:
                st.warning("There was an error parsing the message from the assistant.")
                response = "There was an error parsing the message from the assistant..."
    if response is not None:
        st.session_state.messages.append({"role": "assistant", "content": response})
    return response

if user_openai_api_key:
    # If the user has provided an API key, use it
    # Swap out openai for promptlayer
    promptlayer.api_key = st.secrets["PROMPTLAYER"]
    openai = promptlayer.openai
    openai.api_key = user_openai_api_key
else:
    st.warning("Please enter your OpenAI API key", icon="⚠️")

if not st.session_state.memgpt_agent:        
    if MODE == "Archive":
        # Memory stored from FAISS
        index, archival_database = utils.prepare_archival_index('/mount/src/stmemgpt/memgpt/personas/examples/mapmentor_archive')
        persistence_manager = InMemoryStateManagerWithFaiss(index, archival_database)
        HUMAN = 'wardley_awareness'
        PERSONA = 'mapmentor_docs'
    else:
        # Memory stored in memory
        HUMAN = 'wardley_awareness'
        PERSONA = 'mapmentor_chat'
        persistence_manager = InMemoryStateManager()
    
    memgpt_agent = presets.use_preset('memgpt_chat', MODEL, personas.get_persona_text(PERSONA), humans.get_human_text(HUMAN), interface, persistence_manager)
    st.session_state.memgpt_agent = memgpt_agent

for message in st.session_state.messages:
    if message["role"] in ["user", "assistant"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if user_openai_api_key:
    prompt = st.chat_input(placeholder="How can I help with Wardley Mapping?", key="chat")
    if not prompt == st.session_state.prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        st.session_state.prompt = prompt
        user_message = system.package_user_message(prompt)
        with st.status("Give me a few secs, I'm just thinking about that."):
            new_messages, st.session_state.heartbeat_request, st.session_state.function_failed, st.session_state.token_warning = st.session_state.memgpt_agent.step(user_message, first_message=False, skip_verify=True)
            response = process_assistant_messages(new_messages)
        if response is not None:
            with st.chat_message("assistant"):
                st.write(response)
    
# Skip user inputs if there's a memory warning, function execution failed, or the agent asked for control

if st.session_state.token_warning:
    user_message = system.get_token_limit_warning()
    with st.status("Thinking ... Reached token limit. Saving to memory:"):
        new_messages, st.session_state.heartbeat_request, st.session_state.function_failed, st.session_state.token_warning = st.session_state.memgpt_agent.step(user_message, first_message=False, skip_verify=True)
        response = process_assistant_messages(new_messages)

if st.session_state.function_failed:
    user_message = system.get_heartbeat(constants.FUNC_FAILED_HEARTBEAT_MESSAGE)
    with st.status("Thinking ... Internal error, recovering:"):
        new_messages, st.session_state.heartbeat_request, st.session_state.function_failed, st.session_state.token_warning = st.session_state.memgpt_agent.step(user_message, first_message=False, skip_verify=True)
        response = process_assistant_messages(new_messages)

if st.session_state.heartbeat_request:
    user_message = system.get_heartbeat(constants.REQ_HEARTBEAT_MESSAGE)
    with st.status("Thinking ... Internal processing."):
        new_messages, st.session_state.heartbeat_request, st.session_state.function_failed, st.session_state.token_warning = st.session_state.memgpt_agent.step(user_message, first_message=False, skip_verify=True)
        response = process_assistant_messages(new_messages)
    if response is not None:
        with st.chat_message("assistant"):
            st.write(response)
    st.rerun()
