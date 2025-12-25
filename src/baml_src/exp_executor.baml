function ExpExecutor(
    plan: string, filename: string?
) -> (ConnectToViTool | HandleSaveDialogTool | PressButtonTool | RunOpenViTool | SelectComboBoxTool | SelectTabTool | SetButtonStateTool | SetNumericControlTool | StopViTool | WaitForOperationCompleteTool)[] | ResponseError {
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

// Test Case 1: Basic signal configuration with simple movement (no scan)
test TestSimpleMovementNoScan {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-002:
1. configure signal (frequency=2000, amplitude=4.5, waveform=square)
2. move X left (distance 15 mm)
3. move Y backward (distance 10 mm)
    "#
    filename "simple_movement.tdms"
  }
}

// Test Case 2: Gaussian pulse type with grid scan
test TestGaussianPulseWithScan {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-003:
1. configure signal (pulse_type=gaussian, amplitude=3.0, frequency=1500, attenuation=10, normalized_bandwidth=0.5)
2. execute grid scan (10x12)
    "#
    filename "gaussian_scan.tdms"
  }
}

// Test Case 3: Chirp pulse type with movements and scan
test TestChirpPulseWithScan {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-004:
1. configure signal (pulse_type=chirp, amplitude=5.5, f1=500, f2=2500)
2. move Z down (distance 5 mm)
3. execute grid scan (8x8)
4. move Z up (distance 5 mm)
    "#
    filename "chirp_experiment.tdms"
  }
}

// Test Case 4: Multiple movements in all directions
test TestMultiDirectionalMovements {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-005:
1. configure signal (frequency=1200, amplitude=7.0, waveform=sawtooth)
2. move X right (distance 20 mm)
3. move Y forward (distance 15 mm)
4. move Z up (distance 10 mm)
5. move X left (distance 10 mm)
6. move Y backward (distance 5 mm)
7. move Z down (distance 3 mm)
    "#
    filename "multi_direction.tdms"
  }
}

// Test Case 5: Large grid scan with pre and post movements
test TestLargeGridScanWithMovements {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-006:
1. configure signal (frequency=800, amplitude=6.5, waveform=sine)
2. move X left (distance 25 mm)
3. move Y backward (distance 30 mm)
4. execute grid scan (15x20)
5. move X left (distance 15 mm)
6. move Y forward (distance 20 mm)
7. move Z up (distance 5 mm)
    "#
    filename "large_grid_scan.tdms"
  }
}

// Test Case 6: Scan only (minimal setup)
test TestScanOnly {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-007:
1. configure signal (frequency=1000, amplitude=5.0, waveform=triangle)
2. execute grid scan (6x6)
    "#
    filename "scan_only.tdms"
  }
}

// Test Case 7: Complex Z-axis movements with scan
test TestZAxisComplexity {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-008:
1. configure signal (frequency=1800, amplitude=4.0, waveform=square)
2. move Z down (distance 8 mm)
3. move X right (distance 12 mm)
4. move Z up (distance 4 mm)
5. execute grid scan (7x9)
6. move Z down (distance 2 mm)
    "#
    filename "z_axis_complex.tdms"
  }
}

// Test Case 8: High frequency signal with small grid
test TestHighFrequencySmallGrid {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-009:
1. configure signal (frequency=5000, amplitude=3.5, waveform=sine)
2. move X left (distance 5 mm)
3. move Y forward (distance 5 mm)
4. execute grid scan (3x3)
5. move X right (distance 5 mm)
6. move Y backward (distance 5 mm)
    "#
    filename "high_freq_small.tdms"
  }
}

// Test Case 9: Gaussian pulse with complex movements
test TestGaussianComplexMovements {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-010:
1. configure signal (pulse_type=gaussian, amplitude=4.5, frequency=2000, attenuation=15, normalized_bandwidth=0.8)
2. move X right (distance 18 mm)
3. move Y backward (distance 22 mm)
4. move Z down (distance 7 mm)
5. execute grid scan (12x14)
6. move Z up (distance 7 mm)
7. move X left (distance 12 mm)
8. move Y forward (distance 14 mm)
    "#
    filename "gaussian_complex.tdms"
  }
}

// Test Case 10: Chirp with minimal movements
test TestChirpMinimalMovements {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-011:
1. configure signal (pulse_type=chirp, amplitude=6.0, f1=1000, f2=3000)
2. move X left (distance 10 mm)
3. execute grid scan (9x9)
4. move X left (distance 9 mm)
    "#
    filename "chirp_minimal.tdms"
  }
}

