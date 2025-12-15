// list of tools to set params for experiment
class SetNumericControlTool {
    tool_name "set_numeric_control" @description("Use this tool to set the value of a numeric control on the VI front panel")
    control_name string @description("Name of the numeric control to set")
    value float @description("Value to set the numeric control to")
}

class SelectComboBoxTool {
    tool_name "select_combo_box" @description("Use this tool to select an item from a combo box control on the VI front panel")
    combo_box_name string @description("Name of the combo box control")
    item string @description("Item to select from the combo box")
}

class SelectTabTool {
    tool_name "select_tab" @description("Use this tool to select a tab in a tab control on the VI front panel")
    tab_control_name string @description("Name of the tab control")
    index int @description("Index of the tab to select (0-based)")
}

// list of tools to interact with Labview (not dynamic)
class RunOpenViTool {
    tool_name "run_open_vi" @description("Use this tool to open and run a LabVIEW VI")
    run_vi bool @description("Set to true to run the VI after opening it")
}

class ConnectToViTool {
    tool_name "connect_to_vi" @description("Use this tool to connect to a running LabVIEW VI")
    vi_path string @description("Path to the LabVIEW VI to connect to")
}

class HandleSaveDialogTool {
    tool_name "handle_save_dialog" @description("Use this tool to handle the save dialog in LabVIEW")
    save_directory string @description("Directory to save the file to")
    file_name string @description("Name of the file to save")
}

class PressButtonTool {
    tool_name "press_button" @description("Use this tool to press a button on the VI front panel")
    button_name string @description("Name of the button to press")
}

class SetButtonStateTool {
    tool_name "set_button_state" @description("Use this tool to set the state of a button on the VI front panel")
    button_name string @description("Name of the button to set")
    state bool @description("State to set the button to (true for pressed, false for unpressed)")
}
