# AI Agents

## Overview

The agents directory contains the implementation of specialized AI agents that power College Compass's intelligent guidance system. Each agent is designed to handle specific aspects of the college counseling process.

## Design Philosophy

The agent system follows a hierarchical design with:
1. A base agent class providing common functionality
2. Specialized agents for different counseling aspects
3. An orchestrator managing agent interactions

## Agent Types

### Primary Counselor Agent (`primary_counselor.py`)
- **Purpose**: Main interface for student interactions
- **Features**:
  - Multi-provider LLM support (OpenAI, Anthropic)
  - Context-aware responses
  - Actionable item generation
  - Conversation management
  - Dynamic routing to specialized agents

### Strategic Planning Agent (`strategic_planning.py`)
- **Purpose**: Long-term planning and strategy development
- **Features**:
  - College application timeline creation
  - Goal setting and tracking
  - Milestone management

### Validator Agent (`validator.py`)
- **Purpose**: Ensures accuracy and consistency of advice
- **Features**:
  - Fact-checking
  - Deadline verification
  - Requirements validation

## Implementation Details

### Base Agent Class
- Common functionality for all agents
- Configuration management
- Error handling
- API interaction patterns

### Agent Communication
- Uses a message-passing system
- Maintains conversation context
- Supports multi-turn interactions

### Response Format
Agents use a structured response format:
```python
{
    "content": str,              # Main response content
    "actionable_items": List[Dict],  # Specific actions for students
    "metadata": Dict             # Additional context and tracking info
}
```

## Development Guidelines

1. **Adding New Agents**:
   - Inherit from BaseAgent
   - Implement required interfaces
   - Add to orchestrator registry

2. **API Integration**:
   - Use environment variables for API keys
   - Implement fallback mechanisms
   - Handle rate limiting

3. **Testing**:
   - Unit tests for each agent
   - Integration tests for agent interactions
   - Mock LLM responses for testing

## Future Enhancements

- Enhanced multi-agent collaboration
- Improved context management
- Additional specialized agents for:
  - Essay review
  - Financial aid guidance
  - Interview preparation
