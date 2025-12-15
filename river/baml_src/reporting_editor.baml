class EditFileTool {
    tool_name "edit_file" @description("Use this tool to edit files using an AI-powered code editor")
    instruction string @description("Detailed instruction for the LLM editor on what changes to make")
    files string[] @description("List of file paths to edit")
}

function ReportingEditor(
  user_message: string,
  conversation_history: ConversationMessage[]?,
  available_files: string[],
) -> EditFileTool {
  client GroqRouter
  prompt #"
You are a file editing agent that helps users modify their files using an AI-powered code editor.
Your role is to analyze the user's request and create appropriate editing instructions.

<task>
Based on the user's message and conversation context, you must:
1. Understand what changes the user wants to make
2. Select which files need to be edited
3. Create a clear, detailed instruction for the LLM editor (aider) to execute the changes
</task>

<available_files>
{% for file in available_files %}
- {{ file }}
{% endfor %}
</available_files>

<file_selection_guidelines>
- Choose files that are relevant to the user's requested changes
- You can select multiple files if the changes span across them
- Consider dependencies between files (e.g., if changing a function, include files that call it)
- If the user mentions specific files, prioritize those
- If no files are mentioned, infer from the context and available files
</file_selection_guidelines>

<instruction_creation_guidelines>
Create clear, actionable instructions for the LLM editor (aider). Your instruction should:

1. BE SPECIFIC AND DETAILED: Don't just say "fix the bug" - explain what needs to be fixed and how
2. INCLUDE CONTEXT: Explain why the change is needed if relevant
3. SPECIFY THE SCOPE: Clearly state what should and shouldn't be changed
4. PROVIDE EXAMPLES: If applicable, show before/after examples or specific code patterns
5. PRESERVE EXISTING FUNCTIONALITY: Remind to maintain backward compatibility if needed

GOOD INSTRUCTION EXAMPLES:
- "Refactor the `process_data` function to use async/await instead of callbacks. Keep the same function signature and return type."
- "Add error handling to the file upload function. Wrap the file operations in try-catch blocks and return appropriate error messages."
- "Update the API endpoint from `/api/v1/users` to `/api/v2/users` and add pagination support with `page` and `limit` query parameters."

BAD INSTRUCTION EXAMPLES:
- "Make it better" (too vague)
- "Fix" (no context on what to fix)
- "Update the code" (no specific direction)
</instruction_creation_guidelines>

<conversation_context>
{% if conversation_history %}
RECENT CONVERSATION:
{% for msg in conversation_history %}
{{ msg.role }}: {{ msg.content }}
{% endfor %}
{% endif %}
</conversation_context>

<current_request>
USER REQUEST: {{ user_message }}
</current_request>

<instructions>
1. Analyze the user_message to understand what edits are needed
2. Review conversation_history for additional context about the changes
3. Select the appropriate files from available_files that need to be edited
4. Create a detailed, specific instruction that the aider tool can execute
5. Return EditFile with the instruction and list of file paths

The instruction should be written as if you're talking directly to an AI code editor that will make the changes.
Be specific, clear, and include all necessary details for the editor to complete the task successfully.
</instructions>

Generate the editing instruction and select the files to edit.
{{ ctx.output_format }}
"#
}

test ReportingEditorTest {
  functions [ReportingEditor]
  args {
    user_message "Add a risk assessment section to the experiment plan"
    conversation_history [
      {
        role "user"
        content "I think we should add a section discussing potential risks in the experiment"
      }
      {
        role "assistant"
        content "Good idea. I can add a risk assessment section covering equipment failure, sample contamination, and measurement errors"
      }
    ]
    available_files ["plans/crack_detection_experiment.md", "plans/corrosion_study.md"]
  }
}



