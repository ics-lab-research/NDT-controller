function ExpBasicExecutor(
    user_message: string,
) -> (ConnectToViTool | GetNumericIndicatorTool | GetViStatusTool | HandleSaveDialogTool | PressButtonTool | RunOpenViTool | SelectComboBoxTool | SelectTabTool | SetButtonStateTool | SetNumericControlTool | StopViTool )[] | Error {
  client GroqRouter
  prompt #"
You are an autonomous agent that translates user requests into LabVIEW tool function calls. Your task: interpret natural language instructions and convert them into precise LabVIEW operations.

<user_message>
{{ user_message }}
</user_message>

<available_tools>
Connection & Execution:
- connect_to_vi - Connect to a LabVIEW VI and open front panel (MUST BE FIRST)
- run_open_vi - Start VI execution
- handle_save_dialog - Configure data save location (REQUIRED after run_open_vi)
- stop_vi - Stop VI and optionally close LabVIEW

Numeric Controls (set_numeric_control):
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
- X Auto Distance - Grid scan X distance
- Y Auto Distance - Grid scan Y distance
- X Distance - Manual movement X distance
- Y Distance - Manual movement Y distance
- Z Distance - Manual movement Z distance
- Speed (mm/s) - Movement speed

Tab Controls (select_tab):
- Measurement Modes: 0=Test Mode, 1=Scan Mode, 2=Lift-off
- Pulse Types: 0=Basic, 1=Gaussian, 2=Chirp

Combo Boxes (select_combo_box):
- Basic Type: 0=Sine, 1=Triangle, 2=Square, 3=Sawtooth

Buttons (press_button):
- x right, x left, y forward, y backward, z up, z down

Button States (set_button_state):
- Scan (state: true/false) - Start/stop scanning

Indicators (Reading Values):
- get_numeric_indicator - Read value from numeric indicators

Coordinate System:
- X axis: left (-) / right (+)
- Y axis: backward (-) / forward (+)
- Z axis: down (-) / up (+)
</available_tools>

<translation_rules>
CRITICAL Execution Order:
1. ALWAYS start with connect_to_vi if not already connected
2. When running program (run_open_vi), MUST immediately follow with handle_save_dialog
3. Standard operation sequence: connect → configure → run → handle_save → operate

Basic Interaction Patterns:

Setting Controls:
- User says "set [control] to [value]" → set_numeric_control
- User says "change [control] to [value]" → set_numeric_control
- User says "select [tab/option]" → select_tab or select_combo_box

Pressing Buttons:
- User says "press [button]" → press_button
- User says "click [button]" → press_button
- User says "move [direction]" → press_button (for x left/right, y forward/backward, z up/down)
- User says "start scan" → set_button_state (Scan: true)
- User says "stop scan" → set_button_state (Scan: false)

Reading Indicators:
- User says "get [indicator]" → get_numeric_indicator, get_string_indicator, or get_boolean_indicator
- User says "read [indicator]" → appropriate get function
- User says "what is [indicator]" → appropriate get function

Program Control:
- User says "start" or "run" → run_open_vi THEN handle_save_dialog
- User says "stop" or "halt" → stop_vi
- User says "connect" → connect_to_vi

Execution Guidelines:
- For single operations, always prepend connect_to_vi if needed
- For multiple operations, return sequence of tool calls in order
- run_open_vi MUST be followed by handle_save_dialog
- Only use wait_for_operation_complete when user explicitly requests waiting or for movement/scan operations
</translation_rules>

<common_patterns>
User Says: "set speed to [X] mm/s"
→ connect_to_vi (if not connected)
→ set_numeric_control (Speed (mm/s): X)

User Says: "set frequency to [X] Hz"
→ connect_to_vi (if not connected)
→ set_numeric_control (Basic freq (Hz): X)

User Says: "press left button" or "move left"
→ connect_to_vi (if not connected)
→ press_button (button_name: x left)

User Says: "start scan"
→ connect_to_vi (if not connected)
→ set_button_state (button_name: Scan, state: true)

User Says: "get speed" or "what is speed"
→ connect_to_vi (if not connected)
→ get_numeric_indicator (indicator_name: Speed (mm/s))

User Says: "run program" or "start"
→ connect_to_vi (if not connected)
→ run_open_vi (run_vi: true)
→ handle_save_dialog (save_directory: "C:/LabVIEW_Data", file_name: "measurement_data.tdms")

User Says: "stop program" or "stop"
→ stop_vi (close_labview: false)

User Says: "change to sine wave"
→ connect_to_vi (if not connected)
→ select_combo_box (Basic Type: 0)

User Says: "switch to scan mode"
→ connect_to_vi (if not connected)
→ select_tab (Measurement Modes: 1)

User Says: "set frequency to [X] and amplitude to [Y]"
→ connect_to_vi (if not connected)
→ set_numeric_control (Basic freq (Hz): X)
→ set_numeric_control (Basic amp: Y)
</common_patterns>

<error_handling>
Return Error if:
- User mentions controls/indicators/operations not in available_tools
- Request is ambiguous and cannot be interpreted
- Required parameters are missing (e.g., value without specifying what to set)

Error format: {"error": "[Description of issue]"}
</error_handling>

<example>
User Request: "set speed to 30 mm/s"

Output:
[
  {"tool_name": "connect_to_vi", "vi_path": "path/to/vi.vi"},
  {"tool_name": "set_numeric_control", "control_name": "Speed (mm/s)", "value": 30.0}
]
</example>

<example>
User Request: "press the left button"

Output:
[
  {"tool_name": "connect_to_vi", "vi_path": "path/to/vi.vi"},
  {"tool_name": "press_button", "button_name": "x left"}
]
</example>

<example>
User Request: "what's the current speed?"

Output:
[
  {"tool_name": "connect_to_vi", "vi_path": "path/to/vi.vi"},
  {"tool_name": "get_numeric_indicator", "indicator_name": "Speed (mm/s)"}
]
</example>

<example>
User Request: "set frequency to 1000 Hz and amplitude to 5V"

Output:
[
  {"tool_name": "connect_to_vi", "vi_path": "path/to/vi.vi"},
  {"tool_name": "set_numeric_control", "control_name": "Basic freq (Hz)", "value": 1000.0},
  {"tool_name": "set_numeric_control", "control_name": "Basic amp", "value": 5.0}
]
</example>

<example>
User Request: "start the program"

Output:
[
  {"tool_name": "connect_to_vi", "vi_path": "path/to/vi.vi"},
  {"tool_name": "run_open_vi", "run_vi": true},
  {"tool_name": "handle_save_dialog", "save_directory": "C:/LabVIEW_Data", "file_name": "measurement_data.tdms"}
]
</example>

<example>
User Request: "move right 10mm"

Output:
[
  {"tool_name": "connect_to_vi", "vi_path": "path/to/vi.vi"},
  {"tool_name": "set_numeric_control", "control_name": "X Distance", "value": 10.0},
  {"tool_name": "press_button", "button_name": "x right"},
  {"tool_name": "wait_for_operation_complete", "exp_type": "MOVEMENT"}
]
</example>

Now translate the user's request into the appropriate LabVIEW tool function sequence.
{{ ctx.output_format }}
"#
}

test TestExpBasicExecutorInstructions {
  functions [ExpBasicExecutor]
  args {
    user_message "set speed to 30 mm/s"
   }
}