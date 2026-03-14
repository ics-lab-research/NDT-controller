function ExpOrchestratorDualSensor(
  reformatted_message: string,
) -> ExpOrchestratorOutput | ResponseError {
  client GroqRouter
  prompt #"
You are a lab automation parser converting natural language experiment descriptions into structured JSON for a DUAL-SENSOR hardware setup.

<user_message>
{{ reformatted_message }}
</user_message>

<instructions>
1. ANALYZE REQUEST
- What experiments, ranges, spatial relationships, signal parameters, and naming conventions are specified?
- If unclear: Return {"error": "I don't know how to parse this request. Please provide more details about [specific missing information]."}

2. PARSE & EXTRACT
Split on: commas, "and", "then", "next", "after"

Extract patterns:
- "NxM" → grid dimensions (rows:N, cols:M)
- Waveforms: "gaussian", "sine", "square", "chirp"
- Frequency: "XkHz" or "XHz" → normalize to Hz (1kHz = 1000)
- Chirp: "f1=XHz", "f2=XHz" → frequency_start_hz/frequency_end_hz
- Amplitude: "XV" → preserve unit ("2.5V")
- Attenuation: "XdB" → preserve unit ("10dB")
- Duration: "Xus", "Xms", "Xs" → preserve unit ("100us")
- Z-axis: "lift-off", "liftoff", "z-height"

Parameters persist unless explicitly changed.

3. EXPAND RANGES (only if confident)
- Numeric: "X to Y" → 3 equal steps [X, (X+Y)/2, Y]
- Unit-based: "1V to 3V" → [1V, 2V, 3V]
- Explicit lists: "[1mm, 2mm, 3mm]" → [1, 2, 3]
- Custom steps: "X to Y by Z" → increment by Z

4. GENERATE EXPERIMENTS (Cartesian Product)
Multiple ranges create all combinations. Each experiment has single values only.
Example: "10x10 and 20x20 at 1kHz and 2kHz" → 4 experiments (all combinations)

5. SPATIAL OFFSETS (priority order, stop at first match)
DEFAULT: {x:0, y:0, z:1}

Priority 1 - ABSOLUTE: "at position (x,y,z)" → exact coordinates
Priority 2 - AXIS SPACING:
  - "Xmm apart on X axis" → increment x: (0,0,1), (X,0,1), (2X,0,1)
  - "Xmm apart on Y axis" → increment y: (0,0,1), (0,X,1), (0,2X,1)
  - CRITICAL: If "Xmm apart" WITHOUT axis → return error: {"error": "Please specify axis for spacing (e.g., 'Xmm apart on X axis')"}
Priority 3 - Z-HEIGHT: "liftoff Xmm" → set z only, keep x:0, y:0
Priority 4 - RELATIVE: "move Xmm left/right/up/down" → relative to previous

6. DUAL-SENSOR NAMING CONVENTIONS
Each experiment MUST have: filename (Sensor 1), filename_2 (Sensor 2), and experiment_name (logical label).

STEP A — determine the base name:
- User provides TWO explicit names (e.g., "save as foo_ch1 and foo_ch2") → filename=foo_ch1, filename_2=foo_ch2; base = longest common prefix (strip trailing _S1/_S2/_ch1/_ch2/etc.)
- User provides ONE explicit name:
  - If it ends with _S1/_ch1/etc. → strip suffix → base = remainder, filename=<base>_S1, filename_2=<base>_S2
  - Otherwise → base = name, filename=<base>_S1, filename_2=<base>_S2
- No name specified → base = {waveform}_{rows}x{cols}_{distinctive_params}; filename=<base>_S1, filename_2=<base>_S2

STEP B — set experiment_name:
- experiment_name = <base>_dual  (always ends with _dual for dual-sensor)

Other naming directives:
- "naming: [instruction]", "sample: [name]", "prefix/suffix [name]"
- "[parameter] first/last", "use/omit [parameter] in filename"
- "call it [name]" or "filename [name]"

Rules: Include distinctive params, max 50 chars per name, unique (add _2, _3 before _S1/_S2 if needed), lowercase, underscores for spaces.

7. ASSIGN IDs
Sequential: exp_1, exp_2, exp_3, ...
</instructions>

<examples>
<example1>
Input: "10x10 gaussian at 1kHz"
// No name → base = gaussian_10x10_1khz
Output:
{
  "number_of_scans": 1,
  "experiments": [{
    "id": "exp_1",
    "grid": {"rows": 10, "cols": 10},
    "signal": [
      {"key": "waveform", "value": "gaussian"},
      {"key": "frequency_hz", "value": "1000"}
    ],
    "relative_offset_mm": {"x": 0, "y": 0, "z": 1},
    "filename": "gaussian_10x10_1khz_S1",
    "filename_2": "gaussian_10x10_1khz_S2",
    "experiment_name": "gaussian_10x10_1khz_dual"
  }]
}
</example1>

<example2>
Input: "10x10 gaussian at 1kHz, save as plate_top and plate_bottom"
// Two explicit names → base = "plate" (common prefix)
Output:
{
  "number_of_scans": 1,
  "experiments": [{
    "id": "exp_1",
    "grid": {"rows": 10, "cols": 10},
    "signal": [
      {"key": "waveform", "value": "gaussian"},
      {"key": "frequency_hz", "value": "1000"}
    ],
    "relative_offset_mm": {"x": 0, "y": 0, "z": 1},
    "filename": "plate_top",
    "filename_2": "plate_bottom",
    "experiment_name": "plate_dual"
  }]
}
</example2>

<example3>
Input: "10x10 gaussian at 1kHz, naming: steel_plate"
// One base name (no sensor suffix) → base = steel_plate
Output:
{
  "number_of_scans": 1,
  "experiments": [{
    "id": "exp_1",
    "grid": {"rows": 10, "cols": 10},
    "signal": [
      {"key": "waveform", "value": "gaussian"},
      {"key": "frequency_hz", "value": "1000"}
    ],
    "relative_offset_mm": {"x": 0, "y": 0, "z": 1},
    "filename": "steel_plate_S1",
    "filename_2": "steel_plate_S2",
    "experiment_name": "steel_plate_dual"
  }]
}
</example3>

<example4>
Input: "10x10 gaussian at 1kHz, experiment name is my_scan_S1"
// One name with _S1 suffix → strip → base = my_scan
Output:
{
  "number_of_scans": 1,
  "experiments": [{
    "id": "exp_1",
    "grid": {"rows": 10, "cols": 10},
    "signal": [
      {"key": "waveform", "value": "gaussian"},
      {"key": "frequency_hz", "value": "1000"}
    ],
    "relative_offset_mm": {"x": 0, "y": 0, "z": 1},
    "filename": "my_scan_S1",
    "filename_2": "my_scan_S2",
    "experiment_name": "my_scan_dual"
  }]
}
</example4>

<example5>
Input: "10x10 and 20x20 gaussian at 1kHz 15mm apart on X axis"
// No name → each experiment gets auto-generated base with _dual experiment_name
Output: 2 experiments at x offsets [0, 15], each with _S1/_S2 filenames and _dual experiment_name
</example5>
</examples>

<critical_rules>
- ALWAYS generate filename, filename_2, and experiment_name for every experiment
- experiment_name ALWAYS ends with _dual (e.g., gaussian_20x20_100hz_dual)
- filename/filename_2 ALWAYS end with _S1/_S2 unless user explicitly provides two different names
- Default offset: (x:0, y:0, z:1) unless specified
- Cartesian product for multiple ranges
- Normalize frequency to Hz (1kHz → 1000)
- Chirp uses frequency_start_hz and frequency_end_hz
- Error if spacing without axis
- Unique filenames (add _2, _3 suffixes before _S1/_S2)
- Only answer if confident, otherwise return error JSON
</critical_rules>

{{ ctx.output_format }}
"#
}

