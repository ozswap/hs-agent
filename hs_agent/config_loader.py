"""Simple config loader for workflow configurations."""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_config_folder(folder_path: Path) -> Dict[str, Any]:
    """Load a single config folder (YAML + prompt files) into a dict."""
    config = {}

    # Load main YAML config
    yaml_file = folder_path / "config.yaml"
    if yaml_file.exists():
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)

    # Load prompt files from prompts/ subfolder
    prompts_dir = folder_path / "prompts"
    if prompts_dir.exists():
        prompts = {}
        for prompt_file in prompts_dir.glob("*.md"):
            prompt_name = prompt_file.stem  # e.g., "system", "user", "output_schema"
            with open(prompt_file, 'r') as f:
                prompts[prompt_name] = f.read().strip()

        if prompts:
            config["prompts"] = prompts

    return config


def load_workflow_configs(base_dir: Path = Path("configs/multi_choice_classification")) -> Dict[str, Dict[str, Any]]:
    """Load all workflow config folders into a single dict.

    Returns:
        Dict where keys are folder names (e.g., 'rank_chapter_candidates')
        and values are the loaded config dicts.
    """
    configs = {}

    if not base_dir.exists():
        print(f"⚠️  Config directory not found: {base_dir}")
        return configs

    # Iterate through each subfolder
    for folder in base_dir.iterdir():
        if folder.is_dir() and (folder / "config.yaml").exists():
            folder_name = folder.name
            configs[folder_name] = load_config_folder(folder)
            print(f"✅ Loaded config: {folder_name}")

    return configs


def get_prompt(config: Dict[str, Any], prompt_type: str, **kwargs) -> str:
    """Get a prompt from config and format it with kwargs.

    Args:
        config: Config dict for a specific step
        prompt_type: "system", "user", etc.
        **kwargs: Variables to format into the prompt template

    Returns:
        Formatted prompt string
    """
    prompt_template = config.get("prompts", {}).get(prompt_type, "")

    if not prompt_template:
        return ""

    # Format the template with provided kwargs
    try:
        return prompt_template.format(**kwargs)
    except KeyError as e:
        print(f"⚠️  Missing template variable: {e}")
        return prompt_template  # Return unformatted if variables missing


def get_model_params(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract model parameters from config."""
    model_config = config.get("model", {})
    params = model_config.get("parameters", {})

    return {
        "model_name": model_config.get("name", "gemini-2.5-flash"),
        "temperature": params.get("temperature", 0.1),
        "max_tokens": params.get("max_tokens", 8192),
        "top_p": params.get("top_p", 0.95),
        "thinking_budget": params.get("thinking_budget"),
    }