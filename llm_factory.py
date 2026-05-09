"""
llm_factory.py
--------------
Central utility to load the correct LLM and embedding model
based on the LLM_PROVIDER env variable.

Supported providers:
  - groq   : Groq free-tier (llama3-8b-8192)
  - openai : OpenAI API    (gpt-4o-mini recommended)
  - ollama : Local Ollama  (llama3)
"""

import os
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()


def get_llm(temperature: float = 0.7):
    """Return a LangChain chat model based on the configured provider."""

    if PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model=os.getenv("GROQ_MODEL", "llama3-8b-8192"),
            temperature=temperature,
        )

    elif PROVIDER == "openai":
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=temperature,
            )
        except ImportError:
            raise ValueError("langchain_openai package not installed.")

    elif PROVIDER == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3"),
            temperature=temperature,
        )

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: {PROVIDER!r}. "
            "Choose 'groq', 'openai', or 'ollama'."
        )


def get_embeddings():
    """
    Return a LangChain embeddings model.

    Always uses sentence-transformers locally — no paid embedding API needed.
    Model downloads automatically on first run (~90 MB).
    """
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )