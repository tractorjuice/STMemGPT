#Importing required packages
import streamlit as st
import openai
import promptlayer
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

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
promptlayer.api_key = st.secrets["PROMPTLAYER"]
#MODEL = "gpt-3"
#MODEL = "gpt-3.5-turbo"
#MODEL = "gpt-3.5-turbo-0613"
#MODEL = "gpt-3.5-turbo-16k"
#MODEL = "gpt-3.5-turbo-16k-0613"
MODEL = "gpt-4"
#MODEL = "gpt-4-0613"
#MODEL = "gpt-4-32k-0613"

MODE = "Archive"
#MODE = "Chat"
new_messages = []

if "heartbeat_request" not in st.session_state:
    st.session_state["heartbeat_request"] = None
    
if "function_failed" not in st.session_state:
    st.session_state["function_failed"] = None
    
if "token_warning" not in st.session_state:
    st.session_state["token_warning"] = None
    
if "memgpt_agent" not in st.session_state:
    st.session_state["memgpt_agent"] = False
    
# Swap out openai for promptlayer
openai = promptlayer.openai

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
st.sidebar.markdown("Current Version: 1.0.2")
st.sidebar.divider()

# --------------- New code here
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

if prompt := st.chat_input("How can I help with Wardley Mapping?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    user_message = system.package_user_message(prompt)
    new_messages, st.session_state.heartbeat_request, st.session_state.function_failed, st.session_state.token_warning = st.session_state.memgpt_agent.step(user_message, first_message=False, skip_verify=True)
    
    for item in new_messages:
        if 'function_call' in item and 'arguments' in item['function_call']:
            message_args = json.loads(item['function_call']['arguments'])
            if 'message' in message_args:
                message = message_args['message']
                st.session_state.messages.append({"role": "assistant", "content": message})
                
# Skip user inputs if there's a memory warning, function execution failed, or the agent asked for control

if st.session_state.token_warning:
    user_message = system.get_token_limit_warning()
    new_messages, st.session_state.heartbeat_request, st.session_state.function_failed, st.session_state.token_warning = st.session_state.memgpt_agent.step(user_message, first_message=False, skip_verify=True)

    for item in new_messages:
        if 'function_call' in item and 'arguments' in item['function_call']:
            message_args = json.loads(item['function_call']['arguments'])
            if 'message' in message_args:
                message = message_args['message']
                st.session_state.messages.append({"role": "assistant", "content": message})
                    
elif st.session_state.function_failed:
    user_message = system.get_heartbeat(constants.FUNC_FAILED_HEARTBEAT_MESSAGE)
    new_messages, st.session_state.heartbeat_request, st.session_state.function_failed, st.session_state.token_warning = st.session_state.memgpt_agent.step(user_message, first_message=False, skip_verify=True)
    
    for item in new_messages:
        if 'function_call' in item and 'arguments' in item['function_call']:
            message_args = json.loads(item['function_call']['arguments'])
            if 'message' in message_args:
                message = message_args['message']
                st.session_state.messages.append({"role": "assistant", "content": message})

elif st.session_state.heartbeat_request:
    user_message = system.get_heartbeat(constants.REQ_HEARTBEAT_MESSAGE)
    new_messages, st.session_state.heartbeat_request, st.session_state.function_failed, st.session_state.token_warning = st.session_state.memgpt_agent.step(user_message, first_message=False, skip_verify=True)

    for item in new_messages:
        if 'function_call' in item and 'arguments' in item['function_call']:
            message_args = json.loads(item['function_call']['arguments'])
            if 'message' in message_args:
                message = message_args['message']
                st.session_state.messages.append({"role": "assistant", "content": message})

with st.chat_message("assistant"):
    st.write(message)

st.sidebar.divider()
st.sidebar.write(f"Heartbeat: {st.session_state.heartbeat_request}")
st.sidebar.write(f"Function Failed: {st.session_state.function_failed}")
st.sidebar.write(f"Token Warning: {st.session_state.token_warning}")
st.sidebar.write(f"Msg Total Init: {st.session_state.messages_total_init}")
st.sidebar.write(f"Msg Total: {st.session_state.messages_total}")
st.sidebar.divider()
