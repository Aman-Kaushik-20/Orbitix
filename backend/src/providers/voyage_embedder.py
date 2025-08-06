import logging
from typing import List

import voyageai
from neo4j_graphrag.embeddings.base import Embedder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoyageEmbeddings(Embedder):
    """
    Embedder class for Voyage AI using the official python client for text embeddings.
    """

    def __init__(self, model_name: str = "voyage-3-large", api_key: str = None):
        super().__init__()
        self.model_name = model_name
        
        if not api_key:
            raise ValueError("Voyage AI API key is required.")
            
        self.client = voyageai.Client(api_key=api_key)
        logger.info(f"✅ Initialized VoyageEmbeddings with text model: {self.model_name}")

    def embed_query(self, text: str, new_model_name:str|None=None) -> List[float]:
        """
        Embed a single text query using the standard text embedding model.
        """
        if new_model_name:
            self.model_name=new_model_name

        try:
            result = self.client.embed([text], model=self.model_name, input_type="query")
            return result.embeddings[0]
        except Exception as e:
            logger.error(f"❌ Voyage AI API error during text query embedding: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of text documents using the standard text embedding model.
        """
        try:
            result = self.client.embed(texts, model=self.model_name, input_type="document")
            return result.embeddings
        except Exception as e:
            logger.error(f"❌ Voyage AI API error during text document embedding: {e}")
            raise
