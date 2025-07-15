<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Digital Superman - Azure Architecture to Infrastructure Code

## Project Overview
This is a Flask-based web application that converts Azure architecture diagrams into infrastructure code using 3 AI agents:
1. **Architecture Analyzer** - Analyzes Azure architecture diagrams and extracts components
2. **Policy Checker** - Validates architecture against Azure policies and compliance
3. **Bicep Generator** - Generates Bicep templates and Azure DevOps YAML pipelines

## Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Document all functions and classes with docstrings
- Use descriptive variable and function names

### Architecture Patterns
- Use the agent pattern for AI processing
- Implement proper error handling and logging
- Use configuration management for environment variables
- Follow Flask best practices for web development

### AI Agent Development
- Each agent should be in its own file under `/agents/`
- Use OpenAI GPT-4 for AI processing
- Implement proper prompt engineering
- Handle API failures gracefully
- Parse responses robustly with fallback mechanisms

### File Processing
- Support multiple file formats (PNG, JPG, PDF, XML, Draw.io, VSDX, SVG)
- Extract meaningful content from each format
- Handle file processing errors gracefully
- Implement proper file validation

### Security Considerations
- Validate all file uploads
- Sanitize file names
- Implement proper authentication if needed
- Use environment variables for sensitive data
- Follow Azure security best practices

### Testing
- Write unit tests for each agent
- Test file processing for different formats
- Test error handling scenarios
- Validate generated Bicep templates

## Key Components

### Agents
- `architecture_analyzer.py` - Analyzes architecture diagrams
- `policy_checker.py` - Checks compliance against Azure policies
- `bicep_generator.py` - Generates Bicep templates and pipelines

### Utils
- `file_processor.py` - Handles various file format processing
- `zip_generator.py` - Creates downloadable ZIP packages

### Templates
- `index.html` - Main web interface with modern Bootstrap design

## Environment Setup
1. Copy `.env.example` to `.env`
2. Configure OpenAI API key
3. Optionally configure Azure credentials
4. Install dependencies with `pip install -r requirements.txt`

## API Endpoints
- `GET /` - Main application interface
- `POST /upload` - File upload and processing
- `GET /download/<filename>` - Download generated packages
- `GET /health` - Health check endpoint

## Generated Output
The application generates a ZIP package containing:
- Bicep templates with modules
- Azure DevOps YAML pipelines
- Parameter files for different environments
- Documentation and deployment guides
- Analysis and compliance reports
- PowerShell deployment scripts
