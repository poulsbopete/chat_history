# chat_history.py

import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
from elasticsearch import Elasticsearch
from typing import Optional, Dict, Any, List

load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

es = Elasticsearch(
    os.getenv("ELASTICSEARCH_URL"),
    api_key=os.getenv("ELASTICSEARCH_API_KEY")
)

class ChatHistoryManager:
    def __init__(self):
        self.index_name = "chat_history"
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        if not es.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "provider": {"type": "keyword"},
                        "query": {"type": "text"},
                        "response": {"type": "text"},
                        "embedding": {
                            "type": "dense_vector",
                            "dims": 1536
                        }
                    }
                }
            }
            es.indices.create(index=self.index_name, body=mapping)
    
    def _get_embedding(self, text: str) -> List[float]:
        emb = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        ).data[0].embedding
        return emb
    
    def index_chat(self, query: str, response: str, provider: str):
        embedding = self._get_embedding(query + "\n" + response)
        
        doc = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "query": query,
            "response": response,
            "embedding": embedding
        }
        es.index(index=self.index_name, document=doc)
    
    def search_similar_chats(self, query: str, size: int = 5) -> List[Dict]:
        query_embedding = self._get_embedding(query)
        
        search_body = {
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": query_embedding}
                    }
                }
            },
            "size": size,
            "_source": ["timestamp", "provider", "query", "response"]
        }
        
        response = es.search(index=self.index_name, body=search_body)
        return [hit["_source"] for hit in response["hits"]["hits"]]
    
    def ask_openai(self, question: str) -> str:
        completion = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": question}]
        )
        response = completion.choices[0].message.content
        self.index_chat(question, response, "openai")
        return response
    
    def ask_anthropic(self, question: str) -> str:
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[{"role": "user", "content": question}]
        )
        response = message.content[0].text
        self.index_chat(question, response, "anthropic")
        return response
    
    def ask_google(self, question: str) -> str:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(question)
        response_text = response.text
        self.index_chat(question, response_text, "google")
        return response_text

if __name__ == "__main__":
    manager = ChatHistoryManager()
    
    q = "How do I configure my ingest pipeline?"
    print(f"Question: {q}")
    
    # Test OpenAI
    print("\n--- OpenAI Response ---")
    openai_answer = manager.ask_openai(q)
    print(openai_answer)
    
    # Search for similar past conversations
    print("\n--- Similar Past Conversations ---")
    similar = manager.search_similar_chats(q, size=3)
    for i, chat in enumerate(similar, 1):
        print(f"{i}. [{chat['provider']}] {chat['query'][:50]}...")
        print(f"   {chat['response'][:100]}...")
        print()