"""Factory for creating LLM model instances.

This module provides a centralized factory for creating and configuring
ChatVertexAI models with various settings and output schemas.
"""

import copy
from typing import Any

from langchain_google_vertexai import ChatVertexAI


class ModelFactory:
    """Factory for creating and configuring LLM models."""

    @staticmethod
    def create_base_model(model_name: str, model_params: dict[str, Any]) -> ChatVertexAI:
        """Create a base ChatVertexAI model with standard configuration.

        Args:
            model_name: Name of the model to use (e.g., "gemini-2.5-flash")
            model_params: Model parameters from config containing:
                - model_name: Override model name (optional)
                - temperature: Model temperature (default: 0.1)
                - max_tokens: Maximum tokens (default: 8192)
                - top_p: Top-p sampling (default: 0.95)
                - thinking_budget: Thinking budget for Gemini 2.5+ (optional)

        Returns:
            Configured ChatVertexAI instance
        """
        model_kwargs = {
            "model": model_params.get("model_name", model_name),
            "temperature": model_params.get("temperature", 0.1),
            "max_tokens": model_params.get("max_tokens", 8192),
            "top_p": model_params.get("top_p", 0.95),
        }

        # Add thinking_budget if enabled (Gemini 2.5+ only)
        thinking_budget = model_params.get("thinking_budget")
        if thinking_budget is not None and thinking_budget > 0:
            model_kwargs["thinking_budget"] = thinking_budget
            model_kwargs["include_thoughts"] = True

        return ChatVertexAI(**model_kwargs)

    @staticmethod
    def add_structured_output(
        model: ChatVertexAI,
        schema: dict[str, Any],
        enum_codes: list[str] | None = None,
        enum_field_path: list[str] | None = None,
    ) -> ChatVertexAI:
        """Add structured output schema to a model.

        Args:
            model: Base ChatVertexAI model
            schema: JSON Schema for structured output
            enum_codes: Optional list of codes to constrain enum field
            enum_field_path: Path to the enum field in the schema
                            (e.g., ["properties", "selections", "items", "properties", "code"])

        Returns:
            Model with structured output configured
        """
        # If enum codes provided, add constraint to schema
        if enum_codes and enum_field_path:
            # Deep copy to avoid modifying cached config
            schema = copy.deepcopy(schema)

            # Navigate to the target field and add enum constraint
            current = schema
            for key in enum_field_path[:-1]:
                if key not in current:
                    if key == "properties":
                        current[key] = {}
                    else:
                        current[key] = (
                            {} if isinstance(current.get(key), dict) else current.get(key)
                        )
                current = current[key]

            # Set the enum on the final field
            final_key = enum_field_path[-1]
            if final_key not in current:
                current[final_key] = {"type": "string"}
            if isinstance(current[final_key], dict):
                current[final_key]["enum"] = enum_codes

        return model.with_structured_output(schema)

    @staticmethod
    def create_with_config(
        model_name: str, config: dict[str, Any], enum_codes: list[str] | None = None
    ) -> ChatVertexAI:
        """Create a model configured for a specific workflow step.

        Args:
            model_name: Default model name
            config: Config dict containing:
                - model: Model parameters
                - output_schema: Optional JSON Schema for structured output
            enum_codes: Optional list of codes to constrain selection enum

        Returns:
            Configured ChatVertexAI model

        Example:
            >>> config = {
            ...     "model": {"temperature": 0.1, "thinking_budget": 0},
            ...     "output_schema": {"type": "object", "properties": {...}}
            ... }
            >>> model = ModelFactory.create_with_config("gemini-2.5-flash", config)
        """
        from hs_agent.config_loader import get_model_params

        # Get model parameters from config
        model_params = get_model_params(config)

        # Create base model
        model = ModelFactory.create_base_model(model_name, model_params)

        # Add structured output if schema provided
        if schema := config.get("output_schema"):
            # Add enum constraint if codes provided
            if enum_codes:
                # Detect schema structure and use appropriate field path
                schema_props = schema.get("properties", {})

                if "selected_code" in schema_props:
                    # Single selection schema: properties.selected_code
                    enum_field_path = ["properties", "selected_code"]
                    model = ModelFactory.add_structured_output(
                        model, schema, enum_codes, enum_field_path
                    )
                elif "selections" in schema_props:
                    # Multi-selection schema: properties.selections.items.properties.code
                    enum_field_path = ["properties", "selections", "items", "properties", "code"]
                    model = ModelFactory.add_structured_output(
                        model, schema, enum_codes, enum_field_path
                    )
                else:
                    # No recognized selection field, add schema without enum
                    model = ModelFactory.add_structured_output(model, schema)
            else:
                model = ModelFactory.add_structured_output(model, schema)

        return model

    @staticmethod
    def create_for_multi_selection(
        model_name: str, config: dict[str, Any], candidate_codes: list[str]
    ) -> ChatVertexAI:
        """Create a model specifically for multi-selection with enum constraints.

        This is a convenience method for creating models with enum constraints
        on the selections array, commonly used in multi-choice workflows.

        Args:
            model_name: Default model name
            config: Config dict with model params and output schema
            candidate_codes: List of valid candidate codes to constrain selection

        Returns:
            Configured ChatVertexAI model with enum-constrained selections
        """
        from hs_agent.config_loader import get_model_params

        # Get model parameters
        model_params = get_model_params(config)

        # Create base model
        base_model = ModelFactory.create_base_model(model_name, model_params)

        # Add schema with enum constraints
        if schema := config.get("output_schema"):
            # Deep copy to avoid modifying cached config
            schema = copy.deepcopy(schema)

            # Add enum constraint for selections.items.properties.code
            if (
                "properties" in schema
                and "selections" in schema["properties"]
                and "items" in schema["properties"]["selections"]
            ):
                # Ensure properties exists
                if "properties" not in schema["properties"]["selections"]["items"]:
                    schema["properties"]["selections"]["items"]["properties"] = {}

                # Ensure code field exists
                code_props = schema["properties"]["selections"]["items"]["properties"]
                if "code" not in code_props:
                    code_props["code"] = {"type": "string"}

                # Add enum constraint
                code_props["code"]["enum"] = candidate_codes

            return base_model.with_structured_output(schema)

        return base_model
