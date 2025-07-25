# AI Chat History

Store and search through all your LLM conversations from OpenAI, Anthropic, and Google in an Elasticsearch vector database.

## Features

- **Multi-Provider Support**: OpenAI GPT, Anthropic Claude, Google Gemini
- **Vector Search**: Find similar past conversations using semantic embeddings
- **MCP Integration**: Model Context Protocol server for easy integration
- **Elasticsearch Storage**: Scalable vector database storage

## Quick Start

1. **Install dependencies** (use virtual environment to avoid system conflicts):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure API Keys**:
   Edit `.env` file with your API keys:
   ```env
   OPENAI_API_KEY=your_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key  
   GOOGLE_API_KEY=your_google_key
   ELASTICSEARCH_URL=your_elasticsearch_url
   ELASTICSEARCH_API_KEY=your_elasticsearch_key
   ```

3. **Run**:
   ```bash
   python chat_history.py
   ```

## MCP Server

Run the MCP server to enable integration with MCP-compatible clients:

```bash
python mcp_server.py
```

### MCP Tools Available:

- `search_chat_history` - Search past conversations
- `ask_llm` - Ask questions to any LLM provider
- `get_chat_stats` - Get usage statistics

## Usage Examples

```python
from chat_history import ChatHistoryManager

manager = ChatHistoryManager()

# Ask different providers
openai_response = manager.ask_openai("What is machine learning?")
claude_response = manager.ask_anthropic("Explain quantum computing")
gemini_response = manager.ask_google("How does blockchain work?")

# Search similar conversations
similar = manager.search_similar_chats("machine learning", size=5)
```

## Requirements

- Python 3.8+
- Elasticsearch cluster
- API keys for desired LLM providers