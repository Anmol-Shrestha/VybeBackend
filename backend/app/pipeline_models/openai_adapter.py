from app.pipeline_models.embedding_adapter import EmbeddingAdapter

class OpenAIEmbeddingAdapter(EmbeddingAdapter):
    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    async def embed_query(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
