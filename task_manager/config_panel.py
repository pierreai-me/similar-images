from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QCheckBox, QPushButton, QLabel, QTextEdit, QScrollArea, QFrame,
    QListWidget, QListWidgetItem, QGroupBox, QFileDialog, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Dict, Any

from .database import TaskBatchDatabase, Task, Batch


class TaskConfigWidget(QWidget):
    def __init__(self, database: TaskBatchDatabase):
        super().__init__()
        self.database = database
        self.current_task = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.save_current_task)
        scroll_layout.addRow("Name:", self.name_edit)

        self.db_edit = QLineEdit()
        self.db_edit.textChanged.connect(self.save_current_task)
        db_layout = QHBoxLayout()
        db_layout.addWidget(self.db_edit)
        db_browse_btn = QPushButton("Browse")
        db_browse_btn.clicked.connect(self.browse_db_file)
        db_layout.addWidget(db_browse_btn)
        scroll_layout.addRow("Database:", db_layout)

        self.debug_outdir_edit = QLineEdit()
        self.debug_outdir_edit.textChanged.connect(self.save_current_task)
        debug_outdir_layout = QHBoxLayout()
        debug_outdir_layout.addWidget(self.debug_outdir_edit)
        debug_outdir_browse_btn = QPushButton("Browse")
        debug_outdir_browse_btn.clicked.connect(self.browse_debug_outdir)
        debug_outdir_layout.addWidget(debug_outdir_browse_btn)
        scroll_layout.addRow("Debug Output Dir:", debug_outdir_layout)

        self.gemini_edit = QTextEdit()
        self.gemini_edit.setMaximumHeight(60)
        self.gemini_edit.textChanged.connect(self.save_current_task)
        scroll_layout.addRow("Gemini Configs (one per line):", self.gemini_edit)

        self.local_files_edit = QTextEdit()
        self.local_files_edit.setMaximumHeight(60)
        self.local_files_edit.textChanged.connect(self.save_current_task)
        scroll_layout.addRow("Local Files (one per line):", self.local_files_edit)

        self.logfile_edit = QLineEdit()
        self.logfile_edit.textChanged.connect(self.save_current_task)
        logfile_layout = QHBoxLayout()
        logfile_layout.addWidget(self.logfile_edit)
        logfile_browse_btn = QPushButton("Browse")
        logfile_browse_btn.clicked.connect(self.browse_logfile)
        logfile_layout.addWidget(logfile_browse_btn)
        scroll_layout.addRow("Log File:", logfile_layout)

        self.min_area_spin = QSpinBox()
        self.min_area_spin.setRange(0, 9999999)
        self.min_area_spin.valueChanged.connect(self.save_current_task)
        scroll_layout.addRow("Min Area:", self.min_area_spin)

        self.min_size_edit = QLineEdit()
        self.min_size_edit.setPlaceholderText("width,height")
        self.min_size_edit.textChanged.connect(self.save_current_task)
        scroll_layout.addRow("Min Size:", self.min_size_edit)

        self.no_safe_search_check = QCheckBox()
        self.no_safe_search_check.stateChanged.connect(self.save_current_task)
        scroll_layout.addRow("No Safe Search:", self.no_safe_search_check)

        self.num_images_spin = QSpinBox()
        self.num_images_spin.setRange(0, 9999)
        self.num_images_spin.valueChanged.connect(self.save_current_task)
        scroll_layout.addRow("Number of Images:", self.num_images_spin)

        self.outdir_edit = QLineEdit()
        self.outdir_edit.textChanged.connect(self.save_current_task)
        outdir_layout = QHBoxLayout()
        outdir_layout.addWidget(self.outdir_edit)
        outdir_browse_btn = QPushButton("Browse")
        outdir_browse_btn.clicked.connect(self.browse_outdir)
        outdir_layout.addWidget(outdir_browse_btn)
        scroll_layout.addRow("Output Dir:", outdir_layout)

        self.paths_edit = QTextEdit()
        self.paths_edit.setMaximumHeight(60)
        self.paths_edit.textChanged.connect(self.save_current_task)
        scroll_layout.addRow("Image Paths (one per line):", self.paths_edit)

        self.queries_edit = QLineEdit()
        self.queries_edit.textChanged.connect(self.save_current_task)
        scroll_layout.addRow("Search Queries:", self.queries_edit)

        self.randomize_check = QCheckBox()
        self.randomize_check.stateChanged.connect(self.save_current_task)
        scroll_layout.addRow("Randomize:", self.randomize_check)

        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 32)
        self.threads_spin.valueChanged.connect(self.save_current_task)
        scroll_layout.addRow("Threads:", self.threads_spin)

        self.timestamp_check = QCheckBox()
        self.timestamp_check.stateChanged.connect(self.save_current_task)
        scroll_layout.addRow("Add Timestamp:", self.timestamp_check)

        self.verbose_check = QCheckBox()
        self.verbose_check.stateChanged.connect(self.save_current_task)
        scroll_layout.addRow("Verbose:", self.verbose_check)

        self.visible_check = QCheckBox()
        self.visible_check.stateChanged.connect(self.save_current_task)
        scroll_layout.addRow("Visible Browser:", self.visible_check)

        self.wait_between_scroll_spin = QSpinBox()
        self.wait_between_scroll_spin.setRange(0, 60)
        self.wait_between_scroll_spin.valueChanged.connect(self.save_current_task)
        scroll_layout.addRow("Wait Between Scroll (s):", self.wait_between_scroll_spin)

        self.wait_first_load_spin = QSpinBox()
        self.wait_first_load_spin.setRange(0, 60)
        self.wait_first_load_spin.valueChanged.connect(self.save_current_task)
        scroll_layout.addRow("Wait First Load (s):", self.wait_first_load_spin)

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

    def load_task(self, task: Task):
        self.current_task = task
        
        self.name_edit.setText(task.name or "")
        self.db_edit.setText(task.db or "")
        self.debug_outdir_edit.setText(task.debug_outdir or "")
        self.gemini_edit.setText("\n".join(task.gemini or []))
        self.local_files_edit.setText("\n".join(task.local_files or []))
        self.logfile_edit.setText(task.logfile or "")
        self.min_area_spin.setValue(task.min_area or 0)
        self.min_size_edit.setText(task.min_size or "")
        self.no_safe_search_check.setChecked(task.no_safe_search)
        self.num_images_spin.setValue(task.num_images or 0)
        self.outdir_edit.setText(task.outdir or "")
        self.paths_edit.setText("\n".join(task.paths or []))
        self.queries_edit.setText(task.queries or "")
        self.randomize_check.setChecked(task.randomize)
        self.threads_spin.setValue(task.threads or 1)
        self.timestamp_check.setChecked(task.timestamp)
        self.verbose_check.setChecked(task.verbose)
        self.visible_check.setChecked(task.visible)
        self.wait_between_scroll_spin.setValue(task.wait_between_scroll or 0)
        self.wait_first_load_spin.setValue(task.wait_first_load or 0)

    def save_current_task(self):
        if not self.current_task:
            return

        self.current_task.name = self.name_edit.text()
        self.current_task.db = self.db_edit.text() or None
        self.current_task.debug_outdir = self.debug_outdir_edit.text() or None
        
        gemini_text = self.gemini_edit.toPlainText().strip()
        self.current_task.gemini = [line.strip() for line in gemini_text.split('\n') if line.strip()] if gemini_text else None
        
        local_files_text = self.local_files_edit.toPlainText().strip()
        self.current_task.local_files = [line.strip() for line in local_files_text.split('\n') if line.strip()] if local_files_text else None
        
        self.current_task.logfile = self.logfile_edit.text() or None
        self.current_task.min_area = self.min_area_spin.value() or None
        self.current_task.min_size = self.min_size_edit.text() or None
        self.current_task.no_safe_search = self.no_safe_search_check.isChecked()
        self.current_task.num_images = self.num_images_spin.value() or None
        self.current_task.outdir = self.outdir_edit.text() or None
        
        paths_text = self.paths_edit.toPlainText().strip()
        self.current_task.paths = [line.strip() for line in paths_text.split('\n') if line.strip()] if paths_text else None
        
        self.current_task.queries = self.queries_edit.text() or None
        self.current_task.randomize = self.randomize_check.isChecked()
        self.current_task.threads = self.threads_spin.value() or None
        self.current_task.timestamp = self.timestamp_check.isChecked()
        self.current_task.verbose = self.verbose_check.isChecked()
        self.current_task.visible = self.visible_check.isChecked()
        self.current_task.wait_between_scroll = self.wait_between_scroll_spin.value() or None
        self.current_task.wait_first_load = self.wait_first_load_spin.value() or None

        self.database.save_task(self.current_task)

    def browse_db_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Database File", "", "Database Files (*.db);;All Files (*)")
        if filename:
            self.db_edit.setText(filename)

    def browse_debug_outdir(self):
        dirname = QFileDialog.getExistingDirectory(self, "Select Debug Output Directory")
        if dirname:
            self.debug_outdir_edit.setText(dirname)

    def browse_logfile(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Select Log File", "", "Log Files (*.log);;All Files (*)")
        if filename:
            self.logfile_edit.setText(filename)

    def browse_outdir(self):
        dirname = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dirname:
            self.outdir_edit.setText(dirname)


class BatchConfigWidget(QWidget):
    def __init__(self, database: TaskBatchDatabase):
        super().__init__()
        self.database = database
        self.current_batch = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        basic_group = QGroupBox("Basic Settings")
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.save_current_batch)
        basic_layout.addRow("Name:", self.name_edit)

        self.auto_timestamp_check = QCheckBox()
        self.auto_timestamp_check.stateChanged.connect(self.save_current_batch)
        basic_layout.addRow("Auto-timestamped directories:", self.auto_timestamp_check)

        self.base_output_dir_edit = QLineEdit()
        self.base_output_dir_edit.textChanged.connect(self.save_current_batch)
        base_dir_layout = QHBoxLayout()
        base_dir_layout.addWidget(self.base_output_dir_edit)
        base_dir_browse_btn = QPushButton("Browse")
        base_dir_browse_btn.clicked.connect(self.browse_base_output_dir)
        base_dir_layout.addWidget(base_dir_browse_btn)
        basic_layout.addRow("Base Output Directory:", base_dir_layout)

        scroll_layout.addWidget(basic_group)

        overrides_group = QGroupBox("Parameter Overrides")
        overrides_layout = QVBoxLayout(overrides_group)
        
        self.overrides_edit = QTextEdit()
        self.overrides_edit.setMaximumHeight(100)
        self.overrides_edit.setPlaceholderText("JSON format parameter overrides")
        self.overrides_edit.textChanged.connect(self.save_current_batch)
        overrides_layout.addWidget(self.overrides_edit)

        scroll_layout.addWidget(overrides_group)

        env_group = QGroupBox("Environment Variables")
        env_layout = QVBoxLayout(env_group)
        
        self.env_edit = QTextEdit()
        self.env_edit.setMaximumHeight(100)
        self.env_edit.setPlaceholderText("KEY=value format, one per line")
        self.env_edit.textChanged.connect(self.save_current_batch)
        env_layout.addWidget(self.env_edit)

        scroll_layout.addWidget(env_group)

        tasks_group = QGroupBox("Task Order")
        tasks_layout = QVBoxLayout(tasks_group)
        
        self.task_order_list = QListWidget()
        self.task_order_list.setDragDropMode(QListWidget.InternalMove)
        self.task_order_list.setAcceptDrops(True)
        self.task_order_list.itemChanged.connect(self.save_current_batch)
        tasks_layout.addWidget(self.task_order_list)

        scroll_layout.addWidget(tasks_group)

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

    def load_batch(self, batch: Batch):
        self.current_batch = batch
        
        self.name_edit.setText(batch.name or "")
        self.auto_timestamp_check.setChecked(batch.auto_timestamped_dir)
        self.base_output_dir_edit.setText(batch.base_output_dir or "")
        
        if batch.parameter_overrides:
            import json
            self.overrides_edit.setText(json.dumps(batch.parameter_overrides, indent=2))
        else:
            self.overrides_edit.setText("")
            
        if batch.environment_variables:
            env_text = "\n".join([f"{k}={v}" for k, v in batch.environment_variables.items()])
            self.env_edit.setText(env_text)
        else:
            self.env_edit.setText("")

        self.load_task_order()

    def load_task_order(self):
        self.task_order_list.clear()
        if self.current_batch and self.current_batch.task_order:
            for task_id in self.current_batch.task_order:
                task = self.database.get_task(task_id)
                if task:
                    item = QListWidgetItem(task.name)
                    item.setData(Qt.UserRole, task.id)
                    self.task_order_list.addItem(item)

    def save_current_batch(self):
        if not self.current_batch:
            return

        self.current_batch.name = self.name_edit.text()
        self.current_batch.auto_timestamped_dir = self.auto_timestamp_check.isChecked()
        self.current_batch.base_output_dir = self.base_output_dir_edit.text() or None

        overrides_text = self.overrides_edit.toPlainText().strip()
        if overrides_text:
            try:
                import json
                self.current_batch.parameter_overrides = json.loads(overrides_text)
            except json.JSONDecodeError:
                self.current_batch.parameter_overrides = None
        else:
            self.current_batch.parameter_overrides = None

        env_text = self.env_edit.toPlainText().strip()
        if env_text:
            env_dict = {}
            for line in env_text.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_dict[key.strip()] = value.strip()
            self.current_batch.environment_variables = env_dict
        else:
            self.current_batch.environment_variables = None

        task_order = []
        for i in range(self.task_order_list.count()):
            item = self.task_order_list.item(i)
            task_order.append(item.data(Qt.UserRole))
        self.current_batch.task_order = task_order

        self.database.save_batch(self.current_batch)

    def browse_base_output_dir(self):
        dirname = QFileDialog.getExistingDirectory(self, "Select Base Output Directory")
        if dirname:
            self.base_output_dir_edit.setText(dirname)


