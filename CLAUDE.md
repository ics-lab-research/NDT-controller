# NDT Controller — Project Guide

## What this project is

An AI-powered controller for a **Pulsed Eddy Current Testing (PECT)** lab. The user chats with an LLM agent via a Gradio web UI; the agent interprets natural language commands and controls a **LabVIEW VI** (`.vi` file) to run NDT scans on physical hardware.

## How to run

```bash
uv run ndt          # launch Gradio UI (opens browser)
```

Entry point: `src/main.py` → `create_main_interface()` (Gradio).
Config: `config.toml` (paths, model names, log level, dry_run flag).
Secrets: `.env` file (API keys, `LOG_LEVEL`, `DRY_RUN`).

## Architecture overview

```
User (chat)
    │
    ▼
src/gui/                      ← Gradio UI (chat + experiment tab)
    │
    ▼
src/agents/                   ← LLM agent pipeline
  experiment.py               ← top-level orchestration (handle_experiment_mode)
  experiment_api.py           ← BAML function wrappers (call_exp_router, etc.)
  experiment_planning.py      ← saves plans to JSON
  experiment_execution.py     ← executes tools against LabVIEW
  experiment_dry_run.py       ← dry-run simulation
    │
    ▼
src/baml_src/                 ← BAML prompt definitions (source of truth for LLM calls)
  exp_router.baml             ← classifies intent → ExpAction
  exp_orchestrator.baml       ← parses scan params → list of Experiment structs
  exp_planner.baml            ← creates abstract step-by-step plan
  exp_executor.baml           ← converts plan → concrete LabVIEW tool calls
  exp_basic_executor.baml     ← direct hardware commands (no planning)
  models.baml                 ← shared types (Experiment, State, ExpAction, etc.)
  exp_tools.baml / tools.baml ← LabVIEW tool schemas
    │
    ▼ (auto-generated, do not edit)
src/baml_client/              ← generated Python client from BAML source
    │
    ▼
src/tools/labview_controller/ ← low-level LabVIEW automation (pywinauto + win32)
  labview_api.py
  labview_controller.py
  open_vi.py
  windows_dialog_handler.py
```

## LLM pipeline (experiment mode)

1. **ExpRouter** — classifies user message into `BASIC_CONTROL | SINGLE_SCAN | MULTIPLE_SCAN | ASK_CLARIFICATION`
2. **ExpOrchestrator** — parses reformatted message into `ExpOrchestratorOutput` (list of `Experiment` structs with grid, signal params, offsets, filenames)
3. **ExpPlanner** — takes an `Experiment` + current `State` → returns an abstract natural-language plan
4. **ExpExecutor** — converts the abstract plan → list of typed LabVIEW tool calls (`ExperimentStep[]`)
5. **execute_tool** — runs each tool call against the real LabVIEW VI (or simulates in dry-run mode)

For `BASIC_CONTROL`, steps 2–3 are skipped; **ExpBasicExecutor** converts the command directly to tool calls.

## Key data models (`src/core/models.py` + `src/baml_src/models.baml`)

| Model | Description |
|---|---|
| `Experiment` | Single scan: grid (rows×cols), signal params, offset, filename |
| `ExperimentPlan` | Resolved plan: id, filename, `ExperimentStep[]`, status |
| `ExperimentStatus` | NOT_STARTED / PENDING / SCANNING / RESCAN / COMPLETED / ERROR |
| `State` | `current_position` + `home_position` (RelativeOffset x/y/z mm) |
| `AgentResponse` | Streamed response chunks: response / intermediate_step / status / action |
| `Mode` | IDEA / EXPERIMENT / DATA_SCIENCE / REPORTING |

## Project context (`src/core/`)

- **`ProjectManager`** — facade: holds `ModeManager`, `PathManager`, `StateManager`
- **`StateManager`** — tracks current scanner position (`State`) and multimodal uploads
- **`ModeManager`** — switches between modes, lazy-loads metadata per mode
- **`PathManager`** — ensures required directories exist

## BAML

BAML files live in `src/baml_src/`. After editing `.baml` files, regenerate the client:

```bash
uv run baml-cli generate
```

Never manually edit files in `src/baml_client/` — they are auto-generated.

## Configuration (`config.toml`)

```toml
[paths]
experiment_dir = "EXPERIMENT"   # workspace root for experiments

[experiment]
vi_path = "..."                  # path to the LabVIEW VI file
plans = "labview_experiment_plans.json"

[models]
exp_router = "openrouter/google/gemini-3-flash-preview"
# ... one model key per agent role

[logging]
baml_log = "info"
log_level = "debug"
dry_run = false                  # set true to skip real LabVIEW calls
```

## Dry run mode

Set `dry_run = true` in `config.toml` (or `DRY_RUN=true` in `.env`) to simulate tool execution without touching hardware.

## Code style

See CODESTYLE.md for all coding principles (functional, no OOP, loguru logging, etc.).
