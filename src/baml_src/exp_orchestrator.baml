function ExpOrchestrator(
  reformatted_message: string, 
) -> ExpOrchestratorOutput | ResponseError {
  client GroqRouter
  prompt #"
You are a lab automation parser that converts natural language experiment descriptions into structured JSON configurations. Your task is to extract spatial coordinates, grid dimensions, and signal parameters from experiment descriptions.

<user_message>
{{ reformatted_message }}
</user_message>

You are a lab automation parser that converts natural language experiment descriptions into structured JSON configurations. Your task is to extract spatial coordinates, grid dimensions, signal parameters, and naming conventions from experiment descriptions.

<instructions>
DETAILED INSTRUCTIONS:

1. ANALYZE THE REQUEST
Think through the input before processing:
- What experiments are requested?
- What ranges need expansion?
- What spatial relationships exist?
- What signal parameters are specified?
- What naming conventions are specified?

If unclear or uncertain, respond with JSON error schema: {"error": "I don't know how to parse this request. Please provide more details about [specific missing information]."}

2. PARSE THE TEXT
Split input on delimiters: commas, "and", "then", "next", "after"

3. EXTRACT PARAMETERS
Identify patterns and extract values:
- "NxM"→ grid dimensions (rows:N, cols:M)
- "gaussian", "sine", "square", "chirp" → waveform type
- "XkHz" or "XHz" → frequency_hz (normalize to Hz: 1kHz = 1000)
- "f1=XHz", "f2=XHz" → chirp frequencies (start/end)
- "XV" → amplitude (preserve unit: "2.5V")
- "XdB" → attenuation (preserve unit: "10dB")
- "Xus", "Xms", "Xs" → pulse_width or duration (preserve unit: "100us")
- "lift-off", "liftoff", "z-height" → z-axis positioning values
- "sample:", "sample name" → sample identifier for naming

Parameters persist across experiments unless explicitly changed.

4. EXPAND RANGES
Only expand if confident about range specification:

NUMERIC RANGES (integer endpoints): "X to Y" → 3 equal steps
- "10 to 30" → [10, 20, 30]
- "1000-3000Hz" → [1000, 2000, 3000]

UNIT-BASED RANGES: Standard increments
- Voltage: "1V to 3V" → [1V, 2V, 3V]
- Frequency: "1kHz to 3kHz" → [1kHz, 2kHz, 3kHz]

EXPLICIT LISTS: Use as-is
- "lift-offs [1mm, 2mm, 3mm]" → [1, 2, 3] (z values in mm)
- "[10Hz, 50Hz, 100Hz]" → [10, 50, 100]

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
"liftoff Xmm" or "Z height Xmm" or "lift-off Xmm" → Set z value only, keep x:0, y:0
When multiple lift-off values specified (e.g., "[1mm, 2mm, 3mm]"), apply to z coordinate

PRIORITY 4 - RELATIVE MOVEMENT:
"move Xmm left/right" or "shift Xmm up/down" → Relative to previous offset

PRIORITY 5 - DEFAULT:
{x:0, y:0, z:1}

7. PARSE NAMING CONVENTIONS
Extract naming instructions from user message:

NAMING PATTERNS TO DETECT:
- "naming: [instruction]" → Explicit naming directive
- "sample: [name]" → Sample identifier to include
- "prefix [name]" → Add prefix to all filenames
- "suffix [name]" → Add suffix to all filenames
- "[parameter] first" → Put specified parameter at start of filename
- "[parameter] last" → Put specified parameter at end of filename
- "use [parameter] in filename" → Include specific parameter
- "omit [parameter] from filename" → Exclude specific parameter
- "call it [name]" → Use specific custom name for experiment(s)
- "filename [name]" → Use specific filename

NAMING ORDERS:
- "sample name first" → Start filename with sample identifier
- "waveform first" → Start filename with waveform type
- "frequency first" → Start filename with frequency value
- Default order if not specified: {waveform}_{grid}_{distinctive_params}

SAMPLE IDENTIFIERS:
- "sample: corrosion" → Include "corrosion" in filename
- "sample name: steel_plate" → Include "steel_plate" in filename
- Position based on order directive (first/last/default)

8. GENERATE FILENAMES
Format: Construct based on naming directives or use default pattern

Default pattern: {waveform}_{rows}x{cols}_{distinctive_params}

With naming directives:
- Apply sample name positioning (first/last)
- Apply prefix/suffix if specified
- Include/exclude parameters as directed
- Use custom names if provided for specific experiments

Rules:
- Include most distinctive signal parameters (frequency, amplitude, attenuation, chirp ranges)
- Maximum 50 characters
- Must be unique per experiment
- Add suffix _2, _3, etc. if duplicates exist
- Replace spaces with underscores
- Use lowercase for consistency unless user specifies otherwise

Examples:
- "sample name first" with "sample: corrosion" → "corrosion_square_270x270_200Hz_2.1"
- "prefix exp_" → "exp_gaussian_20x20_1kHz"
- Custom: "call it test_scan" → "test_scan" (for single experiment)
- Per-experiment naming: "call exp_1 baseline and exp_2 test" → apply specific names to specific experiments

9. ASSIGN EXPERIMENT IDS
Sequential format: exp_1, exp_2, exp_3, ...
</instructions>

<example>
Input: "9 scans (3 waveforms x 3 lift-offs): square 270x270 amp=2.1 at 200Hz, gaussian 270x270 amp=3.88 at 1000Hz, chirp 270x270 amp=2.97 f1=500Hz f2=1500Hz, lift-offs [1mm, 2mm, 3mm], sample: corrosion, naming: sample name first"

Processing steps:
1. Parse: 3 waveforms (square, gaussian, chirp) with different parameters
2. Parse: 3 lift-off values [1mm, 2mm, 3mm] for z-axis
3. Parse naming: "sample: corrosion" and "sample name first"
4. Generate 9 experiments (3 waveforms x 3 lift-offs = 9 combinations)
5. Apply naming convention: sample name first in filename
6. Apply lift-off values to z coordinate in offset

Output:
{
  "number_of_scans": 9,
  "experiments": [
    {
      "id": "exp_1",
      "grid": {"rows": 270, "cols": 270},
      "signal": [
        {"key": "waveform", "value": "square"},
        {"key": "frequency_hz", "value": "200"},
        {"key": "amplitude", "value": "2.1"}
      ],
      "relative_offset_mm": {"x": 0, "y": 0, "z": 1},
      "filename": "corrosion_square_270x270_200Hz_2.1"
    },
    {
      "id": "exp_2",
      "grid": {"rows": 270, "cols": 270},
      "signal": [
        {"key": "waveform", "value": "square"},
        {"key": "frequency_hz", "value": "200"},
        {"key": "amplitude", "value": "2.1"}
      ],
      "relative_offset_mm": {"x": 0, "y": 0, "z": 2},
      "filename": "corrosion_square_270x270_200Hz_2.1_2"
    },
    {
      "id": "exp_3",
      "grid": {"rows": 270, "cols": 270},
      "signal": [
        {"key": "waveform", "value": "square"},
        {"key": "frequency_hz", "value": "200"},
        {"key": "amplitude", "value": "2.1"}
      ],
      "relative_offset_mm": {"x": 0, "y": 0, "z": 3},
      "filename": "corrosion_square_270x270_200Hz_2.1_3"
    },
    {
      "id": "exp_4",
      "grid": {"rows": 270, "cols": 270},
      "signal": [
        {"key": "waveform", "value": "gaussian"},
        {"key": "frequency_hz", "value": "1000"},
        {"key": "amplitude", "value": "3.88"}
      ],
      "relative_offset_mm": {"x": 0, "y": 0, "z": 1},
      "filename": "corrosion_gaussian_270x270_1000Hz_3.88"
    },
    {
      "id": "exp_5",
      "grid": {"rows": 270, "cols": 270},
      "signal": [
        {"key": "waveform", "value": "gaussian"},
        {"key": "frequency_hz", "value": "1000"},
        {"key": "amplitude", "value": "3.88"}
      ],
      "relative_offset_mm": {"x": 0, "y": 0, "z": 2},
      "filename": "corrosion_gaussian_270x270_1000Hz_3.88_2"
    },
    {
      "id": "exp_6",
      "grid": {"rows": 270, "cols": 270},
      "signal": [
        {"key": "waveform", "value": "gaussian"},
        {"key": "frequency_hz", "value": "1000"},
        {"key": "amplitude", "value": "3.88"}
      ],
      "relative_offset_mm": {"x": 0, "y": 0, "z": 3},
      "filename": "corrosion_gaussian_270x270_1000Hz_3.88_3"
    },
    {
      "id": "exp_7",
      "grid": {"rows": 270, "cols": 270},
      "signal": [
        {"key": "waveform", "value": "chirp"},
        {"key": "frequency_start_hz", "value": "500"},
        {"key": "frequency_end_hz", "value": "1500"},
        {"key": "amplitude", "value": "2.97"}
      ],
      "relative_offset_mm": {"x": 0, "y": 0, "z": 1},
      "filename": "corrosion_chirp_270x270_500-1500Hz_2.97"
    },
    {
      "id": "exp_8",
      "grid": {"rows": 270, "cols": 270},
      "signal": [
        {"key": "waveform", "value": "chirp"},
        {"key": "frequency_start_hz", "value": "500"},
        {"key": "frequency_end_hz", "value": "1500"},
        {"key": "amplitude", "value": "2.97"}
      ],
      "relative_offset_mm": {"x": 0, "y": 0, "z": 2},
      "filename": "corrosion_chirp_270x270_500-1500Hz_2.97_2"
    },
    {
      "id": "exp_9",
      "grid": {"rows": 270, "cols": 270},
      "signal": [
        {"key": "waveform", "value": "chirp"},
        {"key": "frequency_start_hz", "value": "500"},
        {"key": "frequency_end_hz", "value": "1500"},
        {"key": "amplitude", "value": "2.97"}
      ],
      "relative_offset_mm": {"x": 0, "y": 0, "z": 3},
      "filename": "corrosion_chirp_270x270_500-1500Hz_2.97_3"
    }
  ]
}
</example>

<critical_reminders>
- Default offset is (x:0, y:0, z:1) for ALL experiments unless explicitly specified
- Multiple ranges create separate experiments with ALL combinations (Cartesian product)
- Parse naming conventions from user message and apply to filename generation
- Support naming patterns: sample name first/last, prefix/suffix, custom names, parameter ordering, per-experiment names
- Filenames must be unique - add _2, _3 suffixes to prevent duplicates
- Frequency must be normalized to Hz (1kHz → 1000)
- Chirp signals use frequency_start_hz and frequency_end_hz instead of frequency_hz
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

