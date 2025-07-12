import sqlite3
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Task:
    id: Optional[int] = None
    name: str = ""
    db: Optional[str] = None
    debug_outdir: Optional[str] = None
    gemini: Optional[List[str]] = None
    local_files: Optional[List[str]] = None
    logfile: Optional[str] = None
    min_area: Optional[int] = None
    min_size: Optional[str] = None
    no_safe_search: bool = False
    num_images: Optional[int] = None
    outdir: Optional[str] = None
    paths: Optional[List[str]] = None
    queries: Optional[str] = None
    randomize: bool = False
    threads: Optional[int] = None
    timestamp: bool = False
    verbose: bool = False
    visible: bool = False
    wait_between_scroll: Optional[int] = None
    wait_first_load: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Batch:
    id: Optional[int] = None
    name: str = ""
    auto_timestamped_dir: bool = False
    base_output_dir: Optional[str] = None
    parameter_overrides: Optional[Dict[str, Any]] = None
    environment_variables: Optional[Dict[str, str]] = None
    task_order: Optional[List[int]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TaskBatchDatabase:
    def __init__(self, db_path: str = "task_batch_manager.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    db TEXT,
                    debug_outdir TEXT,
                    gemini TEXT,  -- JSON array
                    local_files TEXT,  -- JSON array
                    logfile TEXT,
                    min_area INTEGER,
                    min_size TEXT,
                    no_safe_search BOOLEAN DEFAULT 0,
                    num_images INTEGER,
                    outdir TEXT,
                    paths TEXT,  -- JSON array
                    queries TEXT,
                    randomize BOOLEAN DEFAULT 0,
                    threads INTEGER,
                    timestamp BOOLEAN DEFAULT 0,
                    verbose BOOLEAN DEFAULT 0,
                    visible BOOLEAN DEFAULT 0,
                    wait_between_scroll INTEGER,
                    wait_first_load INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    auto_timestamped_dir BOOLEAN DEFAULT 0,
                    base_output_dir TEXT,
                    parameter_overrides TEXT,  -- JSON object
                    environment_variables TEXT,  -- JSON object
                    task_order TEXT,  -- JSON array of task IDs
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS batch_tasks (
                    batch_id INTEGER,
                    task_id INTEGER,
                    FOREIGN KEY (batch_id) REFERENCES batches (id) ON DELETE CASCADE,
                    FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
                    PRIMARY KEY (batch_id, task_id)
                )
            """)

    def save_task(self, task: Task) -> int:
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now()
            if task.id is None:
                cursor = conn.execute(
                    """
                    INSERT INTO tasks (
                        name, db, debug_outdir, gemini, local_files, logfile,
                        min_area, min_size, no_safe_search, num_images, outdir,
                        paths, queries, randomize, threads, timestamp, verbose,
                        visible, wait_between_scroll, wait_first_load, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        task.name,
                        task.db,
                        task.debug_outdir,
                        json.dumps(task.gemini) if task.gemini else None,
                        json.dumps(task.local_files) if task.local_files else None,
                        task.logfile,
                        task.min_area,
                        task.min_size,
                        task.no_safe_search,
                        task.num_images,
                        task.outdir,
                        json.dumps(task.paths) if task.paths else None,
                        task.queries,
                        task.randomize,
                        task.threads,
                        task.timestamp,
                        task.verbose,
                        task.visible,
                        task.wait_between_scroll,
                        task.wait_first_load,
                        now,
                        now,
                    ),
                )
                task.id = cursor.lastrowid
            else:
                conn.execute(
                    """
                    UPDATE tasks SET
                        name=?, db=?, debug_outdir=?, gemini=?, local_files=?, logfile=?,
                        min_area=?, min_size=?, no_safe_search=?, num_images=?, outdir=?,
                        paths=?, queries=?, randomize=?, threads=?, timestamp=?, verbose=?,
                        visible=?, wait_between_scroll=?, wait_first_load=?, updated_at=?
                    WHERE id=?
                """,
                    (
                        task.name,
                        task.db,
                        task.debug_outdir,
                        json.dumps(task.gemini) if task.gemini else None,
                        json.dumps(task.local_files) if task.local_files else None,
                        task.logfile,
                        task.min_area,
                        task.min_size,
                        task.no_safe_search,
                        task.num_images,
                        task.outdir,
                        json.dumps(task.paths) if task.paths else None,
                        task.queries,
                        task.randomize,
                        task.threads,
                        task.timestamp,
                        task.verbose,
                        task.visible,
                        task.wait_between_scroll,
                        task.wait_first_load,
                        now,
                        task.id,
                    ),
                )
            conn.commit()
            return task.id

    def get_task(self, task_id: int) -> Optional[Task]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_task(row)
            return None

    def get_all_tasks(self) -> List[Task]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM tasks ORDER BY name")
            return [self._row_to_task(row) for row in cursor.fetchall()]

    def delete_task(self, task_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            conn.commit()

    def save_batch(self, batch: Batch) -> int:
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now()
            if batch.id is None:
                cursor = conn.execute(
                    """
                    INSERT INTO batches (
                        name, auto_timestamped_dir, base_output_dir,
                        parameter_overrides, environment_variables, task_order,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        batch.name,
                        batch.auto_timestamped_dir,
                        batch.base_output_dir,
                        json.dumps(batch.parameter_overrides)
                        if batch.parameter_overrides
                        else None,
                        json.dumps(batch.environment_variables)
                        if batch.environment_variables
                        else None,
                        json.dumps(batch.task_order) if batch.task_order else None,
                        now,
                        now,
                    ),
                )
                batch.id = cursor.lastrowid
            else:
                conn.execute(
                    """
                    UPDATE batches SET
                        name=?, auto_timestamped_dir=?, base_output_dir=?,
                        parameter_overrides=?, environment_variables=?, task_order=?,
                        updated_at=?
                    WHERE id=?
                """,
                    (
                        batch.name,
                        batch.auto_timestamped_dir,
                        batch.base_output_dir,
                        json.dumps(batch.parameter_overrides)
                        if batch.parameter_overrides
                        else None,
                        json.dumps(batch.environment_variables)
                        if batch.environment_variables
                        else None,
                        json.dumps(batch.task_order) if batch.task_order else None,
                        now,
                        batch.id,
                    ),
                )
            conn.commit()
            return batch.id

    def get_batch(self, batch_id: int) -> Optional[Batch]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM batches WHERE id=?", (batch_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_batch(row)
            return None

    def get_all_batches(self) -> List[Batch]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM batches ORDER BY name")
            return [self._row_to_batch(row) for row in cursor.fetchall()]

    def delete_batch(self, batch_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM batches WHERE id=?", (batch_id,))
            conn.commit()

    def add_task_to_batch(self, batch_id: int, task_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO batch_tasks (batch_id, task_id) VALUES (?, ?)",
                (batch_id, task_id),
            )
            conn.commit()

    def remove_task_from_batch(self, batch_id: int, task_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM batch_tasks WHERE batch_id=? AND task_id=?",
                (batch_id, task_id),
            )
            conn.commit()

    def get_batch_tasks(self, batch_id: int) -> List[Task]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT t.* FROM tasks t
                JOIN batch_tasks bt ON t.id = bt.task_id
                WHERE bt.batch_id = ?
                ORDER BY t.name
            """,
                (batch_id,),
            )
            return [self._row_to_task(row) for row in cursor.fetchall()]

    def _row_to_task(self, row) -> Task:
        return Task(
            id=row[0],
            name=row[1],
            db=row[2],
            debug_outdir=row[3],
            gemini=json.loads(row[4]) if row[4] else None,
            local_files=json.loads(row[5]) if row[5] else None,
            logfile=row[6],
            min_area=row[7],
            min_size=row[8],
            no_safe_search=bool(row[9]),
            num_images=row[10],
            outdir=row[11],
            paths=json.loads(row[12]) if row[12] else None,
            queries=row[13],
            randomize=bool(row[14]),
            threads=row[15],
            timestamp=bool(row[16]),
            verbose=bool(row[17]),
            visible=bool(row[18]),
            wait_between_scroll=row[19],
            wait_first_load=row[20],
            created_at=datetime.fromisoformat(row[21]) if row[21] else None,
            updated_at=datetime.fromisoformat(row[22]) if row[22] else None,
        )

    def _row_to_batch(self, row) -> Batch:
        return Batch(
            id=row[0],
            name=row[1],
            auto_timestamped_dir=bool(row[2]),
            base_output_dir=row[3],
            parameter_overrides=json.loads(row[4]) if row[4] else None,
            environment_variables=json.loads(row[5]) if row[5] else None,
            task_order=json.loads(row[6]) if row[6] else None,
            created_at=datetime.fromisoformat(row[7]) if row[7] else None,
            updated_at=datetime.fromisoformat(row[8]) if row[8] else None,
        )
