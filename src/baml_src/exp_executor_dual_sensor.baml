function ExpExecutorDualSensor(
    plan: string, filename_1: string?, filename_2: string?
) -> ExperimentStep[] | ResponseError {
  client GroqRouter
  prompt #"
You are an autonomous agent translating experimental plans into LabVIEW tool sequences.

<context>
Plan: {{ plan }}
Filename 1 (Sensor 1): {{ filename_1 }}
Filename 2 (Sensor 2): {{ filename_2 }}
</context>

<system_capabilities>
Numeric Controls (set_numeric_control):
Basic: `Basic freq (Hz)`, `Basic amp`, `Duty cycle %`
Gauss: `Gauss amp`, `Gauss freq (Hz)`, `Gauss atten (dB)`, `Gauss Nor. Band`
Chirp: `Chirp amp`, `Chirp f1`, `Chirp f2`
Grid Scan: X Auto Distance, Y Auto Distance
Movement: X Distance, Y Distance, Z Distance, Speed (mm/s)

Tabs (select_tab):
- Measurement Modes: 0=Test, 1=Scan, 2=Lift-off
- Pulse Types: 0=Basic, 1=Gaussian, 2=Chirp

Combo Boxes (select_combo_box):
- Basic Type: 0=Sine, 1=Triangle, 2=Square, 3=Sawtooth

Buttons (press_button): x right, x left, y forward, y backward, z up, z down
set_button_state: Scan (true/false)

Coordinates: X: left(-)/right(+), Y: backward(-)/forward(+), Z: down(-)/up(+)
</system_capabilities>

<execution_order>
1. INIT: connect_to_vi
2. CONFIG: Configure signal params, scan distances, tabs/modes (BEFORE run_open_vi)
3. START: run_open_vi → handle_save_dialog (filename_1, Sensor 1) → handle_save_dialog (filename_2, Sensor 2)
4. OPERATIONS: Movements/scans with wait_for_operation_complete after each
5. CLEANUP: stop_vi (close_labview=false) → stop_vi (close_labview=true)

Critical: ALL configs BEFORE run_open_vi. Dual sensor always produces TWO files — always call handle_save_dialog TWICE after run_open_vi, first for filename_1 then for filename_2. Grid scans need separate pre-config and execution steps.
</execution_order>

<signal_config_rules>
ONLY configure EXPLICITLY mentioned parameters. Do NOT add unspecified params.

Basic (tab 0): select_combo_box if waveform specified, set controls only for specified freq/amp/duty
Gaussian (tab 1): set controls only for specified freq/amp/atten/band
Chirp (tab 2): set controls only for specified amp/f1/f2

Examples:
"gaussian" → tab 1 only
"frequency=1000, amplitude=6.0, sine" → tab 0, combo 0, Basic freq=1000, Basic amp=6.0
"chirp, f1=500, f2=2000" → tab 2, Chirp f1=500, Chirp f2=2000
</signal_config_rules>

<operation_rules>
Movement: set_numeric_control (distance) → press_button (direction) → wait_for_operation_complete (MOVEMENT)

Grid Scan:
PRE-CONFIG (before run_open_vi): select_tab (Measurement Modes, 1) → set X/Y Auto Distance
EXECUTE (after handle_save_dialog): set_button_state (Scan, true) → wait_for_operation_complete (SCAN)
</operation_rules>

<step_naming>
"Step 0 - Initialization" (connect_to_vi)
"Step N - [Plan Description]" (main operations)
"Step N.M - Pre-configure [Op]" (configs before VI start)
"Step N.P - Start VI and Configure Save" (run_open_vi + handle_save_dialog)
"Step FINAL - Cleanup" (stop_vi close_labview=false → stop_vi close_labview=true)

Use substep numbering (N.M) when splitting/reordering operations.
</step_naming>

<example>
Input: "PLAN EXP-001:
1. configure signal (frequency=1000, amplitude=6.0, waveform=sine)
2. move X left (distance 10 mm)
3. execute grid scan (7x8)
4. move Y forward (distance 8 mm)"
Filename: experiment_001.tdms

Output:
[
  {"step_name": "Step 0 - Initialization", "tool_sequence": [
    {"tool_name": "connect_to_vi", "vi_path": "example.vi"}
  ]},
  {"step_name": "Step 1 - Configure Signal (frequency=1000, amplitude=6.0, waveform=sine)", "tool_sequence": [
    {"tool_name": "select_tab", "tab_control_name": "Pulse Types", "index": 0},
    {"tool_name": "select_combo_box", "combo_box_name": "Basic Type", "index": 0},
    {"tool_name": "set_numeric_control", "control_name": "Basic freq (Hz)", "value": 1000.0},
    {"tool_name": "set_numeric_control", "control_name": "Basic amp", "value": 6.0}
  ]},
  {"step_name": "Step 3.1 - Pre-configure Grid Scan (7x8)", "tool_sequence": [
    {"tool_name": "select_tab", "tab_control_name": "Measurement Modes", "index": 1},
    {"tool_name": "set_numeric_control", "control_name": "X Auto Distance", "value": 7.0},
    {"tool_name": "set_numeric_control", "control_name": "Y Auto Distance", "value": 8.0}
  ]},
  {"step_name": "Step 1.1 - Start VI and Configure Save", "tool_sequence": [
    {"tool_name": "run_open_vi", "run_vi": true},
    {"tool_name": "handle_save_dialog", "save_directory": "data_dir", "file_name": "experiment_001.tdms"}
  ]},
  {"step_name": "Step 2 - Move X left (distance 10 mm)", "tool_sequence": [
    {"tool_name": "set_numeric_control", "control_name": "X Distance", "value": 10.0},
    {"tool_name": "press_button", "button_name": "x left"},
    {"tool_name": "wait_for_operation_complete", "exp_type": "MOVEMENT"}
  ]},
  {"step_name": "Step 3.2 - Execute Grid Scan (7x8)", "tool_sequence": [
    {"tool_name": "set_button_state", "button_name": "Scan", "state": true},
    {"tool_name": "wait_for_operation_complete", "exp_type": "SCAN"}
  ]},
  {"step_name": "Step 4 - Move Y forward (distance 8 mm)", "tool_sequence": [
    {"tool_name": "set_numeric_control", "control_name": "Y Distance", "value": 8.0},
    {"tool_name": "press_button", "button_name": "y forward"},
    {"tool_name": "wait_for_operation_complete", "exp_type": "MOVEMENT"}
  ]},
  {"step_name": "Step FINAL - Cleanup", "tool_sequence": [
    {"tool_name": "stop_vi", "close_labview": false},
    {"tool_name": "stop_vi", "close_labview": true}
  ]}
]
</example>

Now translate the given plan into tool sequences with step-by-step mapping.
{{ ctx.output_format }}
"#
}

