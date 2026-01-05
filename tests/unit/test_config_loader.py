"""Tests for config_loader module.

Tests cover:
- Markdown reference loading
- Config folder loading
- Workflow configs loading
- Prompt template formatting
- Model parameter extraction
"""

from pathlib import Path


from hs_agent.config_loader import (
    _load_markdown_references,
    get_model_params,
    get_prompt,
    load_config_folder,
    load_workflow_configs,
)


class TestLoadMarkdownReferences:
    """Tests for _load_markdown_references function."""

    def test_loads_md_file(self, tmp_path):
        """Test that .md file references are loaded as content."""
        # Create a markdown file
        md_file = tmp_path / "prompts" / "system.md"
        md_file.parent.mkdir(parents=True, exist_ok=True)
        md_file.write_text("You are an HS code expert.")

        config = {"prompts": {"system": "prompts/system.md"}}

        result = _load_markdown_references(config, tmp_path)

        assert result["prompts"]["system"] == "You are an HS code expert."

    def test_recursive_loading_nested_dict(self, tmp_path):
        """Test recursive loading in nested dicts."""
        # Create markdown files
        (tmp_path / "system.md").write_text("System prompt")
        (tmp_path / "user.md").write_text("User prompt")

        config = {"level1": {"level2": {"prompt": "system.md"}}, "other": "user.md"}

        result = _load_markdown_references(config, tmp_path)

        assert result["level1"]["level2"]["prompt"] == "System prompt"
        assert result["other"] == "User prompt"

    def test_missing_file_keeps_original(self, tmp_path):
        """Test graceful handling of missing .md file."""
        config = {"prompt": "nonexistent.md"}

        result = _load_markdown_references(config, tmp_path)

        assert result["prompt"] == "nonexistent.md"  # Keeps original path

    def test_non_md_strings_unchanged(self, tmp_path):
        """Test non-.md strings are unchanged."""
        config = {"name": "test-model", "prompt": "Just a string, not a file"}

        result = _load_markdown_references(config, tmp_path)

        assert result["name"] == "test-model"
        assert result["prompt"] == "Just a string, not a file"

    def test_handles_lists(self, tmp_path):
        """Test handling of lists in config.

        Note: .md files are only loaded when they are dict values, not list items.
        List items that are strings are preserved unchanged.
        """
        (tmp_path / "item.md").write_text("Item content")

        config = {"items": ["item.md", "regular string"]}

        result = _load_markdown_references(config, tmp_path)

        # .md files in lists are NOT loaded (only dict values are processed)
        assert result["items"][0] == "item.md"  # Preserved unchanged
        assert result["items"][1] == "regular string"

    def test_handles_nested_dicts_in_lists(self, tmp_path):
        """Test that nested dicts inside lists ARE processed."""
        (tmp_path / "nested.md").write_text("Nested content")

        config = {"items": [{"prompt": "nested.md"}, {"name": "regular"}]}

        result = _load_markdown_references(config, tmp_path)

        # Nested dict values ARE loaded
        assert result["items"][0]["prompt"] == "Nested content"
        assert result["items"][1]["name"] == "regular"

    def test_handles_primitives(self, tmp_path):
        """Test handling of primitive values."""
        config = {"number": 42, "boolean": True, "null": None}

        result = _load_markdown_references(config, tmp_path)

        assert result["number"] == 42
        assert result["boolean"] is True
        assert result["null"] is None


class TestLoadConfigFolder:
    """Tests for load_config_folder function."""

    def test_loads_yaml_config(self, tmp_path):
        """Test loading basic config.yaml."""
        config_yaml = tmp_path / "config.yaml"
        config_yaml.write_text(
            "model:\n"
            "  name: gemini-2.5-flash\n"
            "  parameters:\n"
            "    temperature: 0.1\n"
        )

        result = load_config_folder(tmp_path)

        assert result["model"]["name"] == "gemini-2.5-flash"
        assert result["model"]["parameters"]["temperature"] == 0.1

    def test_loads_with_prompt_files(self, tmp_path):
        """Test loading config with prompt .md files."""
        # Create directory structure
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        # Create config.yaml
        config_yaml = tmp_path / "config.yaml"
        config_yaml.write_text(
            "prompts:\n" "  system: prompts/system.md\n" "  user: prompts/user.md\n"
        )

        # Create prompt files
        (prompts_dir / "system.md").write_text("System prompt content")
        (prompts_dir / "user.md").write_text("User prompt content")

        result = load_config_folder(tmp_path)

        assert result["prompts"]["system"] == "System prompt content"
        assert result["prompts"]["user"] == "User prompt content"

    def test_empty_folder_returns_empty(self, tmp_path):
        """Test empty folder returns empty dict."""
        result = load_config_folder(tmp_path)

        assert result == {}

    def test_with_output_schema(self, tmp_path):
        """Test config with output_schema."""
        config_yaml = tmp_path / "config.yaml"
        config_yaml.write_text(
            "output_schema:\n"
            "  type: object\n"
            "  properties:\n"
            "    code:\n"
            "      type: string\n"
        )

        result = load_config_folder(tmp_path)

        assert "output_schema" in result
        assert result["output_schema"]["type"] == "object"


