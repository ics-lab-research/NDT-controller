function ExpExecutor(
    plan: string,
) -> (ConnectToViTool | GetNumericIndicatorTool | GetViStatusTool | HandleSaveDialogTool | PressButtonTool | RunOpenViTool | SelectComboBoxTool | SelectTabTool | SetButtonStateTool | SetNumericControlTool | StopViTool)[] {
  client GroqRouter
  prompt #"
AVAILABLE FUNCTIONS

connect_to_vi(vi_path) - Connect to VI file and also opens the front panel if not already open
get_numeric_indicator(indicator_name) - Get a numeric indicator value from the front panel
get_vi_status() - Get the current status of the connected VI
handle_save_dialog(save_directory, file_name) - Handle the save dialog in LabVIEW
press_button(button_name) - Press a button on the VI front panel
run_open_vi(run_vi) - Open and run a LabVIEW VI
select_combo_box(combo_box_name, item) - Select an item from a combo box control on the VI front panel
select_tab(tab_control_name, index) - Select a tab in a tab control on the VI front panel
set_button_state(button_name, state) - Set the state of a button on the VI front panel
set_numeric_control(control_name, value) - Set the value of a numeric control on the VI front panel
stop_vi(close_labview) - Stop the currently running VI, optionally closing the front panel


"#
}

