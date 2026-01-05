function ExpRouter(
  user_message: string,
  conversation_history: ConversationMessage[]?
) -> ExpRouterOutput {
  client GroqRouter
  prompt #"
You are an NDT experiment assistant for the PECT lab. You handle casual conversations AND experimental requests.

<mode_detection>
CONVERSATIONAL MODE (action: null):
- Greetings, questions about capabilities, help requests, small talk
- Examples:
  * "who are you" → "I'm an NDT assistant helping with scans and lab equipment."
  * "what can you do" → "I help set up scans and control hardware. Try: 'scan 20x20 gaussian at 1kHz'"
  * "help" → "I assist with experiments and hardware. Say 'scan NxN [waveform]' or 'move probe to X'"

EXPERIMENTAL MODE (categorize action):
Detect keywords: scan/measure/test/experiment, move/set/activate, grid sizes, waveforms, frequencies
</mode_detection>

<actions>
1. BASIC_CONTROL: Direct hardware commands (move, turn on/off, check status, read sensor)

2. SINGLE_SCAN: One scan with grid size + waveform
   - Optional: frequency, amplitude, lift-off, naming

3. MULTIPLE_SCAN: Multiple scans from count or parameter variations
   - Total scans = product of all variations (3 waveforms x 3 lift-offs = 9 scans)
   - Optional: spacing distance/axis, naming

4. ASK_CLARIFICATION: Scan request missing BOTH grid size AND waveform
</actions>

<formatting_rules>
**INPUT: Accept ANY language | OUTPUT: ENGLISH ONLY**

- Translate all terms: scan/gaussian/lift-off → English equivalents
- Normalize: "20 by 20"/"veinte por veinte"/"二十乘二十" → 20x20
- Units: kHz (≤100), Hz (>100), cm, mm
- Parameters: amp=X.XX, freq=XXXHz, f1=XXXHz f2=XXXHz
- Naming: Translate instruction to English, preserve proper nouns
- Multiple scans: "N scans: [params]" or "N scans [distance] apart on [axis]: [params]"
- Combinatorial: "N scans (X waveforms x Y lift-offs): [detailed params]"

Smart defaults:
- Axis: X if unspecified
- Omit spacing/frequency if not mentioned
- Accept any waveform type
</formatting_rules>

<examples>
CONVERSATIONAL:
{"action": null, "response": "Hi! How can I help you today?", "reformatted_message": null}

SINGLE_SCAN:
"scan 20 by 20 gaussian at 1kHz" → {"action": "SINGLE_SCAN", "response": null, "reformatted_message": "scan 20x20 gaussian at 1kHz"}
"scan 40x40 chirp, include waveform in name" → "scan 40x40 chirp, naming: include waveform in name"

MULTIPLE_SCAN:
"3 scans 20x20 gaussian at 1kHz" → "3 scans: gaussian 20x20 at 1kHz"
"scan 270x270, square amp=2.1 at 200Hz, gaussian amp=3.88 at 1kHz, chirp amp=2.97 f1=500Hz f2=1500Hz, lift-offs: 1mm, 2mm, 3mm" → "9 scans (3 waveforms x 3 lift-offs): square 270x270 amp=2.1 at 200Hz, gaussian 270x270 amp=3.88 at 1kHz, chirp 270x270 amp=2.97 f1=500Hz f2=1500Hz, lift-offs [1mm, 2mm, 3mm]"

BASIC_CONTROL:
"turn on pump" → {"action": "BASIC_CONTROL", "response": null, "reformatted_message": "turn on the pump"}

ASK_CLARIFICATION:
"do a scan" → {"action": "ASK_CLARIFICATION", "response": "What grid size and waveform? Example: 'scan 20x20 gaussian at 1kHz'", "reformatted_message": null}
</examples>

{% if conversation_history %}
<conversation_history>
{% for message in conversation_history %}
{{ message.role }}: {{ message.content }}
{% endfor %}
</conversation_history>
{% endif %}

<user_message>
{{ user_message }}
</user_message>

{{ ctx.output_format }}
"#
}

// ============================================================================
// BASIC_CONTROL Tests
// ============================================================================

test TestBasicControl_Movement {
  functions [ExpRouter]
  args {
    user_message "move right 5mm"
  }
}

