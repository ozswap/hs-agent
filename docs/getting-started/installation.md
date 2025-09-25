# Installation

This guide will help you set up the HS Agent system on your local machine or production environment.

## Prerequisites

Before installing HS Agent, ensure you have the following:

- **Python 3.12+**: The system requires Python 3.12 or higher
- **Google Cloud Account**: Access to Vertex AI API
- **Git**: For cloning the repository

## Installation Methods

### Using UV (Recommended)

The project uses [UV](https://docs.astral.sh/uv/) for dependency management and virtual environments.

1. **Install UV** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/hs-agent.git
   cd hs-agent
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

### Using pip

If you prefer using pip:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/hs-agent.git
   cd hs-agent
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -e .
   ```

## Environment Setup

### Google Cloud Authentication

1. **Install Google Cloud SDK**:
   ```bash
   # On macOS
   brew install google-cloud-sdk

   # On Ubuntu/Debian
   sudo apt-get install google-cloud-cli
   ```

2. **Authenticate with Google Cloud**:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Set your project**:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

### Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
GOOGLE_CLOUD_PROJECT=your-project-id

# Langfuse Configuration (Optional)
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_HOST=https://cloud.langfuse.com

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
```

### Data Setup

The system requires HS code data files. Ensure you have the following structure:

```
data/
├── hs_codes_2digit.csv
├── hs_codes_4digit.csv
├── hs_codes_6digit.csv
└── product_examples.csv
```

## Verification

Test your installation:

```bash
# Test data loading
uv run python -c "from hs_agent.core.data_loader import HSDataLoader; print('✅ Installation successful')"

# Test traditional classifier
uv run python -c "from hs_agent.agents.traditional.classifier import HSClassifier; print('✅ Traditional agents working')"

# Test LangGraph classifier
uv run python -c "from hs_agent.agents.langgraph.classifier import HSLangGraphClassifier; print('✅ LangGraph agents working')"
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're using the virtual environment and all dependencies are installed
2. **Google Cloud Authentication**: Verify your credentials and project configuration
3. **Data Files Missing**: Check that all required data files are in the `data/` directory

### Getting Help

- Check the [Configuration](configuration.md) guide for detailed setup
- Review the [Quick Start](quickstart.md) guide for basic usage
- Open an issue on GitHub for additional support

## Next Steps

- Follow the [Quick Start](quickstart.md) guide to run your first classification
- Explore the [Configuration](configuration.md) options
- Read the [User Guide](../user-guide/overview.md) for detailed usage