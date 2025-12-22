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
</context>

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
- Basic Type: 0=Sine, 1=Triangle, 2=Square, 3=Sawtooth

Available Buttons (press_button):
- x right, x left, y forward, y backward, z up, z down

set_button_state is ONLY for:
- Scan (state: true/false)

Coordinate System:
- X: left (-) / right (+)
- Y: backward (-) / forward (+)
- Z: down (-) / up (+)
</system_capabilities>
</context>

<instructions>
CRITICAL RULES:
1. ALWAYS start with connect_to_vi
2. Stage 1 (Setup): Configure ALL parameters first (measurement mode, signal configuration, distances) WITHOUT running VI
   - Switch to appropriate Measurement Mode (Scan Mode for scans)
   - Select pulse type tab
   - Select waveform (if Basic pulse type)
   - Set all numeric parameters (frequencies, amplitudes, distances)
3. Stage 2 onwards: Before ANY movement or scan operation, MUST start with:
   - run_open_vi (run_vi: true)
   - handle_save_dialog (save_directory: "data_dir", file_name: provided filename)
4. Movement sequence (after run_open_vi and handle_save_dialog):
   - Distance already set in Stage 1
   - press_button for direction
   - wait_for_operation_complete (exp_type: MOVEMENT)
5. Scan sequence (after run_open_vi and handle_save_dialog):
   - X/Y Auto Distance already set in Stage 1
   - Signal already configured in Stage 1
   - set_button_state (button_name: "Scan", state: true) - NEVER use press_button for Scan
   - wait_for_operation_complete (exp_type: SCAN)
6. ALWAYS include wait_for_operation_complete after movements and scans
7. ALWAYS reconnect with connect_to_vi before each new stage
8. ALWAYS end with stop_vi

Translation Mappings:
- "configure signal" → select Pulse Types tab, select waveform, set freq, amp, etc. parameters
- "move X/Y/Z direction distance" → set X/Y/Z Distance in Stage 1, then execute in later stage
- "grid scan MxN" → Scan Mode, set X/Y Auto Distance to M and N, configure signal in Stage 1, then execute in later stage
- frequency → Basic freq (Hz) for Basic pulse
- amplitude → Basic amp for Basic pulse
- waveform → Sine/Square/Triangle/Sawtooth in Basic Type combo box (Sine=0, Triangle=1, Square=2, Sawtooth=3)

Stage Structure:
- Stage 1: Setup - connect_to_vi, set measurement mode, configure signal, set ALL distances (no run_open_vi, no movements)
- Stage 2: Execution Preparation - connect_to_vi, run_open_vi, handle_save_dialog
- Stage 3: Movements - execute movements with waits (if plan has movements)
- Stage 4: Scan Operation - execute scan with wait (if plan has scan)
- Stage 5: Post-scan Movements - execute return movements with waits (if needed)
- Stage 6: Cleanup - connect_to_vi, stop_vi

If any instruction is unclear or uses controls not listed in system_capabilities, respond with error: "Unknown control or operation: [details]"
</instructions>

<example>
Input Plan:
"PLAN EXP-001:
1. configure signal (frequency=1000, amplitude=6.0, waveform=sine)
2. move X left (distance 10 mm)
3. move Y backward (distance 20 mm)
4. move Z up (distance 15 mm)
5. execute grid scan (7x8)
6. move X left (distance 7 mm)
7. move Y forward (distance 8 mm)"

Input Filename: experiment_001.tdms

