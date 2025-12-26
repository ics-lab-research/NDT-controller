class ExperimentStep {
  step_name string
  tool_sequence (ConnectToViTool | HandleSaveDialogTool | PressButtonTool | RunOpenViTool | SelectComboBoxTool | SelectTabTool | SetButtonStateTool | SetNumericControlTool | StopViTool | WaitForOperationCompleteTool)[]
}

function ExpExecutor(
    plan: string, filename: string?
) -> ExperimentStep[] | ResponseError {
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

<instructions>
MANDATORY EXECUTION ORDER:

1. INITIALIZATION PHASE (Always First):
   - Start with connect_to_vi
   - Configure ALL signal parameters BEFORE running VI
   - Configure scan distances BEFORE running VI (if scan operation exists in plan)
   - Select appropriate tabs and modes BEFORE running VI

2. VI STARTUP PHASE (Required Before Any Operations):
   - Execute run_open_vi with run_vi=true
   - Immediately follow with handle_save_dialog

3. OPERATIONS PHASE:
   - Execute movements and scans in the order specified in the plan
   - ALWAYS include wait_for_operation_complete after each movement or scan
   - For movements: use press_button after setting distance
   - For scans: use set_button_state (NOT press_button) to trigger scan

4. CLEANUP PHASE (Always Last):
   - Execute stop_vi with close_labview=true

SIGNAL CONFIGURATION RULES:

For Basic Pulse Type (sine, triangle, square, sawtooth):
- Select Pulse Types tab with index 0
- Use select_combo_box on "Basic Type" to choose waveform (0=Sine, 1=Triangle, 2=Square, 3=Sawtooth)
- Use set_numeric_control on "Basic freq (Hz)" for frequency
- Use set_numeric_control on "Basic amp" for amplitude

For Gaussian Pulse Type:
- Select Pulse Types tab with index 1
- Use set_numeric_control on "Gauss freq (Hz)", "Gauss amp", "Gauss atten (dB)", "Gauss Nor. Band"

For Chirp Pulse Type:
- Select Pulse Types tab with index 2
- Use set_numeric_control on "Chirp amp", "Chirp f1", "Chirp f2"

MOVEMENT RULES:

For each movement command (move X/Y/Z in direction):
1. Use set_numeric_control to set the distance (X Distance, Y Distance, or Z Distance)
2. Use press_button with the directional button name (x left, x right, y forward, y backward, z up, z down)
3. Use wait_for_operation_complete with exp_type "MOVEMENT"

SCAN RULES:

For grid scan operations (execute grid scan):
PRE-CONFIGURATION (must happen BEFORE run_open_vi):
- Use select_tab on "Measurement Modes" with index 1 to select Scan Mode
- Use set_numeric_control on "X Auto Distance" for horizontal grid steps
- Use set_numeric_control on "Y Auto Distance" for vertical grid steps

EXECUTION (must happen AFTER run_open_vi and handle_save_dialog):
- Use set_button_state on button_name "Scan" with state true (NOT press_button)
- Use wait_for_operation_complete with exp_type "SCAN"

STEP NAMING CONVENTION:

Each step in the output must have a descriptive StepName that maps back to the original plan:
- "Step 0 - Initialization" for connect_to_vi
- "Step N - [Original Plan Description]" for each plan item (e.g., "Step 1 - Configure Signal (frequency=1000, amplitude=6.0, waveform=sine)")
- "Step N.M - Pre-configure [Operation]" for configurations that must happen before VI starts
- "Step N.P - Start VI and Configure Save" for run_open_vi and handle_save_dialog
- "Step FINAL - Cleanup" for stop_vi

If a plan step requires multiple stages (like scan requiring both pre-configuration and execution), create separate steps with substep numbering.
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
  {
    "step_name": "Step 0 - Initialization",
    "tool_sequence": [
      {"tool_name": "connect_to_vi", "vi_path": "example.vi"}
    ]
  },
  {
    "step_name": "Step 1 - Configure Signal (frequency=1000, amplitude=6.0, waveform=sine)",
    "tool_sequence": [
      {"tool_name": "select_tab", "tab_control_name": "Pulse Types", "index": 0},
      {"tool_name": "select_combo_box", "combo_box_name": "Basic Type", "index": 0},
      {"tool_name": "set_numeric_control", "control_name": "Basic freq (Hz)", "value": 1000.0},
      {"tool_name": "set_numeric_control", "control_name": "Basic amp", "value": 6.0}
    ]
  },
  {
    "step_name": "Step 5.1 - Pre-configure Grid Scan (7x8)",
    "tool_sequence": [
      {"tool_name": "select_tab", "tab_control_name": "Measurement Modes", "index": 1},
      {"tool_name": "set_numeric_control", "control_name": "X Auto Distance", "value": 7.0},
      {"tool_name": "set_numeric_control", "control_name": "Y Auto Distance", "value": 8.0}
    ]
  },
  {
    "step_name": "Step 1.1 - Start VI and Configure Save",
    "tool_sequence": [
      {"tool_name": "run_open_vi", "run_vi": true},
      {"tool_name": "handle_save_dialog", "save_directory": "data_dir", "file_name": "experiment_001.tdms"}
    ]
  },
  {
    "step_name": "Step 2 - Move X left (distance 10 mm)",
    "tool_sequence": [
      {"tool_name": "set_numeric_control", "control_name": "X Distance", "value": 10.0},
      {"tool_name": "press_button", "button_name": "x left"},
      {"tool_name": "wait_for_operation_complete", "exp_type": "MOVEMENT"}
    ]
  },
  {
    "step_name": "Step 3 - Move Y backward (distance 20 mm)",
    "tool_sequence": [
      {"tool_name": "set_numeric_control", "control_name": "Y Distance", "value": 20.0},
      {"tool_name": "press_button", "button_name": "y backward"},
      {"tool_name": "wait_for_operation_complete", "exp_type": "MOVEMENT"}
    ]
  },
  {
    "step_name": "Step 4 - Move Z up (distance 15 mm)",
    "tool_sequence": [
      {"tool_name": "set_numeric_control", "control_name": "Z Distance", "value": 15.0},
      {"tool_name": "press_button", "button_name": "z up"},
      {"tool_name": "wait_for_operation_complete", "exp_type": "MOVEMENT"}
    ]
  },
  {
    "step_name": "Step 5.2 - Execute Grid Scan (7x8)",
    "tool_sequence": [
      {"tool_name": "set_button_state", "button_name": "Scan", "state": true},
      {"tool_name": "wait_for_operation_complete", "exp_type": "SCAN"}
    ]
  },
  {
    "step_name": "Step 6 - Move X left (distance 7 mm)",
    "tool_sequence": [
      {"tool_name": "set_numeric_control", "control_name": "X Distance", "value": 7.0},
      {"tool_name": "press_button", "button_name": "x left"},
      {"tool_name": "wait_for_operation_complete", "exp_type": "MOVEMENT"}
    ]
  },
  {
    "step_name": "Step 7 - Move Y forward (distance 8 mm)",
    "tool_sequence": [
      {"tool_name": "set_numeric_control", "control_name": "Y Distance", "value": 8.0},
      {"tool_name": "press_button", "button_name": "y forward"},
      {"tool_name": "wait_for_operation_complete", "exp_type": "MOVEMENT"}
    ]
  },
  {
    "step_name": "Step FINAL - Cleanup",
    "tool_sequence": [
      {"tool_name": "stop_vi", "close_labview": true}
    ]
  }
]
</example>

<output_requirements>
Return a JSON array where each element contains:
- step_name: A descriptive string that maps to the original plan step (e.g., "Step 2 - Move X left (distance 10 mm)")
- tool_sequence: An array of tool function calls to execute for that step

The output must follow the structure shown in the example above.

If the plan is invalid, incomplete, or cannot be translated, return:
{"error": "description of the issue"}
</output_requirements>

<critical_reminders>
1. ALL configurations (signal parameters, scan distances, mode selections) MUST occur BEFORE run_open_vi
2. run_open_vi and handle_save_dialog MUST be executed together before any movement or scan operations
3. ALWAYS use wait_for_operation_complete after movements (exp_type: "MOVEMENT") and scans (exp_type: "SCAN")
4. For scan operations, use set_button_state NOT press_button
5. Step names must be descriptive and map back to the original plan items
6. Follow the mandatory execution order: Initialization → Configuration → VI Startup → Operations → Cleanup
7. Grid scan requires TWO separate steps: pre-configuration step and execution step
8. Use substep numbering (e.g., Step 1.1, Step 5.2) when operations need to be split or reordered
</critical_reminders>

Now translate the given experimental plan into the appropriate tool function sequence with explicit step-by-step mapping.
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