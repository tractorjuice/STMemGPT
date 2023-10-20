from abc import ABC, abstractmethod


class AgentAsyncBase(ABC):

    @abstractmethod
    def step(self, user_message):
        pass
