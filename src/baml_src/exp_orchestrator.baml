function ExpOrchestrator(
  reformatted_message: string, 
) -> ExpOrchestratorOutput | ResponseError {
  client GroqRouter
  prompt #"
You are a lab automation parser converting natural language experiment descriptions into structured JSON.

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

6. NAMING CONVENTIONS
Detect patterns:
- "naming: [instruction]", "sample: [name]", "prefix/suffix [name]"
- "[parameter] first/last", "use/omit [parameter] in filename"
- "call it [name]" or "filename [name]"

Default format: {waveform}_{rows}x{cols}_{distinctive_params}
Apply directives: sample positioning, prefix/suffix, custom names
Rules: Include distinctive params, max 50 chars, unique (add _2, _3 if needed), lowercase, underscores for spaces

7. ASSIGN IDs
Sequential: exp_1, exp_2, exp_3, ...
</instructions>

<examples>
<example1>
Input: "10x10 gaussian at 1kHz"
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
    "filename": "gaussian_10x10_1khz"
  }]
}
</example1>

<example2>
Input: "10x10 and 20x20 square at 500Hz and 1kHz"
Output: 4 experiments (cartesian: 2 grids x 2 frequencies)
[exp_1: 10x10 at 500Hz, exp_2: 10x10 at 1kHz, exp_3: 20x20 at 500Hz, exp_4: 20x20 at 1kHz]
</example2>

<example3>
Input: "20x20 sine at 2kHz, lift-offs [1mm, 2mm, 3mm]"
Output: 3 experiments with z values [1, 2, 3], filenames include Z1, Z2, Z3
</example3>

<example4>
Input: "15x15 gaussian at 800Hz, run 3 times, 10mm apart on X axis"
Output: 3 experiments at x offsets [0, 10, 20]
</example4>

<example5>
Input: "30x30 chirp f1=100Hz f2=500Hz amp=2.5V"
Output: Use frequency_start_hz/frequency_end_hz instead of frequency_hz
</example5>

<example6>
Input: "25x25 square at 1.5kHz, naming: use prefix test_sample_"
Output: filename = "test_sample_square_25x25_1.5khz"
</example6>

<example7>
Input: "20x20 gaussian at 2kHz, naming: steel_plate first"
Output: filename = "steel_plate_gaussian_20x20_2khz"
</example7>

<example8>
Input: "10x10 square at 1kHz, 5mm apart"
Output: {"error": "Please specify axis for spacing (e.g., '5mm apart on X axis')"}
</example8>
</examples>

<critical_rules>
- Default offset: (x:0, y:0, z:1) unless specified
- Cartesian product for multiple ranges
- Normalize frequency to Hz (1kHz → 1000)
- Chirp uses frequency_start_hz and frequency_end_hz
- Error if spacing without axis
- Unique filenames (add _2, _3 suffixes)
- Only answer if confident, otherwise return error JSON
</critical_rules>

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

