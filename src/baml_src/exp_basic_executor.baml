function ExpBasicExecutor(
    user_message: string,
) -> (ConnectToViTool | GetNumericIndicatorTool | GetViStatusTool | HandleSaveDialogTool | PressButtonTool | RunOpenViTool | SelectComboBoxTool | SelectTabTool | SetButtonStateTool | SetNumericControlTool | StopViTool )[] | ResponseError {
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
→ handle_save_dialog (save_directory: "data_dir", file_name: "example.tdms")

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

// ============================================================================
// BASIC CONTROL TESTS
// ============================================================================

test TestSetSpeed {
  functions [ExpBasicExecutor]
  args {
    user_message "set speed to 30 mm/s"
  }
}

test TestSetFrequency {
  functions [ExpBasicExecutor]
  args {
    user_message "set frequency to 1000 Hz"
  }
}

test TestSetAmplitude {
  functions [ExpBasicExecutor]
  args {
    user_message "change amplitude to 5"
  }
}

test TestSetDutyCycle {
  functions [ExpBasicExecutor]
  args {
    user_message "set duty cycle to 50%"
  }
}

// ============================================================================
// BUTTON PRESS TESTS
// ============================================================================

test TestPressLeftButton {
  functions [ExpBasicExecutor]
  args {
    user_message "press the left button"
  }
}

test TestMoveRight {
  functions [ExpBasicExecutor]
  args {
    user_message "move right"
  }
}

test TestClickForward {
  functions [ExpBasicExecutor]
  args {
    user_message "click forward"
  }
}

test TestMoveUp {
  functions [ExpBasicExecutor]
  args {
    user_message "move z up"
  }
}

// ============================================================================
// TAB AND COMBO BOX TESTS
// ============================================================================

test TestSwitchToScanMode {
  functions [ExpBasicExecutor]
  args {
    user_message "switch to scan mode"
  }
}

test TestSelectTestMode {
  functions [ExpBasicExecutor]
  args {
    user_message "change to test mode"
  }
}

test TestSelectGaussianPulse {
  functions [ExpBasicExecutor]
  args {
    user_message "select gaussian pulse type"
  }
}

test TestChangeToCosine {
  functions [ExpBasicExecutor]
  args {
    user_message "change basic type to sine"
  }
}

test TestSelectSquareWave {
  functions [ExpBasicExecutor]
  args {
    user_message "set to square wave"
  }
}

// ============================================================================
// BUTTON STATE TESTS
// ============================================================================

test TestStartScan {
  functions [ExpBasicExecutor]
  args {
    user_message "start scan"
  }
}

test TestStopScan {
  functions [ExpBasicExecutor]
  args {
    user_message "stop scan"
  }
}

test TestEnableScanning {
  functions [ExpBasicExecutor]
  args {
    user_message "enable scan button"
  }
}

// ============================================================================
// INDICATOR READING TESTS
// ============================================================================

test TestGetSpeed {
  functions [ExpBasicExecutor]
  args {
    user_message "get speed"
  }
}

test TestReadFrequency {
  functions [ExpBasicExecutor]
  args {
    user_message "what is the current frequency?"
  }
}

test TestCheckAmplitude {
  functions [ExpBasicExecutor]
  args {
    user_message "read amplitude value"
  }
}

// ============================================================================
// PROGRAM CONTROL TESTS
// ============================================================================

test TestStartProgram {
  functions [ExpBasicExecutor]
  args {
    user_message "start the program"
  }
}

test TestRunVI {
  functions [ExpBasicExecutor]
  args {
    user_message "run"
  }
}

test TestStopProgram {
  functions [ExpBasicExecutor]
  args {
    user_message "stop program"
  }
}

test TestHaltExecution {
  functions [ExpBasicExecutor]
  args {
    user_message "halt"
  }
}

test TestConnectToVI {
  functions [ExpBasicExecutor]
  args {
    user_message "connect to VI"
  }
}

// ============================================================================
// MULTIPLE OPERATION TESTS
// ============================================================================

test TestSetFrequencyAndAmplitude {
  functions [ExpBasicExecutor]
  args {
    user_message "set frequency to 1000 Hz and amplitude to 5V"
  }
}

test TestConfigureBasicPulse {
  functions [ExpBasicExecutor]
  args {
    user_message "set frequency to 500 Hz, amplitude to 3, and duty cycle to 60%"
  }
}

test TestConfigureGaussianParameters {
  functions [ExpBasicExecutor]
  args {
    user_message "set gaussian amplitude to 2 and frequency to 800 Hz"
  }
}

test TestSetupChirpPulse {
  functions [ExpBasicExecutor]
  args {
    user_message "configure chirp with start frequency 100 Hz and end frequency 1000 Hz"
  }
}

// ============================================================================
// MOVEMENT WITH DISTANCE TESTS
// ============================================================================

test TestMoveRightWithDistance {
  functions [ExpBasicExecutor]
  args {
    user_message "move right 10mm"
  }
}

test TestMoveLeftDistance {
  functions [ExpBasicExecutor]
  args {
    user_message "move left 5 millimeters"
  }
}

test TestMoveUpDistance {
  functions [ExpBasicExecutor]
  args {
    user_message "move z up 2mm"
  }
}

test TestMoveForwardAndRight {
  functions [ExpBasicExecutor]
  args {
    user_message "move forward 15mm and right 10mm"
  }
}

// ============================================================================
// GRID SCAN CONFIGURATION TESTS
// ============================================================================

test TestSetGridDistances {
  functions [ExpBasicExecutor]
  args {
    user_message "set X auto distance to 100 and Y auto distance to 50"
  }
}

test TestConfigureScanArea {
  functions [ExpBasicExecutor]
  args {
    user_message "configure scan area with X distance 200 and Y distance 150"
  }
}

// ============================================================================
// COMPLEX WORKFLOW TESTS
// ============================================================================

test TestCompleteSetupAndRun {
  functions [ExpBasicExecutor]
  args {
    user_message "connect, set frequency to 1000 Hz, set amplitude to 5, switch to scan mode, and run"
  }
}

test TestFullScanSequence {
  functions [ExpBasicExecutor]
  args {
    user_message "switch to scan mode, set X auto distance to 100, set Y auto distance to 100, and start scan"
  }
}

test TestMeasurementSetup {
  functions [ExpBasicExecutor]
  args {
    user_message "select gaussian pulse, set gauss amp to 3, set gauss freq to 500 Hz, and run program"
  }
}

// ====================================================== ERROR HANDLING TEST CASES ===============================================

test TestInvalidControl {
  functions [ExpBasicExecutor]
  args {
    user_message "set the voltage to 10V"
  }
}

test TestAmbiguousRequest {
  functions [ExpBasicExecutor]
  args {
    user_message "set it to 50"
  }
}

test TestMissingValue {
  functions [ExpBasicExecutor]
  args {
    user_message "set frequency"
  }
}

test TestUnknownButton {
  functions [ExpBasicExecutor]
  args {
    user_message "press the reset button"
  }
}

test TestInvalidMode {
  functions [ExpBasicExecutor]
  args {
    user_message "switch to debug mode"
  }
}

// ============================================================================
// NATURAL LANGUAGE VARIATIONS TESTS
// ============================================================================

test TestCasualLanguage {
  functions [ExpBasicExecutor]
  args {
    user_message "hey, can you set the speed to like 25?"
  }
}

test TestDetailedRequest {
  functions [ExpBasicExecutor]
  args {
    user_message "I need you to configure the basic frequency control to 1500 Hz"
  }
}

test TestShorthandRequest {
  functions [ExpBasicExecutor]
  args {
    user_message "freq 2000"
  }
}

test TestQuestionFormat {
  functions [ExpBasicExecutor]
  args {
    user_message "can you start the scan for me?"
  }
}

// ============================================================================
// SPECIFIC PULSE TYPE TESTS
// ============================================================================

test TestBasicPulseConfiguration {
  functions [ExpBasicExecutor]
  args {
    user_message "select basic pulse, set to sawtooth, frequency 750 Hz, amplitude 4"
  }
}

test TestGaussianPulseConfiguration {
  functions [ExpBasicExecutor]
  args {
    user_message "switch to gaussian pulse, set attenuation to 20 dB, normalized bandwidth to 0.5"
  }
}

test TestChirpPulseConfiguration {
  functions [ExpBasicExecutor]
  args {
    user_message "select chirp pulse, set amplitude 3, start frequency 50 Hz, end frequency 2000 Hz"
  }
}

// ============================================================================
// COORDINATE SYSTEM TESTS
// ============================================================================

test TestPositiveXMovement {
  functions [ExpBasicExecutor]
  args {
    user_message "move in positive X direction"
  }
}

test TestNegativeYMovement {
  functions [ExpBasicExecutor]
  args {
    user_message "move in negative Y direction"
  }
}

test TestZAxisUp {
  functions [ExpBasicExecutor]
  args {
    user_message "move up along Z axis by 3mm"
  }
}

// ============================================================================
// SPEED AND TIMING TESTS
// ============================================================================

test TestSetMovementSpeed {
  functions [ExpBasicExecutor]
  args {
    user_message "set movement speed to 15 mm per second"
  }
}

test TestFastSpeed {
  functions [ExpBasicExecutor]
  args {
    user_message "change speed to 50 mm/s"
  }
}

test TestSlowSpeed {
  functions [ExpBasicExecutor]
  args {
    user_message "set speed to 5 mm/s for precise movement"
  }
}

// ============================================================================
// ERROR HANDLING TEST CASES
// ============================================================================

// ----------------------------------------------------------------------------
// Category 1: Unknown Controls/Indicators/Operations
// ----------------------------------------------------------------------------

test TestUnknownControl {
  functions [ExpBasicExecutor]
  args {
    user_message "set voltage to 12V"
  }
  // Expected: Error - "voltage" is not in available_tools
}

test TestUnknownIndicator {
  functions [ExpBasicExecutor]
  args {
    user_message "get temperature reading"
  }
  // Expected: Error - "temperature" indicator not in available_tools
}

test TestUnknownButton2 {
  functions [ExpBasicExecutor]
  args {
    user_message "press the emergency stop button"
  }
  // Expected: Error - "emergency stop" button not in available_tools
}

test TestUnknownOperation {
  functions [ExpBasicExecutor]
  args {
    user_message "calibrate the system"
  }
  // Expected: Error - "calibrate" operation not in available_tools
}

test TestInvalidTabOption {
  functions [ExpBasicExecutor]
  args {
    user_message "switch to advanced mode"
  }
  // Expected: Error - "advanced mode" is not a valid tab option
}

test TestInvalidComboBoxOption {
  functions [ExpBasicExecutor]
  args {
    user_message "set waveform to cosine"
  }
  // Expected: Error - "cosine" is not in Basic Type options (Sine, Triangle, Square, Sawtooth)
}

// ----------------------------------------------------------------------------
// Category 2: Ambiguous Requests
// ----------------------------------------------------------------------------

test TestAmbiguousDirection {
  functions [ExpBasicExecutor]
  args {
    user_message "move the stage"
  }
  // Expected: Error - Direction not specified (left/right/forward/backward/up/down)
}

test TestAmbiguousParameter {
  functions [ExpBasicExecutor]
  args {
    user_message "set it to 50"
  }
  // Expected: Error - "it" is ambiguous, control name not specified
}

test TestAmbiguousFrequency {
  functions [ExpBasicExecutor]
  args {
    user_message "change frequency"
  }
  // Expected: Error - No value specified for frequency
}

test TestAmbiguousGet {
  functions [ExpBasicExecutor]
  args {
    user_message "get the current value"
  }
  // Expected: Error - Which indicator/value not specified
}

test TestAmbiguousPulseType {
  functions [ExpBasicExecutor]
  args {
    user_message "set amplitude to 5"
  }
  // Expected: Error - Ambiguous which amplitude (Basic amp, Gauss amp, or Chirp amp)
}

test TestVagueInstruction {
  functions [ExpBasicExecutor]
  args {
    user_message "do something with the scan"
  }
  // Expected: Error - Request too vague to interpret
}

// ----------------------------------------------------------------------------
// Category 3: Missing Required Parameters
// ----------------------------------------------------------------------------

test TestMissingValueForControl {
  functions [ExpBasicExecutor]
  args {
    user_message "set speed"
  }
  // Expected: Error - Value missing for set_numeric_control
}

test TestMissingControlName {
  functions [ExpBasicExecutor]
  args {
    user_message "set to 100 Hz"
  }
  // Expected: Error - Control name not specified
}

test TestMissingDistance {
  functions [ExpBasicExecutor]
  args {
    user_message "move right"
  }
  // Expected: Error - Distance value missing for movement
}

test TestMissingButtonName {
  functions [ExpBasicExecutor]
  args {
    user_message "press button"
  }
  // Expected: Error - Button name not specified
}

test TestMissingTabSelection {
  functions [ExpBasicExecutor]
  args {
    user_message "select tab"
  }
  // Expected: Error - Tab name/mode not specified
}

test TestMissingIndicatorName {
  functions [ExpBasicExecutor]
  args {
    user_message "read indicator"
  }
  // Expected: Error - Indicator name not specified
}

// ----------------------------------------------------------------------------
// Category 4: Invalid Parameter Values
// ----------------------------------------------------------------------------

test TestInvalidNumericValue {
  functions [ExpBasicExecutor]
  args {
    user_message "set speed to fast"
  }
  // Expected: Error - "fast" is not a numeric value
}

test TestNegativeSpeed {
  functions [ExpBasicExecutor]
  args {
    user_message "set speed to -50 mm/s"
  }
  // Expected: Error or handle gracefully - negative speed may be invalid
}

test TestInvalidDutyCycle {
  functions [ExpBasicExecutor]
  args {
    user_message "set duty cycle to 150%"
  }
  // Expected: Error - duty cycle should be 0-100%
}

test TestInvalidTabIndex {
  functions [ExpBasicExecutor]
  args {
    user_message "select tab 5 in measurement modes"
  }
  // Expected: Error - Tab index 5 doesn't exist (only 0-2 available)
}

// ----------------------------------------------------------------------------
// Category 5: Conflicting or Nonsensical Requests
// ----------------------------------------------------------------------------

test TestConflictingDirections {
  functions [ExpBasicExecutor]
  args {
    user_message "move left and right simultaneously"
  }
  // Expected: Error - Conflicting instructions
}

test TestImpossibleOperation {
  functions [ExpBasicExecutor]
  args {
    user_message "stop the program before starting it"
  }
  // Expected: Error or requires state checking
}

test TestNonsensicalRequest {
  functions [ExpBasicExecutor]
  args {
    user_message "make the VI fly"
  }
  // Expected: Error - Nonsensical operation
}

// ----------------------------------------------------------------------------
// Category 6: Empty or Invalid Input
// ----------------------------------------------------------------------------

test TestEmptyMessage {
  functions [ExpBasicExecutor]
  args {
    user_message ""
  }
  // Expected: Error - Empty user message
}

test TestOnlyWhitespace {
  functions [ExpBasicExecutor]
  args {
    user_message "   "
  }
  // Expected: Error - No actual content
}

test TestGibberish {
  functions [ExpBasicExecutor]
  args {
    user_message "asdfghjkl qwerty"
  }
  // Expected: Error - Cannot interpret request
}

// ----------------------------------------------------------------------------
// Category 7: Wrong Context or Mismatched Operations
// ----------------------------------------------------------------------------

test TestWrongControlForPulseType {
  functions [ExpBasicExecutor]
  args {
    user_message "set Gauss amp when using Basic pulse"
  }
  // Expected: Error or warning - Control doesn't match current pulse type
}

test TestSetIndicatorValue {
  functions [ExpBasicExecutor]
  args {
    user_message "set the current position to 100"
  }
  // Expected: Error - Cannot set indicator values (read-only)
}

test TestGetControlValue {
  functions [ExpBasicExecutor]
  args {
    user_message "get the speed control value"
  }
  // Expected: Error - Controls are set, not read (use indicator instead)
}

// ----------------------------------------------------------------------------
// Category 8: Missing Units or Incorrect Units
// ----------------------------------------------------------------------------

test TestMissingUnits {
  functions [ExpBasicExecutor]
  args {
    user_message "set Basic freq to 1000"
  }
  // Expected: Could work or error - units (Hz) not specified
}

test TestWrongUnits {
  functions [ExpBasicExecutor]
  args {
    user_message "set speed to 30 meters per second"
  }
  // Expected: Error - wrong units (should be mm/s)
}

test TestIncompatibleUnits {
  functions [ExpBasicExecutor]
  args {
    user_message "set frequency to 500 volts"
  }
  // Expected: Error - incompatible units for frequency
}