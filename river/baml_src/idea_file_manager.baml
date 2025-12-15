class SearchReplaceBlock {
  search string @description("Exact code/text to find - must match precisely including whitespace")
  replace string @description("Replacement code/text with same indentation and formatting")
  language string @description("Programming language or 'markdown' for .md files")
}

class FileChange {
  file_path string @description("Exact path from available_files list")
  blocks SearchReplaceBlock[] @description("Search/replace operations for this file")
}

class SearchReplaceTool {
  files_to_change FileChange[] @description("Files to modify with their changes")
  reasoning string @description("Why these changes are being made")
}

function FileManager(
    content_to_save: string,
    target_files: string[],
    operation_type: string? @description("'save_new', 'update_existing', or 'auto'")
) -> SearchReplaceTool {
    client GroqRouter
    prompt #"
You are a File Manager for PECT Assistant. Your job is to save or update content to files using search/replace operations.

OPERATION RULES:

1. FOR NEW CONTENT OR EMPTY FILES:
   - Use search="" (empty string)
   - Put the full content in replace field
   - Set language to 'markdown' for .md files, or appropriate language for code

2. FOR UPDATING EXISTING FILES:
   - search must contain EXACT text from the file to be replaced
   - search must match precisely including all whitespace and formatting
   - replace contains the new content with same indentation
   - If updating multiple sections, create multiple SearchReplaceBlock entries

3. FILE PATH REQUIREMENTS:
   - Use EXACT paths from available_files list
   - Only use paths that exist in target_files

4. REASONING FIELD:
   - Clearly explain what content is being saved/updated
   - Mention which files are affected
   - Describe the purpose of the changes

TARGET FILES TO MODIFY:
{% for file in target_files %}
- {{ file }}
{% endfor %}

CONTENT TO SAVE:
{{ content_to_save }}

{% if operation_type %}
OPERATION TYPE: {{ operation_type }}
{% endif %}

INSTRUCTIONS:
- Create a SearchReplaceBlock for each file in target_files
- If operation_type is 'save_new' or files are empty, use search=""
- If operation_type is 'update_existing', ensure search matches existing content exactly
- Set appropriate language for each file
- Provide clear reasoning for the file operations

{{ ctx.output_format }}
"#
}