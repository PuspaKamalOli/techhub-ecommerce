"""
Configuration management for the agentic chatbot.
"""
import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class RAGConfig:
    """Configuration for RAG (Retrieval Augmented Generation) components."""
    knowledge_base_file: str = "speech.txt"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    retrieval_k: int = 3


@dataclass
class LLMConfig:
    """Configuration for LLM (Large Language Model) components."""
    model_name: str = "llama-3.3-70b-versatile"
    ollama_model: str = "qwen2.5:3b"
    use_ollama: bool = True
    temperature: float = 0.3
    max_tokens: int = 500





class ChatbotConfig:
    """Main configuration class."""

    def __init__(self):
        self.rag = RAGConfig()
        self.llm = LLMConfig()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.secret_key = os.getenv("SECRET_KEY")

        if not self.llm.use_ollama and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables. Please set it in .env file.")

    def get_knowledge_base_path(self) -> Path:
        """Get the full path to the knowledge base file."""
        base_dir = Path(__file__).resolve().parent
        return base_dir / self.rag.knowledge_base_file

