from model.task_strategy import TaskAddStrategy, SimpleAddStrategy

# タスク状態定数
TASK_STATES = ["Planned", "Working", "Closed"]

# Strategyパターン: タスク追加方法を切り替え可能
class TaskModel:
    def __init__(self, strategy: TaskAddStrategy = None):
        # self.tasks = [] → 日付ごとにリスト
        # 各タスクは{"text": ..., "state": ..., "attr_ratio": ...}
        self.tasks = {}  # {date_str: [task_dict, ...]}
        self.strategy = strategy or SimpleAddStrategy()
        self._listeners = []
        self.work_hours = {}  # {date_str: hours(float)}

    def set_strategy(self, strategy: TaskAddStrategy):
        # Strategyパターン: 動的に戦略を切り替え
        self.strategy = strategy

    def add_listener(self, listener):
        self._listeners.append(listener)

    def notify(self, date_str):
        # 指定日付のタスクリストを通知
        for listener in self._listeners:
            listener(self.get_tasks(date_str))

    def add_task(self, date_str, task_text, attr_ratio=None):
        if date_str not in self.tasks:
            self.tasks[date_str] = []
        # attr_ratioのバリデーション
        ratio = None
        if attr_ratio is not None:
            try:
                ratio = float(attr_ratio)
                # 小数点第2位まで
                ratio = round(ratio, 2)
                if ratio < 0:
                    ratio = 0.0
                elif ratio > 100:
                    ratio = 100.0
            except Exception:
                ratio = None
        # タスクは辞書で管理
        task = {"text": task_text, "state": "Planned", "attr_ratio": ratio}
        # Strategyに合わせて追加
        self.strategy.add_task(self.tasks[date_str], task)
        self.notify(date_str)

    def get_tasks(self, date_str):
        return self.tasks.get(date_str, [])

    def remove_task(self, date_str, index):
        # 指定日付・インデックスで削除
        if date_str in self.tasks and 0 <= index < len(self.tasks[date_str]):
            del self.tasks[date_str][index]
            self.notify(date_str)

    def change_task_state(self, date_str, index):
        # 状態をPlanned→Working→Closed→Plannedで循環
        if date_str in self.tasks and 0 <= index < len(self.tasks[date_str]):
            task = self.tasks[date_str][index]
            current = task["state"]
            next_idx = (TASK_STATES.index(current) + 1) % len(TASK_STATES)
            task["state"] = TASK_STATES[next_idx]
            self.notify(date_str)

    def set_task_state(self, date_str, index, new_state):
        # ドロップダウンで直接状態をセット
        if date_str in self.tasks and 0 <= index < len(self.tasks[date_str]):
            if new_state in TASK_STATES:
                self.tasks[date_str][index]["state"] = new_state
                self.notify(date_str)

    def set_task_attr_ratio(self, date_str, index, attr_ratio):
        # attr_ratioのバリデーション
        if date_str in self.tasks and 0 <= index < len(self.tasks[date_str]):
            try:
                ratio = float(attr_ratio)
                ratio = round(ratio, 2)
                if ratio < 0:
                    ratio = 0.0
                elif ratio > 100:
                    ratio = 100.0
                self.tasks[date_str][index]["attr_ratio"] = ratio
                self.notify(date_str)
            except Exception:
                pass

    # 勤務時間の保存
    def set_work_hours(self, date_str, hours):
        self.work_hours[date_str] = hours
        self.notify(date_str)

    # 勤務時間の取得
    def get_work_hours(self, date_str):
        return self.work_hours.get(date_str, None)

    # 勤務時間の削除
    def remove_work_hours(self, date_str):
        if date_str in self.work_hours:
            del self.work_hours[date_str]
            self.notify(date_str)
