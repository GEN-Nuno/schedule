from abc import ABC, abstractmethod

# Strategyパターン: タスク追加方法の切り替え
class TaskAddStrategy(ABC):
    @abstractmethod
    def add_task(self, task_list, task):
        pass

class SimpleAddStrategy(TaskAddStrategy):
    def add_task(self, task_list, task):
        task_list.append(task)

class UniqueAddStrategy(TaskAddStrategy):
    def add_task(self, task_list, task):
        if all(t["text"] != task["text"] for t in task_list):
            task_list.append(task)
