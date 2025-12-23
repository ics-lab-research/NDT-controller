import os
from baml_py import ClientRegistry


def get_client_registry(agent: str) -> ClientRegistry:
    """Create and return a ClientRegistry configured for the given agent."""
    env_var = agent.upper().replace("-", "_")
    model_str = os.environ.get(env_var)
    if not model_str:
        raise ValueError(
            f"Model for {agent} not found in environment variables"
        )

    try:
        provider, model = model_str.split("/", 1)
    except ValueError:
        raise ValueError(f"Invalid model format for {agent}: {model_str}")

    # Handle special providers that use openai-generic
    base_url = None
    if provider == "groq":
        actual_provider = "openai-generic"
        base_url = "https://api.groq.com/openai/v1"
        api_key_env = "GROQ_API_KEY"
    elif provider == "openrouter":
        actual_provider = "openai-generic"
        base_url = "https://openrouter.ai/api/v1"
        api_key_env = "OPENROUTER_API_KEY"
    elif provider.startswith("google"):
        actual_provider = "google-ai"
        api_key_env = "GOOGLE_API_KEY"
    else:
        raise ValueError(f"Unknown provider {provider} for agent {agent}")

    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise ValueError(
            f"API key for provider {provider} not found in environment variables"
        )

    cr = ClientRegistry()
    client_name = f"{agent}_client"
    options = {
        "model": model,
        "api_key": api_key,
    }
    if base_url:
        options["base_url"] = base_url
    cr.add_llm_client(
        name=client_name,
        provider=actual_provider,
        options=options,
    )
    cr.set_primary(client_name)
    return cr