// Test Case 11: Return to origin pattern
test TestReturnToOriginPattern {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-012:
1. configure signal (frequency=1500, amplitude=5.5, waveform=triangle)
2. move X right (distance 20 mm)
3. move Y forward (distance 20 mm)
4. execute grid scan (10x10)
5. move X left (distance 30 mm)
6. move Y backward (distance 30 mm)
    "#
    filename "return_origin.tdms"
  }
}

// Test Case 12: Single axis movement with scan
test TestSingleAxisMovement {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-013:
1. configure signal (frequency=2500, amplitude=3.0, waveform=sawtooth)
2. move Y forward (distance 25 mm)
3. execute grid scan (11x11)
4. move Y backward (distance 25 mm)
    "#
    filename "single_axis.tdms"
  }
}

// Test Case 13: Asymmetric grid scan
test TestAsymmetricGridScan {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-014:
1. configure signal (frequency=1100, amplitude=6.0, waveform=sine)
2. move X left (distance 15 mm)
3. move Y backward (distance 20 mm)
4. execute grid scan (5x15)
5. move X left (distance 5 mm)
6. move Y forward (distance 15 mm)
    "#
    filename "asymmetric_grid.tdms"
  }
}

// Test Case 14: All waveform types coverage
test TestSquareWaveform {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-015:
1. configure signal (frequency=900, amplitude=4.8, waveform=square)
2. execute grid scan (6x8)
    "#
    filename "square_waveform.tdms"
  }
}

// Test Case 15: Movement only (no scan)
test TestMovementOnlyNoScan {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-016:
1. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
2. move X right (distance 10 mm)
3. move Y forward (distance 10 mm)
4. move Z up (distance 10 mm)
5. move X left (distance 10 mm)
6. move Y backward (distance 10 mm)
7. move Z down (distance 10 mm)
    "#
    filename "movement_only.tdms"
  }
}

// ====================================================== ERROR HANDLING TEST CASES ===============================================
// Test Case 2: Unknown control - Invalid frequency parameter name
test TestUnknownFrequencyControl {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-003:
1. configure signal (freq=1000, amplitude=5.0, waveform=sine)
2. move X left (distance 10 mm)
    "#
    filename "unknown_control.tdms"
  }
  // Expected: Error - "Unknown control or operation: freq (should be 'frequency')"
}

// Test Case 3: Unknown waveform type
test TestUnknownWaveform {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-004:
1. configure signal (frequency=1500, amplitude=3.0, waveform=cosine)
2. execute grid scan (5x5)
    "#
    filename "unknown_waveform.tdms"
  }
  // Expected: Error - "Unknown control or operation: waveform=cosine (valid: sine, triangle, square, sawtooth)"
}

// Test Case 4: Invalid movement direction
test TestInvalidMovementDirection {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-005:
1. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
2. move X upward (distance 10 mm)
    "#
    filename "invalid_direction.tdms"
  }
  // Expected: Error - "Unknown control or operation: X upward (X only supports left/right)"
}

// Test Case 6: Invalid pulse type
test TestInvalidPulseType {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-007:
1. configure signal (pulse_type=custom, frequency=1000, amplitude=5.0)
2. move Z up (distance 5 mm)
    "#
    filename "invalid_pulse.tdms"
  }
  // Expected: Error - "Unknown control or operation: pulse_type=custom (valid: Basic, Gaussian, Chirp)"
}

// Test Case 7: Missing required signal parameters for Basic pulse
test TestMissingSignalParameters {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-008:
1. configure signal (frequency=1000)
2. execute grid scan (3x3)
    "#
    filename "missing_params.tdms"
  }
  // Expected: Error - "Unknown control or operation: missing amplitude parameter for Basic pulse"
}

// Test Case 8: Invalid scan dimensions format
test TestInvalidScanFormat {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-009:
1. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
2. execute grid scan (5)
    "#
    filename "invalid_scan.tdms"
  }
  // Expected: Error - "Unknown control or operation: grid scan format should be MxN"
}

// Test Case 9: Unknown measurement mode
test TestUnknownMeasurementMode {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-010:
1. set measurement mode to calibration
2. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
    "#
    filename "unknown_mode.tdms"
  }
  // Expected: Error - "Unknown control or operation: measurement mode=calibration (valid: Test Mode, Scan Mode, Lift-off)"
}

// Test Case 10: Invalid button name
test TestInvalidButtonName {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-011:
1. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
2. press start button
    "#
    filename "invalid_button.tdms"
  }
  // Expected: Error - "Unknown control or operation: start button (valid buttons: x right, x left, y forward, y backward, z up, z down)"
}