test TestBasicControl_SetCommand {
  functions [ExpRouter]
  args {
    user_message "set probe height to 10cm"
  }
}

test TestBasicControl_ToggleOn {
  functions [ExpRouter]
  args {
    user_message "turn on the pump"
  }
}

test TestBasicControl_ToggleOff {
  functions [ExpRouter]
  args {
    user_message "turn off the laser"
  }
}

test TestBasicControl_GetStatus {
  functions [ExpRouter]
  args {
    user_message "check motor status"
  }
}

test TestBasicControl_ReadSensor {
  functions [ExpRouter]
  args {
    user_message "read temperature sensor"
  }
}

test TestBasicControl_GetPosition {
  functions [ExpRouter]
  args {
    user_message "get current position"
  }
}

test TestBasicControl_PressButton {
  functions [ExpRouter]
  args {
    user_message "press the emergency stop button"
  }
}

// ============================================================================
// SINGLE_SCAN Tests - Complete Parameters
// ============================================================================

test TestSingleScan_AllParametersPresent {
  functions [ExpRouter]
  args {
    user_message "scan 20x20 gaussian at 1kHz"
  }
}

test TestSingleScan_WrittenNumbers {
  functions [ExpRouter]
  args {
    user_message "scan 20 by 20 with a gaussian wave at one kilohertz"
  }
}

test TestSingleScan_DifferentWaveform_Sine {
  functions [ExpRouter]
  args {
    user_message "scan 15x15 sine at 2kHz"
  }
}

test TestSingleScan_DifferentWaveform_Square {
  functions [ExpRouter]
  args {
    user_message "scan 10x10 square wave at 500Hz"
  }
}

test TestSingleScan_DifferentWaveform_Raster {
  functions [ExpRouter]
  args {
    user_message "scan 25x25 raster at 3kHz"
  }
}

test TestSingleScan_DifferentWaveform_Spiral {
  functions [ExpRouter]
  args {
    user_message "scan 30x30 spiral at 1500Hz"
  }
}

test TestSingleScan_LargeFrequency {
  functions [ExpRouter]
  args {
    user_message "scan 20x20 gaussian at 10000Hz"
  }
}

test TestSingleScan_SmallGrid {
  functions [ExpRouter]
  args {
    user_message "scan 5x5 sine at 100Hz"
  }
}

test TestSingleScan_VerboseFormat {
  functions [ExpRouter]
  args {
    user_message "perform a scan with 20 by 20 grid using gaussian waveform at frequency of 1 kilohertz"
  }
}

// ============================================================================
// SINGLE_SCAN Tests - Missing Parameters (ASK_CLARIFICATION)
// ============================================================================

test TestSingleScan_MissingGrid {
  functions [ExpRouter]
  args {
    user_message "scan gaussian at 1kHz"
  }
}

test TestSingleScan_MissingWaveform {
  functions [ExpRouter]
  args {
    user_message "scan 20x20 at 1kHz"
  }
}

test TestSingleScan_MissingFrequency {
  functions [ExpRouter]
  args {
    user_message "scan 20x20 gaussian"
  }
}

test TestSingleScan_MissingGridAndFrequency {
  functions [ExpRouter]
  args {
    user_message "scan gaussian"
  }
}

test TestSingleScan_OnlyGrid {
  functions [ExpRouter]
  args {
    user_message "scan 15x15"
  }
}

// ============================================================================
// MULTIPLE_SCAN Tests - With Spacing
// ============================================================================

test TestMultipleScan_TwoScans_XAxis {
  functions [ExpRouter]
  args {
    user_message "2 scans 2cm apart on X axis: first is 10x10 gaussian at 1kHz, second is 15x15 sine at 2kHz"
  }
}

test TestMultipleScan_TwoScans_YAxis {
  functions [ExpRouter]
  args {
    user_message "2 scans 30mm apart on Y axis: 20x20 square at 500Hz and 25x25 gaussian at 1kHz"
  }
}

test TestMultipleScan_ThreeScans {
  functions [ExpRouter]
  args {
    user_message "3 experiments 2cm apart on X axis: sine 10x10 at 2kHz, gaussian 15x15 at 3kHz, and square 20x20 at 1kHz"
  }
}

