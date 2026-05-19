from abc import ABC, abstractmethod

class RerankerAdapter(ABC):
    @abstractmethod
    async def rerank(self, query: str, candidates: list[dict]) -> list[dict]:
        pass
