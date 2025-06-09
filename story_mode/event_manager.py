from abc import ABC, abstractmethod

class EventManager(ABC):
    @abstractmethod
    def check_for_events(self):
        pass

    @abstractmethod
    def get_available_events(self):
        pass

    @abstractmethod
    def register_event(self, event):
        pass

    @abstractmethod
    def trigger_event(self, event):
        pass

class ConcreteEventManager(EventManager):
    def check_for_events(self):
        pass

    def get_available_events(self):
        return []

    def register_event(self, event):
        pass

    def trigger_event(self, event):
        pass 