class ConfigPanel(QWidget):
    run_selected = pyqtSignal(object)

    def __init__(self, database: TaskBatchDatabase):
        super().__init__()
        self.database = database
        self.current_item = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.run_button = QPushButton("Run Selected")
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self.run_current_item)
        layout.addWidget(self.run_button)

        self.task_config = TaskConfigWidget(self.database)
        self.batch_config = BatchConfigWidget(self.database)
        
        self.welcome_label = QLabel("Select a task or batch to configure")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet("color: gray; font-size: 16px;")

        layout.addWidget(self.welcome_label)
        layout.addWidget(self.task_config)
        layout.addWidget(self.batch_config)

        self.task_config.hide()
        self.batch_config.hide()

    def show_task_config(self, task: Task):
        self.current_item = task
        self.welcome_label.hide()
        self.batch_config.hide()
        self.task_config.load_task(task)
        self.task_config.show()
        self.run_button.setEnabled(True)

    def show_batch_config(self, batch: Batch):
        self.current_item = batch
        self.welcome_label.hide()
        self.task_config.hide()
        self.batch_config.load_batch(batch)
        self.batch_config.show()
        self.run_button.setEnabled(True)

    def clear_config(self):
        self.current_item = None
        self.task_config.hide()
        self.batch_config.hide()
        self.welcome_label.show()
        self.run_button.setEnabled(False)

    def run_current_item(self):
        if self.current_item:
            self.run_selected.emit(self.current_item)