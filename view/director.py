class SchedulerUIDirector:
    def __init__(self, builder):
        self.builder = builder

    def construct(self):
        self.builder.build_calendar_view()
        self.builder.build_task_view()
        self.builder.build_main_window()
        return self.builder.get_result()