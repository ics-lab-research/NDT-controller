function ExpOrchestrator(
  user_message: string, 
) -> ExpOrchestratorOutput {
  client GroqRouter
  prompt #"
Lab automation agent: convert natural language to structured experiments with filenames and spatial offsets.

PARSING:
1. Split: commas, "and", "then", "next", "after"
2. Persist params unless changed
3. Infer keys:
   - "20x20"→grid rows/cols
   - "gaussian"/"sine"/"square"→waveform
   - "1kHz"/"2000Hz"→frequency_hz
   - "2.5V"→amplitude
   - "10dB"→attenuation
   - "100us"/"5ms"→duration/pulse_width
   - Any signal param→add to signal map
4. EXPAND ranges: "10 to 30"→[10,20,30], "1000-1200Hz"→[1000,1050,1100,1150,1200]
5. CARTESIAN PRODUCT: multiple ranges = all combinations
66. Each experiment = single values, NOT arrays
7. IDs: exp_1, exp_2, exp_3...

RELATIVE OFFSET CALCULATION:
- ALL experiments default to: RelativeOffset(0, 0, 1) - z=1mm liftoff default
- NO automatic x-increment or y-increment between experiments
- User MUST explicitly specify spatial relationships

SPATIAL PARSING:
- "Xcm apart on X axis" / "Xmm apart on X axis" / "X axis spacing Xcm": increment x by X between experiments
  - "2 experiments 2cm apart on X axis": exp_1 (0,0,1), exp_2 (20,0,1)
  - "3 scans 30mm X axis spacing": exp_1 (0,0,1), exp_2 (30,0,1), exp_3 (60,0,1)
- "Xcm apart on Y axis" / "Xmm apart on Y axis" / "Y axis spacing Xcm": increment y by X between experiments
  - "2 experiments 15mm apart on Y axis": exp_1 (0,0,1), exp_2 (0,15,1)
  - "3 scans 10mm Y axis spacing": exp_1 (0,0,1), exp_2 (0,10,1), exp_3 (0,20,1)
- "liftoff X" / "lift off Xmm" / "Z height X": set z value for that experiment
  - "experiment 1 and liftoff 2 is 3mm": exp_1 (0,0,1), exp_2 (0,0,3)
  - "first scan liftoff 2mm, second liftoff 5mm": exp_1 (0,0,2), exp_2 (0,0,5)
- "at position (x,y,z)" / "offset (x,y,z)": use explicit coordinates
  - "scan at (10, 20, 2)": exp (10, 20, 2)
- "move X left/right" / "shift Y up/down": add to previous x/y
  - After exp at (0,0,1), "move 5mm right": next exp at (5,0,1)

OFFSET PRIORITY (highest to lowest):
1. Explicit coordinates: "at position (x,y,z)"
2. Axis-specific spacing: "Xcm apart on X/Y axis" → increment specified axis by X
3. Liftoff instruction: affects only z value
4. Default: RelativeOffset(0, 0, 1) for ALL experiments

IMPORTANT:
- If user says "apart" or "spacing" WITHOUT specifying X axis or Y axis → return error message
- Error message: "Please specify axis for spacing (e.g., '2cm apart on X axis' or '15mm apart on Y axis')"
- All experiments at same location (0,0,1) unless user explicitly specifies otherwise

SIGNAL MAP:
- Flexible key-value pairs
- Common keys: waveform, frequency_hz, amplitude, attenuation, pulse_width, duty_cycle, phase
- Add ANY signal params mentioned

FILENAMES:
- Format: {waveform}_{rows}x{cols}_{key_signal_params}
- Include most distinctive signal params (freq, amp, atten)
- Max 50 chars, unique per experiment
- Example: gaussian_20x20_freq1000_amp2.5V

EXAMPLES:

"scan 10x10 gaussian at 1kHz and 20x20 at 2kHz"
→ 2 experiments:
- exp_1: grid 10x10, signal {waveform: gaussian, frequency_hz: 1000}, offset (0,0,1), filename "gaussian_10x10_freq1000"
- exp_2: grid 20x20, signal {waveform: gaussian, frequency_hz: 2000}, offset (0,0,1), filename "gaussian_20x20_freq2000"

"do 2 experiments 2cm apart on X axis: sine 50x50 at 5kHz and gaussian 30x30 at 3kHz"
→ 2 experiments:
- exp_1: grid 50x50, signal {waveform: sine, frequency_hz: 5000}, offset (0,0,1), filename "sine_50x50_freq5000"
- exp_2: grid 30x30, signal {waveform: gaussian, frequency_hz: 3000}, offset (20,0,1), filename "gaussian_30x30_freq3000"

"experiment 1 and liftoff 2 is 3mm: gaussian 20x20 1kHz and sine 20x20 2kHz"
→ 2 experiments:
- exp_1: grid 20x20, signal {waveform: gaussian, frequency_hz: 1000}, offset (0,0,1), filename "gaussian_20x20_freq1000"
- exp_2: grid 20x20, signal {waveform: sine, frequency_hz: 2000}, offset (0,0,3), filename "sine_20x20_freq2000"

"3 scans 15mm spacing on Y axis, liftoffs 1mm, 2mm, 3mm: sine 10x10 at 1kHz"
→ 3 experiments:
- exp_1: grid 10x10, signal {waveform: sine, frequency_hz: 1000}, offset (0,0,1), filename "sine_10x10_freq1000"
- exp_2: grid 10x10, signal {waveform: sine, frequency_hz: 1000}, offset (0,15,2), filename "sine_10x10_freq1000_2"
- exp_3: grid 10x10, signal {waveform: sine, frequency_hz: 1000}, offset (0,30,3), filename "sine_10x10_freq1000_3"

"2 scans 10mm apart: gaussian 15x15 at 2kHz"
→ ERROR: "Please specify axis for spacing (e.g., '10mm apart on X axis' or '10mm apart on Y axis')"

<input>
{{ user_message }}
</input>

{{ ctx.output_format }}
"#
}

