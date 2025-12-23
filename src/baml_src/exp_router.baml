function ExpRouter(
  user_message: string,
  conversation_history: ConversationMessage[]?
) -> ExpRouterOutput {
  client GroqRouter
  prompt #"
You are a routing agent for the PECT lab automation system. Your task is to analyze user requests, categorize them into one of four actions, and reformat messages into standardized commands.

<instructions>
TASK INSTRUCTIONS:

Step 1: Analyze the user input and identify what information is present or missing.

Step 2: Categorize the request into ONE of these actions:

1. BASIC_CONTROL
   - Use when: User requests direct hardware control (move, set, press, activate, turn on/off, get position, check status, read sensor)
   - Required info: Clear hardware command
   - Output: Reformatted command

2. SINGLE_SCAN
   - Use when: User requests one scan with parameters
   - Required info: Grid size (NxN format) AND waveform type (gaussian/raster/spiral/sine/square) AND frequency (with unit)
   - Output: Standardized scan request

3. MULTIPLE_SCAN
   - Use when: User requests multiple scans or experimental series
   - Required info: All SINGLE_SCAN requirements PLUS either:
     * Spacing distance (value + unit) AND axis (X or Y), OR
     * Multiple liftoff heights specified
   - Output: Structured experiment description

4. ASK_CLARIFICATION
   - Use when: Critical information is missing or request is vague
   - Triggers: Greetings, incomplete parameters, ambiguous spacing
   - Output: Specific clarifying question

Step 3: Reformat the message (if not asking for clarification):
- Normalize units: centimeters→cm, millimeters→mm, kilohertz→kHz, hertz→Hz
- Standardize format: "20 by 20"→20x20, "two"→2, "three"→3
- Make spatial terms explicit: horizontally/left-right→"on X axis", vertically/up-down→"on Y axis"
- Convert written numbers to digits: "one thousand"→1000, "fifteen"→15

Step 4: If asking for clarification, use these specific responses:
- Greeting: "Hi! I can help with: (1) Hardware control (move, set, check status), (2) Single scans (scan 20x20 gaussian at 1kHz), (3) Multiple experiments (3 scans 2cm apart on X axis). What would you like to do?"
- Missing grid: "Please specify the grid dimensions. Example: 'scan 20x20 gaussian' or 'scan 15x15'"
- Missing waveform: "Please specify the waveform type. Example: 'gaussian', 'sine', or 'square'"
- Missing frequency: "Please specify the signal frequency. Example: '1kHz' or '2000Hz'"
- Missing axis only: "Please specify which axis for spacing. Example: '2 scans 30mm apart on X axis' or '2 scans 30mm apart on Y axis'"
- Missing distance and axis: "Please provide spacing details: (1) Distance (e.g., 2cm, 30mm), (2) Axis (X or Y). Example: '3 experiments 2cm apart on X axis'"
</instructions>

<examples>
Input: "scan 20 by 20 with a gaussian wave at one kilohertz"
Output: {"action": "SINGLE_SCAN", "response": null, "reformatted_message": "scan 20x20 gaussian at 1kHz"}

Input: "do two experiments, first one is 10x10 sine at 2k, second is 15x15 gaussian at 3k, put them 2 centimeters apart horizontally"
Output: {"action": "MULTIPLE_SCAN", "response": null, "reformatted_message": "2 experiments 2cm apart on X axis: sine 10x10 at 2kHz and gaussian 15x15 at 3kHz"}

Input: "turn on the pump"
Output: {"action": "BASIC_CONTROL", "response": null, "reformatted_message": "turn on the pump"}

Input: "hello"
Output: {"action": "ASK_CLARIFICATION", "response": "Hi! I can help with: (1) Hardware control (move, set, check status), (2) Single scans (scan 20x20 gaussian at 1kHz), (3) Multiple experiments (3 scans 2cm apart on X axis). What would you like to do?", "reformatted_message": null}

Input: "two scans separated by 30mm"
Output: {"action": "ASK_CLARIFICATION", "response": "Please specify which axis for spacing. Example: '2 scans 30mm apart on X axis' or '2 scans 30mm apart on Y axis'", "reformatted_message": null}

Input: "scan gaussian"
Output: {"action": "ASK_CLARIFICATION", "response": "Please specify the grid dimensions. Example: 'scan 20x20 gaussian' or 'scan 15x15 gaussian'", "reformatted_message": null}
</examples>

<critical_reminders>
- ALWAYS check for ALL required parameters before categorizing
- If ANY required parameter is missing, use ASK_CLARIFICATION
- For MULTIPLE_SCAN with spacing: BOTH distance AND axis are required
- When axis is ambiguous (e.g., "apart" without direction), ask for clarification
- Only reformat when you have complete information
- Think step-by-step before answering
</critical_reminders>

IMPORTANT: If you cannot determine the appropriate action or are unsure about any parameters, use ASK_CLARIFICATION. Only categorize as BASIC_CONTROL, SINGLE_SCAN, or MULTIPLE_SCAN when you are very confident all required information is present.

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
