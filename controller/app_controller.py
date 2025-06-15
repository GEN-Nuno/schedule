from controller.task_controller import TaskController
from view.pyqt_builder import PyQtSchedulerUIBuilder
from view.director import SchedulerUIDirector

class FunctionManager:
    def __init__(self):
        self._main_window = None

    def create_main_window(self):
        if self._main_window is None:
            builder = PyQtSchedulerUIBuilder()
            director = SchedulerUIDirector(builder)
            self._main_window = director.construct()
        return self._main_window

    def get_state(self):
        # シンプルな実装: 常にmainを返す
        return "main"

class AppController:
    def __init__(self, app):
        self.app = app
        self.function_manager = FunctionManager()
        self.main_window = None
        self.task_controller = None

    def show_main_window(self):
        if self.main_window is None:
            self.main_window = self.function_manager.create_main_window()
            # ViewとControllerの接続（Observer/Commandパターン）
            if hasattr(self.main_window, "task_view"):
                self.task_controller = TaskController(self.main_window.task_view)
        self.main_window.show()

    def handle_state(self, state):
        # 状態に応じて画面を表示
        if state == "main":
            self.show_main_window()
        # 他の状態があればここに追加

    def run(self):
        state = self.function_manager.get_state()
        self.handle_state(state)
        self.app.exec_()