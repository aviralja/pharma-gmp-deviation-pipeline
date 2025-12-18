from sentence_transformers import SentenceTransformer

from abc import ABC, abstractmethod
from typing import List

class Embedder(ABC):
    @abstractmethod
    def embed(self, texts: List[str]) -> List[list]:
        pass

class SentenceTransformerEmbedder(Embedder):
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed(self, texts):
        return self.model.encode(
            texts,
            normalize_embeddings=True
        ).tolist()