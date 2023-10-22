#Importing required packages
import streamlit as st
import openai
import promptlayer
import json

#import asyncio
#from absl import app, flags
#import logging
import glob
import os
import sys
import pickle
import readline

#from rich.console import Console
#console = Console()

import interface  # for printing to terminal
import memgpt.agent as agent
import memgpt.system as system
import memgpt.utils as utils
import memgpt.presets as presets
import memgpt.constants as constants
import memgpt.personas.personas as personas
import memgpt.humans.humans as humans
from memgpt.persistence_manager import InMemoryStateManager, InMemoryStateManagerWithPreloadedArchivalMemory, InMemoryStateManagerWithFaiss

#flags.DEFINE_string("persona", default=personas.DEFAULT, required=False, help="Specify persona")
#flags.DEFINE_string("human", default=humans.DEFAULT, required=False, help="Specify human")
#flags.DEFINE_string("model", default=constants.DEFAULT_MEMGPT_MODEL, required=False, help="Specify the LLM model")
#flags.DEFINE_boolean("first", default=False, required=False, help="Use -first to send the first message in the sequence")
#flags.DEFINE_boolean("debug", default=False, required=False, help="Use -debug to enable debugging output")
#flags.DEFINE_boolean("no_verify", default=False, required=False, help="Bypass message verification")
#flags.DEFINE_string("archival_storage_faiss_path", default="", required=False, help="Specify archival storage with FAISS index to load (a folder with a .index and .json describing documents to be loaded)")
#flags.DEFINE_string("archival_storage_files", default="", required=False, help="Specify files to pre-load into archival memory (glob pattern)")
#flags.DEFINE_string("archival_storage_files_compute_embeddings", default="", required=False, help="Specify files to pre-load into archival memory (glob pattern), and compute embeddings over them")
#flags.DEFINE_string("archival_storage_sqldb", default="", required=False, help="Specify SQL database to pre-load into archival memory")

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

# Swap out your 'import openai'
openai = promptlayer.openai

st.set_page_config(page_title="Learn Wardley Mapping Bot (Memory Infinte)")
st.sidebar.title("Learn Wardley Mapping (Infinite)")
st.sidebar.divider()
st.sidebar.markdown("Developed by Mark Craddock](https://twitter.com/mcraddock)", unsafe_allow_html=True)
st.sidebar.markdown("Current Version: 0.2.0")
st.sidebar.markdown("Using GPT-4 API")
st.sidebar.divider()

if "model" not in st.session_state:
    st.session_state["model"] = 'gpt-4'

if "system" not in st.session_state:
    st.session_state["system"] = []

if "functions" not in st.session_state:
    st.session_state["functions"] = []
    
if "memory" not in st.session_state:
    st.session_state["memory"] = []

if "_messages" not in st.session_state:
    st.session_state["_messages"] = []

if "messages_total" not in st.session_state:
    st.session_state["messages_total"] = 0

if "messages_total_init" not in st.session_state:
    st.session_state["messages_total_init"] = 0

if "interface" not in st.session_state:
    st.session_state["interface"] = []

if "persistence_manager" not in st.session_state:
    st.session_state["persistence_manager"] = []

if "pause_heartbeats_start" not in st.session_state:
    st.session_state["pause_heartbeats_start"] = False

if "pause_heartbeats_minutes" not in st.session_state:
    st.session_state["pause_heartbeats_minutes"] = 0

if "first_message_verify_mono" not in st.session_state:
    st.session_state["first_message_verify_mono"] = False

if "agent_alerted_about_memory_pressure" not in st.session_state:
    st.session_state["agent_alerted_about_memory_pressure"] = []

if "all_new_messages" not in st.session_state:
    st.session_state["all_new_messages"] = []
    
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = MODEL

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
            "role": "system",
            "content": f"""
             Interact with WardleyMapBot, your personal guide to learning and creating Wardley Maps.
             Discover the power of Wardley Mapping for strategic planning and decision-making by choosing to 'Learn' about the components of a Wardley Map, or 'Vocabulary' and I will provide a list of common terms and their definitions. or 'Create' your own map with step-by-step guidance.
             If you need assistance, type 'Help' for support. Begin your Wardley Mapping journey now!
             """
        })
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
            If you have any specific questions or need clarification on any aspect of Wardley Mapping, feel free to ask.
            """
        })

# --------------- New code here
persistence_manager = InMemoryStateManager()
memgpt_agent = presets.use_preset('memgpt_chat', MODEL, personas.get_persona_text('simonwarbley'), humans.get_human_text('awareness'), interface, persistence_manager)
print_messages = interface.print_messages
print_messages(memgpt_agent.messages)

for message in st.session_state.messages:
    if message["role"] in ["user", "assistant"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("How can I help with Wardley Mapping?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        # --------------- New code here
        user_message = system.package_user_message(prompt)
        new_messages, heartbeat_request, function_failed, token_warning = memgpt_agent.step(user_message, first_message=False, skip_verify=True)
        #st.sidebar.write("New Messages:")
        #st.sidebar.warning(new_messages)

        for item in new_messages:
            if 'function_call' in item and 'arguments' in item['function_call']:
                message_args = json.loads(item['function_call']['arguments'])
                if 'message' in message_args:
                    message = message_args['message']
                    st.write(message)
                    st.session_state.messages.append({"role": "assistant", "content": message})

        st.write("Msg Total Init")
        st.write(st.session_state.messages_total_init)
        st.write("Msg Total")
        st.write(st.session_state.messages_total)
        st.write("Agent Msg")
        st.write(st.session_state.agent_messages)
        st.write("Pers Msg")
        st.write(st.session_state.persistence_all_messages)

        
        #full_response = ""
        #for response in openai.ChatCompletion.create(
        #    model=st.session_state["openai_model"],
        #    messages=[
        #        {"role": m["role"], "content": m["content"]}
        #        for m in st.session_state.messages
        #    ],
        #    stream=True,
        #    pl_tags=["stmemgptv1"]
        #):
        #    full_response += response.choices[0].delta.get("content", "")
        #    message_placeholder.markdown(full_response + "▌")
        #message_placeholder.markdown(full_response)
    #st.session_state.messages.append({"role": "assistant", "content": message})
