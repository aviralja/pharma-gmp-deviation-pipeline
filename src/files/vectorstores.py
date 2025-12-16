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
    def __init__(self, collection_name: str):
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