Output:
[ 
  // Stage 1: Setup - Configure ALL parameters WITHOUT running VI
  {"tool_name": "connect_to_vi", "vi_path": "example.vi"}, // Connect to LabVIEW VI - ALWAYS FIRST
  {"tool_name": "select_tab", "tab_control_name": "Measurement Modes", "index": 1}, // Switch to Scan Mode for grid scanning
  {"tool_name": "select_tab", "tab_control_name": "Pulse Types", "index": 0}, // Select Basic pulse type
  {"tool_name": "select_combo_box", "combo_box_name": "Basic Type", "index": 0}, // Select Sine waveform (0=Sine, 1=Triangle, 2=Square, 3=Sawtooth)
  {"tool_name": "set_numeric_control", "control_name": "Basic freq (Hz)", "value": 1000.0}, // Set signal frequency to 1000 Hz
  {"tool_name": "set_numeric_control", "control_name": "Basic amp", "value": 6.0}, // Set signal amplitude to 6.0
  {"tool_name": "set_numeric_control", "control_name": "X Auto Distance", "value": 7.0}, // Set grid scan X distance to 7 (for 7x8 grid)
  {"tool_name": "set_numeric_control", "control_name": "Y Auto Distance", "value": 8.0}, // Set grid scan Y distance to 8 (for 7x8 grid)
  {"tool_name": "set_numeric_control", "control_name": "X Distance", "value": 10.0}, // Set X movement distance for later execution
  {"tool_name": "set_numeric_control", "control_name": "Y Distance", "value": 20.0}, // Set Y movement distance for later execution
  {"tool_name": "set_numeric_control", "control_name": "Z Distance", "value": 15.0}, // Set Z movement distance for later execution

  // Stage 2: Execution Preparation - Run VI and configure save dialog
  {"tool_name": "run_open_vi", "run_vi": true}, // Run the VI to enable operations - REQUIRED before any movement/scan
  {"tool_name": "handle_save_dialog", "save_directory": "data_dir", "file_name": "experiment_001.tdms"}, // Configure save location - REQUIRED before any movement/scan

  // Stage 3: Pre-scan Movements - Execute movements to target position
  {"tool_name": "connect_to_vi", "vi_path": "example.vi"}, // Reconnect to ensure VI state
  {"tool_name": "press_button", "button_name": "x left"}, // Execute X left movement (distance already set in Stage 1)
  {"tool_name": "wait_for_operation_complete", "exp_type": "MOVEMENT"}, // CRITICAL: Wait for X movement to complete
  {"tool_name": "press_button", "button_name": "y backward"}, // Execute Y backward movement (distance already set in Stage 1)
  {"tool_name": "wait_for_operation_complete", "exp_type": "MOVEMENT"}, // CRITICAL: Wait for Y movement to complete
  {"tool_name": "press_button", "button_name": "z up"}, // Execute Z up movement (distance already set in Stage 1)
  {"tool_name": "wait_for_operation_complete", "exp_type": "MOVEMENT"}, // CRITICAL: Wait for Z movement to complete

  // Stage 4: Scan Operation - Execute grid scan
  {"tool_name": "connect_to_vi", "vi_path": "example.vi"}, // Reconnect to ensure VI state
  {"tool_name": "set_button_state", "button_name": "Scan", "state": true}, // Start the scan operation - MUST use set_button_state, NOT press_button
  {"tool_name": "wait_for_operation_complete", "exp_type": "SCAN"}, // CRITICAL: Wait for scan to complete before proceeding

  // Stage 5: Post-scan Movements - Return movements to compensate
  {"tool_name": "connect_to_vi", "vi_path": "example.vi"}, // Reconnect for return movements
  {"tool_name": "set_numeric_control", "control_name": "X Distance", "value": 7.0}, // Set return X distance (step 6 in plan)
  {"tool_name": "press_button", "button_name": "x left"}, // Move X left as specified in step 6
  {"tool_name": "wait_for_operation_complete", "exp_type": "MOVEMENT"}, // Wait for X return movement
  {"tool_name": "set_numeric_control", "control_name": "Y Distance", "value": 8.0}, // Set return Y distance (step 7 in plan)
  {"tool_name": "press_button", "button_name": "y forward"}, // Move Y forward as specified in step 7
  {"tool_name": "wait_for_operation_complete", "exp_type": "MOVEMENT"}, // Wait for Y return movement

  // Stage 6: Cleanup - Stop VI and close LabVIEW
  {"tool_name": "connect_to_vi", "vi_path": "example.vi"}, // Final connection for cleanup
  {"tool_name": "stop_vi", "close_labview": true} // Stop VI and close LabVIEW - ALWAYS LAST
]
</example>

<critical_reminders>
- ALWAYS include connect_to_vi as the first operation
- Stage 1: Set ALL parameters (mode, signal, distances) WITHOUT running VI
- Before ANY movement or scan: MUST have run_open_vi and handle_save_dialog
- Movement/scan operations: ALWAYS follow with wait_for_operation_complete
- Scan button: MUST use set_button_state (button_name: "Scan", state: true), NEVER use press_button
- Use save_directory="data_dir" and file_name from the provided filename parameter
- Movement directions: X (left/right), Y (backward/forward), Z (down/up)
- Grid scan MxN means M steps in X direction, N steps in Y direction
- Reconnect with connect_to_vi before each major stage
- ALWAYS end with stop_vi
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
1. configure signal (frequency=1000, amplitude=5.0, waveform=triangle)
2. move X right (distance 10 mm)
3. move Y forward (distance 20 mm)
4. move Z up (distance 15 mm)
5. execute grid scan (5x5)
6. move X right (distance 5 mm) 
7. move Y forward (distance 5 mm)"
    "#

    filename "experiment_exp_001.tdms"
  }
}

test TestBasicPlanExecution2 {
  functions [ExpExecutor]
  args {
    plan #"
"PLAN EXP-002:
1. configure signal (frequency=1000, amplitude=5.0, waveform=gaussian)
2. move X right (distance 10 mm)
3. move Y forward (distance 20 mm)
5. execute grid scan (15x15)
6. move X right (distance 5 mm)
7. move Y forward (distance 10 mm)
8. move Z down (distance 30 mm)"
    "#

    filename "experiment_exp_002.tdms"
  }
}