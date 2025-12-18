function ExpRouter(
  user_message: string,
  conversation_history: ConversationMessage[]?
) -> ExpRouterOutput | Error{
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

test TestError {
  functions [ExpRouter]
  args {
    user_message "do the experiment"
  }
}

test TestExpRouter {
  functions [ExpRouter]
  args {
    user_message "who are you"
  }
}

// ============================================
// BASIC_CONTROL Tests
// ============================================

test TestBasicControl_Movement {
  functions [ExpRouter]
  args {
    user_message "move right 5mm"
  }
}

test TestBasicControl_Position {
  functions [ExpRouter]
  args {
    user_message "go to position X=10, Y=20"
  }
}

test TestBasicControl_Status {
  functions [ExpRouter]
  args {
    user_message "check current position"
  }
}

test TestBasicControl_Parameter {
  functions [ExpRouter]
  args {
    user_message "set temperature to 37 degrees"
  }
}

test TestBasicControl_Activation {
  functions [ExpRouter]
  args {
    user_message "turn on the pump"
  }
}

// ============================================
// SINGLE_SCAN Tests
// ============================================

test TestSingleScan_BasicDimensions {
  functions [ExpRouter]
  args {
    user_message "scan 20x20"
  }
}

test TestSingleScan_WithWaveform {
  functions [ExpRouter]
  args {
    user_message "scan 20x20 with gaussian"
  }
}

test TestSingleScan_Complete {
  functions [ExpRouter]
  args {
    user_message "scan 20 by 20 with a gaussian wave at one kilohertz"
  }
}

test TestSingleScan_RasterMethod {
  functions [ExpRouter]
  args {
    user_message "do a raster scan 15x15"
  }
}

test TestSingleScan_Colloquial {
  functions [ExpRouter]
  args {
    user_message "measure fifteen by fifteen with sine wave at 2k"
  }
}

test TestSingleScan_SpiralMethod {
  functions [ExpRouter]
  args {
    user_message "spiral scan 10x10 from 500Hz to 1000Hz"
  }
}

// ============================================
// MULTIPLE_SCAN Tests
// ============================================

test TestMultipleScan_SimpleCount {
  functions [ExpRouter]
  args {
    user_message "run 5 scans"
  }
}

test TestMultipleScan_WithSpacingX {
  functions [ExpRouter]
  args {
    user_message "do two experiments, first one is 10x10 sine at 2k, second is 15x15 gaussian at 3k, put them 2 centimeters apart horizontally"
  }
}

test TestMultipleScan_WithSpacingY {
  functions [ExpRouter]
  args {
    user_message "run 3 scans vertically separated by 15 millimeters, use sine wave 10x10 at 1000 hertz"
  }
}

test TestMultipleScan_LiftoffVariation {
  functions [ExpRouter]
  args {
    user_message "scan with liftoff heights 1, 2, and 3 millimeters: gaussian twenty by twenty at 5kHz"
  }
}

test TestMultipleScan_Sequential {
  functions [ExpRouter]
  args {
    user_message "scan A then scan B, both 20x20 gaussian"
  }
}

test TestMultipleScan_RepeatUntil {
  functions [ExpRouter]
  args {
    user_message "scan 10x10 every hour until temperature reaches 50"
  }
}

test TestMultipleScan_ExperimentPlan {
  functions [ExpRouter]
  args {
    user_message "create experiment with 4 scans at different frequencies"
  }
}

test TestMultipleScan_XAxisSpacing {
  functions [ExpRouter]
  args {
    user_message "3 scans 25mm apart on X axis, gaussian 20x20 at 1kHz"
  }
}

// ============================================
// ASK_CLARIFICATION Tests - Greetings
// ============================================

test TestClarification_Greeting1 {
  functions [ExpRouter]
  args {
    user_message "hi"
  }
}

test TestClarification_Greeting2 {
  functions [ExpRouter]
  args {
    user_message "hello there"
  }
}

test TestClarification_WhatCanYouDo {
  functions [ExpRouter]
  args {
    user_message "what can you do"
  }
}

// ============================================
// ASK_CLARIFICATION Tests - Missing Parameters
// ============================================

test TestClarification_MissingAxis {
  functions [ExpRouter]
  args {
    user_message "two scans separated by 30mm"
  }
}

test TestClarification_MissingGridSize {
  functions [ExpRouter]
  args {
    user_message "scan gaussian"
  }
}

test TestClarification_MissingWaveform {
  functions [ExpRouter]
  args {
    user_message "scan 20x20 at 1kHz"
  }
}

test TestClarification_MissingFrequency {
  functions [ExpRouter]
  args {
    user_message "scan 15x15 gaussian"
  }
}

test TestClarification_VagueSpacing {
  functions [ExpRouter]
  args {
    user_message "3 experiments spaced out"
  }
}

test TestClarification_IncompleteScan {
  functions [ExpRouter]
  args {
    user_message "scan"
  }
}

test TestClarification_IncompleteMove {
  functions [ExpRouter]
  args {
    user_message "move"
  }
}

test TestClarification_VagueHelp {
  functions [ExpRouter]
  args {
    user_message "help me with something"
  }
}

// ============================================
// EDGE CASES & COMPLEX SCENARIOS
// ============================================

test TestEdgeCase_MixedUnits {
  functions [ExpRouter]
  args {
    user_message "scan twenty by 20 with gaussian at 2 kilohertz"
  }
}

test TestEdgeCase_LongForm {
  functions [ExpRouter]
  args {
    user_message "I need to run three experiments separated by two centimeters along the horizontal axis using sine waveform on a ten by ten grid at one thousand hertz"
  }
}

test TestEdgeCase_AmbiguousAxis {
  functions [ExpRouter]
  args {
    user_message "4 scans 10mm apart"
  }
}

test TestEdgeCase_MultipleParameters {
  functions [ExpRouter]
  args {
    user_message "set speed to 100, temperature to 25, and pressure to 1 bar"
  }
}

test TestEdgeCase_LoadPlan {
  functions [ExpRouter]
  args {
    user_message "load experiment plan from file"
  }
}

// ============================================
// CONVERSATION CONTEXT Tests
// ============================================

test TestContext_FollowUp {
  functions [ExpRouter]
  args {
    user_message "now do the same but at 3kHz"
    conversation_history [
      {role: "user", content: "scan 20x20 gaussian at 1kHz"},
      {role: "assistant", content: "Executing scan 20x20 gaussian at 1kHz"}
    ]
  }
}

test TestContext_ClarificationFollowUp {
  functions [ExpRouter]
  args {
    user_message "on the X axis and 20x20 using basic sine"
    conversation_history [
      {role: "user", content: "two scans separated by 30mm"},
      {role: "assistant", content: "Please specify which axis for spacing"}
    ]
  }
}

test TestContext_ParameterAddition {
  functions [ExpRouter]
  args {
    user_message "add gaussian waveform"
    conversation_history [
      {role: "user", content: "scan 15x15 at 2kHz"},
      {role: "assistant", content: "Please specify the waveform type"}
    ]
  }
}

// ============================================
// UNIT CONVERSION Tests
// ============================================

test TestUnitConversion_Centimeters {
  functions [ExpRouter]
  args {
    user_message "3 scans 5 centimeters apart on Y axis, sine 10x10 at 1kHz"
  }
}

test TestUnitConversion_Millimeters {
  functions [ExpRouter]
  args {
    user_message "2 scans 15 millimeters apart on X axis"
  }
}

test TestUnitConversion_Kilohertz {
  functions [ExpRouter]
  args {
    user_message "scan 20x20 gaussian at 2 kilohertz"
  }
}

test TestUnitConversion_Hertz {
  functions [ExpRouter]
  args {
    user_message "scan 10x10 sine at 1500 hertz"
  }
}

// ============================================
// SPATIAL TERM Tests
// ============================================

test TestSpatialTerm_Horizontally {
  functions [ExpRouter]
  args {
    user_message "2 scans horizontally 3cm apart, gaussian 15x15 at 1kHz"
  }
}

test TestSpatialTerm_Vertically {
  functions [ExpRouter]
  args {
    user_message "4 scans vertically 2cm apart, sine 10x10 at 2kHz"
  }
}

test TestSpatialTerm_LeftRight {
  functions [ExpRouter]
  args {
    user_message "3 scans left-right direction 25mm spacing, gaussian 20x20 at 1kHz"
  }
}

test TestSpatialTerm_UpDown {
  functions [ExpRouter]
  args {
    user_message "3 scans up-down direction 30mm spacing, sine 15x15 at 3kHz"
  }
}

test TestSpatialTerm_XDirection {
  functions [ExpRouter]
  args {
    user_message "2 scans in x-direction 4cm apart, gaussian 10x10 at 1kHz"
  }
}

test TestSpatialTerm_YDirection {
  functions [ExpRouter]
  args {
    user_message "2 scans in y-direction 5cm apart, sine 12x12 at 2kHz"
  }
}