from abc import ABC, abstractmethod
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import chromadb
from chromadb.config import Settings

class VectorStore(ABC):

    @abstractmethod
    def add(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        pass

    @abstractmethod
    def query(self, text: str, top_k: int):
        pass




class QdrantStore(VectorStore):
    def __init__(self, collection: str):
        self.client = QdrantClient(path="./qdrant_data")
        self.collection = collection

        self.client.recreate_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )

    def add(self, texts, metadatas, ids):
        self.client.upload_collection(
            collection_name=self.collection,
            documents=texts,
            metadata=metadatas,
            ids=ids
        )

    def query(self, text, top_k=5):
        return self.client.search(
            collection_name=self.collection,
            query_text=text,
            limit=top_k
        )

# your interface


class ChromaStore(VectorStore):
    def __init__(self, collection_name: str, use_cloud: bool = True):
        """Initialize ChromaDB client (cloud or local)
        
        Args:
            collection_name: Name of the collection
            use_cloud: If True, uses ChromaDB Cloud; if False, uses local persistent client
        """
        import os
        
        if use_cloud:
            # Use ChromaDB Cloud for production
            self.client = chromadb.CloudClient(
                api_key=os.environ.get('CHROMA_API_KEY'),
                tenant=os.environ.get('CHROMA_TENANT'),
                database=os.environ.get('CHROMA_DATABASE', 'Pharma')
            )
        else:
            # Use local persistent client for development
            self.client = chromadb.PersistentClient(
                path="./chroma_data"
            )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

    def add(self, texts, metadatas, ids):
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, text, top_k=5):
        return self.collection.query(
            query_texts=[text],
            n_results=top_k
        )


class MongoDBStore(VectorStore):
    """MongoDB vector store with embeddings for similarity search"""
    
    def __init__(self, collection_name: str, connection_string: str = None, db_name: str = "pharma_gmp"):
        """
        Initialize MongoDB vector store.
        
        Args:
            collection_name: Name of the MongoDB collection
            connection_string: MongoDB connection URI (e.g., mongodb://localhost:27017/ or MongoDB Atlas URI)
            db_name: Database name
        """
        if connection_string is None:
            connection_string = "mongodb://localhost:27017/"
        
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        
        # Initialize embedding model (384-dim for efficiency)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create index on id field for faster lookups
        self.collection.create_index("id", unique=True)
        
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        return self.model.encode(text).tolist()
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def add(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        """Add documents with embeddings to MongoDB"""
        documents = []
        for text, metadata, doc_id in zip(texts, metadatas, ids):
            embedding = self._get_embedding(text)
            documents.append({
                "id": doc_id,
                "text": text,
                "embedding": embedding,
                "metadata": metadata
            })
        
        # Insert or update documents
        for doc in documents:
            self.collection.replace_one(
                {"id": doc["id"]},
                doc,
                upsert=True
            )
    
    def query(self, text: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Query similar documents using vector similarity.
        Returns format compatible with ChromaDB for easy replacement.
        """
        query_embedding = self._get_embedding(text)
        
        # Get all documents (for small datasets)
        # For large datasets, consider using MongoDB Atlas Vector Search
        all_docs = list(self.collection.find({}, {"_id": 0}))
        
        # Calculate similarities
        similarities = []
        for doc in all_docs:
            similarity = self._cosine_similarity(query_embedding, doc["embedding"])
            similarities.append({
                "id": doc["id"],
                "text": doc["text"],
                "metadata": doc["metadata"],
                "similarity": similarity,
                "distance": 1 - similarity  # Convert to distance metric
            })
        
        # Sort by similarity (descending) and get top_k
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        top_results = similarities[:top_k]
        
        # Format output to match ChromaDB structure
        return {
            "ids": [[r["id"] for r in top_results]],
            "documents": [[r["text"] for r in top_results]],
            "metadatas": [[r["metadata"] for r in top_results]],
            "distances": [[r["distance"] for r in top_results]]
        }
    
    def delete_collection(self):
        """Delete the entire collection"""
        self.collection.drop()
    
    def count(self) -> int:
        """Get count of documents in collection"""
        return self.collection.count_documents({})
