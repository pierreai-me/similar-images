# Task Batch Manager

A PyQt5-based GUI application for managing and executing similar image search tasks in batches.

## Features

- **Task Management**: Create, edit, and organize individual si.py tasks with full parameter mapping
- **Batch Processing**: Group tasks into batches with sequential execution
- **Parameter Overrides**: Batch-level settings that override individual task parameters
- **Real-time Monitoring**: Progress tracking, logging, and execution status
- **Drag & Drop**: Reorder tasks within batches
- **Auto-timestamped Directories**: Automatic directory organization with timestamps
- **Browser Integration**: Embedded browser view for visible mode execution

## Installation

1. Install PyQt5 and dependencies:
```bash
pip install PyQt5 PyQtWebEngine
```

2. Install the existing project requirements:
```bash
pip install -r requirements.in
```

## Usage

### Starting the Application

```bash
python task_manager_app.py
```

### Interface Overview

The application has a three-panel layout:

#### Left Panel: Lists
- **Tasks List**: Shows all created tasks with "New Task" button
- **Batches List**: Shows all created batches with "New Batch" button
- **Context Menus**: Right-click tasks/batches for Run, Duplicate, Delete options

#### Top Right Panel: Configuration
- **Run Selected Button**: Execute the currently selected task or batch
- **Task Configuration**: When a task is selected, shows form with all si.py parameters
- **Batch Configuration**: When a batch is selected, shows:
  - Batch name and auto-timestamped directory option
  - Parameter overrides (JSON format)
  - Environment variables (KEY=value format)
  - Task ordering area (drag tasks from left panel)

#### Bottom Right Panel: Execution/Monitor
- **Stop Button**: Halt current execution
- **Monitor Tab**: Real-time progress, status, and logs
- **Browser Tab**: Embedded browser view (when running in visible mode)
- **History Tab**: Past execution results (future feature)

### Creating Tasks

1. Click "New Task" in the left panel
2. Enter a task name
3. Configure parameters in the right panel (maps directly to si.py parameters):
   - Database file path
   - Output directories
   - Image sources (local files, paths, queries)
   - Filter settings (Gemini, image size/area)
   - Browser settings (visible mode, wait times)
   - Execution settings (threads, verbosity)

### Creating Batches

1. Click "New Batch" in the left panel
2. Enter a batch name
3. Configure batch settings:
   - **Auto-timestamped directories**: Creates `{base_dir}/{YYYYMMDD_HHMMSS}/` structure
   - **Parameter overrides**: JSON object that overrides task parameters
   - **Environment variables**: Set env vars for all tasks in batch (e.g., `GEMINI_API_KEY=your_key_here`)
   - **Task order**: Drag tasks from left panel to reorder execution

### Parameter Mapping

All si.py command-line parameters are available in the GUI:

| si.py Parameter | GUI Control | Description |
|-----------------|-------------|-------------|
| `--db` | Database field | SQLite database path |
| `-D` | Debug Output Dir | Debug output directory |
| `-g` | Gemini Configs | Gemini filter config files |
| `-l` | Local Files | Local image files |
| `-L` | Log File | Log file path |
| `--min-area` | Min Area | Minimum image area |
| `--min-size` | Min Size | Minimum image dimensions |
| `--no-safe-search` | No Safe Search | Disable safe search |
| `-n` | Number of Images | Image count limit |
| `-o` | Output Dir | Output directory |
| `-p` | Image Paths | Image paths for similarity search |
| `-q` | Search Queries | Text search queries |
| `-r` | Randomize | Randomize image order |
| `-t` | Threads | Number of threads |
| `-T` | Add Timestamp | Add timestamp to paths |
| `-v` | Verbose | Verbose logging |
| `--visible` | Visible Browser | Show browser window |
| `--wait-between-scroll` | Wait Between Scroll | Scroll delay |
| `--wait-first-load` | Wait First Load | Initial load delay |

### Execution

- **Single Task**: Select a task and click "Run Selected"
- **Batch**: Select a batch and click "Run Selected"
- **Real-time Monitoring**: Watch progress in the Monitor tab
- **Stopping**: Click "Stop" to halt execution

### Data Persistence

All tasks and batches are automatically saved to a local SQLite database (`task_batch_manager.db`). Changes are persisted immediately as you edit.

## Technical Details

- **Framework**: PyQt5 with embedded WebEngine
- **Database**: SQLite for local persistence
- **Execution**: Threading for non-blocking GUI
- **Integration**: Direct function calls to existing si.py modules (no subprocess spawning)

## Directory Structure

```
task_manager/
├── __init__.py
├── database.py          # SQLite schema and data models
├── main_window.py       # Main application window
├── left_panel.py        # Tasks and batches lists
├── config_panel.py      # Configuration forms
└── execution_panel.py   # Execution monitoring and control
```