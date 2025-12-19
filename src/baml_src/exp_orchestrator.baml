function ExpOrchestrator(
  reformatted_message: string, 
) -> ExpOrchestratorOutput | Error {
  client GroqRouter
  prompt #"
You are a lab automation parser that converts natural language experiment descriptions into structured JSON configurations. Your task is to extract spatial coordinates, grid dimensions, and signal parameters from experiment descriptions.

<user_message>
{{ reformatted_message }}
</user_message>

<instructions>
DETAILED INSTRUCTIONS:

1. ANALYZE THE REQUEST
Think through the input before processing:
- What experiments are requested?
- What ranges need expansion?
- What spatial relationships exist?
- What signal parameters are specified?

If unclear or uncertain, respond with JSON error schema: {"error": "I don't know how to parse this request. Please provide more details about [specific missing information]."}

2. PARSE THE TEXT
Split input on delimiters: commas, "and", "then", "next", "after"

3. EXTRACT PARAMETERS
Identify patterns and extract values:
- "NxM"→ grid dimensions (rows:N, cols:M)
- "gaussian", "sine", "square" → waveform type
- "XkHz" or "XHz" → frequency_hz (normalize to Hz: 1kHz = 1000)
- "XV" → amplitude (preserve unit: "2.5V")
- "XdB" → attenuation (preserve unit: "10dB")
- "Xus", "Xms", "Xs" → pulse_width or duration (preserve unit: "100us")

Parameters persist across experiments unless explicitly changed.

4. EXPAND RANGES
Only expand if confident about range specification:

NUMERIC RANGES (integer endpoints): "X to Y" → 3 equal steps
- "10 to 30" → [10, 20, 30]
- "1000-3000Hz" → [1000, 2000, 3000]

UNIT-BASED RANGES: Standard increments
- Voltage: "1V to 3V" → [1V, 2V, 3V]
- Frequency: "1kHz to 3kHz" → [1kHz, 2kHz, 3kHz]

CUSTOM STEPS: "X to Y by Z" → use Z as increment
- "1V to 3V by 0.5V" → [1V, 1.5V, 2V, 2.5V, 3V]

5. GENERATE EXPERIMENTS VIA CARTESIAN PRODUCT
Multiple ranges create all combinations. Each experiment contains single values only, not arrays.

Example: "10x10 and 20x20 at 1kHz and 2kHz" produces 4 experiments:
- exp_1: 10x10 at 1kHz
- exp_2: 10x10 at 2kHz
- exp_3: 20x20 at 1kHz
- exp_4: 20x20 at 2kHz

6. DETERMINE SPATIAL OFFSETS
DEFAULT: All experiments start at offset (x:0, y:0, z:1) unless explicitly specified.

Apply offset rules in priority order (stop at first match):

PRIORITY 1 - ABSOLUTE POSITION:
"at position (x,y,z)" or "offset (x,y,z)" → Use exact coordinates
Example: "at (10,20,2)" → offset: {x:10, y:20, z:2}

PRIORITY 2 - AXIS SPACING:
"Xmm apart on X axis" → Increment x: exp_1 (0,0,1), exp_2 (X,0,1), exp_3 (2X,0,1)
"Xmm apart on Y axis" → Increment y: exp_1 (0,0,1), exp_2 (0,X,1), exp_3 (0,2X,1)

CRITICAL: If spacing mentioned WITHOUT axis (e.g., "10mm apart"), return error:
{"error": "Please specify axis for spacing (e.g., '10mm apart on X axis' or '10mm apart on Y axis')"}

PRIORITY 3 - Z-HEIGHT:
"liftoff Xmm" or "Z height Xmm" → Set z value only, keep x:0, y:0

PRIORITY 4 - RELATIVE MOVEMENT:
"move Xmm left/right" or "shift Xmm up/down" → Relative to previous offset

PRIORITY 5 - DEFAULT:
{x:0, y:0, z:1}

7. GENERATE FILENAMES
Format: {waveform}_{rows}x{cols}_{distinctive_params}

Rules:
- Include most distinctive signal parameters (frequency, amplitude, attenuation)
- Maximum 50 characters
- Must be unique per experiment
- Add suffix _2, _3, etc. if duplicates exist

8. ASSIGN EXPERIMENT IDS
Sequential format: exp_1, exp_2, exp_3, ...
</instructions>

<example>
Input: "scan 20x20 gaussian at 2kHz amplitude 1V to 3V"

Processing steps:
1. Parse: grid=20x20, waveform=gaussian, frequency=2kHz (2000 Hz), amplitude range=1V to 3V
2. Expand amplitude: [1V, 2V, 3V] (3 steps)
3. Generate 3 experiments (Cartesian product)
4. Apply default offset (0,0,1) to all
5. Create unique filenames

Output:
{
  "number_of_scans": 3,
  "experiments": [
    {
      "id": "exp_1",
      "grid": {"rows": 20, "cols": 20},
      "signal": [
        {"key": "waveform", "value": "gaussian"},
        {"key": "frequency_hz", "value": "2000"},
        {"key": "amplitude", "value": "1V"}
      ],
      "relative_offset_mm": {"x": 0, "y": 0, "z": 1},
      "filename": "gaussian_20x20_2000Hz_1V"
    },
    {
      "id": "exp_2",
      "grid": {"rows": 20, "cols": 20},
      "signal": [
        {"key": "waveform", "value": "gaussian"},
        {"key": "frequency_hz", "value": "2000"},
        {"key": "amplitude", "value": "2V"}
      ],
      "relative_offset_mm": {"x": 0, "y": 0, "z": 1},
      "filename": "gaussian_20x20_2000Hz_2V"
    },
    {
      "id": "exp_3",
      "grid": {"rows": 20, "cols": 20},
      "signal": [
        {"key": "waveform", "value": "gaussian"},
        {"key": "frequency_hz", "value": "2000"},
        {"key": "amplitude", "value": "3V"}
      ],
      "relative_offset_mm": {"x": 0, "y": 0, "z": 1},
      "filename": "gaussian_20x20_2000Hz_3V"
    }
  ]
}
</example>

<critical_reminders>
- Default offset is (x:0, y:0, z:1) for ALL experiments unless explicitly specified
- Multiple ranges create separate experiments with ALL combinations (Cartesian product)
- Filenames must be unique - add _2, _3 suffixes to prevent duplicates
- Frequency must be normalized to Hz (1kHz → 1000)
- Return error if spacing mentioned without axis specification
- Only process if confident - respond with error JSON if uncertain
- Think through the request before answering
- Answer only if you are very confident about the parsing
</critical_reminders>

{{ ctx.output_format }}
"#
}

