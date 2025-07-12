from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QMenu,
    QMessageBox,
    QInputDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QDrag

from .database import TaskBatchDatabase, Task, Batch


class TaskListWidget(QListWidget):
    def __init__(self, database: TaskBatchDatabase):
        super().__init__()
        self.database = database
        self.setDragDropMode(QListWidget.DragOnly)
        self.setDefaultDropAction(Qt.CopyAction)
        self.refresh()

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            task = item.data(Qt.UserRole)
            if task and task.id:
                drag = QDrag(self)
                mimeData = QMimeData()
                mimeData.setText(f"task_id:{task.id}")
                drag.setMimeData(mimeData)
                drag.exec_(Qt.CopyAction)

    def refresh(self):
        self.clear()
        tasks = self.database.get_all_tasks()
        for task in tasks:
            item = QListWidgetItem(task.name)
            item.setData(Qt.UserRole, task)
            self.addItem(item)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if item is None:
            return

        menu = QMenu(self)
        run_action = menu.addAction("Run")
        duplicate_action = menu.addAction("Duplicate")
        delete_action = menu.addAction("Delete")

        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == run_action:
            self.run_task(item)
        elif action == duplicate_action:
            self.duplicate_task(item)
        elif action == delete_action:
            self.delete_task(item)

    def run_task(self, item):
        pass

    def duplicate_task(self, item):
        task = item.data(Qt.UserRole)
        new_task = Task(
            name=f"{task.name} (Copy)",
            db=task.db,
            debug_outdir=task.debug_outdir,
            gemini=task.gemini,
            local_files=task.local_files,
            logfile=task.logfile,
            min_area=task.min_area,
            min_size=task.min_size,
            no_safe_search=task.no_safe_search,
            num_images=task.num_images,
            outdir=task.outdir,
            paths=task.paths,
            queries=task.queries,
            randomize=task.randomize,
            threads=task.threads,
            timestamp=task.timestamp,
            verbose=task.verbose,
            visible=task.visible,
            wait_between_scroll=task.wait_between_scroll,
            wait_first_load=task.wait_first_load,
        )
        self.database.save_task(new_task)
        self.refresh()

    def delete_task(self, item):
        task = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self,
            "Delete Task",
            f"Delete task '{task.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.database.delete_task(task.id)
            self.refresh()


class BatchListWidget(QListWidget):
    def __init__(self, database: TaskBatchDatabase):
        super().__init__()
        self.database = database
        self.refresh()

    def refresh(self):
        self.clear()
        batches = self.database.get_all_batches()
        for batch in batches:
            item = QListWidgetItem(batch.name)
            item.setData(Qt.UserRole, batch)
            self.addItem(item)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if item is None:
            return

        menu = QMenu(self)
        run_action = menu.addAction("Run")
        duplicate_action = menu.addAction("Duplicate")
        delete_action = menu.addAction("Delete")

        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == run_action:
            self.run_batch(item)
        elif action == duplicate_action:
            self.duplicate_batch(item)
        elif action == delete_action:
            self.delete_batch(item)

    def run_batch(self, item):
        pass

    def duplicate_batch(self, item):
        batch = item.data(Qt.UserRole)
        new_batch = Batch(
            name=f"{batch.name} (Copy)",
            auto_timestamped_dir=batch.auto_timestamped_dir,
            base_output_dir=batch.base_output_dir,
            parameter_overrides=batch.parameter_overrides.copy()
            if batch.parameter_overrides
            else None,
            environment_variables=batch.environment_variables.copy()
            if batch.environment_variables
            else None,
            task_order=batch.task_order.copy() if batch.task_order else None,
        )
        self.database.save_batch(new_batch)
        self.refresh()

    def delete_batch(self, item):
        batch = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self,
            "Delete Batch",
            f"Delete batch '{batch.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.database.delete_batch(batch.id)
            self.refresh()


class LeftPanel(QWidget):
    task_selected = pyqtSignal(object)
    batch_selected = pyqtSignal(object)
    selection_cleared = pyqtSignal()

    def __init__(self, database: TaskBatchDatabase):
        super().__init__()
        self.database = database
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        layout = QVBoxLayout(self)

        tasks_header = QHBoxLayout()
        tasks_label = QLabel("Tasks")
        tasks_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        new_task_btn = QPushButton("New Task")
        new_task_btn.clicked.connect(self.create_new_task)
        tasks_header.addWidget(tasks_label)
        tasks_header.addStretch()
        tasks_header.addWidget(new_task_btn)
        layout.addLayout(tasks_header)

        self.task_list = TaskListWidget(self.database)
        layout.addWidget(self.task_list)

        batches_header = QHBoxLayout()
        batches_label = QLabel("Batches")
        batches_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        new_batch_btn = QPushButton("New Batch")
        new_batch_btn.clicked.connect(self.create_new_batch)
        batches_header.addWidget(batches_label)
        batches_header.addStretch()
        batches_header.addWidget(new_batch_btn)
        layout.addLayout(batches_header)

        self.batch_list = BatchListWidget(self.database)
        layout.addWidget(self.batch_list)

    def connect_signals(self):
        self.task_list.itemClicked.connect(self.on_task_selected)
        self.batch_list.itemClicked.connect(self.on_batch_selected)

    def on_task_selected(self, item):
        self.batch_list.clearSelection()
        task = item.data(Qt.UserRole)
        self.task_selected.emit(task)

    def on_batch_selected(self, item):
        self.task_list.clearSelection()
        batch = item.data(Qt.UserRole)
        self.batch_selected.emit(batch)

    def create_new_task(self):
        name, ok = QInputDialog.getText(self, "New Task", "Task name:")
        if ok and name:
            task = Task(name=name)
            task_id = self.database.save_task(task)
            task.id = task_id
            self.task_list.refresh()
            for i in range(self.task_list.count()):
                item = self.task_list.item(i)
                if item.data(Qt.UserRole).id == task_id:
                    self.task_list.setCurrentItem(item)
                    self.on_task_selected(item)
                    break

    def create_new_batch(self):
        name, ok = QInputDialog.getText(self, "New Batch", "Batch name:")
        if ok and name:
            batch = Batch(name=name)
            batch_id = self.database.save_batch(batch)
            batch.id = batch_id
            self.batch_list.refresh()
            for i in range(self.batch_list.count()):
                item = self.batch_list.item(i)
                if item.data(Qt.UserRole).id == batch_id:
                    self.batch_list.setCurrentItem(item)
                    self.on_batch_selected(item)
                    break

    def refresh_lists(self):
        self.task_list.refresh()
        self.batch_list.refresh()
