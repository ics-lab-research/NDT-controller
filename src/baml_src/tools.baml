class ToolResult {
    name string
    success bool
    output string | map<string, string>?
    error string?
}

class WaitForOperationCompleteTool {
    tool_name "wait_for_operation_complete" @description("Use this tool to wait until a specific operation is complete by monitoring an indicator on the VI front panel")
    exp_type ExpType
}