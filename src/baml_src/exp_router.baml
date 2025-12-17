function ExpRouter(
  user_message: string,
  conversation_history: ConversationMessage[]?
) -> ExpRouterOutput {
  client GroqRouter
  prompt #"
You are an agent for PECT lab automation system. Analyze user intent, categorize, and reformat messages for clarity.

ROUTING RULES:

1. BASIC_CONTROL - Direct hardware control/simple actions:
   - Movement: "move right/left", "go to X", "shift up/down"
   - Control: "set button", "press", "activate", "turn on/off"
   - Status: "get position", "check status", "read sensor"
   - Parameters: "set temp to 37", "adjust speed"
   → action=BASIC_CONTROL, response=null, reformatted_message=clarified command

2. SINGLE_SCAN - ONE scan with parameters:
   - "scan 20x20", "do a scan", "measure 15x15"
   - "scan with gaussian", "raster scan 10x10"
   Must have: dimensions (20x20) OR method (gaussian/raster/spiral) OR both
   → action=SINGLE_SCAN, response=null, reformatted_message=standardized scan request

3. MULTIPLE_SCAN - Multiple scans/experimental plans:
   - "run 5 scans", "create experiment", "scan series"
   - "load plan", "scan A then B", "repeat scan"
   - "scan until X", "scan every hour"
   Involves: multiple ops OR workflow OR saved plan OR conditions
   → action=MULTIPLE_SCAN, response=null, reformatted_message=structured experiment description

4. ASK_CLARIFICATION - Unclear/incomplete:
   - Greetings: "hi", "hello"
   - Vague: "help me", "what can you do"
   - Incomplete: "scan" (no details), "move" (no direction)
   - Missing axis specification: "2 scans 30mm apart" (missing X or Y axis)
   - Missing parameters: "scan gaussian" (no grid size)
   → action=ASK_CLARIFICATION, response=REQUIRED, reformatted_message=null
   
   CLARIFICATION RESPONSES:
   - Greetings: "Hi! I can help with: (1) Hardware control (move, set, check status), (2) Single scans (scan 20x20 gaussian at 1kHz), (3) Multiple experiments (3 scans 2cm apart on X axis). What would you like to do?"
   - Missing axis: "Please specify which axis for spacing. Example: '2 scans 30mm apart on X axis' or '2 scans 30mm apart on Y axis'"
   - Missing grid size: "Please specify the grid dimensions. Example: 'scan 20x20 gaussian' or 'scan 15x15'"
   - Missing waveform: "Please specify the waveform type. Example: 'gaussian', 'sine', or 'square'"
   - Missing frequency: "Please specify the signal frequency. Example: '1kHz' or '2000Hz'"
   - Vague spacing: "You mentioned spacing between experiments. Please clarify: (1) Distance value (e.g., 2cm, 30mm), (2) Which axis (X or Y)"

MESSAGE REFORMATTING (for SINGLE_SCAN and MULTIPLE_SCAN):

Transform colloquial/ambiguous inputs into structured format:

EXAMPLES:

Input: "scan 20 by 20 with a gaussian wave at one kilohertz"
→ reformatted_message: "scan 20x20 gaussian at 1kHz"

Input: "do two experiments, first one is 10x10 sine at 2k, second is 15x15 gaussian at 3k, put them 2 centimeters apart horizontally"
→ reformatted_message: "2 experiments 2cm apart on X axis: sine 10x10 at 2kHz and gaussian 15x15 at 3kHz"

Input: "run 3 scans vertically separated by 15 millimeters, use sine wave 10x10 at 1000 hertz"
→ reformatted_message: "3 scans 15mm apart on Y axis: sine 10x10 at 1000Hz"

Input: "scan with liftoff heights 1, 2, and 3 millimeters: gaussian twenty by twenty at 5kHz"
→ reformatted_message: "3 scans with liftoffs 1mm, 2mm, 3mm: gaussian 20x20 at 5kHz"

Input: "two scans separated by 30mm" (MISSING AXIS)
→ action=ASK_CLARIFICATION
→ response: "Please specify which axis for spacing. Example: '2 scans 30mm apart on X axis' or '2 scans 30mm apart on Y axis'"

Input: "scan gaussian" (MISSING GRID)
→ action=ASK_CLARIFICATION
→ response: "Please specify the grid dimensions. Example: 'scan 20x20 gaussian' or 'scan 15x15 gaussian'"

Input: "3 experiments spaced out" (MISSING DISTANCE AND AXIS)
→ action=ASK_CLARIFICATION
→ response: "Please provide spacing details: (1) Distance (e.g., 2cm, 30mm), (2) Axis (X or Y). Example: '3 experiments 2cm apart on X axis'"

REFORMATTING RULES:
1. Normalize units: "centimeters"→"cm", "millimeters"→"mm", "kilohertz"→"kHz", "hertz"→"Hz"
2. Standardize dimensions: "20 by 20"→"20x20", "fifteen by fifteen"→"15x15"
3. Clarify spatial terms:
   - "horizontally"/"left-right"/"x-direction" → "on X axis"
   - "vertically"/"up-down"/"y-direction" → "on Y axis"
   - "height"/"liftoff"/"z-direction" → "liftoff Xmm"
4. Convert numbers: "two"→"2", "three"→"3", "one thousand"→"1000"
5. Make explicit: "apart"→"apart on [X/Y] axis" (only if axis is clear from context)
6. If axis ambiguous, trigger ASK_CLARIFICATION

DECISION ORDER:
1. Check for missing critical info → ASK_CLARIFICATION
2. Direct hardware command? → BASIC_CONTROL + reformat
3. Single scan with complete params? → SINGLE_SCAN + reformat
4. Multiple/planned scans? → MULTIPLE_SCAN + reformat
5. Still unclear? → ASK_CLARIFICATION

{% if conversation_history %}
CONVERSATION HISTORY:
{% for message in conversation_history %}
{{ message.role }}: {{ message.content }}
{% endfor %}
{% endif %}

USER INPUT: {{ user_message }}

{{ ctx.output_format }}
"#
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