# Configuration-Driven HS Agent System

## 🔧 Overview

The HS Agent now uses a **configuration-driven architecture** that separates:
- **Model configurations** (YAML files)
- **Prompt templates** (Markdown files)
- **Structured output schemas** (YAML definitions)
- **Processing parameters** (YAML configurations)

This approach enables easy prompt engineering, model tuning, and system customization without code changes.

## 📁 Architecture

```
hs_agent/config/
├── loader.py                    # Configuration loader with markdown auto-loading
├── processor.py                 # Configuration-driven step processor
├── multi_choice_agent.yaml      # Master configuration
├── steps/                       # Step-specific configurations
│   ├── initial_ranking.yaml
│   ├── multi_selection.yaml
│   ├── chapter_classification.yaml
│   ├── heading_classification.yaml
│   └── subheading_classification.yaml
└── prompts/                     # Markdown prompt templates
    ├── initial_ranking_system.md
    ├── initial_ranking_user.md
    ├── multi_selection_system.md
    └── multi_selection_user.md
```

## 🚀 Key Features

### 1. **Markdown Auto-Loading**
```yaml
prompts:
  system: initial_ranking_system.md  # Auto-loads markdown file
  user: initial_ranking_user.md      # Auto-loads markdown file
```

The config loader automatically detects `.md` endings and loads the corresponding markdown files from the `prompts/` directory.

### 2. **Template Variable Substitution**
Markdown prompts support template variables:
```markdown
**📦 PRODUCT**: "{{product_description}}"
**🎯 LEVEL**: {{level_name}} Level ({{level_digit}}-digit codes)
{{parent_context}}
```

Variables are automatically substituted during execution.

### 3. **Hierarchical Configuration**
```yaml
# Master configuration
pipeline:
  - name: "chapter_classification"
    config: "steps/chapter_classification.yaml"

# Step-specific configuration
flow:
  - step: "initial_ranking"
    config: "initial_ranking.yaml"
  - step: "multi_selection"
    config: "multi_selection.yaml"
```

### 4. **Model Configuration Separation**
```yaml
model:
  provider: "google_vertex_ai"
  name: "gemini-1.5-pro"
  temperature: 0.1
  max_tokens: 4000
  timeout_seconds: 30
```

## 📖 Configuration Files

### Master Configuration (`multi_choice_agent.yaml`)
- Overall agent architecture
- Pipeline definition
- Default parameters
- Model configurations
- Quality control settings

### Step Configurations (`steps/*.yaml`)
- Step-specific model settings
- Prompt file references
- Structured output schemas
- Processing parameters
- Retry configurations

### Prompt Templates (`prompts/*.md`)
- System prompts with classification expertise
- User prompts with task-specific instructions
- Template variables for dynamic content
- Readable markdown formatting

## 🔄 Two-Step Process Configuration

### Step 1: Initial Ranking
```yaml
# steps/initial_ranking.yaml
name: "initial_ranking"
description: "Broad initial ranking with high K for comprehensive coverage"

model:
  temperature: 0.1    # Low temperature for consistent ranking
  max_tokens: 4000

prompts:
  system: initial_ranking_system.md
  user: initial_ranking_user.md

parameters:
  default_top_k: 20   # High K for broad coverage
```

### Step 2: Multi-Selection
```yaml
# steps/multi_selection.yaml
name: "multi_selection"
description: "Refined selection from broadly ranked candidates (1 to max_n range)"

model:
  temperature: 0.2    # Slightly higher for creative selection
  max_tokens: 3000

prompts:
  system: multi_selection_system.md
  user: multi_selection_user.md

parameters:
  default_max_selections: 3
  default_min_confidence: 0.6
```

## 🛠️ Usage

### Configuration Loader
```python
from hs_agent.config.loader import ConfigLoader

loader = ConfigLoader()

# Load main configuration
main_config = loader.load_config("multi_choice_agent.yaml")

# Load step configuration with markdown auto-loading
step_config = loader.load_step_config("initial_ranking")

# Direct prompt access
prompt_content = loader.get_prompt_content("initial_ranking_system.md")
```

### Configurable Processor
```python
from hs_agent.config.processor import ConfigurableStepProcessor

processor = ConfigurableStepProcessor()

# Execute two-step classification
result = await processor.execute_two_step_classification(
    product_description="cotton fabric",
    codes_dict=chapter_codes,
    level=ClassificationLevel.CHAPTER,
    initial_ranking_k=20,
    max_selections=3,
    min_confidence=0.6
)
```

## 📝 Prompt Engineering

### System Prompts (`*_system.md`)
- Define agent expertise and role
- Establish classification principles
- Set quality standards
- Provide decision frameworks

### User Prompts (`*_user.md`)
- Present specific classification tasks
- Include template variables for dynamic content
- Provide clear instructions and constraints
- Request structured outputs

### Template Variables
- `{{product_description}}` - Product to classify
- `{{level_name}}` - Classification level (CHAPTER/HEADING/SUBHEADING)
- `{{level_digit}}` - Digit count (2/4/6)
- `{{parent_context}}` - Parent code information
- `{{candidates_list}}` - Available candidates
- `{{max_selections}}` - Maximum selections allowed
- `{{min_confidence}}` - Minimum confidence threshold

## 🎯 Benefits

### For Developers
- **Separation of Concerns**: Logic, configuration, and prompts separated
- **Easy Testing**: Individual steps can be tested with different configs
- **Version Control**: Track prompt changes independently from code
- **Maintainability**: Clear structure for complex systems

### For Prompt Engineers
- **Readable Prompts**: Markdown formatting for better readability
- **Template System**: Dynamic content without string concatenation
- **Quick Iteration**: Change prompts without code deployment
- **A/B Testing**: Easy to compare different prompt versions

### For Operations
- **Configuration Management**: Centralized settings
- **Model Tuning**: Adjust parameters without code changes
- **Quality Control**: Configurable thresholds and validation
- **Observability**: Structured logging and monitoring

## 🔧 Configuration Examples

### Adding a New Step
1. Create step configuration: `steps/my_new_step.yaml`
2. Create prompt templates: `prompts/my_new_step_*.md`
3. Update master configuration pipeline
4. Use `ConfigurableStepProcessor` to execute

### Customizing Prompts
1. Edit markdown files in `prompts/` directory
2. Use template variables for dynamic content
3. Test with `test_config_system.py`
4. Deploy without code changes

### Tuning Model Parameters
1. Modify `model` section in step configurations
2. Adjust temperature, tokens, timeout
3. Configure retry logic and quality thresholds
4. Monitor performance and iterate

The configuration system transforms the HS Agent into a highly maintainable, flexible, and prompt-engineering-friendly platform! 🎉