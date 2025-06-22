from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QCheckBox, QCalendarWidget,
    QListWidget, QLineEdit, QPushButton, QHBoxLayout, QComboBox, QDialog, QInputDialog
)
from PyQt5.QtCore import pyqtSignal, QDate
from .abstract_builder import SchedulerUIBuilder
import re

class PyQtCalendarView(QWidget):
    date_selected = pyqtSignal(str)  # 追加: 日付選択シグナル

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calendar View")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        self.calendar = QCalendarWidget(self)
        self.calendar.setGridVisible(True)
        layout.addWidget(self.calendar)

        self.setLayout(layout)
        # 日付変更時にシグナル発火
        self.calendar.selectionChanged.connect(self.on_date_changed)

    def on_date_changed(self):
        date = self.calendar.selectedDate()
        date_str = date.toString("yyyy-MM-dd")
        self.date_selected.emit(date_str)

    def get_selected_date(self):
        return self.calendar.selectedDate().toString("yyyy-MM-dd")

class TaskListDialog(QDialog):
    # タスク追加・削除のシグナル
    task_added = pyqtSignal(str, str)  # (text, attr)
    task_deleted = pyqtSignal(int)

    def __init__(self, task_master_list):
        super().__init__()
        self.setWindowTitle("Task List")
        self.setGeometry(200, 200, 400, 400)
        self.task_master_list = task_master_list  # [{text, attr}, ...]

        layout = QVBoxLayout()

        self.list_widget = QListWidget(self)
        self.refresh_list()
        layout.addWidget(self.list_widget)

        input_layout = QHBoxLayout()
        self.input_line = QLineEdit(self)
        input_layout.addWidget(self.input_line)
        self.attr_combo = QComboBox(self)
        self.attr_combo.addItems(["Free", "Mon", "Tue", "Wed", "Thu", "Fri"])
        input_layout.addWidget(self.attr_combo)
        self.add_button = QPushButton("Add", self)
        input_layout.addWidget(self.add_button)
        layout.addLayout(input_layout)

        self.delete_button = QPushButton("Delete Selected", self)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

        self.add_button.clicked.connect(self.on_add)
        self.delete_button.clicked.connect(self.on_delete)

    def refresh_list(self):
        self.list_widget.clear()
        for t in self.task_master_list:
            self.list_widget.addItem(f"{t['text']} ({t['attr']})")

    def on_add(self):
        text = self.input_line.text()
        attr = self.attr_combo.currentText()
        if text and not any(t['text'] == text for t in self.task_master_list):
            self.task_master_list.append({'text': text, 'attr': attr})
            self.refresh_list()
            self.input_line.clear()
            self.task_added.emit(text, attr)

    def on_delete(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self.task_master_list):
            del self.task_master_list[row]
            self.refresh_list()
            self.task_deleted.emit(row)

