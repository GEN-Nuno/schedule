import os
import json
from model.task_model import TaskModel
from view.pyqt_builder import TaskListDialog

INIT_CONF_PATH = os.path.join(os.path.dirname(__file__), '..', 'init.conf')

# Commandパターン: タスク追加処理をオブジェクト化し、Controllerから実行
class AddTaskCommand:
    def __init__(self, model):
        self.model = model

    def execute(self, date_str, task_text, attr_ratio=None):
        self.model.add_task(date_str, task_text, attr_ratio)

# ControllerはObserverとしてViewのイベントを受信し、Commandで処理を委譲
class TaskController:
    def __init__(self, task_view):
        self.model = TaskModel()
        self.add_task_command = AddTaskCommand(self.model)
        self.task_view = task_view
        self.current_date = self.task_view.get_selected_date()
        # init.confから全データをロード
        conf = self.load_conf()
        self.task_master_list = conf.get("task_master_list", [
            {"text": "Sample Task 1", "attr": "Free"},
            {"text": "Sample Task 2", "attr": "Mon"}
        ])
        self.model.tasks = conf.get("calendar_tasks", {})
        self.model.work_hours = conf.get("work_hours", {})
        self.task_view.set_task_master_list(self.task_master_list)
        # Observerパターン: ViewのシグナルをControllerが受信
        self.task_view.task_added.connect(self.handle_add_task)
        self.task_view.date_changed.connect(self.handle_date_changed)
        # 編集・削除・状態切替のシグナルを接続
        self.task_view.task_delete_requested.connect(self.handle_delete_task)
        self.task_view.task_state_change_requested.connect(self.handle_change_task_state)
        self.task_view.task_attr_ratio_change_requested.connect(self.handle_change_task_attr_ratio)
        # 勤務時間関連シグナル
        self.task_view.work_hours_saved.connect(self.handle_save_work_hours)
        self.task_view.work_hours_deleted.connect(self.handle_delete_work_hours)
        # Observerパターン: Modelの変更をViewに通知
        self.model.add_listener(self.update_view)
        # 初期表示
        self.update_view(self.model.get_tasks(self.current_date))
        self.task_view.task_selected_to_add.connect(self.handle_add_task_from_master)
        self.task_view.open_task_list_requested.connect(self.open_task_list_window)

    def handle_add_task(self, task_text, attr_ratio=None):
        # Commandパターン: タスク追加処理を委譲
        self.add_task_command.execute(self.current_date, task_text, attr_ratio)
        self.save_conf()

    def handle_date_changed(self, date_str):
        self.current_date = date_str
        self.update_view(self.model.get_tasks(date_str))

    def handle_delete_task(self, index):
        self.model.remove_task(self.current_date, index)
        self.save_conf()

    def handle_change_task_state(self, index, new_state):
        self.model.set_task_state(self.current_date, index, new_state)
        self.save_conf()

    def handle_change_task_attr_ratio(self, index, new_ratio):
        self.model.set_task_attr_ratio(self.current_date, index, new_ratio)
        self.save_conf()

    def handle_save_work_hours(self, hours):
        # 入力値はstr型なのでfloatに変換
        try:
            h = float(hours)
            self.model.set_work_hours(self.current_date, h)
            self.save_conf()
        except ValueError:
            pass  # 不正な入力は無視

    def handle_delete_work_hours(self):
        self.model.remove_work_hours(self.current_date)
        self.save_conf()

    def handle_add_task_from_master(self, task_text):
        # マスターリストから選択して追加（attr_ratioはNone）
        self.add_task_command.execute(self.current_date, task_text, None)
        self.save_conf()

    def load_conf(self):
        # 設定ファイルを読み込み
        try:
            with open(INIT_CONF_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # バリデーション
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
        # デフォルト
        return {}

    def save_conf(self):
        # 設定ファイルに保存
        data = {
            "task_master_list": self.task_master_list,
            "calendar_tasks": self.model.tasks,
            "work_hours": self.model.work_hours
        }
        try:
            with open(INIT_CONF_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def open_task_list_window(self):
        dialog = TaskListDialog(self.task_master_list)
        dialog.task_added.connect(self.on_master_task_added)
        dialog.task_deleted.connect(self.on_master_task_deleted)
        dialog.exec_()
        # 閉じた後にコンボボックスを更新
        self.task_view.set_task_master_list(self.task_master_list)
        self.save_conf()

    def on_master_task_added(self, text, attr):
        self.task_view.set_task_master_list(self.task_master_list)
        self.save_conf()

    def on_master_task_deleted(self, idx):
        self.task_view.set_task_master_list(self.task_master_list)
        self.save_conf()

    def update_view(self, tasks):
        self.task_view.task_list.clear()
        for t in tasks:
            # 状態とattr_ratioを表示に含める
            ratio_str = ""
            if t.get("attr_ratio") is not None:
                ratio_str = f" ({t['attr_ratio']}%)"
            self.task_view.task_list.addItem(f"{t['text']} [{t['state']}]"+ratio_str)
        # 勤務時間表示も更新
        hours = self.model.get_work_hours(self.current_date)
        self.task_view.set_work_hours_display(hours)
