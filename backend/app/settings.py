from pydantic import BaseModel
import os

class Settings(BaseModel):
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "local-384")
    llm_provider: str = os.getenv("LLM_PROVIDER", "stub")  # stub | openai | ollama
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")  # Model to use with Ollama (e.g., qwen2.5:0.5b, llama3.2, mistral, llama2, phi3)
    vector_store: str = os.getenv("VECTOR_STORE", "qdrant")  # qdrant | memory
    collection_name: str = os.getenv("COLLECTION_NAME", "policy_helper")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "700"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "80"))
    data_dir: str = os.getenv("DATA_DIR", "/app/data")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")  # DEBUG | INFO | WARNING | ERROR
    log_file_path: str | None = os.getenv("LOG_FILE_PATH")  # Optional: path to log file (e.g., /app/logs/app.log)

settings = Settings()