// Basic single experiment tests
test TestBasicSingleExperiment {
  functions [ExpOrchestrator]
  args {
    user_message "scan 10x10 gaussian at 1kHz"
  }
}

test TestSingleExperimentWithMultipleParams {
  functions [ExpOrchestrator]
  args {
    user_message "scan 20x20 sine at 5kHz amplitude 3V attenuation 15dB"
  }
}

// Multiple experiments without spatial offset
test TestMultipleExperimentsBasic {
  functions [ExpOrchestrator]
  args {
    user_message "scan 10x10 gaussian at 1kHz amplitude 2V and 20x20 at 2kHz"
  }
}

test TestMultipleExperimentsAllAtOrigin {
  functions [ExpOrchestrator]
  args {
    user_message "gaussian 20x20 at 1kHz and sine 20x20 at 2kHz and square 30x30 at 3kHz"
  }
}

test TestMultipleExperimentsAllAtOrigin2 {
  functions [ExpOrchestrator]
  args {
    user_message "gaussian 20x20 from 1000Hz to 1200Hz"
  }
}

// X-axis spacing tests
test TestXAxisSpacingCentimeters {
  functions [ExpOrchestrator]
  args {
    user_message "do 2 experiments 2cm apart on X axis: sine 50x50 at 5kHz and gaussian 30x30 at 3kHz"
  }
}

test TestXAxisSpacingMillimeters {
  functions [ExpOrchestrator]
  args {
    user_message "3 scans 30mm apart on X axis: gaussian 15x15 at 2kHz"
  }
}

test TestXAxisSpacingAlternativeSyntax {
  functions [ExpOrchestrator]
  args {
    user_message "2 experiments with X axis spacing 25mm: sine 10x10 at 1kHz and square 10x10 at 1.5kHz"
  }
}

// Y-axis spacing tests
test TestYAxisSpacingMillimeters {
  functions [ExpOrchestrator]
  args {
    user_message "3 scans 15mm spacing on Y axis: sine 10x10 at 1kHz"
  }
}

test TestYAxisSpacingCentimeters {
  functions [ExpOrchestrator]
  args {
    user_message "2 experiments 3cm apart on Y axis: gaussian 20x20 at 4kHz and sine 20x20 at 5kHz"
  }
}

// Liftoff tests
test TestLiftoffSingleValue {
  functions [ExpOrchestrator]
  args {
    user_message "scan 20x20 gaussian at 2kHz with liftoff 5mm"
  }
}

test TestLiftoffMultipleExperiments {
  functions [ExpOrchestrator]
  args {
    user_message "experiment 1 and liftoff 2 is 3mm: gaussian 20x20 1kHz and sine 20x20 2kHz"
  }
}

test TestLiftoffWithSpacing {
  functions [ExpOrchestrator]
  args {
    user_message "3 scans 15mm spacing on Y axis, liftoffs 1mm, 2mm, 3mm: sine 10x10 at 1kHz"
  }
}

test TestIndividualLiftoffs {
  functions [ExpOrchestrator]
  args {
    user_message "first scan liftoff 2mm, second liftoff 5mm: gaussian 15x15 at 3kHz and square 15x15 at 3kHz"
  }
}

// Explicit position tests
test TestExplicitPosition {
  functions [ExpOrchestrator]
  args {
    user_message "scan at position (10, 20, 2): gaussian 20x20 at 2kHz"
  }
}

test TestMultipleExplicitPositions {
  functions [ExpOrchestrator]
  args {
    user_message "scan at (0,0,1) gaussian 10x10 1kHz, at (15,0,2) sine 10x10 2kHz, at (30,0,3) square 10x10 3kHz"
  }
}

test TestExplicitOffsetSyntax {
  functions [ExpOrchestrator]
  args {
    user_message "gaussian 20x20 at 2kHz with offset (5, 10, 1.5)"
  }
}

// Range expansion tests
test TestFrequencyRange {
  functions [ExpOrchestrator]
  args {
    user_message "scan 10x10 gaussian at 1000-1200Hz"
  }
}

test TestSimpleRange {
  functions [ExpOrchestrator]
  args {
    user_message "scan 15x15 sine at frequencies 1 to 3 kHz"
  }
}

