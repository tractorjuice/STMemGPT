import json
import re
import streamlit as st

from colorama import Fore, Style, init

from memgpt.utils import printd

init(autoreset=True)

# DEBUG = True  # puts full message outputs in the terminal
DEBUG = False  # only dumps important messages in the terminal

def important_message(msg):
    print(f'{msg}')
    st.sidebar.warning(f'{msg}')

def internal_monologue(msg):
    # ANSI escape code for italic is '\x1B[3m'
    print(f'💭 {msg}')
    st.sidebar.write(f'💭 {msg}')

def assistant_message(msg):
    print(f'🤖 {msg}')
    st.sidebar.write(f'🤖 {msg}')

def memory_message(msg):
    print(f'🧠 {msg}')
    st.sidebar.write(f'🧠 {msg}')
    
def system_message(msg):
    printd(f'🖥️ [system] {msg}')
    st.sidebar.write(f'🖥️ [system] {msg}')
    
def user_message(msg, raw=False):
    if isinstance(msg, str):
        if raw:
            printd(f'🧑 {msg}')
            return
        else:
            try:
                msg_json = json.loads(msg)
            except:
                printd(f"Warning: failed to parse user message into json")
                printd(f'🧑 {{msg}')
                return

    if msg_json['type'] == 'user_message':
        msg_json.pop('type')
        printd(f'🧑 {msg_json}')
    elif msg_json['type'] == 'heartbeat':
        if DEBUG:
            msg_json.pop('type')
            printd(f'💓 {msg_json}}')
    elif msg_json['type'] == 'system_message':
        msg_json.pop('type')
        printd(f'🖥️ {msg_json}')
    else:
        printd(f'🧑 {msg_json}')

def function_message(msg):

    if isinstance(msg, dict):
        printd(f'⚡ [function] {msg}')
        return

    if msg.startswith('Success: '):
        printd(f'⚡🟢 [function] {msg}')
    elif msg.startswith('Error: '):
        printd(f'⚡🔴 [function] {msg}')
    elif msg.startswith('Running '):
        if DEBUG:
            printd(f'⚡ [function] {msg}')
        else:
            if 'memory' in msg:
                match = re.search(r'Running (\w+)\((.*)\)', msg)
                if match:
                    function_name = match.group(1)
                    function_args = match.group(2)
                    print(f'⚡🧠 [function] updating memory with {function_name}:')
                    st.sidebar.write(f'⚡🧠 [function] updating memory with {function_name}:')
                    try:
                        msg_dict = eval(function_args)
                        if function_name == 'archival_memory_search':
                            print(f'\tquery: {msg_dict["query"]}, page: {msg_dict["page"]}')
                            st.sidebar.write(f'\tquery: {msg_dict["query"]}, page: {msg_dict["page"]}')
                        else:
                            st.sidebar.warning(msg_dict)
                            #print(f'\t {msg_dict["old_content"]}\n\t→ {msg_dict["new_content"]}')
                            #st.sidebar.write(f'\t {msg_dict["old_content"]}\n\t→ {msg_dict["new_content"]}')
                    except Exception as e:
                        printd(e)
                        printd(msg_dict)
                        pass
                else:
                    printd(f"Warning: did not recognize function message")
                    printd(f'⚡ [function] {msg}')
            elif 'send_message' in msg:
                # ignore in debug mode
                pass
            else:
                printd(f'⚡ [function] {msg}')
    else:
        try:
            msg_dict = json.loads(msg)
            if "status" in msg_dict and msg_dict["status"] == "OK":
                printd(f'⚡ [function] {msg}')
        except Exception:
            printd(f"Warning: did not recognize function message {type(msg)} {msg}")
            printd(f'⚡ [function] {msg}')

def print_messages(message_sequence):
    for msg in message_sequence:
        role = msg['role']
        content = msg['content']

        if role == 'system':
            system_message(content)
        elif role == 'assistant':
            # Differentiate between internal monologue, function calls, and messages
            if msg.get('function_call'):
                if content is not None:
                    internal_monologue(content)
                function_message(msg['function_call'])
                # assistant_message(content)
            else:
                internal_monologue(content)
        elif role == 'user':
            user_message(content)
        elif role == 'function':
            function_message(content)
        else:
            print(f'Unknown role: {content}')

def print_messages_simple(message_sequence):
    for msg in message_sequence:
        role = msg['role']
        content = msg['content']

        if role == 'system':
            system_message(content)
        elif role == 'assistant':
            assistant_message(content)
        elif role == 'user':
            user_message(content, raw=True)
        else:
            print(f'Unknown role: {content}')

def print_messages_raw(message_sequence):
    for msg in message_sequence:
        print(msg)
        st.write(msg)
