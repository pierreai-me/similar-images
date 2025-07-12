import sys

from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QSplitter, QWidget

from .config_panel import ConfigPanel
from .database import TaskBatchDatabase
from .execution_panel import ExecutionPanel
from .left_panel import LeftPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("TaskBatchManager", "TaskBatchManager")
        self.database = TaskBatchDatabase()
        self.init_ui()
        self.connect_signals()
        self.restore_geometry()

    def init_ui(self):
        self.setWindowTitle("Task Batch Manager")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)

        self.left_panel = LeftPanel(self.database)
        main_splitter.addWidget(self.left_panel)

        right_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(right_splitter)

        self.config_panel = ConfigPanel(self.database)
        right_splitter.addWidget(self.config_panel)

        self.execution_panel = ExecutionPanel()
        right_splitter.addWidget(self.execution_panel)

        self.main_splitter = main_splitter
        self.right_splitter = right_splitter

        # Set default sizes
        main_splitter.setSizes([300, 1100])
        right_splitter.setSizes([450, 450])

    def connect_signals(self):
        self.left_panel.task_selected.connect(self.config_panel.show_task_config)
        self.left_panel.batch_selected.connect(self.config_panel.show_batch_config)
        self.left_panel.selection_cleared.connect(self.config_panel.clear_config)

        self.config_panel.run_selected.connect(self.execution_panel.run_task_or_batch)
        self.execution_panel.stop_requested.connect(self.stop_execution)

    def stop_execution(self):
        pass

    def restore_geometry(self):
        # Restore window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # Restore splitter positions
        main_splitter_state = self.settings.value("main_splitter_state")
        if main_splitter_state:
            self.main_splitter.restoreState(main_splitter_state)

        right_splitter_state = self.settings.value("right_splitter_state")
        if right_splitter_state:
            self.right_splitter.restoreState(right_splitter_state)

    def save_geometry(self):
        # Save window geometry
        self.settings.setValue("geometry", self.saveGeometry())

        # Save splitter positions
        self.settings.setValue("main_splitter_state", self.main_splitter.saveState())
        self.settings.setValue("right_splitter_state", self.right_splitter.saveState())

    def closeEvent(self, event):
        self.save_geometry()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
