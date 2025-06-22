from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QLineEdit, QListWidget, QInputDialog
from PyQt5.QtCore import pyqtSignal
import re

class SelectTaskView(QWidget):
    task_attr_ratio_change_requested = pyqtSignal(int, float)  # (index, new_ratio)

    def __init__(self, parent=None):
        super().__init__(parent)

        # レイアウトの初期化
        main_layout = QVBoxLayout(self)
        self.filter_layout = QHBoxLayout()
        main_layout.addLayout(self.filter_layout)
        
        # 状態フィルターUI追加
        self.working_checkbox = QCheckBox('Working')
        self.planned_checkbox = QCheckBox('Planned')
        self.working_checkbox.setChecked(True)
        self.planned_checkbox.setChecked(True)
        self.filter_layout.addWidget(self.working_checkbox)
        self.filter_layout.addWidget(self.planned_checkbox)

        # タスクリスト
        self.task_list = QListWidget()
        main_layout.addWidget(self.task_list)

        # タスクリストのダブルクリックで体感割合編集
        self.task_list.itemDoubleClicked.connect(self.edit_attr_ratio_dialog)

    def get_status_filter(self):
        status = []
        if self.working_checkbox.isChecked():
            status.append('working')
        if self.planned_checkbox.isChecked():
            status.append('planned')
        return status

    def edit_attr_ratio_dialog(self, item):
        index = self.task_list.row(item)
        current_text = item.text()
        # 既存の体感割合を抽出（例: "タスク名 [状態] (xx%)" の形式）
        m = re.search(r"\(([\d\.]+)%\)", current_text)
        default = float(m.group(1)) if m else 0.0
        ratio, ok = QInputDialog.getDouble(self, "体感割合の編集", "新しい体感割合(0.00～100.00):", default, 0, 100, 2)
        if ok:
            self.task_attr_ratio_change_requested.emit(index, ratio)