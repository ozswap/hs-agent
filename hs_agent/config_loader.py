"""Simple config loader for workflow configurations."""

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, create_model

from hs_agent.utils.logger import get_logger

logger = get_logger(__name__)


def _load_markdown_references(config: dict | list | Any, base_path: Path) -> dict | list | Any:
    """Recursively load .md file references in config.

    Any string value ending with .md will be treated as a file path and loaded.

    Args:
        config: Config dict/list/value to process
        base_path: Base path to resolve relative file paths

    Returns:
        Processed config with .md files loaded as strings
    """
    if isinstance(config, dict):
        result = {}
        for key, value in config.items():
            if isinstance(value, str) and value.endswith(".md"):
                # Try to load the markdown file
                file_path = base_path / value
                if file_path.exists():
                    try:
                        with open(file_path) as f:
                            result[key] = f.read().strip()
                    except Exception as e:
                        logger.warning(f"Failed to load {value}: {e}")
                        result[key] = value  # Keep original path on error
                else:
                    # File doesn't exist, keep the original value
                    result[key] = value
            else:
                # Recursively process nested structures
                result[key] = _load_markdown_references(value, base_path)
        return result
    elif isinstance(config, list):
        return [_load_markdown_references(item, base_path) for item in config]
    else:
        return config


def load_config_folder(folder_path: Path) -> dict[str, Any]:
    """Load a single config folder (YAML + prompt files) into a dict."""
    config = {}

    # Load main YAML config
    yaml_file = folder_path / "config.yaml"
    if yaml_file.exists():
        with open(yaml_file) as f:
            config = yaml.safe_load(f)

    # Recursively load any .md file references in the config
    if config:
        config = _load_markdown_references(config, folder_path)

    # Note: prompt files are already loaded by _load_markdown_references
    # No additional processing needed

    # JSON Schema is now used directly - no Pydantic model creation needed
    if "output_schema" in config:
        logger.debug("JSON Schema loaded for config")

    return config


def load_workflow_configs(
    base_dir: Path = Path("configs/multi_choice_classification"),
) -> dict[str, dict[str, Any]]:
    """Load all workflow config folders into a single dict.

    Returns:
        Dict where keys are folder names (e.g., 'select_chapter_candidates')
        and values are the loaded config dicts.
    """
    configs = {}

    if not base_dir.exists():
        logger.warning(f"Config directory not found: {base_dir}")
        return configs

    # Iterate through each subfolder
    for folder in base_dir.iterdir():
        if folder.is_dir() and (folder / "config.yaml").exists():
            folder_name = folder.name
            configs[folder_name] = load_config_folder(folder)
            logger.debug(f"Loaded config: {folder_name}")

    return configs


def get_prompt(config: dict[str, Any], prompt_type: str, **kwargs) -> str:
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
        logger.warning(f"Missing template variable: {e}")
        return prompt_template  # Return unformatted if variables missing


def _parse_type_string(type_str: str, defined_models: dict[str, type[BaseModel]]) -> Any:
    """Parse a type string from YAML to actual Python type.

    Args:
        type_str: Type as string (e.g., "str", "List[ModelName]", "Optional[int]")
        defined_models: Dictionary of already defined model classes

    Returns:
        Actual Python type object
    """
    type_str = type_str.strip()

    # Handle Optional[...]
    if type_str.startswith("Optional[") and type_str.endswith("]"):
        inner_type = type_str[9:-1]
        return _parse_type_string(inner_type, defined_models) | None

    # Handle List[...]
    if type_str.startswith("List[") and type_str.endswith("]"):
        inner_type = type_str[5:-1]
        return list[_parse_type_string(inner_type, defined_models)]

    # Handle Dict[...]
    if type_str.startswith("Dict["):
        return dict[str, Any]

    # Check if it's a defined model
    if type_str in defined_models:
        return defined_models[type_str]

    # Handle primitive types
    type_mapping = {
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "Any": Any,
    }

    return type_mapping.get(type_str, str)


def _extract_model_description(markdown: str, model_name: str) -> str | None:
    """Extract model-level description from output_schema.md file.

    Looks for the first paragraph after the model name header.

    Args:
        markdown: Content of output_schema.md file
        model_name: Name of the model to extract description for

    Returns:
        Model description or None
    """
    if not markdown:
        return None

    # Look for ## ModelName Schema pattern
    pattern = rf"##\s+{model_name}\s+Schema\s*\n+(.*?)(?=\n##|\n###|$)"
    match = re.search(pattern, markdown, re.DOTALL)

    if match:
        desc_section = match.group(1).strip()
        # Extract first paragraph (before any ### headers or blank lines)
        first_para = desc_section.split("\n\n")[0].strip()
        first_para = first_para.split("\n###")[0].strip()
        if first_para:
            return first_para

    return None


def create_models_from_schema(
    schema_dict: dict[str, dict[str, dict[str, str]]], schema_md_content: str | None = None
) -> type[BaseModel] | None:
    """Create Pydantic models from YAML schema definition.

    Args:
        schema_dict: Dictionary from config["output_schema"] with format:
            {
                "ModelName": {
                    "__description__": "Model-level description",  # Optional
                    "field_name": {
                        "type": "str",
                        "description": "Field description"
                    },
                    "other_field": {"type": "List[OtherModel]"}
                },
                "OtherModel": {...}
            }
        schema_md_content: Optional markdown content to auto-extract descriptions

    Returns:
        The first model class (main output model), or None if parsing fails
    """
    if not schema_dict:
        return None

    try:
        defined_models: dict[str, type[BaseModel]] = {}

        # Get all class names in order
        class_names = list(schema_dict.keys())

        # Create models in reverse order (nested models first)
        for class_name in reversed(class_names):
            fields_def = schema_dict[class_name]

            # Extract model-level description
            model_description = fields_def.get("__description__")

            # Note: .md files are already loaded by _load_markdown_references
            # So model_description will be the file content, not the path

            # If no inline description, try to load from markdown
            if not model_description and schema_md_content:
                model_description = _extract_model_description(schema_md_content, class_name)

            # Build fields dict for create_model
            fields = {}
            for field_name, field_config in fields_def.items():
                # Skip special __description__ key
                if field_name == "__description__":
                    continue

                type_str = field_config.get("type", "str")
                field_type = _parse_type_string(type_str, defined_models)

                # Get optional description
                description = field_config.get("description")

                # Use Field() if description is provided, otherwise use ...
                if description:
                    fields[field_name] = (field_type, Field(description=description))
                else:
                    fields[field_name] = (field_type, ...)

            # Create the model with __doc__ if description available
            if fields:
                if model_description:
                    model = create_model(class_name, __doc__=model_description, **fields)
                else:
                    model = create_model(class_name, **fields)
                defined_models[class_name] = model

        # Return the first model (main output model)
        if class_names and class_names[0] in defined_models:
            return defined_models[class_names[0]]

        return None

    except Exception as e:
        logger.warning(f"Failed to create models from schema: {e}")
        logger.debug("Schema error traceback", exc_info=True)
        return None


def get_model_params(config: dict[str, Any]) -> dict[str, Any]:
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


def get_output_model(config: dict[str, Any]) -> type[BaseModel] | None:
    """Extract the dynamically created output model from config.

    Args:
        config: Config dict for a specific step

    Returns:
        Pydantic BaseModel class if output_model was created, None otherwise
    """
    return config.get("output_model")
