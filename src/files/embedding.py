
import os
from abc import ABC, abstractmethod
from typing import List
from openai import OpenAI


class Embedder(ABC):
    @abstractmethod
    def embed(self, texts: List[str]) -> List[list]:
        pass


class SentenceTransformerEmbedder(Embedder):
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str | None = None
    ):
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
        self.model = model

    def embed(self, texts: List[str]) -> List[list]:
        if not texts:
            return []

        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )

        # Keep same return shape as SentenceTransformer
        return [item.embedding for item in response.data]
