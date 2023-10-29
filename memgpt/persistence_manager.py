from abc import ABC, abstractmethod
import pickle
import streamlit as st

from .memory import DummyRecallMemory, DummyRecallMemoryWithEmbeddings, DummyArchivalMemory, DummyArchivalMemoryWithEmbeddings, DummyArchivalMemoryWithFaiss
from .utils import get_local_time, printd


class PersistenceManager(ABC):

    @abstractmethod
    def trim_messages(self, num):
        pass

    @abstractmethod
    def prepend_to_messages(self, added_messages):
        pass

    @abstractmethod
    def append_to_messages(self, added_messages):
        pass

    @abstractmethod
    def swap_system_message(self, new_system_message):
        pass

    @abstractmethod
    def update_memory(self, new_memory):
        pass


class InMemoryStateManager(PersistenceManager):
    """In-memory state manager has nothing to manage, all agents are held in-memory"""

    recall_memory_cls = DummyRecallMemory
    archival_memory_cls = DummyArchivalMemory

    def __init__(self):
        # Memory held in-state useful for debugging stateful versions
        if "persistence_memory" not in st.session_state:
            st.session_state["persistence_memory"] = None
        self.memory = st.session_state.persistence_memory
        
        if "persistence_messages" not in st.session_state:
            st.session_state["persistence_messages"] = []
        self.messages = st.session_state.persistence_messages

        if "persistence_all_messages" not in st.session_state:
            st.session_state["persistence_all_messages"] = []
        self.all_messages = st.session_state.persistence_all_messages

    @staticmethod
    def load(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)

    def save(self, filename):
        with open(filename, 'wb') as fh:
            pickle.dump(self, fh, protocol=pickle.HIGHEST_PROTOCOL)

    def init(self, agent):
        printd(f"Initializing InMemoryStateManager with agent object")
        #self.all_messages = [{'timestamp': get_local_time(), 'message': msg} for msg in agent.messages.copy()]
        st.session_state.persistence_all_messages = [{'timestamp': get_local_time(), 'message': msg} for msg in agent.messages.copy()]
        self.all_messages = st.session_state.persistence_all_messages
        
        #self.messages = [{'timestamp': get_local_time(), 'message': msg} for msg in agent.messages.copy()]
        st.session_state.persistence_messages = [{'timestamp': get_local_time(), 'message': msg} for msg in agent.messages.copy()]
        self.messages = st.session_state.persistence_messages
        
        #self.memory = agent.memory
        st.session_state.persistence_memory = st.session_state.agent_memory
        self.memory = st.session_state.persistence_memory
        
        printd(f"InMemoryStateManager.all_messages.len = {len(st.session_state.persistence_all_messages)}")
        printd(f"InMemoryStateManager.messages.len = {len(st.session_state.persistence_messages)}")

        # Persistence manager also handles DB-related state
        #self.recall_memory = self.recall_memory_cls(message_database=self.all_messages)
        self.recall_memory = self.recall_memory_cls(message_database=st.session_state.persistence_all_messages)
        self.archival_memory_db = []
        self.archival_memory = self.archival_memory_cls(archival_memory_database=self.archival_memory_db)

    def trim_messages(self, num):
        # printd(f"InMemoryStateManager.trim_messages")
        #self.messages = [self.messages[0]] + self.messages[num:]
        st.session_state.persistence_messages = [st.session_state.persistence_messages[0]] + st.session_state.persistence_messages[num:]
        self.messages = st.session_state.persistence_messages

    def prepend_to_messages(self, added_messages):
        # first tag with timestamps
        added_messages = [{'timestamp': get_local_time(), 'message': msg} for msg in added_messages]

        printd(f"InMemoryStateManager.prepend_to_message")
        #self.messages = [self.messages[0]] + added_messages + self.messages[1:]
        st.session_state.persistence_messages = [st.session_state.persistence_messages[0]] + added_messages + st.session_state.persistence_messages[1:]
        self.messages = st.session_state.persistence_messages
        
        #self.all_messages.extend(added_messages)
        st.session_state.persistence_all_messages.extend(added_messages)
        self.all_messages = st.session_state.persistence_all_messages

    def append_to_messages(self, added_messages):
        # first tag with timestamps
        added_messages = [{'timestamp': get_local_time(), 'message': msg} for msg in added_messages]
        printd(f"InMemoryStateManager.append_to_messages")
       
        #self.messages = self.messages + added_messages
        st.session_state.persistence_messages = st.session_state.persistence_messages + added_messages
        self.messages = st.session_state.persistence_messages
    
        #self.all_messages.extend(added_messages)
        st.session_state.persistence_all_messages.extend(added_messages)
        self.all_messages = st.session_state.persistence_all_messages

    def swap_system_message(self, new_system_message):
        # first tag with timestamps
        new_system_message = {'timestamp': get_local_time(), 'message': new_system_message}

        printd(f"InMemoryStateManager.swap_system_message")
        #self.messages[0] = new_system_message
        st.session_state.persistence_messages[0] = new_system_message
        self.messages[0] = st.session_state.persistence_messages[0]
        
        #self.all_messages.append(new_system_message)
        st.session_state.persistence_all_messages.append(new_system_message)
        self.all_messages = st.session_state.persistence_all_messages

    def update_memory(self, new_memory):
        printd(f"InMemoryStateManager.update_memory")
        #self.memory = new_memory
        st.session_state.persistence_memory = new_memory
        self.memory = st.session_state.persistence_memory


