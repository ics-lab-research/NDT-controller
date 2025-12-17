class ConversationMessage {
  role "user" | "assistant"
  content string
}

enum ExpAction {
  BASIC_CONTROL
  SINGLE_SCAN
  MULTIPLE_SCAN
  ASK_CLARIFICATION
}

class SignalParameter {
  key string
  value string
}

class Grid {
  rows int
  cols int
}

class RelativeOffset {
  x int
  y int
  z int
}

class Experiment {
  id string
  grid Grid
  signal SignalParameter[]
  relative_offset_mm RelativeOffset
  filename string
}

enum ScanStatus {
  IDLE
  IN_PROGRESS
  COMPLETED
  ERROR
}

class State {
  current_position RelativeOffset
  home_position RelativeOffset
  
}

// ==================Output models===================
class ExpRouterOutput {
  action ExpAction
  response string? @description("For ASK_CLARIFICATION only")
  reformatted_message string? @description("Clarified/reformatted user message")
}

class ExpOrchestratorOutput {
  number_of_scans int
  experiments Experiment[]
}