test TestError {
  functions [ExpOrchestrator]
  args {
    reformatted_message "fsdf afsdfda fasdf"
  }
}

// Basic single experiment tests
test TestBasicSingleExperiment {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz"
  }
}

test TestSingleExperimentWithMultipleParams {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 20x20 sine at 5kHz amplitude 3V attenuation 15dB"
  }
}

// Multiple experiments without spatial offset
test TestMultipleExperimentsBasic {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz amplitude 2V and 20x20 at 2kHz"
  }
}

test TestMultipleExperimentsAllAtOrigin {
  functions [ExpOrchestrator]
  args {
    reformatted_message "gaussian 20x20 at 1kHz and sine 20x20 at 2kHz and square 30x30 at 3kHz"
  }
}

test TestMultipleExperimentsAllAtOrigin2 {
  functions [ExpOrchestrator]
  args {
    reformatted_message "gaussian 20x20 from 1000Hz to 1200Hz"
  }
}

// X-axis spacing tests
test TestXAxisSpacingCentimeters {
  functions [ExpOrchestrator]
  args {
    reformatted_message "do 2 experiments 2cm apart on X axis: sine 50x50 at 5kHz and gaussian 30x30 at 3kHz"
  }
}

test TestXAxisSpacingMillimeters {
  functions [ExpOrchestrator]
  args {
    reformatted_message "3 scans 30mm apart on X axis: gaussian 15x15 at 2kHz"
  }
}

test TestXAxisSpacingAlternativeSyntax {
  functions [ExpOrchestrator]
  args {
    reformatted_message "2 experiments with X axis spacing 25mm: sine 10x10 at 1kHz and square 10x10 at 1.5kHz"
  }
}

// Y-axis spacing tests
test TestYAxisSpacingMillimeters {
  functions [ExpOrchestrator]
  args {
    reformatted_message "3 scans 15mm spacing on Y axis: sine 10x10 at 1kHz"
  }
}

test TestYAxisSpacingCentimeters {
  functions [ExpOrchestrator]
  args {
    reformatted_message "2 experiments 3cm apart on Y axis: gaussian 20x20 at 4kHz and sine 20x20 at 5kHz"
  }
}

// Liftoff tests
test TestLiftoffSingleValue {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 20x20 gaussian at 2kHz with liftoff 5mm"
  }
}

test TestLiftoffMultipleExperiments {
  functions [ExpOrchestrator]
  args {
    reformatted_message "experiment 1 and liftoff 2 is 3mm: gaussian 20x20 1kHz and sine 20x20 2kHz"
  }
}

test TestLiftoffWithSpacing {
  functions [ExpOrchestrator]
  args {
    reformatted_message "3 scans 15mm spacing on Y axis, liftoffs 1mm, 2mm, 3mm: sine 10x10 at 1kHz"
  }
}

test TestIndividualLiftoffs {
  functions [ExpOrchestrator]
  args {
    reformatted_message "first scan liftoff 2mm, second liftoff 5mm: gaussian 15x15 at 3kHz and square 15x15 at 3kHz"
  }
}

