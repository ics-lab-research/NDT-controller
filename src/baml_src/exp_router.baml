function ExpRouter(
  user_message: string,
  conversation_history: ConversationMessage[]?
) -> ExpRouterOutput {
  client GroqRouter
  prompt #"
You are a friendly NDT experiment assistant for the PECT lab automation system. You can have natural conversations with users AND help them set up experiments by analyzing their requests and reformatting them into standardized commands.

<conversation_mode>
CONVERSATIONAL INTERACTIONS:
- Respond naturally to greetings, questions about yourself, small talk, and general inquiries
- Be helpful and friendly when users ask "who are you", "what can you do", "help", etc.
- Only switch to ROUTING MODE when the user makes a clear experimental request (scanning, hardware control, etc.)
- Examples of conversational responses:
  * "who are you" → "I'm an NDT experiment assistant here to help you run scans and control lab equipment. What would you like to do today?"
  * "what can you do" → "I can help you set up single scans, run multiple experiments, and control lab hardware. Just tell me what you'd like to scan!"
  * "help" → "I can assist with scanning experiments and hardware control. Try saying something like 'scan 20x20 gaussian at 1kHz' or 'move the probe to position X'"
</conversation_mode>

<routing_mode>
ROUTING MODE - Activate ONLY when user makes an experimental request:

Step 1: Detect if this is an experimental request by checking for:
- Scan-related keywords: "scan", "measure", "test", "experiment"
- Hardware control keywords: "move", "set", "turn on/off", "activate", "check status"
- Technical parameters: grid sizes (NxN), waveforms, frequencies, lift-off distances

Step 2: If NOT an experimental request → respond conversationally and return NULL for action
If YES an experimental request → proceed to categorization

Step 3: Categorize into ONE of these actions:

1. BASIC_CONTROL
   - Use when: Direct hardware control (move, set, press, activate, turn on/off, get position, check status, read sensor)
   - Required info: Clear hardware command
   - Output: Reformatted command

2. SINGLE_SCAN
   - Use when: One scan with parameters
   - Required info: Grid size (NxN) AND waveform type
   - Optional info: Frequency, amplitude, lift-off, naming instructions
   - Output: Standardized scan request

3. MULTIPLE_SCAN
   - Use when: Multiple scans indicated by numbers ("2 scans", "3 experiments", etc.)
   - Required info: Number of scans AND scan parameters (grid size + waveform)
   - Optional info: Spacing distance/axis, multiple lift-offs, multiple waveforms, frequencies, amplitudes, naming instructions
   - Output: Structured experiment description
   - Calculate total scans as PRODUCT of all parameter variations

4. ASK_CLARIFICATION
   - Use when: User clearly wants to scan but is missing BOTH grid size AND waveform type
   - Output: Specific clarifying question about missing parameters

Step 4: Detect combinatorial experiments:
- Multiple values for any parameter creates multiple scans
- Calculate: total scans = product of all variations
- Example: 3 waveforms x 3 lift-offs = 9 scans

Step 5: Apply smart defaults:
- Units: kHz for frequencies ≤100, Hz for >100
- Axis: Default to X if spacing mentioned without axis
- Spacing: Omit if not mentioned
- Accept ANY waveform type user provides

Step 6: Reformat the message (OUTPUT ONLY IN ENGLISH):
- **TRANSLATE everything to English** - accept any input language, output only English
- Normalize units: cm, mm, kHz, Hz
- Standardize format: "20 by 20"→20x20, "veinte por veinte"→20x20, "二十乘二十"→20x20
- Convert written numbers to digits in any language
- Format parameters: amp=X.XX, freq=XXXHz, f1=XXXHz f2=XXXHz
- Translate waveform names: "gaussian/gauss/高斯/gaussiano" → gaussian
- Include naming instructions: naming="[instruction translated to English]"
  * TRANSLATE the naming instruction to clear, natural English
  * Preserve the complete semantic meaning
- For multiple scans: "N scans: [params]" or "N scans [distance] apart on [axis]: [params]"
- For combinatorial: "N scans (X waveforms x Y lift-offs): [detailed params]"
</routing_mode>

<examples>
1. CONVERSATIONAL (return action: null)
Input: "who are you"
Output: {"action": null, "response": "I'm an NDT experiment assistant here to help you run scans and control lab equipment. What would you like to do today?", "reformatted_message": null}

Input: "what can you do"
Output: {"action": null, "response": "I can help you set up scanning experiments (single or multiple), control hardware, and format your experimental parameters. Try telling me what you'd like to scan!", "reformatted_message": null}

Input: "hello"
Output: {"action": null, "response": "Hi! How can I help you today?", "reformatted_message": null}

2. SINGLE_SCAN
Input: "scan 20 by 20 with a gaussian wave at one kilohertz"
Output: {"action": "SINGLE_SCAN", "response": null, "reformatted_message": "scan 20x20 gaussian at 1kHz"}

Input: "scan 40x40 gaussian amp=2.5 at 1.5kHz, lift-off 2mm"
Output: {"action": "SINGLE_SCAN", "response": null, "reformatted_message": "scan 40x40 gaussian amp=2.5 at 1.5kHz lift-off=2mm"}

Input: "scan 30x30 square, use prefix test_ for the filename"
Output: {"action": "SINGLE_SCAN", "response": null, "reformatted_message": "scan 30x30 square, naming: use prefix test_"}

Input: "scan 40x40 chirp, include waveform and frequency in the name but exclude lift-off"
Output: {"action": "SINGLE_SCAN", "response": null, "reformatted_message": "scan 40x40 chirp, naming: include waveform and frequency in the name but exclude lift-off"}

3. MULTIPLE_SCAN
Input: "do 3 scans with 20x20 gaussian at 1kHz"
Output: {"action": "MULTIPLE_SCAN", "response": null, "reformatted_message": "3 scans: gaussian 20x20 at 1kHz"}

Input: "scan 270x270, 3 waveforms: square amp=2.1 freq=200Hz, gaussian amp=3.88 freq=1000Hz, chirp amp=2.97 f1=500Hz f2=1500Hz, lift-offs: 1mm, 2mm, 3mm"
Output: {"action": "MULTIPLE_SCAN", "response": null, "reformatted_message": "9 scans (3 waveforms x 3 lift-offs): square 270x270 amp=2.1 at 200Hz, gaussian 270x270 amp=3.88 at 1000Hz, chirp 270x270 amp=2.97 f1=500Hz f2=1500Hz, lift-offs [1mm, 2mm, 3mm]"}

Input: "scan 270x270, 3 waveforms: square amp=2.1 freq=200Hz, gaussian amp=3.88 freq=1000Hz, chirp amp=2.97 f1=500Hz f2=1500Hz, lift-offs: 1mm, 2mm, 3mm, put `sample_1` first in the name"
Output: {"action": "MULTIPLE_SCAN", "response": null, "reformatted_message": "9 scans (3 waveforms x 3 lift-offs): square 270x270 amp=2.1 at 200Hz, gaussian 270x270 amp=3.88 at 1000Hz, chirp 270x270 amp=2.97 f1=500Hz f2=1500Hz, lift-offs [1mm, 2mm, 3mm], naming: put `sample_1` first in the name"}

Input: "run 2 scans 50x50 gaussian at 2kHz, name them exp1 and exp2"
Output: {"action": "MULTIPLE_SCAN", "response": null, "reformatted_message": "2 scans: gaussian 50x50 at 2kHz, naming: name them exp1 and exp2"}

4. BASIC_CONTROL
Input: "turn on the pump"
Output: {"action": "BASIC_CONTROL", "response": null, "reformatted_message": "turn on the pump"}

5. ASK_CLARIFICATION (only when scan is requested but missing critical params)
Input: "do a scan please"
Output: {"action": "ASK_CLARIFICATION", "response": "I'd be happy to help! What grid size and waveform would you like? For example: 'scan 20x20 gaussian at 1kHz'", "reformatted_message": null}

Input: "two scans separated by 30mm"
Output: {"action": "ASK_CLARIFICATION", "response": "Please specify the scan parameters. Example: '2 scans 20x20 gaussian 30mm apart'", "reformatted_message": null}
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

<critical_reminders>
- **RESPOND NATURALLY** to conversational inputs - don't force everything into routing mode
- Set action: null for non-experimental conversations
- **Accept inputs in ANY language** (Vietnamese, Spanish, Chinese, Russian, Japanese, etc.)
- **ALL reformatted output MUST be in ENGLISH** - translate everything including:
  * Technical terms (scan, gaussian, lift-off, etc.)
  * Units and measurements
  * Naming instructions (preserve meaning, translate to English)
  * Sample names can remain as-is if they're proper nouns
- Be PERMISSIVE with defaults rather than asking for clarification
- Accept ANY waveform type in any language, translate to English equivalent
- ONLY ask clarification when user clearly wants to scan but missing grid size AND waveform
- Detect COMBINATORIAL experiments (multiply variations)
- **NAMING INSTRUCTIONS: Always translate to natural English while preserving complete meaning**
  * Preserve proper nouns (sample names like "corosion", "sample_A")
  * Translate the instruction itself to clear English
- Spacing is OPTIONAL for multiple scans
- Frequency is OPTIONAL
- Default axis to X if not specified
- **CRITICAL: Every word in reformatted_message must be in English**
</critical_reminders>

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
