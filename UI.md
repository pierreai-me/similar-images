# Task Batch Manager

## **Core Concepts**
- **Tasks**: Equivalent to individual si.py executions with specific parameters. Basically when the app processes a task it needs to do the equivalent of what si.py does.
- **Batches**: Ordered collections of tasks that run sequentially
- **Tasks can belong to multiple batches** (many-to-many relationship)
- **Batch-level parameter overrides** for consistency across tasks

## **UI Layout - Three Panel Design**

### **Left Panel: Lists**
- **Top section**: Tasks list with "New Task" button in section header
- **Bottom section**: Batches list with "New Batch" button in section header
- **Selection behavior**: Click any item to show configuration in top-right
- **Context menus**: Right-click for "Run", "Delete", "Duplicate" operations

### **Top Right Panel: Configuration**
- **"Run Selected" button** at top of panel (enabled when an item is selected)
- **Task selected**: Form with exact si.py parameters mapped to UI controls
- **Batch selected**:
  - Batch name and settings
  - Auto-generate timestamped output directory option
  - Parameter overrides (number of threads, debug dir, etc.)
  - Environment variables (add/remove key-value pairs)
  - Task ordering area (drag-and-drop from left panel)
- **Auto-save**: Changes persist immediately
- **Nothing selected**: Welcome message or help text

### **Bottom Right Panel: Execution/Monitor**
- **"Stop" button** at top of panel
- **Three tabs**:
  - **Monitor**: Current execution status, progress bars, real-time logs
  - **Browser**: Embedded browser view (when running in visible mode)
  - **History**: Past execution results (future feature)
- **Shows results of current/last execution**

## **No Toolbar**
- All actions integrated into panel headers and context menus

## **Key Features**

### **Smart Directory Management**
- **Auto-timestamped batch directories (option)**: `{base_dir}/{YYYYMMDD_HHMMSS}/`
- **Task-specific subdirectories**: `{base_dir}/{timestamp}/{task_name}/`
- **Batch overrides**: All tasks in batch use the batch's output directory structure

### **Parameter System**
- **Exact mapping**: Every si.py parameter has corresponding UI control
- **Batch overrides**: Batch-level settings override individual task parameters
- **Environment variables**: Batch-level env vars applied to all tasks
- **Default values**: Save common settings to avoid repetitive input

### **Execution Flow**
- **Current execution only**: Focus on monitoring active batch/task
- **Real-time updates**: Progress bars, logs, status indicators
- **Browser integration**: Embedded view when running in visible mode
- **Sequential execution**: Tasks in batch run one after another

## **Technical Implementation**

### **Technology Stack**
- **PyQt**: Native Windows application framework
- **SQLite**: Local database for persistence
- **Embedded browser**: For visible mode display

### **Key Implementation Requirements**
1. **Parameter mapping**: Create UI controls for every si.py command-line argument
2. **Drag-and-drop**: Tasks can be dragged from left panel into batch configuration
3. **Auto-save**: All changes persist immediately to SQLite
4. **No process management**: Each task must create objects and call functions just like si.py does
5. **Browser embedding**: Show browser window within bottom-right panel
6. **Real-time logging**: Show logging to logging tab
