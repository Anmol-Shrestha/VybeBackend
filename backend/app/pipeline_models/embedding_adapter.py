from abc import ABC, abstractmethod

class EmbeddingAdapter(ABC):
    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        pass
