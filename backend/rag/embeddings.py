from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from backend.config import get_settings


@lru_cache
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=get_settings().embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
