function ExpOrchestrator(
  reformatted_message: string, 
) -> ExpOrchestratorOutput | ResponseError {
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

// ============================================================================
// BASIC SINGLE EXPERIMENT TESTS
// ============================================================================

test TestBasicSingleExperiment {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz"
  }
}

test TestSingleExperimentWithAmplitude {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 20x20 sine at 5kHz amplitude 2.5V"
  }
}

test TestSingleExperimentWithMultipleParams {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 15x15 square at 3kHz amplitude 1.5V attenuation 10dB pulse width 100us"
  }
}

// ============================================================================
// RANGE EXPANSION TESTS
// ============================================================================

test TestAmplitudeRange {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 20x20 gaussian at 2kHz amplitude 1V to 3V"
  }
}

test TestFrequencyRange {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 sine frequency 1kHz to 3kHz amplitude 2V"
  }
}

test TestGridSizeRange {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 to 30x30 gaussian at 2kHz"
  }
}

test TestCustomStepRange {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 20x20 sine at 2kHz amplitude 1V to 3V by 0.5V"
  }
}

test TestNumericRangeWithDash {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 sine at 1000-3000Hz amplitude 2V"
  }
}

// ============================================================================
// CARTESIAN PRODUCT TESTS
// ============================================================================

test TestMultipleGridSizesAndFrequencies {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 and 20x20 at 1kHz and 2kHz"
  }
}

test TestThreeParameterCombinations {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 and 20x20 gaussian at 1kHz and 2kHz amplitude 1V and 2V"
  }
}

test TestMultipleWaveforms {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 15x15 gaussian and sine at 2kHz amplitude 2.5V"
  }
}

// ============================================================================
// SPATIAL OFFSET TESTS
// ============================================================================

test TestDefaultOffset {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz"
  }
}

test TestAbsolutePosition {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz at position (10,20,2)"
  }
}

test TestXAxisSpacing {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 and 20x20 and 30x30 gaussian at 1kHz 15mm apart on X axis"
  }
}

test TestYAxisSpacing {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 and 20x20 gaussian at 1kHz 25mm apart on Y axis"
  }
}

test TestZHeightLiftoff {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 20x20 gaussian at 2kHz liftoff 5mm"
  }
}

test TestZHeightSpecification {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 15x15 sine at 3kHz Z height 3mm"
  }
}

test TestSpacingWithoutAxis_ShouldError {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 and 20x20 gaussian at 1kHz 10mm apart"
  }
}

// ============================================================================
// SEQUENTIAL EXPERIMENT TESTS
// ============================================================================

test TestSequentialExperiments {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz, then scan 20x20 sine at 2kHz"
  }
}

test TestSequentialWithParameterPersistence {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz amplitude 2V, then 20x20 at 2kHz"
  }
}

// ============================================================================
// UNIT NORMALIZATION TESTS
// ============================================================================

test TestFrequencyInHz {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 500Hz"
  }
}

test TestFrequencyInKHz {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 2.5kHz"
  }
}

test TestMixedUnits {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz amplitude 2.5V attenuation 15dB pulse width 200us"
  }
}

test TestDurationInMilliseconds {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz duration 50ms"
  }
}

test TestDurationInSeconds {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 sine at 2kHz duration 2s"
  }
}

// ============================================================================
// FILENAME GENERATION TESTS
// ============================================================================

test TestUniqueFilenames {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz amplitude 1V and 2V and 3V"
  }
}

test TestFilenameDuplicatePrevention {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz, then scan 10x10 gaussian at 1kHz"
  }
}

test TestLongParameterFilename {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 25x25 square at 5kHz amplitude 3.7V attenuation 20dB pulse width 150us"
  }
}

// ============================================================================
// ERROR HANDLING TESTS
// ============================================================================

test TestAmbiguousRequest_ShouldError {
  functions [ExpOrchestrator]
  args {
    reformatted_message "do some experiments with ultrasound"
  }
}

test TestMissingGridSize_ShouldError {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan gaussian at 1kHz"
  }
}