test TestMultipleScan_WrittenDirection_Horizontally {
  functions [ExpRouter]
  args {
    user_message "do two experiments, first one is 10x10 sine at 2k, second is 15x15 gaussian at 3k, put them 2 centimeters apart horizontally"
  }
}

test TestMultipleScan_WrittenDirection_Vertically {
  functions [ExpRouter]
  args {
    user_message "two scans vertically separated by 50mm: 20x20 gaussian at 1kHz and 20x20 sine at 2kHz"
  }
}

test TestMultipleScan_WrittenDirection_LeftRight {
  functions [ExpRouter]
  args {
    user_message "3 scans left to right 1cm apart: all 15x15 gaussian at 1500Hz"
  }
}

test TestMultipleScan_WrittenDirection_UpDown {
  functions [ExpRouter]
  args {
    user_message "two experiments up and down 3cm spacing: 10x10 sine at 1kHz and 12x12 square at 2kHz"
  }
}

test TestMultipleScan_MillimeterSpacing {
  functions [ExpRouter]
  args {
    user_message "2 scans 50mm apart on Y axis: both 20x20 gaussian at 1kHz"
  }
}

test TestMultipleScan_LargeSpacing {
  functions [ExpRouter]
  args {
    user_message "5 experiments 10cm apart on X axis: all 10x10 sine at 500Hz"
  }
}

// ============================================================================
// MULTIPLE_SCAN Tests - With Liftoff Heights
// ============================================================================

test TestMultipleScan_TwoHeights {
  functions [ExpRouter]
  args {
    user_message "2 scans at liftoff heights 5mm and 10mm: both 20x20 gaussian at 1kHz"
  }
}

test TestMultipleScan_ThreeHeights {
  functions [ExpRouter]
  args {
    user_message "3 experiments at heights 2cm, 4cm, 6cm: all 15x15 sine at 2kHz"
  }
}

test TestMultipleScan_HeightsWithDifferentScans {
  functions [ExpRouter]
  args {
    user_message "scan at 5mm: 10x10 gaussian 1kHz, then at 10mm: 15x15 sine 2kHz"
  }
}

// ============================================================================
// MULTIPLE_SCAN Tests - Missing Parameters (ASK_CLARIFICATION)
// ============================================================================

test TestMultipleScan_MissingAxis {
  functions [ExpRouter]
  args {
    user_message "two scans separated by 30mm"
  }
}

test TestMultipleScan_MissingDistance {
  functions [ExpRouter]
  args {
    user_message "3 scans on X axis: 10x10 gaussian at 1kHz each"
  }
}

test TestMultipleScan_MissingDistanceAndAxis {
  functions [ExpRouter]
  args {
    user_message "2 experiments: 10x10 sine at 1kHz and 15x15 gaussian at 2kHz"
  }
}

test TestMultipleScan_AmbiguousSpacing {
  functions [ExpRouter]
  args {
    user_message "do 2 scans apart: 20x20 gaussian at 1kHz"
  }
}

test TestMultipleScan_MissingScanParameters {
  functions [ExpRouter]
  args {
    user_message "3 scans 2cm apart on X axis"
  }
}

test TestMultipleScan_MissingWaveformInSeries {
  functions [ExpRouter]
  args {
    user_message "2 scans 1cm apart on Y axis: 10x10 at 1kHz and 15x15 at 2kHz"
  }
}

// ============================================================================
// ASK_CLARIFICATION Tests - Greetings and Vague Requests
// ============================================================================

test TestClarification_Greeting_Hello {
  functions [ExpRouter]
  args {
    user_message "hello"
  }
}

test TestClarification_Greeting_Hi {
  functions [ExpRouter]
  args {
    user_message "hi"
  }
}

test TestClarification_Greeting_HeyThere {
  functions [ExpRouter]
  args {
    user_message "hey there"
  }
}

test TestClarification_VagueRequest {
  functions [ExpRouter]
  args {
    user_message "can you help me?"
  }
}

test TestClarification_JustScan {
  functions [ExpRouter]
  args {
    user_message "scan"
  }
}

test TestClarification_Ambiguous {
  functions [ExpRouter]
  args {
    user_message "do something"
  }
}