class TestLoadWorkflowConfigs:
    """Tests for load_workflow_configs function."""

    def test_loads_multiple_folders(self, tmp_path):
        """Test loading all configs from workflow directory."""
        # Create two config folders
        for folder_name in ["step1", "step2"]:
            folder = tmp_path / folder_name
            folder.mkdir()
            (folder / "config.yaml").write_text(f"name: {folder_name}\n")

        result = load_workflow_configs(tmp_path)

        assert "step1" in result
        assert "step2" in result
        assert result["step1"]["name"] == "step1"
        assert result["step2"]["name"] == "step2"

    def test_skips_non_config_folders(self, tmp_path):
        """Test folders without config.yaml are skipped."""
        # Create one valid and one invalid folder
        valid = tmp_path / "valid"
        valid.mkdir()
        (valid / "config.yaml").write_text("valid: true\n")

        invalid = tmp_path / "invalid"
        invalid.mkdir()
        # No config.yaml

        result = load_workflow_configs(tmp_path)

        assert "valid" in result
        assert "invalid" not in result

    def test_nonexistent_directory_returns_empty(self):
        """Test nonexistent directory returns empty dict."""
        result = load_workflow_configs(Path("/nonexistent/path"))

        assert result == {}

    def test_skips_files(self, tmp_path):
        """Test files (not dirs) are skipped."""
        # Create a config folder
        folder = tmp_path / "valid"
        folder.mkdir()
        (folder / "config.yaml").write_text("valid: true\n")

        # Create a file at root level
        (tmp_path / "not_a_folder.yaml").write_text("ignored: true\n")

        result = load_workflow_configs(tmp_path)

        assert "valid" in result
        assert "not_a_folder.yaml" not in result


class TestGetPrompt:
    """Tests for get_prompt function."""

    def test_returns_formatted_prompt(self):
        """Test prompt template variable substitution."""
        config = {"prompts": {"user": "Product: {product_description}\nLevel: {level}"}}

        result = get_prompt(
            config, "user", product_description="laptop computer", level="CHAPTER"
        )

        assert result == "Product: laptop computer\nLevel: CHAPTER"

    def test_missing_prompt_returns_empty(self):
        """Test empty string returned for missing prompt."""
        config = {"prompts": {}}

        result = get_prompt(config, "nonexistent")

        assert result == ""

    def test_empty_prompts_dict(self):
        """Test empty prompts section returns empty string."""
        config = {}

        result = get_prompt(config, "user")

        assert result == ""

    def test_missing_variable_returns_template(self):
        """Test graceful handling of missing template variable."""
        config = {"prompts": {"user": "Product: {product_description} Code: {code}"}}

        # Only provide one variable
        result = get_prompt(config, "user", product_description="laptop")

        # Returns unformatted template when variable missing
        assert "Product: {product_description}" in result

    def test_no_variables_in_template(self):
        """Test prompt with no variables."""
        config = {"prompts": {"system": "You are an HS code expert."}}

        result = get_prompt(config, "system")

        assert result == "You are an HS code expert."

    def test_multiple_prompts(self):
        """Test getting different prompt types."""
        config = {"prompts": {"system": "System: {role}", "user": "User: {query}"}}

        system = get_prompt(config, "system", role="expert")
        user = get_prompt(config, "user", query="classify laptop")

        assert system == "System: expert"
        assert user == "User: classify laptop"


class TestGetModelParams:
    """Tests for get_model_params function."""

    def test_extracts_all_params(self):
        """Test extraction of all model parameters."""
        config = {
            "model": {
                "name": "gemini-2.5-pro",
                "parameters": {
                    "temperature": 0.2,
                    "max_tokens": 4096,
                    "top_p": 0.9,
                    "thinking_budget": 1024,
                },
            }
        }

        result = get_model_params(config)

        assert result["model_name"] == "gemini-2.5-pro"
        assert result["temperature"] == 0.2
        assert result["max_tokens"] == 4096
        assert result["top_p"] == 0.9
        assert result["thinking_budget"] == 1024

    def test_default_values(self):
        """Test default model parameters."""
        config = {}

        result = get_model_params(config)

        assert result["model_name"] == "gemini-2.5-flash"
        assert result["temperature"] == 0.1
        assert result["max_tokens"] == 8192
        assert result["top_p"] == 0.95
        assert result["thinking_budget"] is None

    def test_partial_params(self):
        """Test partial parameters with defaults for missing."""
        config = {"model": {"name": "custom-model", "parameters": {"temperature": 0.5}}}

        result = get_model_params(config)

        assert result["model_name"] == "custom-model"
        assert result["temperature"] == 0.5
        assert result["max_tokens"] == 8192  # Default
        assert result["top_p"] == 0.95  # Default

    def test_empty_parameters(self):
        """Test empty parameters section."""
        config = {"model": {"name": "test-model"}}

        result = get_model_params(config)

        assert result["model_name"] == "test-model"
        assert result["temperature"] == 0.1