test TestMissingWaveform_ShouldError {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 at 1kHz"
  }
}

test TestInvalidGridFormat_ShouldError {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10 by 10 gaussian at 1kHz"
  }
}

// ============================================================================
// COMPLEX REALISTIC SCENARIOS
// ============================================================================

test TestComplexParameterSweep {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 to 30x30 gaussian at 1kHz to 3kHz amplitude 1V to 3V 20mm apart on X axis"
  }
}

test TestMultipleExperimentsWithDifferentOffsets {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz at position (0,0,1), then 20x20 sine at 2kHz at position (50,0,1)"
  }
}

test TestMixedWaveformsAndParameters {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 15x15 gaussian and sine and square at 2kHz and 3kHz amplitude 2V"
  }
}

test TestCompleteParameterSpecification {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 20x20 gaussian at 2.5kHz amplitude 2.5V attenuation 12dB pulse width 100us liftoff 3mm"
  }
}

// ============================================================================
// EDGE CASES
// ============================================================================

test TestSingleValueInRange {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz amplitude 2V to 2V"
  }
}

test TestLargeGridSize {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 100x100 gaussian at 1kHz"
  }
}

test TestVerySmallAmplitude {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 sine at 1kHz amplitude 0.1V"
  }
}

test TestHighFrequency {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 10000Hz"
  }
}

test TestDecimalGridSize {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10.5x10.5 gaussian at 1kHz"
  }
}

// ============================================================================
// NATURAL LANGUAGE VARIATIONS
// ============================================================================

test TestNaturalLanguageAndDelimiter {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz and then scan 20x20 sine at 2kHz"
  }
}

test TestNaturalLanguageNext {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz next scan 20x20 sine at 2kHz"
  }
}

test TestNaturalLanguageAfter {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz after that scan 20x20 sine at 2kHz"
  }
}

test TestVerboseDescription {
  functions [ExpOrchestrator]
  args {
    reformatted_message "please run a 10x10 grid scan using a gaussian waveform at a frequency of 1kHz with an amplitude of 2V"
  }
}

// ============================================================================
// RELATIVE POSITIONING TESTS
// ============================================================================

test TestRelativeMoveRight {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz, then move 20mm right and scan 10x10 sine at 2kHz"
  }
}

test TestRelativeMoveUp {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 gaussian at 1kHz, then shift 15mm up and scan 10x10 sine at 2kHz"
  }
}

// ============================================================================
// MULTIPLE OFFSET SPECIFICATIONS
// ============================================================================

test TestMultipleExperimentsXAxisSpacing {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 and 20x20 and 30x30 and 40x40 gaussian at 1kHz 10mm apart on X axis"
  }
}

test TestCombinedSpacingAndZHeight {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 and 20x20 gaussian at 1kHz 15mm apart on Y axis liftoff 5mm"
  }
}

// ====================================================== ERROR HANDLING TEST CASES ===============================================
// Test 1: Ambiguous spacing without axis specification
test TestErrorSpacingWithoutAxis {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 at 1kHz, 10mm apart"
  }
}

// Test 2: Unclear experiment description
test TestErrorUnclearRequest {
  functions [ExpOrchestrator]
  args {
    reformatted_message "do something with signals"
  }
}

// Test 3: Missing critical parameters
test TestErrorMissingParameters {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan at some frequency"
  }
}

// Test 4: Ambiguous range specification
test TestErrorAmbiguousRange {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 at frequencies between low and high"
  }
}

// Test 5: Conflicting spatial instructions
test TestErrorConflictingSpatial {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 at position (5,5,1) and also 10mm apart"
  }
}

// Test 6: Unparseable units
test TestErrorInvalidUnits {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 at 1kHz with amplitude 5 whatnots"
  }
}

// Test 7: Incomplete range specification
test TestErrorIncompleteRange {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan from 1V to"
  }
}

// Test 8: Vague waveform specification
test TestErrorVagueWaveform {
  functions [ExpOrchestrator]
  args {
    reformatted_message "scan 10x10 with some kind of wave at 1kHz"
  }
}