class PyQtTaskView(QWidget):
    # タスク追加イベントのシグナル
    task_added = pyqtSignal(str, float)  # (task_text, attr_ratio)
    date_changed = pyqtSignal(str)
    # 編集・削除・状態切替のシグナル
    task_delete_requested = pyqtSignal(int)
    # ドロップダウン選択式: (index, new_state)
    task_state_change_requested = pyqtSignal(int, str)
    # 勤務時間保存・削除のシグナル
    work_hours_saved = pyqtSignal(str)
    work_hours_deleted = pyqtSignal()
    # 新規: タスク選択追加用シグナル
    task_selected_to_add = pyqtSignal(str)
    open_task_list_requested = pyqtSignal()
    # タスク属性比率変更シグナル
    task_attr_ratio_change_requested = pyqtSignal(int, float)  # (index, new_ratio)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Task View")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        self.task_list = QListWidget(self)
        layout.addWidget(self.task_list)

        # 追加: タスク選択用コンボボックス＋例外チェック
        select_layout = QHBoxLayout()
        self.task_select_combo = QComboBox(self)
        select_layout.addWidget(QLabel("Select Task:"))
        select_layout.addWidget(self.task_select_combo)
        self.exception_checkbox = QCheckBox("例外")
        select_layout.addWidget(self.exception_checkbox)
        self.add_task_button = QPushButton("Add Task", self)
        select_layout.addWidget(self.add_task_button)
        layout.addLayout(select_layout)

        # 追加: タスクリストウィンドウ呼び出しボタン
        self.open_task_list_button = QPushButton("Check Task List", self)
        layout.addWidget(self.open_task_list_button)

        # ボタン群
        btn_layout = QHBoxLayout()
        self.delete_task_button = QPushButton("Delete Task", self)
        btn_layout.addWidget(self.delete_task_button)
        layout.addLayout(btn_layout)

        # 状態変更用ドロップダウン
        state_layout = QHBoxLayout()
        self.state_combo = QComboBox(self)
        self.state_combo.addItems(["Planned", "Working", "Closed"])
        state_layout.addWidget(QLabel("Change State:"))
        state_layout.addWidget(self.state_combo)
        layout.addLayout(state_layout)

        # 勤務時間入力欄
        wh_layout = QHBoxLayout()
        self.work_hours_input = QLineEdit(self)
        self.work_hours_input.setPlaceholderText("Enter work hours (e.g. 8.0)")
        wh_layout.addWidget(QLabel("Work Hours:"))
        wh_layout.addWidget(self.work_hours_input)
        self.save_work_hours_button = QPushButton("Save", self)
        wh_layout.addWidget(self.save_work_hours_button)
        self.delete_work_hours_button = QPushButton("Delete", self)
        wh_layout.addWidget(self.delete_work_hours_button)
        layout.addLayout(wh_layout)

        # 勤務時間表示ラベル
        self.work_hours_display = QLabel("", self)
        layout.addWidget(self.work_hours_display)

        self.setLayout(layout)

        # シグナル接続
        self.add_task_button.clicked.connect(self.on_add_task_from_combo)
        self.open_task_list_button.clicked.connect(self.open_task_list_requested.emit)
        self.delete_task_button.clicked.connect(self.on_delete_task)
        # ドロップダウン選択時
        self.state_combo.currentIndexChanged.connect(self.on_state_combo_changed)
        # タスクリスト選択時にドロップダウンを同期
        self.task_list.currentRowChanged.connect(self.sync_state_combo)
        # 勤務時間ボタンのシグナル
        self.save_work_hours_button.clicked.connect(self.on_save_work_hours)
        self.delete_work_hours_button.clicked.connect(self.on_delete_work_hours)
        self.exception_checkbox.stateChanged.connect(self.update_task_combo_filter)

        # タスクマスターリスト初期化
        self._task_master_list = []

        self.task_list.itemDoubleClicked.connect(self.edit_attr_ratio_dialog)

    def set_task_master_list(self, task_master_list):
        # task_master_list: [{'text':..., 'attr':...}, ...]
        self._task_master_list = task_master_list
        self.update_task_combo_filter()

    def update_task_combo_filter(self):
        # カレンダーで選択中日付の曜日を取得
        date_str = self.get_selected_date()
        qdate = QDate.fromString(date_str, "yyyy-MM-dd")
        weekday = qdate.dayOfWeek()  # 1=Mon, ..., 7=Sun
        weekday_map = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri"}
        weekday_str = weekday_map.get(weekday, None)
        show_all = self.exception_checkbox.isChecked()
        self.task_select_combo.clear()
        for t in self._task_master_list:
            if t['attr'] == "Free" or show_all or t['attr'] == weekday_str:
                self.task_select_combo.addItem(f"{t['text']} ({t['attr']})")

    def on_add_task_from_combo(self):
        text = self.task_select_combo.currentText()
        if text:
            # "text (attr)" からtext部分だけ抽出
            task_text = text.split(" (")[0]
            self.task_selected_to_add.emit(task_text)

    def on_delete_task(self):
        row = self.task_list.currentRow()
        if row >= 0:
            self.task_delete_requested.emit(row)

    def on_state_combo_changed(self, idx):
        row = self.task_list.currentRow()
        if row >= 0:
            state = self.state_combo.currentText()
            self.task_state_change_requested.emit(row, state)

    def sync_state_combo(self, row):
        # タスクリスト選択時に状態をドロップダウンに反映
        if row < 0:
            return
        item = self.task_list.item(row)
        if item:
            # 表示は "text [state]" なので末尾[]から状態を取得
            text = item.text()
            if "[" in text and text.endswith("]"):
                state = text[text.rfind("[")+1:-1]
                idx = self.state_combo.findText(state)
                if idx >= 0:
                    self.state_combo.blockSignals(True)
                    self.state_combo.setCurrentIndex(idx)
                    self.state_combo.blockSignals(False)

    def set_selected_date(self, date_str):
        # 必要ならUIに日付表示など
        self.date_changed.emit(date_str)
        self.update_task_combo_filter()

    def get_selected_date(self):
        # 親ウィンドウからセットされる想定
        return getattr(self, "_current_date", QDate.currentDate().toString("yyyy-MM-dd"))

    def on_save_work_hours(self):
        hours = self.work_hours_input.text()
        self.work_hours_saved.emit(hours)

    def on_delete_work_hours(self):
        self.work_hours_deleted.emit()

    def set_work_hours_display(self, hours):
        if hours is None:
            self.work_hours_display.setText("Work Hours: (not set)")
        else:
            self.work_hours_display.setText(f"Work Hours: {hours}")

    def emit_task_added(self):
        task_text = self.task_combo.currentText()
        ratio_text = self.attr_ratio_input.text()
        try:
            attr_ratio = float(ratio_text)
            attr_ratio = round(attr_ratio, 2)
            if not (0 <= attr_ratio <= 100):
                attr_ratio = None
        except Exception:
            attr_ratio = None
        self.task_added.emit(task_text, attr_ratio)

    def edit_attr_ratio_dialog(self, item):
        index = self.task_list.row(item)
        current_text = item.text()
        m = re.search(r"\(([\d\.]+)%\)", current_text)
        default = float(m.group(1)) if m else 0.0
        ratio, ok = QInputDialog.getDouble(self, "体感割合の編集", "新しい体感割合(0.00～100.00):", default, 0, 100, 2)
        if ok:
            self.task_attr_ratio_change_requested.emit(index, ratio)