// Explicit position tests
test TestExplicitPosition {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan at position (10, 20, 2): gaussian 20x20 at 2kHz"
  }
}

test TestMultipleExplicitPositions {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan at (0,0,1) gaussian 10x10 1kHz, at (15,0,2) sine 10x10 2kHz, at (30,0,3) square 10x10 3kHz"
  }
}

test TestExplicitOffsetSyntax {
  functions [ExpOrchestrator]
  args {
    reformatted_message "gaussian 20x20 at 2kHz with offset (5, 10, 1.5)"
  }
}

// Range expansion tests
test TestFrequencyRange {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1000-1200Hz"
  }
}

test TestSimpleRange {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 15x15 sine at frequencies 1 to 3 kHz"
  }
}

test TestAmplitudeRange {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 20x20 gaussian at 2kHz amplitude 1V to 3V"
  }
}

// Cartesian product tests
test TestCartesianProductTwoRanges {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1-2kHz amplitude 1-2V"
  }
}

test TestCartesianProductThreeRanges {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 sine frequency 1-2kHz amplitude 1-2V attenuation 5-10dB"
  }
}

// Signal parameter variety tests
test TestPulseWidthParameter {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 15x15 square at 10kHz pulse width 100us"
  }
}

test TestDutyCycleParameter {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 20x20 square at 5kHz duty cycle 25%"
  }
}

test TestPhaseParameter {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 sine at 1kHz phase 90 degrees"
  }
}

test TestMultipleSignalParams {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 20x20 gaussian at 3kHz amplitude 2.5V attenuation 12dB pulse width 50us duty cycle 50%"
  }
}

// Error case tests
test TestSpacingWithoutAxisError {
  functions [ExpOrchestrator]
  args {
    reformatted_message "2 scans 10mm apart: gaussian 15x15 at 2kHz"
  }
}

test TestSpacingWithoutAxisError2 {
  functions [ExpOrchestrator]
  args {
    reformatted_message "3 experiments with 5cm spacing: sine 10x10 at 1kHz"
  }
}

// Complex combination tests
test TestComplexXSpacingWithRanges {
  functions [ExpOrchestrator]
  args {
    reformatted_message "2 scans 20mm apart on X axis: gaussian 10x10 at 1-2kHz"
  }
}

test TestComplexYSpacingWithMultipleParams {
  functions [ExpOrchestrator]
  args {
    reformatted_message "3 experiments 10mm spacing on Y axis: sine 20x20 at 2kHz amplitude 3V attenuation 10dB"
  }
}

test TestComplexMixedSpacingAndLiftoff {
  functions [ExpOrchestrator]
  args {
    reformatted_message "2 scans 15mm apart on X axis, first liftoff 1mm second liftoff 3mm: gaussian 25x25 at 4kHz amplitude 2V"
  }
}

// Persistence tests
test TestParameterPersistence {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz amplitude 2V, then 20x20 at 2kHz, then 30x30"
  }
}

test TestGridPersistence {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 15x15 gaussian at 1kHz, then sine at 2kHz, then square at 3kHz"
  }
}

// Waveform variety tests
test TestSquareWaveform {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 20x20 square at 10kHz"
  }
}

test TestMixedWaveforms {
  functions [ExpOrchestrator]
  args {
    reformatted_message "gaussian 10x10 at 1kHz, sine 10x10 at 2kHz, square 10x10 at 3kHz"
  }
}

// Natural language variations
test TestNaturalLanguageVariation1 {
  functions [ExpOrchestrator]
  args {
    reformatted_message "do a scan with 20x20 grid using gaussian waveform at frequency 2000Hz"
  }
}

test TestNaturalLanguageVariation2 {
  functions [ExpOrchestrator]
  args {
    reformatted_message "run experiment: sine wave, 15 by 15 grid, 3.5 kHz, 2.8 volts"
  }
}

test TestNaturalLanguageVariation3 {
  functions [ExpOrchestrator]
  args {
    reformatted_message "I need to scan a 10x10 area with sine at 1kHz then move 2cm right on X axis and scan 10x10 with gaussian at 1kHz"
  }
}

// Edge cases
test TestSinglePointGrid {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 1x1 gaussian at 5kHz"
  }
}

test TestLargeGrid {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 100x100 sine at 10kHz"
  }
}

test TestHighFrequency {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 20x20 gaussian at 100kHz"
  }
}

test TestLowFrequency {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 20x20 sine at 100Hz"
  }
}

test TestZeroLiftoff {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz liftoff 0mm"
  }
}

// Duration/time-based parameters
test TestDurationParameter {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 15x15 gaussian at 2kHz duration 5ms"
  }
}

test TestMultipleTimeParams {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 20x20 square at 5kHz pulse width 200us duration 10ms"
  }
}

