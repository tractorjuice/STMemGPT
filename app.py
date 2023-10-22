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

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "memgpt_agent" not in st.session_state:
    st.session_state["memgpt_agent"] = False
    
# Swap out your 'import openai'
openai = promptlayer.openai

st.set_page_config(page_title="Learn Wardley Mapping Bot (Memory Infinte)")
st.sidebar.title("Learn Wardley Mapping (Infinite)")
st.sidebar.divider()
st.sidebar.markdown("Developed by Mark Craddock](https://twitter.com/mcraddock)", unsafe_allow_html=True)
st.sidebar.markdown("Current Version: 0.7.0")
st.sidebar.markdown("Core components:")
st.sidebar.markdown("Streamlit, OpenAI, Memgpt ( InMemoryStateManager)")
st.sidebar.divider()

# --------------- New code here
if not st.session_state.memgpt_agent:
    persistence_manager = InMemoryStateManager()
    memgpt_agent = presets.use_preset('memgpt_chat', MODEL, personas.get_persona_text('simonwarbley'), humans.get_human_text('awareness'), interface, persistence_manager)
    print_messages = interface.print_messages
    print_messages(memgpt_agent.messages)
    st.session_state.memgpt_agent = memgpt_agent

for message in st.session_state.messages:
    if message["role"] in ["user", "assistant"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("How can I help with Wardley Mapping?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        # --------------- New code here
        user_message = system.package_user_message(prompt)
        new_messages, heartbeat_request, function_failed, token_warning = st.session_state.memgpt_agent.step(user_message, first_message=False, skip_verify=True)

        #st.sidebar.divider()
        #st.sidebar.write(f"Heartbeat: {heartbeat_request}")
        
        if heartbeat_request:
            user_message = system.get_heartbeat(constants.REQ_HEARTBEAT_MESSAGE)
            new_messages, heartbeat_request, function_failed, token_warning = st.session_state.memgpt_agent.step(user_message, first_message=False, skip_verify=True)
            heartbeat_request = False

        st.sidebar.divider()
        #st.sidebar.write(f"Heartbeat: {heartbeat_request}")
        #st.sidebar.write(f"Function Failed: {function_failed}")
        #st.sidebar.write(f"Token Warning: {token_warning}")
        #st.sidebar.write(f"Msg Total Init: {st.session_state.messages_total_init}")
        #st.sidebar.write(f"Msg Total: {st.session_state.messages_total}")
        #st.sidebar.divider()
        #st.sidebar.write(f"Pers Msg: {st.session_state.persistence_all_messages}")

        for item in new_messages:
            if 'function_call' in item and 'arguments' in item['function_call']:
                message_args = json.loads(item['function_call']['arguments'])
                if 'message' in message_args:
                    message = message_args['message']
                    st.write(message)
                    st.session_state.messages.append({"role": "assistant", "content": message})