class PyQtMainWindow(QMainWindow):
    def __init__(self, calendar_view, task_view):
        super().__init__()
        self.setWindowTitle("Scheduler")
        self.setGeometry(100, 100, 800, 600)

        self.calendar_view = calendar_view
        self.task_view = task_view

        # カレンダーとタスクビューの連携
        self.calendar_view.date_selected.connect(self.on_calendar_date_changed)
        # 初期日付をタスクビューにセット
        init_date = self.calendar_view.get_selected_date()
        self.task_view._current_date = init_date
        self.task_view.set_selected_date(init_date)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)

        layout.addWidget(self.calendar_view)
        layout.addWidget(self.task_view)

    def on_calendar_date_changed(self, date_str):
        self.task_view._current_date = date_str
        self.task_view.set_selected_date(date_str)

# Builderパターン: UI部品の組み立てを担当
class PyQtSchedulerUIBuilder(SchedulerUIBuilder):
    def __init__(self):
        self.calendar_view = None
        self.task_view = None
        self.main_window = None

    def build_calendar_view(self):
        self.calendar_view = PyQtCalendarView()

    def build_task_view(self):
        self.task_view = PyQtTaskView()

    def build_main_window(self):
        if self.calendar_view is None or self.task_view is None:
            raise Exception("Views must be built before main window")
        self.main_window = PyQtMainWindow(self.calendar_view, self.task_view)

    def get_result(self):
        return self.main_window

__all__ = ["PyQtSchedulerUIBuilder", "TaskListDialog"]