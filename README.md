# Workflow Visualization

Flask-based workflow visualization tool with DAG (Directed Acyclic Graph) and timeline rendering, featuring an Excel-like interface for workflow task management.

## Features

- **Workflow DAG Visualization**: Interactive directed graph showing task dependencies with reversed arrows (task → dependency)
- **Timeline/Gantt Chart**: Visual representation of task schedules and timelines
- **Excel-style Table Interface**: Edit tasks with inline preview and modal popup editors
- **Task Management**: Create, edit, delete, and validate workflow tasks
- **Knowledge Base Integration**: Markdown-based documentation linked to workflow tasks
- **Section Filtering**: View tasks by section or all tasks combined
- **Data Validation**: Built-in workflow validation with cycle detection

## Installation

### Requirements

- Python >= 3.10
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
- Dependencies listed in `pyproject.toml`

### Setup

```bash
# Install dependencies using uv
uv sync

# Optional: Install Graphviz support for enhanced DAG layouts
uv sync --extra graphviz
```

### Dependencies

**Core:**
- Flask >= 3.0.0 - Web framework
- NetworkX >= 3.2.0 - Graph generation and layout
- Matplotlib >= 3.8.0 - Timeline/Gantt chart rendering
- Pandas >= 2.3.3 - Data manipulation
- Markdown >= 3.5.0 - Knowledge documentation rendering
- Pillow - Image processing
- python-dateutil >= 2.8.2 - Date parsing
- reportlab >= 4.0.0 - PDF generation support

**Optional:**
- pygraphviz >= 1.11 - Graphviz integration for improved DAG layouts

## Usage

### Running the Application

```bash
uv run miwada-test.py
```

The application will start on `http://127.0.0.1:5000`

On startup, the application automatically regenerates DAG and timeline images from the workflow data.

### Additional Tools

A Dash-based prototype is available in `test.py`:
```bash
uv run test.py
```
Runs on `http://127.0.0.1:8050`

## Application Structure

### File Organization

```
.
├── miwada-test.py          # Main Flask application
├── data/
│   └── workflow.json       # Workflow data (source of truth)
├── templates/
│   └── index.html          # Main UI template with modal editors
├── static/
│   ├── dag.png             # Generated DAG image
│   ├── timeline.png        # Generated timeline/Gantt chart
│   └── knowledge/          # Markdown documentation
│       ├── A/
│       │   └── form_a.md   # Task A knowledge base
│       └── B/
│           └── form_b.md   # Task B knowledge base
└── test.py                 # Dash prototype (separate app)
```

### Key Routes

- **`/`** (GET) - Main workflow visualization UI
  - Displays task table, DAG, and timeline
  - Query parameter: `?section=<section_name>` for filtering

- **`/update`** (POST) - Save workflow changes
  - Accepts JSON with workflow data
  - Validates and updates `workflow.json`

- **`/validate`** (GET) - Workflow validation endpoint
  - Checks for cycles and data consistency

- **`/dag.png`** (GET) - Serve generated DAG image
  - Regenerated on application startup

- **`/timeline.png`** (GET) - Serve generated timeline image
  - Regenerated on application startup

- **`/knowledge/<node_id>`** (GET) - Display knowledge documentation
  - Renders markdown files for specific workflow tasks

- **`/static/<path>`** (GET) - Serve static assets
  - Images, CSS, JavaScript, and knowledge files

## Workflow Data Format

The workflow is stored in `data/workflow.json` with the following structure:

```json
{
  "tasks": [
    {
      "id": "unique_id",
      "name": "Task Name",
      "section": "Section Name",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "doc": "Documentation text",
      "action": "Action description",
      "note": "Additional notes",
      "dependencies": ["dep_id_1", "dep_id_2"]
    }
  ]
}
```

## User Interface Features

### Modal Editing System

- Click on Doc/Action/Note preview cells to open full-screen modal editor
- Keyboard shortcuts:
  - `Esc` - Close modal without saving
  - Modal provides 300px textarea for comfortable editing

### Text Alignment

- All Doc/Action/Note fields use top-left alignment for better readability
- Preview cells show first 60px of content

### Section Filtering

- Dropdown selector to filter tasks by section
- "All Sections" option displays complete workflow
- DAG and timeline update dynamically based on selection

## Development

### Main Application Flow

1. **Startup**: `miwada-test.py` loads `workflow.json` and generates DAG/timeline images
2. **Rendering**: Flask serves HTML template with task data and embedded DAG SVG
3. **Editing**: User modifies tasks in Excel-like table interface
4. **Validation**: Client-side and server-side validation before saving
5. **Persistence**: POST to `/update` saves changes to `workflow.json`
6. **Regeneration**: Images regenerated on next application startup

### DAG Generation

- Uses NetworkX for graph structure
- Arrow direction: task → dependency (reversed from typical dependency graphs)
- Layout options:
  - Pygraphviz (dot layout) if available
  - Matplotlib fallback with spring layout

### Timeline Generation

- Matplotlib-based Gantt chart
- Color-coded by section
- Displays task duration and dependencies

## Known Limitations

- Images regenerated only on application startup (not on workflow updates)
- Knowledge files must follow naming convention: `static/knowledge/<node_id>/<filename>.md`
- Section filtering requires exact match of section names

## License

Internal tool for workflow visualization and management.
