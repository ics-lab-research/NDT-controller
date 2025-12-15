enum Intent {
  DISCUSS      // Q&A, analysis, explanation → routes to PECTExpert
  GENERATE     // Create new content → routes to Brainstormer
  FILE_WRITE   // Save/update files → routes to FileManager
}

enum ContextType {
  SYSTEM_SPECS
  EXPERIMENT_PLAN
  DATA_SCIENCE_PLAN
  EXISTING_IDEA
}

class IntentClassifierOutput {
  intent Intent
  confidence float @description("0.0 to 1.0 confidence score")

  extracted_context string @description("Complete context from conversation for downstream agent")
  
  // For DISCUSS
  requires_external_docs bool
  
  // For GENERATE
  required_context_types ContextType[]?
  
  // For FILE_WRITE
  content_to_save string?
  target_files string[]?
  operation_type string? @description("save_new, update_existing, or auto")
  
  reasoning string
}

class CachedContexts {
  system_specs bool
  experiment_plan bool
  data_science_plan bool
  existing_idea bool
}

class ConversationState {
  available_files string[]
  cached_contexts CachedContexts
}

function IntentClassifier(
    user_message: string,
    last_3_messages: ConversationMessage[],
    conversation_state: ConversationState
) -> IntentClassifierOutput {
    client GroqRouter
    prompt #"
You are an intent classifier for PECT Assistant. The downstream agent receives NO conversation history, only your output.

CRITICAL: Extract all relevant context. The next agent is context-blind without you.

INTENT TYPES:

DISCUSS - Routes to PECTExpert
- Questions, explanations, analysis, comparisons
- Keywords: what, why, how, explain, analyze, compare, discuss

Required extraction:
- extracted_context: All relevant info from conversation (3-10 sentences)
  Include: previous answers, mentioned systems, data, results
  Replace pronouns with explicit nouns (no "it", "this", "that")
- user_request_summary: Restate question with full context
  Example: "How does photoelectrochemical CO2 reduction work?" not "How does this work?"
- requires_external_docs: true if needs papers/external research

GENERATE - Routes to Brainstormer
- Create new ideas, plans, experiments, methodologies
- Keywords: generate, create, design, develop, brainstorm, propose, suggest

Required extraction:
- extracted_context: Complete background for generation (5-15 sentences)
  Include: what has been discussed, existing work, constraints, goals, technical details
  Pull from cached_contexts if available
- required_context_types: Which cached contexts needed

FILE_WRITE - Routes to FileManager
- Save, update, modify files
- Keywords: save, update, write, edit, approve

Required extraction:
- extracted_context: What is being saved and why (1-2 sentences)
- content_to_save: Actual content to write
- target_files: File names/paths
- operation_type: save_new, update_existing, or auto

EXTRACTION RULES:
1. Downstream agent sees only your output, nothing else
2. Replace all pronouns with explicit references
3. Include numbers and parameters mentioned
4. Keep technical terms exact
5. Make extracted_context self-contained
6. Focus on relevance, skip irrelevant details

CONTEXT:

{% if last_3_messages %}
<recent_conversation>
{% for msg in last_3_messages %}
{{ msg.role }}: {{ msg.content }}
{% endfor %}
</recent_conversation>
{% endif %}

<conversation_state>
Available files: {{ conversation_state.available_files }}

Cached contexts:
- system_specs: {{ "Yes" if conversation_state.cached_contexts.system_specs else "No" }}
- experiment_plan: {{ "Yes" if conversation_state.cached_contexts.experiment_plan else "No" }}
- data_science_plan: {{ "Yes" if conversation_state.cached_contexts.data_science_plan else "No" }}
- existing_ideas: {{ "Yes" if conversation_state.cached_contexts.existing_idea else "No" }}
</conversation_state>

USER MESSAGE: {{ user_message }}

PROCESS:
1. Analyze user message for intent keywords
2. Extract all relevant context from conversation and cached contexts
3. Restate user request with full context
4. Classify intent with confidence (0.9-1.0 explicit, 0.6-0.8 moderate, 0.4-0.6 ambiguous)
5. Determine additional needs
6. Validate: Is extracted_context self-contained? Does user_request_summary resolve all ambiguity?

{{ ctx.output_format }}
"#
}