import base64

from openai import OpenAI

from backend.app.core.config import settings


class OpenAIImageEmbeddingService:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError('OpenAI API key not configured')
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model

    def create_embedding(self, image_bytes: bytes, content_type: str) -> list[float]:
        image_payload = base64.b64encode(image_bytes).decode('utf-8')
        data_url = f'data:{content_type};base64,{image_payload}'
        response = self.client.embeddings.create(model=self.model, input=data_url)
        return response.data[0].embedding
