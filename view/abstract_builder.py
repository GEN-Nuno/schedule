from abc import ABC, abstractmethod

class SchedulerUIBuilder(ABC):
    @abstractmethod
    def build_calendar_view(self):
        pass

    @abstractmethod
    def build_task_view(self):
        pass

    @abstractmethod
    def build_main_window(self):
        pass

    @abstractmethod
    def get_result(self):
        pass