// Test Case 11: Invalid numeric control name
test TestInvalidNumericControl {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-012:
1. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
2. set scan resolution to 100
    "#
    filename "invalid_numeric.tdms"
  }
  // Expected: Error - "Unknown control or operation: scan resolution (not in available numeric controls)"
}

// Test Case 12: Missing distance for movement
test TestMissingDistance {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-013:
1. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
2. move X left
    "#
    filename "missing_distance.tdms"
  }
  // Expected: Error - "Unknown control or operation: missing distance parameter for movement"
}

// Test Case 13: Invalid combo box option
test TestInvalidComboBoxOption {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-014:
1. configure signal (frequency=1000, amplitude=5.0, waveform=pulse)
2. move Y forward (distance 10 mm)
    "#
    filename "invalid_combo.tdms"
  }
  // Expected: Error - "Unknown control or operation: waveform=pulse (valid for Basic Type: sine, triangle, square, sawtooth)"
}

// Test Case 14: Conflicting pulse type parameters
test TestConflictingPulseParameters {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-015:
1. configure signal (frequency=1000, amplitude=5.0, waveform=sine, chirp_f1=500, chirp_f2=2000)
    "#
    filename "conflicting_params.tdms"
  }
  // Expected: Error - "Unknown control or operation: mixing Basic pulse parameters with Chirp parameters"
}

// Test Case 15: Invalid state value for button
test TestInvalidButtonState {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-016:
1. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
2. set Scan button to maybe
    "#
    filename "invalid_state.tdms"
  }
  // Expected: Error - "Unknown control or operation: button state must be true/false"
}

// Test Case 16: Unknown Gaussian pulse parameter
test TestUnknownGaussianParameter {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-017:
1. configure Gaussian pulse (frequency=1000, amplitude=5.0, attenuation=10, bandwidth=0.5, phase=90)
    "#
    filename "unknown_gaussian.tdms"
  }
  // Expected: Error - "Unknown control or operation: phase parameter not available for Gaussian pulse"
}

// Test Case 17: Invalid Chirp parameters
test TestInvalidChirpParameters {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-018:
1. configure Chirp pulse (amplitude=5.0, start_frequency=500)
2. execute grid scan (4x4)
    "#
    filename "invalid_chirp.tdms"
  }
  // Expected: Error - "Unknown control or operation: missing f2 parameter for Chirp pulse"
}

// Test Case 18: Ambiguous movement instruction
test TestAmbiguousMovement {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-019:
1. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
2. move diagonally (distance 10 mm)
    "#
    filename "ambiguous_movement.tdms"
  }
  // Expected: Error - "Unknown control or operation: diagonal movement not supported"
}

// Test Case 19: Invalid speed value context
test TestInvalidSpeedContext {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-020:
1. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
2. set speed to fast
    "#
    filename "invalid_speed.tdms"
  }
  // Expected: Error - "Unknown control or operation: speed must be numeric value in mm/s"
}

// Test Case 20: Missing filename parameter
test TestMissingFilename {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-021:
1. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
2. execute grid scan (5x5)
    "#
    filename null
  }
  // Expected: Error - "Unknown control or operation: filename is required for save dialog"
}

// Test Case 21: Invalid tab index reference
test TestInvalidTabIndex {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-022:
1. switch to measurement mode 5
2. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
    "#
    filename "invalid_tab.tdms"
  }
  // Expected: Error - "Unknown control or operation: measurement mode index 5 (valid: 0=Test Mode, 1=Scan Mode, 2=Lift-off)"
}

// Test Case 22: Unrecognized operation type
test TestUnrecognizedOperation {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-023:
1. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
2. rotate probe 45 degrees
    "#
    filename "unrecognized_op.tdms"
  }
  // Expected: Error - "Unknown control or operation: rotate probe (operation not supported)"
}

// Test Case 23: Empty or malformed plan
test TestEmptyPlan {
  functions [ExpExecutor]
  args {
    plan ""
    filename "empty_plan.tdms"
  }
  // Expected: Error - "Unknown control or operation: plan is empty or malformed"
}

// Test Case 24: Invalid distance units
test TestInvalidDistanceUnits {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-024:
1. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
2. move X left (distance 10 cm)
    "#
    filename "invalid_units.tdms"
  }
  // Expected: Error - "Unknown control or operation: distance must be in mm (millimeters)"
}

// Test Case 25: Multiple conflicting operations
test TestConflictingOperations {
  functions [ExpExecutor]
  args {
    plan #"
PLAN EXP-025:
1. switch to Test Mode
2. execute grid scan (3x3)
    "#
    filename "conflicting_ops.tdms"
  }
  // Expected: Error - "Unknown control or operation: grid scan requires Scan Mode, but Test Mode is selected"
}