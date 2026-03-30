"""
RAG Service - Handles Retrieval Augmented Generation operations.
Single Responsibility: Only responsible for RAG operations.
"""
from pathlib import Path
from typing import List, Optional
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from AI.config import RAGConfig
from langchain_huggingface import HuggingFaceEmbeddings


class RAGService:
    """
    Service for RAG (Retrieval Augmented Generation) operations.
    Handles document loading, embedding, and retrieval.
    """
    
    def __init__(self, config: RAGConfig, knowledge_base_path: Path):
        self.config = config
        self.knowledge_base_path = knowledge_base_path
        self.retriever = None
        self._initialize()
    
    def _initialize(self):
        """Initialize RAG components."""
        if not self.knowledge_base_path.exists():
            raise FileNotFoundError(
                f"Knowledge base file not found at {self.knowledge_base_path}"
            )
        
        # Load documents
        loader = TextLoader(str(self.knowledge_base_path))
        docs = loader.load()
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )
        documents = text_splitter.split_documents(docs)
        
        # Initialize embeddings
        embedding_model = HuggingFaceEmbeddings(
            model_name=self.config.embedding_model
        )
        
        # Create vector store
        vectorstore = FAISS.from_documents(documents, embedding_model)
        self.retriever = vectorstore.as_retriever(
            search_kwargs={"k": self.config.retrieval_k}
        )
    
    def retrieve_context(self, query: str, limit: Optional[int] = None) -> str:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: Search query
            limit: Maximum number of documents to retrieve (uses config default if None)
            
        Returns:
            Concatenated context from retrieved documents
        """
        if self.retriever is None:
            return ""
        
        try:
            docs = self.retriever.invoke(query)
            if limit:
                docs = docs[:limit]
            return "\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"RAG retrieval error: {str(e)}")
            return ""
    
    def retrieve_documents(self, query: str, limit: Optional[int] = None) -> List[Document]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            limit: Maximum number of documents to retrieve
            
        Returns:
            List of retrieved documents
        """
        if self.retriever is None:
            return []
        
        try:
            docs = self.retriever.invoke(query)
            if limit:
                docs = docs[:limit]
            return docs
        except Exception as e:
            print(f"RAG retrieval error: {str(e)}")
            return []

