from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTabWidget,
    QTextEdit, QProgressBar, QLabel
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
import logging

from .database import Task, Batch


class LogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.append(msg)


class TaskExecutor(QThread):
    progress_updated = pyqtSignal(int, str)
    task_completed = pyqtSignal(bool, str)
    log_message = pyqtSignal(str)

    def __init__(self, task_or_batch, database):
        super().__init__()
        self.item = task_or_batch
        self.database = database
        self.should_stop = False

    def run(self):
        try:
            if isinstance(self.item, Task):
                self.run_task(self.item)
            elif isinstance(self.item, Batch):
                self.run_batch(self.item)
        except Exception as e:
            self.task_completed.emit(False, str(e))

    def run_task(self, task: Task):
        self.log_message.emit(f"Starting task: {task.name}")
        self.progress_updated.emit(0, f"Running task: {task.name}")

        try:
            from similar_images.bing_selenium import BingSelenium
            from similar_images.crappy_db import CrappyDB
            from similar_images.filters.db_filters import (
                DbExactDupFilter, DbNearDupFilter, DbUrlFilter
            )
            from similar_images.filters.gemini_filters import GeminiFilter
            from similar_images.filters.image_filters import ImageFilter
            from similar_images.image_sources import (
                BrowserImageSource, BrowserQuerySource, LocalFileImageSource
            )
            from similar_images.scraper import Scraper
            import tempfile
            import os
            import json
            import datetime

            if self.should_stop:
                return

            self.progress_updated.emit(10, "Setting up filters and database")

            crappy_db = None
            filter_objects = []
            
            if task.db:
                crappy_db = CrappyDB(task.db)
                filter_objects += [
                    DbUrlFilter(crappy_db),
                    DbExactDupFilter(crappy_db),
                    DbNearDupFilter(crappy_db),
                ]

            min_size = None
            if task.min_size:
                try:
                    width, height = map(int, task.min_size.split(','))
                    min_size = (width, height)
                except ValueError:
                    min_size = (640, 480)

            if min_size or task.min_area:
                min_size = min_size or (640, 480)
                min_area = task.min_area or 0
                filter_objects.append(ImageFilter(min_size=min_size, min_area=min_area))

            if task.gemini:
                for config_path in task.gemini:
                    try:
                        with open(config_path, 'rt') as f:
                            config_dict = json.loads(f.read())
                            filter_objects.append(GeminiFilter(**config_dict))
                    except (FileNotFoundError, json.JSONDecodeError) as e:
                        self.log_message.emit(f"Error loading Gemini config {config_path}: {e}")

            self.progress_updated.emit(30, "Setting up browser")

            browser = None
            home_tmp_dir = tempfile.mkdtemp(dir=os.environ["HOME"])
            
            if task.paths or task.queries:
                headless = not task.visible
                browser = BingSelenium(
                    headless=headless,
                    user_data_dir=home_tmp_dir,
                    wait_between_scroll=task.wait_between_scroll,
                    wait_first_load=task.wait_first_load,
                    safe_search=not task.no_safe_search,
                )

            if self.should_stop:
                return

            self.progress_updated.emit(50, "Setting up image sources")

            image_sources = []
            if task.local_files:
                image_sources.append(LocalFileImageSource(task.local_files, random=task.randomize))
            if task.paths:
                image_sources.append(BrowserImageSource(browser, task.paths, random=task.randomize))
            if task.queries:
                image_sources.append(BrowserQuerySource(browser, task.queries, random=task.randomize))

            if not image_sources:
                raise ValueError("No image sources specified")

            outdir = task.outdir
            debug_outdir = task.debug_outdir
            logfile = task.logfile

            if task.timestamp:
                now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                if outdir:
                    outdir = f"{outdir}/{now_str}"
                if debug_outdir:
                    debug_outdir = f"{debug_outdir}/{now_str}"
                if logfile:
                    logfile = f"{logfile}.{now_str}"

            self.progress_updated.emit(70, "Running scraper")

            for i, image_source in enumerate(image_sources):
                if self.should_stop:
                    return
                    
                progress = 70 + (i / len(image_sources)) * 25
                self.progress_updated.emit(int(progress), f"Processing image source {i+1}/{len(image_sources)}")
                
                scraper = Scraper(
                    image_source=image_source,
                    db=crappy_db,
                    filters=filter_objects,
                    outdir=outdir,
                    debug_outdir=debug_outdir,
                    count=task.num_images,
                    concurrency=task.threads,
                )
                scraper.sync_scrape()

            self.progress_updated.emit(100, f"Task completed: {task.name}")
            self.task_completed.emit(True, f"Task '{task.name}' completed successfully")

        except Exception as e:
            self.log_message.emit(f"Error in task {task.name}: {str(e)}")
            self.task_completed.emit(False, f"Task failed: {str(e)}")

    def run_batch(self, batch: Batch):
        self.log_message.emit(f"Starting batch: {batch.name}")
        
        if not batch.task_order:
            self.task_completed.emit(False, "No tasks in batch")
            return

        total_tasks = len(batch.task_order)
        
        for i, task_id in enumerate(batch.task_order):
            if self.should_stop:
                return
                
            task = self.database.get_task(task_id)
            if not task:
                self.log_message.emit(f"Task {task_id} not found, skipping")
                continue

            progress = int((i / total_tasks) * 100)
            self.progress_updated.emit(progress, f"Running task {i+1}/{total_tasks}: {task.name}")

            modified_task = self.apply_batch_overrides(task, batch)
            self.run_task(modified_task)

        self.progress_updated.emit(100, f"Batch completed: {batch.name}")
        self.task_completed.emit(True, f"Batch '{batch.name}' completed successfully")

    def apply_batch_overrides(self, task: Task, batch: Batch) -> Task:
        modified_task = Task(
            id=task.id, name=task.name, db=task.db, debug_outdir=task.debug_outdir,
            gemini=task.gemini, local_files=task.local_files, logfile=task.logfile,
            min_area=task.min_area, min_size=task.min_size, no_safe_search=task.no_safe_search,
            num_images=task.num_images, outdir=task.outdir, paths=task.paths,
            queries=task.queries, randomize=task.randomize, threads=task.threads,
            timestamp=task.timestamp, verbose=task.verbose, visible=task.visible,
            wait_between_scroll=task.wait_between_scroll, wait_first_load=task.wait_first_load
        )

        if batch.auto_timestamped_dir and batch.base_output_dir:
            import datetime
            now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_dir = f"{batch.base_output_dir}/{now_str}"
            task_dir = f"{base_dir}/{task.name}"
            
            if not modified_task.outdir:
                modified_task.outdir = task_dir
            if not modified_task.debug_outdir:
                modified_task.debug_outdir = f"{task_dir}/debug"

        if batch.parameter_overrides:
            for key, value in batch.parameter_overrides.items():
                if hasattr(modified_task, key):
                    setattr(modified_task, key, value)

        return modified_task

    def stop(self):
        self.should_stop = True


class MonitorTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(self.log_text.font())
        layout.addWidget(self.log_text)

        self.setup_logging()

    def setup_logging(self):
        self.log_handler = LogHandler(self.log_text)
        self.log_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        
        logger = logging.getLogger()
        logger.addHandler(self.log_handler)
        logger.setLevel(logging.INFO)

    def update_progress(self, value, text):
        self.progress_bar.setValue(value)
        self.status_label.setText(text)
        if value == 100:
            QTimer.singleShot(2000, lambda: self.progress_bar.setVisible(False))

    def show_progress(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

    def add_log_message(self, message):
        self.log_text.append(message)


class BrowserTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("about:blank"))
        layout.addWidget(self.web_view)

        placeholder_label = QLabel("Browser view will appear here when running in visible mode")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("color: gray; font-size: 14px;")
        layout.addWidget(placeholder_label)


class HistoryTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setText("Execution history will appear here (future feature)")
        layout.addWidget(self.history_text)


class ExecutionPanel(QWidget):
    stop_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.executor = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_execution)
        layout.addWidget(self.stop_button)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.monitor_tab = MonitorTab()
        self.tabs.addTab(self.monitor_tab, "Monitor")

        self.browser_tab = BrowserTab()
        self.tabs.addTab(self.browser_tab, "Browser")

        self.history_tab = HistoryTab()
        self.tabs.addTab(self.history_tab, "History")

    def run_task_or_batch(self, item):
        if self.executor and self.executor.isRunning():
            return

        from .main_window import MainWindow
        main_window = self.parent()
        while main_window and not isinstance(main_window, MainWindow):
            main_window = main_window.parent()
        
        if not main_window:
            return

        self.monitor_tab.show_progress()
        self.stop_button.setEnabled(True)
        self.tabs.setCurrentIndex(0)

        self.executor = TaskExecutor(item, main_window.database)
        self.executor.progress_updated.connect(self.monitor_tab.update_progress)
        self.executor.task_completed.connect(self.on_task_completed)
        self.executor.log_message.connect(self.monitor_tab.add_log_message)
        self.executor.start()

    def stop_execution(self):
        if self.executor and self.executor.isRunning():
            self.executor.stop()
            self.executor.wait(5000)
            if self.executor.isRunning():
                self.executor.terminate()
        
        self.stop_button.setEnabled(False)
        self.monitor_tab.status_label.setText("Stopped")
        self.stop_requested.emit()

    def on_task_completed(self, success, message):
        self.stop_button.setEnabled(False)
        self.monitor_tab.add_log_message(message)
        if success:
            self.monitor_tab.status_label.setText("Completed successfully")
        else:
            self.monitor_tab.status_label.setText("Failed")