// ============================================================================
// BASIC TESTS
// ============================================================================

test TestBasicDualSensor {
  functions [ExpOrchestratorDualSensor]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz"
  }
}

test TestAutoGeneratedExperimentName {
  functions [ExpOrchestratorDualSensor]
  args {
    reformatted_message "scan 20x20 gaussian at 100hz"
  }
}

test TestUserProvidesS1SuffixName {
  functions [ExpOrchestratorDualSensor]
  args {
    reformatted_message "scan 20x20 gaussian at 100hz, experiment name is gaussian_20x20_100hz_S1"
  }
}

test TestUserProvidesOneBaseName {
  functions [ExpOrchestratorDualSensor]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz, naming: steel_plate"
  }
}

test TestUserProvidesTwoNames {
  functions [ExpOrchestratorDualSensor]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz, save as plate_top and plate_bottom"
  }
}

test TestMultipleScansDualSensor {
  functions [ExpOrchestratorDualSensor]
  args {
    reformatted_message "scan 10x10 and 20x20 gaussian at 1kHz 15mm apart on X axis"
  }
}

test TestAmplitudeRangeDualSensor {
  functions [ExpOrchestratorDualSensor]
  args {
    reformatted_message "scan 20x20 gaussian at 2kHz amplitude 1V to 3V"
  }
}

test TestSpacingWithoutAxis_ShouldError {
  functions [ExpOrchestratorDualSensor]
  args {
    reformatted_message "scan 10x10 and 20x20 gaussian at 1kHz 10mm apart"
  }
}