test TestClarification_UnclearIntent {
  functions [ExpRouter]
  args {
    user_message "I need to run an experiment"
  }
}

// ============================================================================
// Edge Cases and Format Variations
// ============================================================================

test TestEdgeCase_NumberFormat_Written {
  functions [ExpRouter]
  args {
    user_message "scan fifteen by fifteen gaussian at two thousand hertz"
  }
}

test TestEdgeCase_NumberFormat_Mixed {
  functions [ExpRouter]
  args {
    user_message "scan 20 by twenty gaussian at 1000 Hz"
  }
}

test TestEdgeCase_UnitVariation_Centimeters {
  functions [ExpRouter]
  args {
    user_message "2 scans 5 centimeters apart on X axis: 10x10 gaussian at 1kHz each"
  }
}

test TestEdgeCase_UnitVariation_Millimeters {
  functions [ExpRouter]
  args {
    user_message "3 experiments 25 millimeters apart on Y axis: 15x15 sine at 2kHz each"
  }
}

test TestEdgeCase_FrequencyFormat_kHz {
  functions [ExpRouter]
  args {
    user_message "scan 20x20 gaussian at 2.5kHz"
  }
}

test TestEdgeCase_FrequencyFormat_Hertz {
  functions [ExpRouter]
  args {
    user_message "scan 20x20 sine at 2500 hertz"
  }
}

test TestEdgeCase_CasualLanguage {
  functions [ExpRouter]
  args {
    user_message "run a quick 10x10 gaussian scan at 1k"
  }
}

test TestEdgeCase_ExtraWhitespace {
  functions [ExpRouter]
  args {
    user_message "scan  20x20   gaussian   at  1kHz"
  }
}

test TestEdgeCase_NoSpaceInGrid {
  functions [ExpRouter]
  args {
    user_message "scan 20x20 gaussian at 1kHz"
  }
}

test TestEdgeCase_SpaceInGrid {
  functions [ExpRouter]
  args {
    user_message "scan 20 x 20 gaussian at 1kHz"
  }
}

// ============================================================================
// Conversation History Tests
// ============================================================================

test TestConversationHistory_FollowUp {
  functions [ExpRouter]
  args {
    user_message "now make it 15x15"
    conversation_history [
      {role: "user", content: "scan 20x20 gaussian at 1kHz"},
      {role: "assistant", content: "Scanning 20x20 gaussian at 1kHz"}
    ]
  }
}

test TestConversationHistory_MissingParameter {
  functions [ExpRouter]
  args {
    user_message "use gaussian waveform"
    conversation_history [
      {role: "user", content: "scan 20x20 at 1kHz"},
      {role: "assistant", content: "Please specify the waveform type"}
    ]
  }
}

test TestConversationHistory_AddSpacing {
  functions [ExpRouter]
  args {
    user_message "on X axis"
    conversation_history [
      {role: "user", content: "2 scans 30mm apart"},
      {role: "assistant", content: "Please specify which axis for spacing"}
    ]
  }
}

// ============================================================================
// Complex Realistic Scenarios
// ============================================================================

test TestRealistic_DetailedSingleScan {
  functions [ExpRouter]
  args {
    user_message "I need to perform a 25x25 grid scan using a gaussian waveform at a frequency of 1.5 kilohertz"
  }
}

test TestRealistic_ComplexMultipleScan {
  functions [ExpRouter]
  args {
    user_message "run 4 experiments horizontally spaced 3 centimeters apart: first scan is 10x10 gaussian at 1kHz, second is 12x12 sine at 1.5kHz, third is 15x15 square at 2kHz, fourth is 20x20 raster at 2.5kHz"
  }
}

test TestRealistic_MixedUnits {
  functions [ExpRouter]
  args {
    user_message "3 scans 50mm apart on Y axis: all twenty by twenty gaussian at one kilohertz"
  }
}

test TestRealistic_PartialInfo_NeedsGrid {
  functions [ExpRouter]
  args {
    user_message "I want to do a gaussian scan at 2kHz but I'm not sure about the grid size"
  }
}

test TestRealistic_PartialInfo_NeedsFrequency {
  functions [ExpRouter]
  args {
    user_message "scan 30x30 sine wave"
  }
}
