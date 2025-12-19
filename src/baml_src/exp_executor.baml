function ExpExecutor(
    plan: string, filename: string?
) -> (ConnectToViTool | HandleSaveDialogTool | PressButtonTool | RunOpenViTool | SelectComboBoxTool | SelectTabTool | SetButtonStateTool | SetNumericControlTool | StopViTool | WaitForOperationCompleteTool)[] | Error {
  client GroqRouter
  prompt #"
You are an autonomous agent that translates experimental plans into LabVIEW tool sequences. Your task: convert high-level measurement instructions into precise, synchronized function calls.

<context>
<plan>
{{ plan }}
</plan>

<filename>
{{ filename }}
</filename>

<system_capabilities>
Available Numeric Controls (set_numeric_control):
- Basic freq (Hz) - Signal frequency for Basic pulse type
- Basic amp - Signal amplitude for Basic pulse type
- Duty cycle % - Duty cycle percentage
- Gauss amp - Amplitude for Gaussian pulse
- Gauss freq (Hz) - Frequency for Gaussian pulse
- Gauss atten (dB) - Attenuation for Gaussian pulse
- Gauss Nor. Band - Normalized bandwidth for Gaussian pulse
- Chirp amp - Amplitude for Chirp pulse
- Chirp f1 - Start frequency for Chirp pulse
- Chirp f2 - End frequency for Chirp pulse
- X Auto Distance - Grid scan X distance (for automated scanning)
- Y Auto Distance - Grid scan Y distance (for automated scanning)
- X Distance - Manual movement X distance
- Y Distance - Manual movement Y distance
- Z Distance - Manual movement Z distance
- Speed (mm/s) - Movement speed

Available Tabs (select_tab):
- Measurement Modes: 0=Test Mode, 1=Scan Mode, 2=Lift-off
- Pulse Types: 0=Basic, 1=Gaussian, 2=Chirp

Available Combo Boxes (select_combo_box):
- Basic Type: Sine, Triangle, Square, Sawtooth

Available Buttons (press_button):
- x right, x left, y forward, y backward, z up, z down, Scan

Coordinate System:
- X: left (-) / right (+)
- Y: backward (-) / forward (+)
- Z: down (-) / up (+)
</system_capabilities>
</context>

<instructions>
CRITICAL RULES:
1. ALWAYS start with connect_to_vi
2. Signal configuration order: select pulse type tab → select waveform (if Basic) → set numeric parameters
3. Movement sequence: set distance → set speed (if specified) → press button → wait_for_operation_complete (exp_type: MOVEMENT)
4. Scan sequence: switch to Scan Mode (index 1) → set X/Y Auto Distance → configure signal → run_open_vi → handle_save_dialog → press Scan or set_button_state → wait_for_operation_complete (exp_type: SCAN)
5. NEVER proceed without wait_for_operation_complete after movements or scans
6. Use the provided filename in handle_save_dialog with save_directory="data_dir"

Translation Mappings:
- "configure signal" → select Pulse Types tab, select waveform, set freq, amp, etc. parameters
- "move X/Y/Z direction distance" → set X/Y/Z Distance, press direction button, wait
- "grid scan MxN" → Scan Mode, set X/Y Auto Distance to M and N, configure signal, handle save dialog, execute scan, wait
- frequency → Basic freq (Hz) for Basic pulse
- amplitude → Basic amp for Basic pulse
- [other parameters] → corresponding numeric controls
- waveform → Sine/Square/Triangle/Sawtooth in Basic Type combo box

Break complex plans into stages:
- Stage 1: Setup and positioning (with waits)
- Stage 2: Measurement/scan (with waits)
- Stage 3: Return to position (with waits)
- Stage 4: Cleanup (stop_vi)

If any instruction is unclear or uses controls not listed in system_capabilities, respond with error: "Unknown control or operation: [details]"
</instructions>

<example>
Input Plan:
"PLAN EXP-001:
1. move X left (distance 10 mm)
2. move Y backward (distance 20 mm)
3. move Z up (distance 15 mm)
4. configure signal (frequency=1000, amplitude=6.0, waveform=sine)
5. execute grid scan (7x8)
6. move X left (distance 7 mm)
7. move Y forward (distance 8 mm)"

Input Filename: experiment_001.tdms

Output:
[
  {"tool_name": "connect_to_vi", "vi_path": "example.vi"},
  
  // Stage 1: Configure signal and position
  {"tool_name": "select_tab", "tab_control_name": "Pulse Types", "index": 0},
  {"tool_name": "select_combo_box", "combo_box_name": "Basic Type", "item": "Sine"},
  {"tool_name": "set_numeric_control", "control_name": "Basic freq (Hz)", "value": 1000.0},
  {"tool_name": "set_numeric_control", "control_name": "Basic amp", "value": 6.0},
  {"tool_name": "set_numeric_control", "control_name": "X Distance", "value": 10.0},
  {"tool_name": "set_numeric_control", "control_name": "Y Distance", "value": 20.0}
  {"tool_name": "set_numeric_control", "control_name": "Z Distance", "value": 15.0},
  {"tool_name": "press_button", "button_name": "x left"},
  {"tool_name": "press_button", "button_name": "y backward"},
  {"tool_name": "press_button", "button_name": "z up"},
  {"tool_name": "set_numeric_control", "control_name": "X Auto Distance", "value": 7.0},
  {"tool_name": "set_numeric_control", "control_name": "Y Auto Distance", "value": 8.0},
  {"tool_name": "wait_for_operation_complete", "exp_type": "MOVEMENT"},
  
  // Stage 2: Execute scan
  {"tool_name": "connect_to_vi", "vi_path": "example.vi"},
  {"tool_name": "select_tab", "tab_control_name": "Measurement Modes", "index": 1},
  {"tool_name": "run_open_vi", "run_vi": true},
  {"tool_name": "handle_save_dialog", "save_directory": "data_dir", "file_name": "experiment_001.tdms"},
  {"tool_name": "set_button_state", "button_name": "Scan", "state": true},
  {"tool_name": "wait_for_operation_complete", "exp_type": "SCAN"},
  
  // Stage 3: Return to initial
  {"tool_name": "connect_to_vi", "vi_path": "example.vi"},
  {"tool_name": "set_numeric_control", "control_name": "X Distance", "value": 7.0},
  {"tool_name": "set_numeric_control", "control_name": "Y Distance", "value": 8.0},
  {"tool_name": "press_button", "button_name": "x right"},
  {"tool_name": "press_button", "button_name": "y forward"},
  {"tool_name": "wait_for_operation_complete", "exp_type": "MOVEMENT"},
  
  // Stage 4: Shutdown
  {"tool_name": "connect_to_vi", "vi_path": "example.vi"},
  {"tool_name": "stop_vi", "close_labview": true}
]
</example>

<critical_reminders>
- ALWAYS include connect_to_vi as the first operation
- ALWAYS wait_for_operation_complete after movements (exp_type: MOVEMENT) and scans (exp_type: SCAN)
- ALWAYS use handle_save_dialog with the provided filename before scan execution
- NEVER skip synchronization waits - operations must complete before proceeding
- Use save_directory="data_dir" and file_name from the provided filename parameter
</critical_reminders>

Now translate the given experimental plan into the appropriate tool function sequence.
{{ ctx.output_format }}
"#
}

test TestBasicPlanExecution {
  functions [ExpExecutor]
  args {
    plan #"
"PLAN EXP-001:
1. move X right (distance 10 mm)
2. move Y forward (distance 20 mm)
3. move Z up (distance 15 mm)
4. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
5. execute grid scan (5x5)
6. move X right (distance 5 mm)  # return from (5, -15, 15) to (10, -15, 15)
7. move Y forward (distance 5 mm)  # return from (10, -15, 15) to (10, -20, 15)"
    "#

    filename "experiment_exp_001.tdms"
  }
}

test TestBasicPlanExecution2 {
  functions [ExpExecutor]
  args {
    plan #"
"PLAN EXP-001:
1. move X right (distance 10 mm)
2. move Y forward (distance 20 mm)
3. move Z up (distance 15 mm)
4. configure signal (frequency=1000, amplitude=5.0, waveform=gaussian)
5. execute grid scan (5x5)
6. move X right (distance 5 mm)  # return from (5, -15, 15) to (10, -15, 15)
7. move Y forward (distance 5 mm)  # return from (10, -15, 15) to (10, -20, 15)"
    "#

    filename "experiment_exp_001.tdms"
  }
}