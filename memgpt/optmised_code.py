





import streamlit as st
import openai
import promptlayer
import json
import interface
import memgpt.agent as agent
import memgpt.system as system
import memgpt.utils as utils
import memgpt.presets as presets
import memgpt.personas.personas as personas
import memgpt.humans.humans as humans
from memgpt.persistence_manager import InMemoryStateManager, InMemoryStateManagerWithFaiss

# Initialize session state variables
for var_name, default_value in [("heartbeat_request", False), ("function_failed", False), 
                                ("token_warning", False), ("memgpt_agent", False), ("messages", [])]:
    if var_name not in st.session_state:
        st.session_state[var_name] = default_value

# ... [rest of the initial setup code remains the same]

def process_messages(new_messages):
    for item in new_messages:
        if 'function_call' in item and 'arguments' in item['function_call']:
            try:
                message_args = json.loads(item['function_call']['arguments'])
                if 'message' in message_args:
                    message = message_args['message']
                    with st.chat_message("user"):
                        st.write(message)
                    st.session_state.messages.append({"role": "assistant", "content": message})
            except json.JSONDecodeError:
                st.warning("There was an error parsing the message from the assistant.")

def handle_error_state(error_type):
    if error_type == "token_warning":
        user_message = system.get_token_limit_warning()
    elif error_type == "function_failed":
        user_message = system.get_heartbeat(constants.FUNC_FAILED_HEARTBEAT_MESSAGE)
    elif error_type == "heartbeat_request":
        user_message = system.get_heartbeat(constants.REQ_HEARTBEAT_MESSAGE)
    else:
        return

    new_messages, st.session_state.heartbeat_request, st.session_state.function_failed, st.session_state.token_warning = st.session_state.memgpt_agent.step(user_message, first_message=False, skip_verify=True)
    process_messages(new_messages)

# Main interaction
if prompt := st.chat_input("How can I help with Wardley Mapping?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    user_message = system.package_user_message(prompt)
    with st.status("Give me a few secs, I'm just thinking about that."):
        new_messages, st.session_state.heartbeat_request, st.session_state.function_failed, st.session_state.token_warning = st.session_state.memgpt_agent.step(user_message, first_message=False, skip_verify=True)
    process_messages(new_messages)

# Error Handling
for error_type in ["token_warning", "function_failed", "heartbeat_request"]:
    if st.session_state[error_type]:
        handle_error_state(error_type)
        break

# ... [rest of the code remains the same]
