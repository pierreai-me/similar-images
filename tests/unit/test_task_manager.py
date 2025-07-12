import tempfile
import os
from task_manager.database import TaskBatchDatabase, Task, Batch


def test_task_crud():
    """Test basic CRUD operations for tasks."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_db:
        db_path = temp_db.name

    try:
        db = TaskBatchDatabase(db_path)

        # Create task
        task = Task(name="Test Task", queries="test query", num_images=10)
        task_id = db.save_task(task)
        assert task_id is not None
        assert task.id == task_id

        # Read task
        retrieved_task = db.get_task(task_id)
        assert retrieved_task is not None
        assert retrieved_task.name == "Test Task"
        assert retrieved_task.queries == "test query"
        assert retrieved_task.num_images == 10

        # Update task
        retrieved_task.name = "Updated Task"
        db.save_task(retrieved_task)
        updated_task = db.get_task(task_id)
        assert updated_task.name == "Updated Task"

        # List all tasks
        all_tasks = db.get_all_tasks()
        assert len(all_tasks) == 1
        assert all_tasks[0].name == "Updated Task"

        # Delete task
        db.delete_task(task_id)
        deleted_task = db.get_task(task_id)
        assert deleted_task is None

    finally:
        os.unlink(db_path)


def test_batch_crud():
    """Test basic CRUD operations for batches."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_db:
        db_path = temp_db.name

    try:
        db = TaskBatchDatabase(db_path)

        # Create batch
        batch = Batch(
            name="Test Batch",
            auto_timestamped_dir=True,
            base_output_dir="/tmp/test",
            parameter_overrides={"verbose": True},
            environment_variables={"TEST_VAR": "test_value"},
            task_order=[1, 2, 3],
        )
        batch_id = db.save_batch(batch)
        assert batch_id is not None
        assert batch.id == batch_id

        # Read batch
        retrieved_batch = db.get_batch(batch_id)
        assert retrieved_batch is not None
        assert retrieved_batch.name == "Test Batch"
        assert retrieved_batch.auto_timestamped_dir is True
        assert retrieved_batch.base_output_dir == "/tmp/test"
        assert retrieved_batch.parameter_overrides == {"verbose": True}
        assert retrieved_batch.environment_variables == {"TEST_VAR": "test_value"}
        assert retrieved_batch.task_order == [1, 2, 3]

        # Update batch
        retrieved_batch.name = "Updated Batch"
        retrieved_batch.task_order = [3, 2, 1]
        db.save_batch(retrieved_batch)
        updated_batch = db.get_batch(batch_id)
        assert updated_batch.name == "Updated Batch"
        assert updated_batch.task_order == [3, 2, 1]

        # List all batches
        all_batches = db.get_all_batches()
        assert len(all_batches) == 1
        assert all_batches[0].name == "Updated Batch"

        # Delete batch
        db.delete_batch(batch_id)
        deleted_batch = db.get_batch(batch_id)
        assert deleted_batch is None

    finally:
        os.unlink(db_path)


def test_batch_task_relationship():
    """Test many-to-many relationship between batches and tasks."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_db:
        db_path = temp_db.name

    try:
        db = TaskBatchDatabase(db_path)

        # Create tasks
        task1 = Task(name="Task 1", queries="query1")
        task2 = Task(name="Task 2", queries="query2")
        task1_id = db.save_task(task1)
        task2_id = db.save_task(task2)

        # Create batch
        batch = Batch(name="Test Batch", task_order=[task1_id, task2_id])
        batch_id = db.save_batch(batch)

        # Add tasks to batch
        db.add_task_to_batch(batch_id, task1_id)
        db.add_task_to_batch(batch_id, task2_id)

        # Get batch tasks
        batch_tasks = db.get_batch_tasks(batch_id)
        assert len(batch_tasks) == 2
        task_names = {task.name for task in batch_tasks}
        assert task_names == {"Task 1", "Task 2"}

        # Remove task from batch
        db.remove_task_from_batch(batch_id, task1_id)
        batch_tasks = db.get_batch_tasks(batch_id)
        assert len(batch_tasks) == 1
        assert batch_tasks[0].name == "Task 2"

    finally:
        os.unlink(db_path)


def test_task_parameter_serialization():
    """Test that task parameters are properly serialized/deserialized."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_db:
        db_path = temp_db.name

    try:
        db = TaskBatchDatabase(db_path)

        # Create task with complex parameters
        task = Task(
            name="Complex Task",
            gemini=["config1.json", "config2.json"],
            local_files=["file1.jpg", "file2.jpg"],
            paths=["path1", "path2"],
            min_size="800,600",
            no_safe_search=True,
            visible=True,
        )
        task_id = db.save_task(task)

        # Retrieve and verify
        retrieved_task = db.get_task(task_id)
        assert retrieved_task.gemini == ["config1.json", "config2.json"]
        assert retrieved_task.local_files == ["file1.jpg", "file2.jpg"]
        assert retrieved_task.paths == ["path1", "path2"]
        assert retrieved_task.min_size == "800,600"
        assert retrieved_task.no_safe_search is True
        assert retrieved_task.visible is True

    finally:
        os.unlink(db_path)