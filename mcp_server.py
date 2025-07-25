#!/usr/bin/env python3

import asyncio
import json
from typing import Any, Sequence
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from pydantic import AnyUrl
from chat_history import ChatHistoryManager

server = Server("chat-history-server")
chat_manager = ChatHistoryManager()

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    return [
        Resource(
            uri=AnyUrl("chat://history"),
            name="Chat History",
            description="Access to stored chat history and responses",
            mimeType="application/json",
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    if str(uri) == "chat://history":
        # Return recent chat history
        recent_chats = chat_manager.search_similar_chats("", size=10)
        return json.dumps(recent_chats, indent=2)
    else:
        raise ValueError(f"Unknown resource: {uri}")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_chat_history",
            description="Search through past chat conversations using semantic similarity",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find similar past conversations",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="ask_llm",
            description="Ask a question to an LLM provider and store the response",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to ask the LLM",
                    },
                    "provider": {
                        "type": "string",
                        "description": "LLM provider to use",
                        "enum": ["openai", "anthropic", "google"],
                        "default": "openai"
                    }
                },
                "required": ["question"],
            },
        ),
        Tool(
            name="get_chat_stats",
            description="Get statistics about stored chat history",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    if arguments is None:
        arguments = {}
    
    if name == "search_chat_history":
        query = arguments.get("query", "")
        limit = arguments.get("limit", 5)
        
        results = chat_manager.search_similar_chats(query, size=limit)
        
        if not results:
            return [TextContent(type="text", text="No similar conversations found.")]
        
        response_text = f"Found {len(results)} similar conversations:\n\n"
        for i, chat in enumerate(results, 1):
            response_text += f"{i}. **[{chat['provider'].upper()}]** {chat['timestamp']}\n"
            response_text += f"   **Q:** {chat['query']}\n"
            response_text += f"   **A:** {chat['response'][:200]}{'...' if len(chat['response']) > 200 else ''}\n\n"
        
        return [TextContent(type="text", text=response_text)]
    
    elif name == "ask_llm":
        question = arguments.get("question", "")
        provider = arguments.get("provider", "openai")
        
        if not question:
            return [TextContent(type="text", text="Please provide a question to ask.")]
        
        try:
            if provider == "openai":
                response = chat_manager.ask_openai(question)
            elif provider == "anthropic":
                response = chat_manager.ask_anthropic(question)
            elif provider == "google":
                response = chat_manager.ask_google(question)
            else:
                return [TextContent(type="text", text=f"Unknown provider: {provider}")]
            
            return [TextContent(type="text", text=f"**Question:** {question}\n\n**Response from {provider.upper()}:**\n{response}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error asking {provider}: {str(e)}")]
    
    elif name == "get_chat_stats":
        try:
            # Get total count from Elasticsearch
            from elasticsearch import Elasticsearch
            import os
            es = Elasticsearch(
                os.getenv("ELASTICSEARCH_URL"),
                api_key=os.getenv("ELASTICSEARCH_API_KEY")
            )
            
            stats_query = {
                "aggs": {
                    "provider_counts": {
                        "terms": {
                            "field": "provider"
                        }
                    }
                },
                "size": 0
            }
            
            response = es.search(index="chat_history", body=stats_query)
            total_chats = response['hits']['total']['value']
            provider_stats = response['aggregations']['provider_counts']['buckets']
            
            stats_text = f"**Chat History Statistics:**\n\n"
            stats_text += f"Total conversations: {total_chats}\n\n"
            stats_text += "**By Provider:**\n"
            for provider in provider_stats:
                stats_text += f"- {provider['key'].upper()}: {provider['doc_count']}\n"
            
            return [TextContent(type="text", text=stats_text)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting stats: {str(e)}")]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="chat-history-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())