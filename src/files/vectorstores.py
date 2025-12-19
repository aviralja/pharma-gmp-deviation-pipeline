from abc import ABC, abstractmethod
from typing import List, Dict, Any
# from qdrant_client import QdrantClient
# from qdrant_client.models import Distance, VectorParams
# import chromadb
# from chromadb.config import Settings
from pymongo import MongoClient
from typing import List, Dict
import numpy as np


from files.embedding import SentenceTransformerEmbedder
import os
from dotenv import load_dotenv
load_dotenv()
  # reads .env file

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

class VectorStore(ABC):

    @abstractmethod
    def add(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        pass

    @abstractmethod
    def query(self, text: str, top_k: int):
        pass




# class QdrantStore(VectorStore):
#     def __init__(self, collection: str):
#         self.client = QdrantClient(path="./qdrant_data")
#         self.collection = collection

#         self.client.recreate_collection(
#             collection_name=collection,
#             vectors_config=VectorParams(size=768, distance=Distance.COSINE),
#         )

#     def add(self, texts, metadatas, ids):
#         self.client.upload_collection(
#             collection_name=self.collection,
#             documents=texts,
#             metadata=metadatas,
#             ids=ids
#         )

#     def query(self, text, top_k=5):
#         return self.client.search(
#             collection_name=self.collection,
#             query_text=text,
#             limit=top_k
#         )

# # your interface


# class ChromaStore(VectorStore):
#     def __init__(self, collection_name: str):
#         self.client = chromadb.PersistentClient(
#             path="./chroma_data"
#         )

        

#         self.collection = self.client.get_or_create_collection(
#             name=collection_name
#         )

#     def add(self, texts, metadatas, ids):
#         self.collection.add(
#             documents=texts,
#             metadatas=metadatas,
#             ids=ids
#         )

#     def query(self, text, top_k=5):
#         return self.collection.query(
#             query_texts=[text],
#             n_results=top_k
#         )
    
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


class MongoVectorStore(VectorStore):
    def __init__(
        self
    ):
        self.client = MongoClient(MONGO_URI)
        self.collection = self.client[MONGO_DB][MONGO_COLLECTION]
        self.embedder = SentenceTransformerEmbedder()

    def add(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        embeddings = self.embedder.embed(texts)

        docs = []
        for i in range(len(texts)):
            docs.append({
                "_id": ids[i],
                "text": texts[i],
                "embedding": embeddings[i],
                "metadata": metadatas[i]
            })

        self.collection.insert_many(docs)

    def query(self, text: str, top_k: int = 5):
        query_vector = self.embedder.embed([text])[0]

        results = []
        for doc in self.collection.find():
            score = cosine_similarity(query_vector, doc["embedding"])
            results.append({
                "id": doc["_id"],
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": score
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

