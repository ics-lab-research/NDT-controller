class ConversationMessage {
  role "user" | "assistant"
  content string
}

class Error {
  error string @description("Error message describing what went wrong")
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

enum ExpType {
  MOVEMENT
  SCAN
}

class State {
  current_position RelativeOffset
  home_position RelativeOffset
}

// ==================Output models===================
class ExpRouterOutput {
  action ExpAction
  response string? @description("only for ASK_CLARIFICATION")
  reformatted_message string? @description("for all except ASK_CLARIFICATION")
}

class ExpOrchestratorOutput {
  number_of_scans int
  experiments Experiment[]
}