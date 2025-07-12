import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget,
    QSplitter, QFrame
)
from PyQt5.QtCore import Qt

from .left_panel import LeftPanel
from .config_panel import ConfigPanel
from .execution_panel import ExecutionPanel
from .database import TaskBatchDatabase


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.database = TaskBatchDatabase()
        self.init_ui()
        self.connect_signals()

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


def main():
    import os
    if os.environ.get('DISPLAY') is None:
        print("No DISPLAY environment variable found.")
        print("To run the GUI, either:")
        print("1. Set up X11 forwarding: export DISPLAY=:0.0")
        print("2. Use virtual display: export DISPLAY=:99 && Xvfb :99 -screen 0 1024x768x24 &")
        print("3. Install X server on Windows (VcXsrv/Xming)")
        return
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()