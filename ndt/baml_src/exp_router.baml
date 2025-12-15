enum ExpAction {
    BASIC_CONTROL
    SINGLE_SCAN
    MULTIPLE_SCAN
    ASK_CLARIFICATION
}

class ExpRouterOutput {
  action ExpAction
  response string? @description("message to show user, only for ASK_CLARIFICATION")
}

function ExpRouter(
  user_message: string,
  conversation_history: ConversationMessage[]?
) -> ExpRouterOutput {
  client GroqRouter
  prompt #"
You are a coordinator for a PECT lab automation system. Analyze the user's message and categorize the intent.

ROUTING DECISION LOGIC

OPTION 1: BASIC_CONTROL
Use when user wants direct hardware control or simple single actions:
- Movement commands: "move to right", "move left", "go to position X", "shift up/down"
- Button/actuator control: "set button stop", "press button", "activate relay", "turn on/off"
- Status queries: "get position", "check status", "read sensor"
- Simple parameter changes: "set temperature to 37", "adjust speed"

Keywords: move, set, press, activate, turn, go, shift, position, button, stop, start

→ action="BASIC_CONTROL"
→ response: null (system will execute command directly)

OPTION 2: SINGLE_SCAN
Use when user requests ONE scanning operation with clear parameters:
- Explicit single scan: "scan 20x20", "do a scan", "perform one scan"
- Scan with method specified: "scan 20x20 with gaussian", "run a raster scan 10x10"
- One-time measurement: "measure this area 15x15", "take a scan of 5x5 grid"

Must have EITHER:
- Grid dimensions (e.g., "20x20", "10x10")
- OR scan method (e.g., "gaussian", "raster", "spiral")
- OR both

Keywords: scan, measure, take, one scan, single scan, do a scan

→ action="SINGLE_SCAN"
→ response: null (system will execute scan)

OPTION 3: MULTIPLE_SCAN
Use when user wants to create/load/execute a complex experimental plan with multiple scans:
- Explicit multiple scans: "run 5 scans", "do multiple scans", "scan 3 times"
- Experimental plan requests: "create experiment", "generate experiment plan", "design study"
- Loading saved plans: "load plan", "use saved plan", "resume experiment"
- Sequential operations: "scan area A then B", "do scan series"
- Plans with conditions: "scan until X", "repeat scan every hour"

Must involve EITHER:
- Multiple scan operations
- OR experimental workflow/plan
- OR saved plan reference
- OR conditional/repeated scanning

Keywords: multiple, experiment, plan, create, generate, load, series, repeat, schedule

→ action="MULTIPLE_SCAN"
→ response: null (system will invoke plan creation/loading agent)

OPTION 4: ASK_CLARIFICATION
Use when:
- Simple greeting without context: "hi", "hello", "hey"
- Ambiguous intent: "do something", "help me", "what can you do"
- Incomplete scan specification: "scan for me" (no dimensions or method)
- Missing critical parameters: "move" (no direction), "scan" (no details)
- Unclear scope: "test this sample" (no methodology)

→ action="ASK_CLARIFICATION"
→ response: REQUIRED - Ask specific question to clarify user intent:
  - For greetings: "Hi! Would you like to: (1) Control the system directly, (2) Run a single scan, or (3) Create/load an experimental plan?"
  - For incomplete scans: "I can help you scan. Please specify: grid dimensions (e.g., 20x20) and/or scan method (e.g., gaussian, raster)"
  - For vague requests: Ask for the specific missing information

DECISION TREE
1. Is it a direct hardware command? → BASIC_CONTROL
2. Is it a single, one-time scan with parameters? → SINGLE_SCAN
3. Does it involve multiple scans or experimental planning? → MULTIPLE_SCAN
4. Is the intent unclear or information missing? → ASK_CLARIFICATION

{% if conversation_history %}
CONVERSATION HISTORY:
{% for message in conversation_history %}
{{ message.role }}: {{ message.content }}
{% endfor %}
{% endif %}

USER MESSAGE:
{{ user_message }}

{{ ctx.output_format }}
"#
}


test TestExpRouter {
  functions [ExpRouter]
  args {
    user_message "scan for me 20x20 using gaussian"
  }
}

test TestExpRouter2 {
  functions [ExpRouter]
  args {
    user_message "move to right by 10mm"
  }
}

test TestExpRouter3 {
  functions [ExpRouter]
  args {
    user_message "I am at coordinate (0, 0), moving to (5, 5)"
  }
}

test TestExpRouter4 {
  functions [ExpRouter]
  args {
    user_message "set speed to 5 mm/s"
  }
}

test TestExpRouter5 {
  functions [ExpRouter]
  args {
    user_message "who are you?"
  }
}