test TestAmplitudeRange {
  functions [ExpOrchestrator]
  args {
    user_message "scan 20x20 gaussian at 2kHz amplitude 1V to 3V"
  }
}

// Cartesian product tests
test TestCartesianProductTwoRanges {
  functions [ExpOrchestrator]
  args {
    user_message "scan 10x10 gaussian at 1-2kHz amplitude 1-2V"
  }
}

test TestCartesianProductThreeRanges {
  functions [ExpOrchestrator]
  args {
    user_message "scan 10x10 sine frequency 1-2kHz amplitude 1-2V attenuation 5-10dB"
  }
}

// Signal parameter variety tests
test TestPulseWidthParameter {
  functions [ExpOrchestrator]
  args {
    user_message "scan 15x15 square at 10kHz pulse width 100us"
  }
}

test TestDutyCycleParameter {
  functions [ExpOrchestrator]
  args {
    user_message "scan 20x20 square at 5kHz duty cycle 25%"
  }
}

test TestPhaseParameter {
  functions [ExpOrchestrator]
  args {
    user_message "scan 10x10 sine at 1kHz phase 90 degrees"
  }
}

test TestMultipleSignalParams {
  functions [ExpOrchestrator]
  args {
    user_message "scan 20x20 gaussian at 3kHz amplitude 2.5V attenuation 12dB pulse width 50us duty cycle 50%"
  }
}

// Error case tests
test TestSpacingWithoutAxisError {
  functions [ExpOrchestrator]
  args {
    user_message "2 scans 10mm apart: gaussian 15x15 at 2kHz"
  }
}

test TestSpacingWithoutAxisError2 {
  functions [ExpOrchestrator]
  args {
    user_message "3 experiments with 5cm spacing: sine 10x10 at 1kHz"
  }
}

// Complex combination tests
test TestComplexXSpacingWithRanges {
  functions [ExpOrchestrator]
  args {
    user_message "2 scans 20mm apart on X axis: gaussian 10x10 at 1-2kHz"
  }
}

test TestComplexYSpacingWithMultipleParams {
  functions [ExpOrchestrator]
  args {
    user_message "3 experiments 10mm spacing on Y axis: sine 20x20 at 2kHz amplitude 3V attenuation 10dB"
  }
}

test TestComplexMixedSpacingAndLiftoff {
  functions [ExpOrchestrator]
  args {
    user_message "2 scans 15mm apart on X axis, first liftoff 1mm second liftoff 3mm: gaussian 25x25 at 4kHz amplitude 2V"
  }
}

// Persistence tests
test TestParameterPersistence {
  functions [ExpOrchestrator]
  args {
    user_message "scan 10x10 gaussian at 1kHz amplitude 2V, then 20x20 at 2kHz, then 30x30"
  }
}

test TestGridPersistence {
  functions [ExpOrchestrator]
  args {
    user_message "scan 15x15 gaussian at 1kHz, then sine at 2kHz, then square at 3kHz"
  }
}

// Waveform variety tests
test TestSquareWaveform {
  functions [ExpOrchestrator]
  args {
    user_message "scan 20x20 square at 10kHz"
  }
}

test TestMixedWaveforms {
  functions [ExpOrchestrator]
  args {
    user_message "gaussian 10x10 at 1kHz, sine 10x10 at 2kHz, square 10x10 at 3kHz"
  }
}

// Natural language variations
test TestNaturalLanguageVariation1 {
  functions [ExpOrchestrator]
  args {
    user_message "do a scan with 20x20 grid using gaussian waveform at frequency 2000Hz"
  }
}

test TestNaturalLanguageVariation2 {
  functions [ExpOrchestrator]
  args {
    user_message "run experiment: sine wave, 15 by 15 grid, 3.5 kHz, 2.8 volts"
  }
}

test TestNaturalLanguageVariation3 {
  functions [ExpOrchestrator]
  args {
    user_message "I need to scan a 10x10 area with sine at 1kHz then move 2cm right on X axis and scan 10x10 with gaussian at 1kHz"
  }
}

// Edge cases
test TestSinglePointGrid {
  functions [ExpOrchestrator]
  args {
    user_message "scan 1x1 gaussian at 5kHz"
  }
}

test TestLargeGrid {
  functions [ExpOrchestrator]
  args {
    user_message "scan 100x100 sine at 10kHz"
  }
}

test TestHighFrequency {
  functions [ExpOrchestrator]
  args {
    user_message "scan 20x20 gaussian at 100kHz"
  }
}

test TestLowFrequency {
  functions [ExpOrchestrator]
  args {
    user_message "scan 20x20 sine at 100Hz"
  }
}

test TestZeroLiftoff {
  functions [ExpOrchestrator]
  args {
    user_message "scan 10x10 gaussian at 1kHz liftoff 0mm"
  }
}

// Duration/time-based parameters
test TestDurationParameter {
  functions [ExpOrchestrator]
  args {
    user_message "scan 15x15 gaussian at 2kHz duration 5ms"
  }
}

test TestMultipleTimeParams {
  functions [ExpOrchestrator]
  args {
    user_message "scan 20x20 square at 5kHz pulse width 200us duration 10ms"
  }
}