class InMemoryStateManagerWithPreloadedArchivalMemory(InMemoryStateManager):
    archival_memory_cls = DummyArchivalMemory
    recall_memory_cls = DummyRecallMemory

    def __init__(self, archival_memory_db):
        self.archival_memory_db = archival_memory_db

    def init(self, agent):
        print(f"Initializing InMemoryStateManager with agent object")
        st.sidebar.write(f"Initializing InMemoryStateManager with agent object")
        #self.all_messages = [{'timestamp': get_local_time(), 'message': msg} for msg in agent.messages.copy()]
        st.session_state.persistence_all_messages = [{'timestamp': get_local_time(), 'message': msg} for msg in agent.messages.copy()]
        self.all_messages = st.session_state.persistence_all_messages
        
        #self.messages = [{'timestamp': get_local_time(), 'message': msg} for msg in agent.messages.copy()]
        st.session_state.persistence_messages = [{'timestamp': get_local_time(), 'message': msg} for msg in agent.messages.copy()]
        self.messages = st.session_state.persistence_messages
        
        #self.memory = agent.memory
        st.session_state.persistence_memory = agent.memory
        self.memory = st.session_state.persistence_memory
        
        #print(f"InMemoryStateManager.all_messages.len = {len(self.all_messages)}")
        print(f"InMemoryStateManager.all_messages.len = {len(st.session_state.persistence_all_messages)}")
        st.sidebar.write(f"InMemoryStateManager.all_messages.len = {len(st.session_state.persistence_all_messages)}")
        
        #print(f"InMemoryStateManager.messages.len = {len(self.messages)}")
        print(f"InMemoryStateManager.messages.len = {len(st.session_state.persistence_messages)}")
        st.sidebar.write(f"InMemoryStateManager.messages.len = {len(st.session_state.persistence_messages)}")

        print(f"Recall Memory = {len(st.session_state.persistence_all_messages)}")
        st.sidebar.write(f"Recall Memory = {len(st.session_state.persistence_all_messages)}")

        print(f"Archive Memory = {len(self.archival_memory_db)}")
        st.sidebar.write(f"Archive Memory = {len(self.archival_memory_db)}")
        
        #self.recall_memory = self.recall_memory_cls(message_database=self.all_messages)
        self.recall_memory = self.recall_memory_cls(message_database=st.session_state.persistence_all_messages)
        self.archival_memory = self.archival_memory_cls(archival_memory_database=self.archival_memory_db)


class InMemoryStateManagerWithEmbeddings(InMemoryStateManager):
    archival_memory_cls = DummyArchivalMemoryWithEmbeddings
    recall_memory_cls = DummyRecallMemoryWithEmbeddings


class InMemoryStateManagerWithFaiss(InMemoryStateManager):
    archival_memory_cls = DummyArchivalMemoryWithFaiss
    recall_memory_cls = DummyRecallMemoryWithEmbeddings

    def __init__(self, archival_index, archival_memory_db, a_k=100):
        super().__init__()
        self.archival_index = archival_index
        self.archival_memory_db = archival_memory_db
        self.a_k = a_k

    def save(self, _filename):
        raise NotImplementedError

    def init(self, agent):
        print(f"Initializing InMemoryStateManager with agent object")
        #self.all_messages = [{'timestamp': get_local_time(), 'message': msg} for msg in agent.messages.copy()]
        st.session_state.persistence_all_messages = [{'timestamp': get_local_time(), 'message': msg} for msg in agent.messages.copy()]
        self.all_messages = st.session_state.persistence_all_messages
        
        #self.messages = [{'timestamp': get_local_time(), 'message': msg} for msg in agent.messages.copy()]
        st.session_state.persistence_messages = [{'timestamp': get_local_time(), 'message': msg} for msg in agent.messages.copy()]
        self.messages = st.session_state.persistence_messages
        
        #self.memory = agent.memory
        st.session_state.persistence_memory = agent.memory
        self.memory = st.session_state.persistence_memory
        
        #print(f"InMemoryStateManager.all_messages.len = {len(self.all_messages)}")
        print(f"InMemoryStateManager.all_messages.len = {len(st.session_state.persistence_all_messages)}")    
        #print(f"InMemoryStateManager.messages.len = {len(self.messages)}")
        print(f"InMemoryStateManager.messages.len = {len(st.session_state.persistence_messages)}")

        print(f"Recall Memory = {len(st.session_state.persistence_all_messages)}")
        st.sidebar.write(f"Recall Memory = {len(st.session_state.persistence_all_messages)}")

        print(f"Archive Memory = {len(self.archival_memory_db)}")
        st.sidebar.write(f"Archive Memory = {len(self.archival_memory_db)}")

        # Persistence manager also handles DB-related state
        #self.recall_memory = self.recall_memory_cls(message_database=self.all_messages)
        self.recall_memory = self.recall_memory_cls(message_database=st.session_state.persistence_all_messages)
        self.archival_memory = self.archival_memory_cls(index=self.archival_index, archival_memory_database=self.archival_memory_db, k=self.a_k)
